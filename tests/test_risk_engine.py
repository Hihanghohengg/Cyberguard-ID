"""Tests for risk engine."""

from __future__ import annotations

import pytest

from src.core.schemas import Comment, Prediction, RiskLevel
from src.services.risk_engine import RiskEngine


class TestRiskEngine:
    """Tests for RiskEngine."""

    @pytest.fixture
    def engine(self):
        return RiskEngine()

    def test_base_score_normal(self, engine):
        """Normal comments have 0 base score."""
        pred = Prediction(predicted_label="normal")
        result = engine.score_prediction(pred)
        assert result.base_risk_score == 0
        assert result.risk_level == RiskLevel.LOW.value

    def test_base_score_threat(self, engine):
        """Hate speech strong have base score 6."""
        pred = Prediction(predicted_label="hate_speech_strong")
        result = engine.score_prediction(pred)
        assert result.base_risk_score == 6
        assert result.risk_level == RiskLevel.CRITICAL.value

    def test_base_score_hate_speech(self, engine):
        """Hate speech moderate has base score 5."""
        pred = Prediction(predicted_label="hate_speech_moderate")
        result = engine.score_prediction(pred)
        assert result.base_risk_score == 5
        assert result.risk_level == RiskLevel.HIGH.value

    def test_additional_target_individual(self, engine):
        """Target individual adds +1."""
        pred = Prediction(predicted_label="abusive")
        comment = Comment(
            id="c1",
            normalized_text="dasar lo bodoh",
        )
        result = engine.score_prediction(pred, comment)
        assert result.additional_risk_score >= 1

    def test_additional_minor_indicator(self, engine):
        """Minor indicator adds +1."""
        pred = Prediction(predicted_label="abusive")
        comment = Comment(
            id="c1",
            normalized_text="anak itu bodoh sekali",
        )
        result = engine.score_prediction(pred, comment)
        assert result.additional_risk_score >= 1

    def test_additional_incitement(self, engine):
        """Incitement adds +2."""
        pred = Prediction(predicted_label="hate_speech_strong")
        comment = Comment(
            id="c1",
            normalized_text="ayo kita keroyok dia",
        )
        result = engine.score_prediction(pred, comment)
        assert result.additional_risk_score >= 2

    def test_additional_doxxing(self, engine):
        """Doxxing indicator adds +2."""
        pred = Prediction(predicted_label="hate_speech_strong")
        comment = Comment(
            id="c1",
            normalized_text="gue tau alamat rumah lo",
        )
        result = engine.score_prediction(pred, comment)
        assert result.additional_risk_score >= 2

    def test_cluster_bonus(self, engine):
        """Cluster with 3+ comments adds +1."""
        pred = Prediction(predicted_label="abusive")
        cluster_info = {"comment_count": 5, "unique_author_count": 3}
        result = engine.score_prediction(pred, cluster_info=cluster_info)
        assert result.additional_risk_score >= 2  # both bonuses

    def test_risk_level_low(self, engine):
        """Score 0-1 maps to LOW."""
        assert engine._determine_risk_level(0) == RiskLevel.LOW.value
        assert engine._determine_risk_level(1) == RiskLevel.LOW.value

    def test_risk_level_medium(self, engine):
        """Score 2-3 maps to MEDIUM."""
        assert engine._determine_risk_level(2) == RiskLevel.MEDIUM.value
        assert engine._determine_risk_level(3) == RiskLevel.MEDIUM.value

    def test_risk_level_high(self, engine):
        """Score 4-5 maps to HIGH."""
        assert engine._determine_risk_level(4) == RiskLevel.HIGH.value
        assert engine._determine_risk_level(5) == RiskLevel.HIGH.value

    def test_risk_level_critical(self, engine):
        """Score 6+ maps to CRITICAL."""
        assert engine._determine_risk_level(6) == RiskLevel.CRITICAL.value
        assert engine._determine_risk_level(10) == RiskLevel.CRITICAL.value

    def test_total_score_calculation(self, engine):
        """Total = base + additional."""
        pred = Prediction(predicted_label="threat_intimidation")
        comment = Comment(id="c1", normalized_text="ayo kita keroyok dia")
        result = engine.score_prediction(pred, comment)
        assert result.total_risk_score == result.base_risk_score + result.additional_risk_score

    def test_batch_score(self, engine, sample_comments, sample_predictions):
        """Batch scoring processes all predictions."""
        results = engine.batch_score(sample_predictions, sample_comments)
        assert len(results) == len(sample_predictions)
        for r in results:
            assert r.total_risk_score >= 0
            assert r.risk_level in ("low", "medium", "high", "critical")
