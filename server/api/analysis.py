"""CyberGuard-ID — Analysis API Routes.

Handles YouTube URL analysis, CSV upload analysis, analysis listing,
and real-time progress streaming via Server-Sent Events.
"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
import uuid
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server.dependencies import get_config, get_engine, get_storage
from src.core.exceptions import CyberGuardError
from src.core.logging_config import get_logger
from src.core.schemas import Review

logger = get_logger("analysis_api")
router = APIRouter(prefix="/api", tags=["analysis"])

# In-memory progress queues for SSE streaming
_progress_queues: dict[str, queue.Queue] = {}


class CommentReviewRequest(BaseModel):
    """Request body for human review of a single comment."""

    reviewer_label: str
    reviewer_risk_level: str = "low"
    decision: str = "CONFIRMED"
    note: str = ""


class AnalyzeRequest(BaseModel):
    """Request body for YouTube URL analysis."""

    url: str = Field(..., description="YouTube video URL")
    name: str = Field("", description="Analysis name (auto-generated if empty)")
    max_comments: int = Field(5000, ge=10, le=10000, description="Max top-level comments")
    include_replies: bool = Field(True, description="Include reply threads")


class AnalyzeResponse(BaseModel):
    """Response after starting an analysis."""

    analysis_id: str
    status: str
    message: str


class AnalysisListItem(BaseModel):
    """Summary item for analysis listing."""

    id: str
    name: str
    source_type: str
    status: str
    started_at: str
    total_comments: int
    harmful_count: int
    high_count: int
    critical_count: int
    video_title: str = ""


class CommentItem(BaseModel):
    """A comment with its prediction data."""

    id: str
    author_hash: str
    original_text: str
    normalized_text: str
    published_at: str
    like_count: int
    is_reply: bool
    predicted_label: str
    confidence: float
    second_label: str
    margin: float
    verification_status: str
    total_risk_score: int
    risk_level: str
    review_decision: str | None = None
    reviewer_label: str | None = None


def _make_progress_callback(analysis_id: str):
    """Create a progress callback that pushes to the SSE queue."""
    q = queue.Queue()
    _progress_queues[analysis_id] = q

    def callback(step: int, message: str):
        q.put({"step": step, "message": message, "total_steps": 9})

    return callback


def _run_youtube_analysis_thread(
    analysis_id: str,
    url: str,
    name: str,
    max_comments: int,
    include_replies: bool,
) -> None:
    """Run YouTube analysis in a background thread."""
    q = _progress_queues.get(analysis_id)
    try:
        engine = get_engine()
        def callback(step: int, message: str):
            if q:
                q.put({"step": step, "message": message, "total_steps": 9})

        engine.run_youtube_analysis(
            url=url,
            name=name,
            max_comments=max_comments,
            include_replies=include_replies,
            progress_callback=callback,
            analysis_id=analysis_id,
        )
        if q:
            q.put({"step": 9, "message": "Analisis selesai!", "total_steps": 9, "done": True})
    except CyberGuardError as e:
        if q:
            q.put({"error": e.user_message, "done": True})
    except Exception as e:
        if q:
            q.put({"error": str(e)[:500], "done": True})


def _run_csv_analysis_thread(
    analysis_id: str,
    file_content: bytes,
    name: str,
) -> None:
    """Run CSV analysis in a background thread."""
    q = _progress_queues.get(analysis_id)
    try:
        engine = get_engine()
        def callback(step: int, message: str):
            if q:
                q.put({"step": step, "message": message, "total_steps": 9})

        engine.run_csv_analysis(
            file_content=file_content,
            name=name,
            progress_callback=callback,
            analysis_id=analysis_id,
        )
        if q:
            q.put({"step": 9, "message": "Analisis selesai!", "total_steps": 9, "done": True})
    except CyberGuardError as e:
        if q:
            q.put({"error": e.user_message, "done": True})
    except Exception as e:
        if q:
            q.put({"error": str(e)[:500], "done": True})


@router.post("/analyze", response_model=AnalyzeResponse)
async def start_analysis(req: AnalyzeRequest):
    """Start a new YouTube URL analysis."""
    config = get_config()

    if not config.api_status.youtube_available:
        raise HTTPException(
            status_code=400,
            detail="YouTube API key belum dikonfigurasi. Set YOUTUBE_API_KEY di .env",
        )

    if not config.api_status.model_available:
        raise HTTPException(
            status_code=400,
            detail="Model belum tersedia. Jalankan 'python run.py --train' untuk melatih model.",
        )

    name = req.name or f"Analisis {req.url[:50]}"
    analysis_id = uuid.uuid4().hex[:16]

    # Create progress queue for SSE
    _make_progress_callback(analysis_id)

    # Run in background thread (non-blocking)
    thread = threading.Thread(
        target=_run_youtube_analysis_thread,
        args=(analysis_id, req.url, name, req.max_comments, req.include_replies),
        daemon=True,
    )
    thread.start()

    return AnalyzeResponse(
        analysis_id=analysis_id,
        status="STARTED",
        message=f"Analisis dimulai untuk {req.url}",
    )


@router.post("/analyze/csv", response_model=AnalyzeResponse)
async def start_csv_analysis(
    file: UploadFile = File(...),
    name: str = Form(""),
):
    """Start a new CSV file analysis."""
    config = get_config()

    if not config.api_status.model_available:
        raise HTTPException(
            status_code=400,
            detail="Model belum tersedia. Jalankan 'python run.py --train' untuk melatih model.",
        )

    file_content = await file.read()
    analysis_name = name or f"CSV: {file.filename}"
    analysis_id = uuid.uuid4().hex[:16]

    # Create progress queue for SSE
    _make_progress_callback(analysis_id)

    # Run in background thread
    thread = threading.Thread(
        target=_run_csv_analysis_thread,
        args=(analysis_id, file_content, analysis_name),
        daemon=True,
    )
    thread.start()

    return AnalyzeResponse(
        analysis_id=analysis_id,
        status="STARTED",
        message=f"Analisis CSV dimulai: {file.filename}",
    )


@router.get("/analyze/{analysis_id}/progress")
async def stream_progress(analysis_id: str):
    """Stream analysis progress via Server-Sent Events."""
    q = _progress_queues.get(analysis_id)
    if not q:
        raise HTTPException(status_code=404, detail="Analysis not found or already completed")

    async def event_generator():
        try:
            while True:
                try:
                    data = q.get(timeout=0.5)
                    yield f"data: {json.dumps(data)}\n\n"
                    if data.get("done"):
                        break
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield ": heartbeat\n\n"
                await asyncio.sleep(0.1)
        finally:
            # Cleanup
            _progress_queues.pop(analysis_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/analyses")
def list_analyses(limit: int = 50) -> list[dict[str, Any]]:
    """List all analyses ordered by most recent."""
    storage = get_storage()
    analyses = storage.list_analyses(limit=limit)
    return [
        {
            "id": a.id,
            "name": a.name,
            "source_type": a.source_type,
            "status": a.status,
            "started_at": a.started_at,
            "completed_at": a.completed_at,
            "total_comments": a.total_comments,
            "harmful_count": a.harmful_count,
            "high_count": a.high_count,
            "critical_count": a.critical_count,
            "uncertain_count": a.uncertain_count,
            "video_title": a.video_title,
            "video_id": a.video_id,
            "channel_title": a.channel_title,
            "error_message": a.error_message,
        }
        for a in analyses
    ]


@router.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: str) -> dict[str, Any]:
    """Get detailed analysis information."""
    storage = get_storage()
    analysis = storage.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    stats = storage.get_analysis_stats(analysis_id)
    clusters = storage.get_clusters(analysis_id)

    return {
        "analysis": {
            "id": analysis.id,
            "name": analysis.name,
            "source_type": analysis.source_type,
            "source_url": analysis.source_url,
            "video_id": analysis.video_id,
            "video_title": analysis.video_title,
            "channel_title": analysis.channel_title,
            "status": analysis.status,
            "started_at": analysis.started_at,
            "completed_at": analysis.completed_at,
            "total_comments": analysis.total_comments,
            "harmful_count": analysis.harmful_count,
            "uncertain_count": analysis.uncertain_count,
            "high_count": analysis.high_count,
            "critical_count": analysis.critical_count,
            "model_version": analysis.model_version,
            "error_message": analysis.error_message,
        },
        "stats": {
            "total_comments": stats.total_comments,
            "category_distribution": stats.category_distribution,
            "risk_distribution": stats.risk_distribution,
            "verification_distribution": stats.verification_distribution,
            "harmful_count": stats.harmful_count,
            "uncertain_count": stats.uncertain_count,
            "high_count": stats.high_count,
            "critical_count": stats.critical_count,
            "cluster_count": stats.cluster_count,
            "reviewed_count": stats.reviewed_count,
            "repeated_attack_clusters": stats.repeated_attack_clusters,
        },
        "clusters": [
            {
                "id": c.id,
                "cluster_key": c.cluster_key,
                "dominant_label": c.dominant_label,
                "comment_count": c.comment_count,
                "unique_author_count": c.unique_author_count,
                "average_similarity": c.average_similarity,
                "risk_level": c.risk_level,
                "indication_level": c.indication_level,
            }
            for c in clusters
        ],
    }


@router.get("/analysis/{analysis_id}/comments")
def get_analysis_comments(
    analysis_id: str,
    page: int = 1,
    per_page: int = 50,
    risk_level: str = "",
    label: str = "",
    search: str = "",
) -> dict[str, Any]:
    """Get paginated comments with predictions for an analysis."""
    storage = get_storage()
    analysis = storage.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    predictions = storage.get_predictions(analysis_id)

    # Apply filters
    if risk_level:
        predictions = [p for p in predictions if p.get("risk_level") == risk_level]
    if label:
        predictions = [p for p in predictions if p.get("predicted_label") == label]
    if search:
        search_lower = search.lower()
        predictions = [p for p in predictions if search_lower in (p.get("original_text", "") or "").lower()]

    total = len(predictions)
    start = (page - 1) * per_page
    end = start + per_page
    page_data = predictions[start:end]

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
        "comments": [
            {
                "id": p.get("id", ""),
                "author_hash": p.get("author_hash", ""),
                "original_text": p.get("original_text", ""),
                "normalized_text": p.get("normalized_text", ""),
                "published_at": p.get("published_at", ""),
                "like_count": p.get("like_count", 0),
                "is_reply": bool(p.get("is_reply", False)),
                "predicted_label": p.get("predicted_label", ""),
                "confidence": p.get("confidence", 0),
                "second_label": p.get("second_label", ""),
                "second_confidence": p.get("second_confidence", 0),
                "margin": p.get("margin", 0),
                "verification_status": p.get("verification_status", ""),
                "base_risk_score": p.get("base_risk_score", 0),
                "additional_risk_score": p.get("additional_risk_score", 0),
                "total_risk_score": p.get("total_risk_score", 0),
                "risk_level": p.get("risk_level", ""),
                "review_decision": p.get("review_decision"),
                "reviewer_label": p.get("reviewer_label"),
            }
            for p in page_data
        ],
    }


@router.delete("/analysis/{analysis_id}")
def delete_analysis(analysis_id: str):
    """Delete an analysis and its associated data."""
    storage = get_storage()
    deleted = storage.delete_analysis(analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {"message": "Analysis deleted", "id": analysis_id}


@router.delete("/analyses")
def clear_all_analyses():
    """Delete all analyses history."""
    storage = get_storage()
    count = storage.clear_all_analyses()
    return {"message": "All analyses cleared", "deleted_count": count}


@router.get("/adaptive/stats")
def get_adaptive_stats():
    """Get active learning and continuous adaptation stats."""
    from src.services.adaptive_learning import AdaptiveLearningService

    config = get_config()
    adaptive_service = AdaptiveLearningService(config.db_path)
    return adaptive_service.get_stats()


@router.post("/analysis/{analysis_id}/comments/{comment_id}/review")
def review_comment(
    analysis_id: str,
    comment_id: str,
    req: CommentReviewRequest,
) -> dict[str, Any]:
    """Save human review decision for a comment in an analysis and train adaptive memory."""
    storage = get_storage()
    analysis = storage.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    review = Review(
        comment_id=comment_id,
        reviewer_label=req.reviewer_label,
        reviewer_risk_level=req.reviewer_risk_level,
        decision=req.decision,
        note=req.note,
    )
    review_id = storage.save_review(review)

    # Feed human correction into Adaptive Learning Memory
    try:
        from src.services.adaptive_learning import AdaptiveLearningService

        comment = storage.get_comment(comment_id)
        if comment:
            # Find original prediction
            conn = storage._get_connection()
            pred_row = conn.execute(
                "SELECT predicted_label FROM predictions WHERE comment_id = ?",
                (comment_id,),
            ).fetchone()
            orig_pred = pred_row["predicted_label"] if pred_row else "unknown"

            config = get_config()
            adaptive_service = AdaptiveLearningService(config.db_path)
            adaptive_service.record_human_correction(
                original_text=comment.original_text,
                normalized_text=comment.normalized_text,
                corrected_label=req.reviewer_label,
                original_predicted_label=orig_pred,
                reviewer_decision=req.decision,
                note=req.note,
            )
    except Exception as e:
        logger.warning("Failed to record adaptive learning feedback: %s", e)

    return {
        "status": "success",
        "message": "Review berhasil disimpan dan AI telah mempelajari koreksi ini.",
        "review_id": review_id,
        "comment_id": comment_id,
        "reviewer_label": req.reviewer_label,
        "learned": True,
    }
