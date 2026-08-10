"""Tests for repetition detector."""

from __future__ import annotations

import pytest

from src.core.schemas import Comment, IndicationLevel, Prediction
from src.services.repetition_detector import RepetitionDetector


class TestRepetitionDetector:
    """Tests for RepetitionDetector."""

    @pytest.fixture
    def detector(self):
        return RepetitionDetector(similarity_threshold=0.80)

    def test_too_few_comments(self, detector):
        """Returns empty for fewer than 2 comments."""
        comments = [Comment(id="c1", original_text="test")]
        preds = [Prediction(comment_id="c1", predicted_label="bahasa_kasar")]
        clusters, members = detector.detect(comments, preds, "a1")
        assert clusters == []
        assert members == []

    def test_no_harmful_comments(self, detector):
        """Returns empty when no harmful comments exist."""
        comments = [
            Comment(id="c1", original_text="bagus sekali", normalized_text="bagus sekali"),
            Comment(id="c2", original_text="terima kasih", normalized_text="terima kasih"),
        ]
        preds = [
            Prediction(comment_id="c1", predicted_label="normal_konstruktif"),
            Prediction(comment_id="c2", predicted_label="normal_konstruktif"),
        ]
        clusters, members = detector.detect(comments, preds, "a1")
        assert clusters == []

    def test_similar_harmful_comments(self, detector):
        """Detects clusters of similar harmful comments."""
        comments = [
            Comment(
                id="c1",
                original_text="dasar bodoh lo muka jelek",
                normalized_text="dasar bodoh lo muka jelek",
                author_hash="USER_A",
            ),
            Comment(
                id="c2",
                original_text="dasar bodoh muka jelek banget",
                normalized_text="dasar bodoh muka jelek banget",
                author_hash="USER_B",
            ),
            Comment(
                id="c3",
                original_text="dasar bodoh jelek banget lo",
                normalized_text="dasar bodoh jelek banget lo",
                author_hash="USER_C",
            ),
        ]
        preds = [
            Prediction(comment_id="c1", predicted_label="personal_harassment"),
            Prediction(comment_id="c2", predicted_label="personal_harassment"),
            Prediction(comment_id="c3", predicted_label="personal_harassment"),
        ]
        clusters, members = detector.detect(comments, preds, "a1")
        assert len(clusters) >= 1
        assert len(members) >= 2

    def test_indication_level_early(self, detector):
        """1-2 harmful comments -> early indication."""
        comments = [
            Comment(id="c1", author_hash="USER_A"),
            Comment(id="c2", author_hash="USER_B"),
        ]
        preds = [
            Prediction(comment_id="c1", predicted_label="bahasa_kasar"),
            Prediction(comment_id="c2", predicted_label="bahasa_kasar"),
        ]
        level = detector._determine_indication(comments, preds, 2)
        assert level == IndicationLevel.EARLY.value

    def test_indication_level_moderate(self, detector):
        """3+ harmful comments -> moderate indication."""
        comments = [Comment(id=f"c{i}", author_hash=f"USER_{i}") for i in range(3)]
        preds = [Prediction(comment_id=f"c{i}", predicted_label="personal_harassment") for i in range(3)]
        level = detector._determine_indication(comments, preds, 2)
        assert level == IndicationLevel.MODERATE.value

    def test_indication_level_strong(self, detector):
        """5+ harmful from 3+ authors -> strong indication."""
        comments = [Comment(id=f"c{i}", author_hash=f"USER_{i}") for i in range(5)]
        preds = [Prediction(comment_id=f"c{i}", predicted_label="personal_harassment") for i in range(5)]
        level = detector._determine_indication(comments, preds, 5)
        assert level == IndicationLevel.STRONG.value

    def test_indication_level_critical(self, detector):
        """Threats repeated -> critical indication."""
        comments = [Comment(id=f"c{i}") for i in range(2)]
        preds = [
            Prediction(comment_id="c0", predicted_label="threat_intimidation"),
            Prediction(comment_id="c1", predicted_label="threat_intimidation"),
        ]
        level = detector._determine_indication(comments, preds, 2)
        assert level == IndicationLevel.CRITICAL.value
