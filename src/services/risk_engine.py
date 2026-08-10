"""CyberGuard-ID — Risk Engine Service.

Computes risk scores by combining base category scores with additional
indicator scores. Determines risk levels transparently and auditably.
"""

from __future__ import annotations

from typing import Any

from src.core.logging_config import get_logger
from src.core.schemas import Comment, Prediction, RiskLevel

logger = get_logger("risk_engine")


class RiskEngine:
    """Computes transparent, auditable risk scores for comments."""

    def __init__(
        self,
        base_scores: dict[str, int] | None = None,
        additional_scores: dict[str, int] | None = None,
        risk_levels: dict[str, dict[str, int]] | None = None,
    ) -> None:
        self.base_scores = base_scores or {
            "normal": 0,
            "abusive": 4,  # Elevate abusive to High Risk threshold
            "hate_speech_weak": 4, # High Risk
            "hate_speech_moderate": 5, # High Risk
            "hate_speech_strong": 6, # Critical Risk
        }

        self.additional_scores = additional_scores or {
            "target_individual_detected": 1,
            "target_minor_suspected": 1,
            "repeated_harmful_comments_min_3": 1,
            "unique_authors_min_3": 1,
            "incitement_to_attack": 2,
            "doxxing_indicator": 2,
        }

        self.risk_levels = risk_levels or {
            "low": {"min": 0, "max": 1},
            "medium": {"min": 2, "max": 3},
            "high": {"min": 4, "max": 5},
            "critical": {"min": 6},
        }

    def score_prediction(
        self,
        prediction: Prediction,
        comment: Comment | None = None,
        cluster_info: dict[str, Any] | None = None,
    ) -> Prediction:
        """Compute risk score for a prediction.

        Args:
            prediction: The prediction to score.
            comment: Associated comment for additional analysis.
            cluster_info: Optional cluster context.

        Returns:
            Updated prediction with risk scores.
        """
        # Base score from category
        base = self.base_scores.get(prediction.predicted_label, 0)
        prediction.base_risk_score = base

        # Additional indicators
        additional = 0

        if comment:
            text = (comment.normalized_text or comment.original_text).lower()

            # Check for target individual mentions
            if self._has_target_individual(text):
                additional += self.additional_scores.get("target_individual_detected", 1)

            # Check for minor-related indicators
            if self._has_minor_indicator(text):
                additional += self.additional_scores.get("target_minor_suspected", 1)

            # Check for incitement
            if self._has_incitement(text):
                additional += self.additional_scores.get("incitement_to_attack", 2)

            # Check for doxxing indicators
            if self._has_doxxing_indicator(text):
                additional += self.additional_scores.get("doxxing_indicator", 2)

        # Cluster-based additions
        if cluster_info:
            if cluster_info.get("comment_count", 0) >= 3:
                additional += self.additional_scores.get("repeated_harmful_comments_min_3", 1)
            if cluster_info.get("unique_author_count", 0) >= 3:
                additional += self.additional_scores.get("unique_authors_min_3", 1)

        prediction.additional_risk_score = additional
        prediction.total_risk_score = base + additional
        prediction.risk_level = self._determine_risk_level(prediction.total_risk_score)

        # If the risk score increased due to additional factors, escalate the label
        # Otherwise, preserve the original prediction
        if additional > 0:
            if prediction.total_risk_score >= 6:
                prediction.predicted_label = "hate_speech_strong"
            elif prediction.total_risk_score == 5:
                prediction.predicted_label = "hate_speech_moderate"
            elif prediction.total_risk_score == 4 and prediction.predicted_label == "normal":
                # Escalate normal to at least abusive if they scored high on indicators
                prediction.predicted_label = "abusive"

        return prediction

    def batch_score(
        self,
        predictions: list[Prediction],
        comments: list[Comment],
        cluster_map: dict[str, dict[str, Any]] | None = None,
    ) -> list[Prediction]:
        """Score a batch of predictions.

        Args:
            predictions: List of predictions.
            comments: Corresponding comments.
            cluster_map: Optional mapping of comment_id -> cluster info.

        Returns:
            Updated predictions with risk scores.
        """
        comment_map = {c.id: c for c in comments}

        for pred in predictions:
            comment = comment_map.get(pred.comment_id)
            cluster_info = (cluster_map or {}).get(pred.comment_id)
            self.score_prediction(pred, comment, cluster_info)

        return predictions

    def _determine_risk_level(self, total_score: int) -> str:
        """Map total risk score to risk level."""
        if total_score >= self.risk_levels.get("critical", {}).get("min", 6):
            return RiskLevel.CRITICAL.value
        if total_score >= self.risk_levels.get("high", {}).get("min", 4):
            return RiskLevel.HIGH.value
        if total_score >= self.risk_levels.get("medium", {}).get("min", 2):
            return RiskLevel.MEDIUM.value
        return RiskLevel.LOW.value

    def _has_target_individual(self, text: str) -> bool:
        """Check if text targets a specific individual."""
        target_patterns = [
            "<mention>",
            "lo ",
            "lu ",
            "kamu ",
            "elu ",
            "dia ",
            "si ",
            "dasar ",
        ]
        return any(p in text for p in target_patterns)

    def _has_minor_indicator(self, text: str) -> bool:
        """Check if text mentions or targets a minor."""
        minor_keywords = [
            "anak",
            "bocah",
            "bocil",
            "adek",
            "adik",
            "murid",
            "siswa",
            "pelajar",
            "anak kecil",
        ]
        return any(k in text for k in minor_keywords)

    def _has_incitement(self, text: str) -> bool:
        """Check for incitement to attack patterns."""
        incitement_keywords = [
            "hajar",
            "gebukin",
            "keroyok",
            "serang",
            "ayo kita",
            "bantai",
            "basmi",
            "habisi",
            "bunuh",
            "siksa",
        ]
        return any(k in text for k in incitement_keywords)

    def _has_doxxing_indicator(self, text: str) -> bool:
        """Check for potential doxxing indicators."""
        doxxing_keywords = [
            "alamat",
            "rumah",
            "sekolah",
            "kampus",
            "nomor hp",
            "no hp",
            "whatsapp",
            "wa ",
            "alamat rumah",
            "tempat tinggal",
        ]
        return any(k in text for k in doxxing_keywords)
