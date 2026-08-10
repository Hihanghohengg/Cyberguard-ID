"""Tests for classifier service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from src.core.exceptions import ModelNotFoundError
from src.core.schemas import Prediction, VerificationStatus
from src.services.classifier import ClassifierService


class TestClassifierService:
    """Tests for ClassifierService."""

    def test_model_not_loaded(self, tmp_path):
        """Raises error when model not loaded."""
        svc = ClassifierService(
            model_path=tmp_path / "nonexistent.joblib",
            metadata_path=tmp_path / "meta.json",
        )
        with pytest.raises(ModelNotFoundError):
            svc.predict(["test"], ["id1"])

    def test_model_not_found(self, tmp_path):
        """Raises ModelNotFoundError for missing file."""
        svc = ClassifierService(
            model_path=tmp_path / "nonexistent.joblib",
            metadata_path=tmp_path / "meta.json",
        )
        with pytest.raises(ModelNotFoundError):
            svc.load()

    def test_empty_input(self, tmp_path):
        """Empty input returns empty list."""
        svc = ClassifierService(
            model_path=tmp_path / "model.joblib",
            metadata_path=tmp_path / "meta.json",
        )
        svc._loaded = True
        svc.pipeline = MagicMock()
        result = svc.predict([], [])
        assert result == []

    def test_verification_model_verified(self):
        """High confidence + strong margin -> MODEL_VERIFIED."""
        svc = ClassifierService(
            model_path=Path("."),
            metadata_path=Path("."),
        )
        status = svc._get_verification_status(0.90, 0.20)
        assert status == VerificationStatus.MODEL_VERIFIED.value

    def test_verification_recommended_review(self):
        """Moderate confidence -> RECOMMENDED_REVIEW."""
        svc = ClassifierService(
            model_path=Path("."),
            metadata_path=Path("."),
        )
        status = svc._get_verification_status(0.75, 0.12)
        assert status == VerificationStatus.RECOMMENDED_REVIEW.value

    def test_verification_mandatory_review(self):
        """Low-moderate confidence -> MANDATORY_REVIEW."""
        svc = ClassifierService(
            model_path=Path("."),
            metadata_path=Path("."),
        )
        status = svc._get_verification_status(0.60, 0.12)
        assert status == VerificationStatus.MANDATORY_REVIEW.value

    def test_verification_uncertain_low_confidence(self):
        """Low confidence -> UNCERTAIN."""
        svc = ClassifierService(
            model_path=Path("."),
            metadata_path=Path("."),
        )
        status = svc._get_verification_status(0.40, 0.15)
        assert status == VerificationStatus.UNCERTAIN.value

    def test_verification_uncertain_low_margin(self):
        """Low margin -> UNCERTAIN even with ok confidence."""
        svc = ClassifierService(
            model_path=Path("."),
            metadata_path=Path("."),
        )
        status = svc._get_verification_status(0.60, 0.05)
        assert status == VerificationStatus.UNCERTAIN.value

    def test_uncertain_abstention(self):
        """UNCERTAIN status maps to 'normal' label fallback."""
        svc = ClassifierService(
            model_path=Path("."),
            metadata_path=Path("."),
        )
        svc._loaded = True
        svc.classes = ["C0", "C1"]

        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.predict_proba.return_value = np.array([[0.45, 0.42]])
        svc.pipeline = mock_pipeline

        predictions = svc.predict(["test text"], ["id1"])
        assert len(predictions) == 1
        # Low confidence + low margin should be uncertain
        assert predictions[0].predicted_label == "normal"
        assert predictions[0].verification_status == VerificationStatus.UNCERTAIN.value

    def test_prediction_output_schema(self):
        """Prediction has all required fields."""
        pred = Prediction(
            comment_id="c1",
            predicted_label="abusive",
            confidence=0.85,
            second_label="normal",
            second_confidence=0.10,
            margin=0.75,
            verification_status=VerificationStatus.MODEL_VERIFIED.value,
            base_risk_score=1,
        )
        assert pred.comment_id == "c1"
        assert pred.predicted_label == "abusive"
        assert pred.confidence == 0.85
        assert pred.margin == 0.75
