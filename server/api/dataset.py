"""CyberGuard-ID — Dataset Management API Routes.

Endpoints for uploading, previewing, editing labels, and exporting datasets.
"""

from __future__ import annotations

import io
import queue
import subprocess
import sys
import threading
import uuid
from typing import Any

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.services.classifier import ClassifierService

from server.dependencies import get_config, get_project_root

router = APIRouter(prefix="/api/dataset", tags=["dataset"])


class LabelUpdate(BaseModel):
    """Request to update a label for a specific row."""

    row_index: int
    label: str


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(""),
):
    """Upload a labeled CSV dataset for training."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > 50:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    # Validate CSV
    try:
        df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}") from e

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Check for text column
    if "text" not in df.columns:
        text_aliases = ["comment", "komentar", "content", "comment_text", "teks"]
        found = False
        for alias in text_aliases:
            if alias in df.columns:
                df = df.rename(columns={alias: "text"})
                found = True
                break
        if not found:
            raise HTTPException(
                status_code=400,
                detail=f"CSV must have a 'text' column. Found: {list(df.columns)}",
            )

    # Add label column if missing
    if "label" not in df.columns:
        df["label"] = ""

    # Save to data/raw
    data_dir = get_project_root() / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)

    filename = name or file.filename or "dataset.csv"
    if not filename.endswith(".csv"):
        filename += ".csv"

    # Sanitize filename
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
    if not safe_name:
        safe_name = "dataset.csv"

    save_path = data_dir / safe_name
    df.to_csv(save_path, index=False, encoding="utf-8")

    # Compute label stats
    label_counts = {}
    if "label" in df.columns:
        label_counts = df["label"].value_counts(dropna=False).to_dict()
        # Convert NaN key
        label_counts = {str(k) if pd.notna(k) else "unlabeled": int(v) for k, v in label_counts.items()}  # type: ignore
        if "" in label_counts:
            unlabeled = label_counts.pop("", 0)
            label_counts["unlabeled"] = label_counts.get("unlabeled", 0) + unlabeled

    return {
        "filename": safe_name,
        "rows": len(df),
        "columns": list(df.columns),
        "label_distribution": label_counts,
        "message": f"Dataset saved: {safe_name} ({len(df)} rows)",
    }


@router.get("/files")
def list_dataset_files() -> list[dict[str, Any]]:
    """List all dataset files in data/raw."""
    data_dir = get_project_root() / "data" / "raw"
    files = []

    if data_dir.exists():
        for f in sorted(data_dir.rglob("*.csv")):
            try:
                df = pd.read_csv(f, encoding="utf-8", nrows=0)
                with open(f, encoding="utf-8") as fp:
                    row_count = sum(1 for _ in fp) - 1
                files.append(
                    {
                        "filename": f.relative_to(data_dir).as_posix(),
                        "size_kb": round(f.stat().st_size / 1024, 1),
                        "rows": max(row_count, 0),
                        "columns": list(df.columns),
                        "modified": f.stat().st_mtime,
                    }
                )
            except Exception:
                files.append(
                    {
                        "filename": f.relative_to(data_dir).as_posix(),
                        "size_kb": round(f.stat().st_size / 1024, 1),
                        "rows": 0,
                        "columns": [],
                        "modified": f.stat().st_mtime,
                    }
                )

    return files


@router.get("/files/{filename:path}/preview")
def preview_dataset(
    filename: str,
    page: int = 1,
    per_page: int = 50,
) -> dict[str, Any]:
    """Preview a dataset with pagination."""
    data_dir = get_project_root() / "data" / "raw"
    file_path = data_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found")

    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {e}") from e

    df.columns = df.columns.str.strip().str.lower()

    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    page_df = df.iloc[start:end]

    # Convert to records, handling NaN
    rows = []
    for idx, row in page_df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                record[col] = ""
            else:
                record[col] = str(val) if not isinstance(val, (int, float)) else val
        record["_index"] = int(idx)
        rows.append(record)

    # Label distribution
    label_counts = {}
    if "label" in df.columns:
        counts = df["label"].value_counts(dropna=False)
        label_counts = {str(k) if pd.notna(k) else "unlabeled": int(v) for k, v in counts.items()}  # type: ignore
        if "" in label_counts:
            unlabeled = label_counts.pop("", 0)
            label_counts["unlabeled"] = label_counts.get("unlabeled", 0) + unlabeled

    return {
        "filename": filename,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
        "columns": list(df.columns),
        "rows": rows,
        "label_distribution": label_counts,
    }


@router.put("/files/{filename:path}/label")
def update_label(filename: str, update: LabelUpdate):
    """Update the label for a specific row in a dataset."""
    config = get_config()
    valid_labels = set(config.training_labels)

    if update.label and update.label not in valid_labels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid label: '{update.label}'. Valid labels: {sorted(valid_labels)}",
        )

    data_dir = get_project_root() / "data" / "raw"
    file_path = data_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found")

    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {e}") from e

    df.columns = df.columns.str.strip().str.lower()

    if "label" not in df.columns:
        df["label"] = ""

    if update.row_index < 0 or update.row_index >= len(df):
        raise HTTPException(status_code=400, detail=f"Row index out of range: {update.row_index}")

    df.at[update.row_index, "label"] = update.label
    df.to_csv(file_path, index=False, encoding="utf-8")

    return {
        "message": f"Label updated for row {update.row_index}",
        "row_index": update.row_index,
        "label": update.label,
    }


@router.get("/files/{filename:path}/export")
def export_labeled_dataset(filename: str):
    """Export the labeled dataset as a downloadable CSV."""
    data_dir = get_project_root() / "data" / "raw"
    file_path = data_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found")

    return StreamingResponse(
        open(file_path, "rb"),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


_train_queues: dict[str, queue.Queue] = {}


@router.post("/train")
def start_training():
    """Start the training process."""
    job_id = str(uuid.uuid4())
    q = queue.Queue()
    _train_queues[job_id] = q

    def run_train():
        try:
            q.put({"step": 1, "message": "Memulai pelatihan model...", "total_steps": 5})
            
            # Re-load or spawn train_model.py
            process = subprocess.Popen(
                [sys.executable, "scripts/train_model.py"],
                cwd=str(get_project_root()),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                if "Preprocessing texts" in line:
                    q.put({"step": 2, "message": "Memproses teks (Preprocessing)...", "total_steps": 5})
                elif "Building pipeline" in line:
                    q.put({"step": 3, "message": "Membangun pipeline model...", "total_steps": 5})
                elif "Evaluating on test set" in line:
                    q.put({"step": 4, "message": "Mengevaluasi hasil (Test Set)...", "total_steps": 5})
                elif "Saving model" in line:
                    q.put({"step": 5, "message": "Menyimpan model ke disk...", "total_steps": 5})

            process.wait()

            if process.returncode != 0:
                q.put({"step": -1, "message": f"Error: Gagal melatih model (code {process.returncode})"})
            else:
                q.put({"step": 100, "message": "Selesai!"})

        except Exception as e:
            q.put({"step": -1, "message": f"Error: {str(e)}"})
        finally:
            q.put(None)

    threading.Thread(target=run_train, daemon=True).start()

    return {"job_id": job_id, "status": "started"}


@router.get("/train/{job_id}/progress")
def stream_training_progress(job_id: str):
    """Stream training progress via SSE."""
    q = _train_queues.get(job_id)
    if not q:
        raise HTTPException(status_code=404, detail="Job not found")

    def event_stream():
        try:
            while True:
                item = q.get()
                if item is None:
                    break
                
                # Format to JSON string
                import json
                data = json.dumps(item)
                yield f"data: {data}\n\n"
                
                if item.get("step") in (-1, 100):
                    break
        finally:
            _train_queues.pop(job_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
