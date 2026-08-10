"""Tests for Adaptive Continuous Learning Service."""

import pytest

from src.services.adaptive_learning import AdaptiveLearningService


@pytest.fixture
def adaptive_service(tmp_path):
    db_path = tmp_path / "test_adaptive.db"
    service = AdaptiveLearningService(db_path)
    service.initialize()
    return service


class TestAdaptiveLearningService:
    """Test suite for human correction recording and pattern retrieval."""

    def test_record_and_match_human_correction(self, adaptive_service):
        """When user corrects a false positive, the model should immediately recall it."""
        text = "anjir keren parah bajunya"
        norm = "anjir keren parah bajunya"

        # Record correction: user verified it's normal_konstruktif
        success = adaptive_service.record_human_correction(
            original_text=text,
            normalized_text=norm,
            corrected_label="normal_konstruktif",
            original_predicted_label="bahasa_kasar",
            reviewer_decision="OVERRIDDEN",
            note="Slang positif pujian",
        )
        assert success is True

        # Query match
        match = adaptive_service.match_exemplar(norm)
        assert match is not None
        assert match["corrected_label"] == "normal_konstruktif"
        assert match["original_predicted_label"] == "bahasa_kasar"

        # Applied count incremented
        stats = adaptive_service.get_stats()
        assert stats["total_learned_exemplars"] == 1
        assert stats["total_applied_corrections"] >= 1

    def test_stats_aggregation(self, adaptive_service):
        """Stats should correctly aggregate counts and categories."""
        adaptive_service.record_human_correction(
            original_text="test 1",
            normalized_text="test 1",
            corrected_label="normal_konstruktif",
            original_predicted_label="bahasa_kasar",
        )
        adaptive_service.record_human_correction(
            original_text="test 2",
            normalized_text="test 2",
            corrected_label="kritik_wajar",
            original_predicted_label="hate_speech",
        )

        stats = adaptive_service.get_stats()
        assert stats["total_learned_exemplars"] == 2
        assert "normal_konstruktif" in stats["corrections_by_category"]
        assert "kritik_wajar" in stats["corrections_by_category"]
