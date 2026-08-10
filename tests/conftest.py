"""CyberGuard-ID — Test Configuration and Fixtures."""

from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path

import pytest

# Set test environment before importing config
os.environ["APP_ENV"] = "test"
os.environ["ANONYMIZATION_SALT"] = "test-salt-value"
os.environ["YOUTUBE_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def config(project_root: Path):
    """Load test configuration."""
    from src.core.config import load_config

    return load_config()


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    from src.services.storage import StorageService

    storage = StorageService(db_path)
    storage.initialize()

    yield storage

    storage.close()
    with contextlib.suppress(OSError):
        db_path.unlink()


@pytest.fixture
def sample_comments():
    """Generate sample Comment objects for testing."""
    from src.core.schemas import Comment

    return [
        Comment(
            id="c001",
            analysis_id="a001",
            external_comment_id="ext001",
            author_hash="USER_ABC123",
            original_text="Terima kasih informasinya.",
            normalized_text="terima kasih informasinya.",
            published_at="2026-01-15T10:00:00Z",
            is_reply=False,
        ),
        Comment(
            id="c002",
            analysis_id="a001",
            external_comment_id="ext002",
            author_hash="USER_DEF456",
            original_text="Muka lo jelek banget",
            normalized_text="muka lo jelek banget",
            published_at="2026-01-15T11:00:00Z",
            is_reply=False,
        ),
        Comment(
            id="c003",
            analysis_id="a001",
            external_comment_id="ext003",
            author_hash="USER_GHI789",
            original_text="Gue bunuh lo kalau ketemu",
            normalized_text="gue bunuh lo kalau ketemu",
            published_at="2026-01-15T12:00:00Z",
            is_reply=False,
        ),
        Comment(
            id="c004",
            analysis_id="a001",
            external_comment_id="ext004",
            author_hash="USER_JKL012",
            original_text="Anjir apa banget dah",
            normalized_text="anjir apa banget dah",
            published_at="2026-01-15T13:00:00Z",
            is_reply=False,
        ),
    ]


@pytest.fixture
def sample_predictions():
    """Generate sample Prediction objects."""
    from src.core.schemas import Prediction, VerificationStatus

    return [
        Prediction(
            id="p001",
            comment_id="c001",
            predicted_label="normal_konstruktif",
            confidence=0.92,
            second_label="kritik_wajar",
            second_confidence=0.05,
            margin=0.87,
            verification_status=VerificationStatus.MODEL_VERIFIED.value,
            base_risk_score=0,
        ),
        Prediction(
            id="p002",
            comment_id="c002",
            predicted_label="personal_harassment",
            confidence=0.78,
            second_label="bahasa_kasar",
            second_confidence=0.12,
            margin=0.66,
            verification_status=VerificationStatus.RECOMMENDED_REVIEW.value,
            base_risk_score=2,
        ),
        Prediction(
            id="p003",
            comment_id="c003",
            predicted_label="threat_intimidation",
            confidence=0.63,
            second_label="personal_harassment",
            second_confidence=0.20,
            margin=0.43,
            verification_status=VerificationStatus.MANDATORY_REVIEW.value,
            base_risk_score=5,
        ),
        Prediction(
            id="p004",
            comment_id="c004",
            predicted_label="bahasa_kasar",
            confidence=0.45,
            second_label="normal_konstruktif",
            second_confidence=0.40,
            margin=0.05,
            verification_status=VerificationStatus.UNCERTAIN.value,
            base_risk_score=1,
        ),
    ]


@pytest.fixture
def preprocessor():
    """Create a TextPreprocessor instance."""
    from src.services.preprocessing import TextPreprocessor

    slang = {"gw": "saya", "lo": "kamu", "gblk": "bodoh", "bgt": "banget"}
    return TextPreprocessor(slang)
