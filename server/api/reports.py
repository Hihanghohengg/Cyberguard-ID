"""CyberGuard-ID — Report API Routes.

Endpoints for retrieving, downloading, and regenerating analysis reports.
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from server.dependencies import get_engine, get_storage

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{analysis_id}")
def get_report_summary(analysis_id: str) -> dict[str, Any]:
    """Get report summary for an analysis."""
    storage = get_storage()
    reports = storage.get_reports(analysis_id)
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found for this analysis")

    report = reports[0]  # Most recent
    summary = {}
    with contextlib.suppress(json.JSONDecodeError, TypeError):
        summary = json.loads(report.summary_json)

    return {
        "id": report.id,
        "analysis_id": report.analysis_id,
        "provider": report.provider,
        "generated_at": report.generated_at,
        "summary": summary,
        "has_html": bool(report.html_path and Path(report.html_path).exists()),
        "has_csv": bool(report.csv_path and Path(report.csv_path).exists()),
        "has_json": bool(report.json_path and Path(report.json_path).exists()),
    }


@router.get("/{analysis_id}/html")
def download_html_report(analysis_id: str):
    """Download the HTML report file."""
    storage = get_storage()
    reports = storage.get_reports(analysis_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports[0]
    if not report.html_path or not Path(report.html_path).exists():
        raise HTTPException(status_code=404, detail="HTML report file not found")

    return FileResponse(
        report.html_path,
        media_type="text/html",
        filename=f"cyberguard_report_{analysis_id}.html",
    )


@router.get("/{analysis_id}/html/preview")
def preview_html_report(analysis_id: str):
    """Return HTML report content for inline preview."""
    storage = get_storage()
    reports = storage.get_reports(analysis_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports[0]
    if not report.html_path or not Path(report.html_path).exists():
        raise HTTPException(status_code=404, detail="HTML report file not found")

    with open(report.html_path, encoding="utf-8") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content)


@router.get("/{analysis_id}/csv")
def download_csv_report(analysis_id: str):
    """Download the CSV report file."""
    storage = get_storage()
    reports = storage.get_reports(analysis_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports[0]
    if not report.csv_path or not Path(report.csv_path).exists():
        raise HTTPException(status_code=404, detail="CSV report file not found")

    return FileResponse(
        report.csv_path,
        media_type="text/csv",
        filename=f"cyberguard_data_{analysis_id}.csv",
    )


@router.get("/{analysis_id}/json")
def download_json_report(analysis_id: str):
    """Download the JSON report file."""
    storage = get_storage()
    reports = storage.get_reports(analysis_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports[0]
    if not report.json_path or not Path(report.json_path).exists():
        raise HTTPException(status_code=404, detail="JSON report file not found")

    return FileResponse(
        report.json_path,
        media_type="application/json",
        filename=f"cyberguard_report_{analysis_id}.json",
    )


@router.post("/{analysis_id}/regenerate")
def regenerate_report(analysis_id: str):
    """Regenerate reports for an existing analysis."""
    storage = get_storage()
    analysis = storage.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.status not in ("COMPLETED", "WAITING_HUMAN_REVIEW"):
        raise HTTPException(
            status_code=400,
            detail="Analysis must be completed before regenerating reports",
        )

    engine = get_engine()
    engine.regenerate_reports(analysis_id)

    return {"message": "Reports regenerated", "analysis_id": analysis_id}
