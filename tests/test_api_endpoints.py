"""Verify that FastAPI server endpoints and router mounting work correctly."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from server.dependencies import get_storage
from server.main import app, RUNTIME_API_KEY
from src.core.schemas import AnalysisRun, Comment, Prediction

client = TestClient(app, headers={"x-api-key": RUNTIME_API_KEY})


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "cyberguard-id"}


def test_label_schema():
    res = client.get("/api/system/labels")
    assert res.status_code == 200
    data = res.json()
    assert len(data["categories"]) >= 5
    assert "normal" in data["training_labels"]


def test_dataset_files():
    res = client.get("/api/dataset/files")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_list_analyses():
    res = client.get("/api/analyses")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_spa_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "<title>CyberGuard-ID" in res.text


def test_system_status():
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "api_status" in data
    assert "model" in data


def test_comment_review_flow():
    import uuid

    storage = get_storage()
    unique_suffix = uuid.uuid4().hex[:8]
    run_id = f"rev_{unique_suffix}"
    comment_id = f"c_{unique_suffix}"

    # Create temporary analysis and comment
    storage.create_analysis(
        AnalysisRun(
            id=run_id,
            name="Review Test Run",
            source_type="CSV",
            status="COMPLETED",
        )
    )
    storage.save_comments(
        [
            Comment(
                id=comment_id,
                analysis_id=run_id,
                original_text="konten ujaran kebencian parah",
                normalized_text="konten ujaran kebencian parah",
            )
        ]
    )
    storage.save_predictions(
        [
            Prediction(
                id=f"p_{unique_suffix}",
                comment_id=comment_id,
                predicted_label="hate_speech_strong",
                confidence=0.88,
                risk_level="high",
            )
        ]
    )

    # Review endpoint
    res = client.post(
        f"/api/analysis/{run_id}/comments/{comment_id}/review",
        json={
            "reviewer_label": "hate_speech",
            "reviewer_risk_level": "high",
            "decision": "CONFIRMED",
            "note": "Sudah diverifikasi moderator",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["comment_id"] == comment_id

    # Cleanup
    del_res = client.delete(f"/api/analysis/{run_id}")
    assert del_res.status_code == 200


if __name__ == "__main__":
    print("Testing health...")
    test_health()
    print("Testing label schema...")
    test_label_schema()
    print("Testing dataset files...")
    test_dataset_files()
    print("Testing list analyses...")
    test_list_analyses()
    print("Testing spa root...")
    test_spa_root()
    print("Testing system status...")
    test_system_status()
    print("Testing comment review...")
    test_comment_review_flow()
    print("All FastAPI endpoints verified successfully!")
