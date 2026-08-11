"""CyberGuard-ID — Classifier Service.

Loads the trained IndoBERT pipeline and provides
classification with confidence scores, margin computation, and verification
status assignment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from src.core.exceptions import ModelNotFoundError
from src.core.logging_config import get_logger
from src.core.schemas import Prediction, VerificationStatus

logger = get_logger("classifier")

class ClassifierService:
    """Classifies comments using the trained moderation pipeline."""

    def __init__(
        self,
        model_path: Path,
        metadata_path: Path,
        confidence_thresholds: dict[str, float] | None = None,
        base_scores: dict[str, int] | None = None,
        adaptive_service: Any | None = None,
    ) -> None:
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.adaptive_service = adaptive_service
        self.pipeline: Any = None
        self.metadata: dict[str, Any] = {}
        self.classes: list[str] = []

        # Default thresholds
        self.thresholds = confidence_thresholds or {
            "highly_confident": 0.85,
            "accepted": 0.70,
            "mandatory_review": 0.55,
            "minimum_margin": 0.10,
            "strong_margin": 0.15,
        }

        self.base_scores = base_scores or {
            "normal": 0,
            "abusive": 1,
            "hate_speech_weak": 2,
            "hate_speech_moderate": 3,
            "hate_speech_strong": 4,
        }

        self.label_mapping = {
            "C0": "normal",
            "C1": "abusive",
            "C2": "hate_speech_weak",
            "C3": "hate_speech_moderate",
            "C4": "hate_speech_strong",
            "C5": "normal"
        }

        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        """Whether the model is loaded and ready."""
        return self._loaded

    def load(self) -> None:
        """Load the IndoBERT model pipeline.

        Raises:
            ModelNotFoundError: If the model file does not exist.
        """
        try:
            logger.info("Loading IndoBERT Deep Learning model.")
            from src.services.indo_bert_classifier import IndoBERTClassifier
            self.pipeline = IndoBERTClassifier(local_model_path="models/indobert_cyberguard")
            self.pipeline.load()
            self.classes = ["C0", "C1", "C2", "C3", "C4"]
            
            if self.metadata_path.exists():
                with open(self.metadata_path, encoding="utf-8") as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
                
            self._loaded = True
        except Exception as e:
            raise ModelNotFoundError(f"Failed to load model: {e}") from e

    def predict(
        self,
        texts: list[str],
        comment_ids: list[str],
        raw_texts: list[str] | None = None,
        progress_callback: Any | None = None,
    ) -> list[Prediction]:
        """Classify a batch of texts with contextual intelligence & adaptive learning.

        Args:
            texts: Preprocessed comment texts.
            comment_ids: Corresponding comment IDs.
            raw_texts: Optional original unnormalized texts for semantic context.

        Returns:
            List of Prediction objects with labels, confidence, and verification status.
        """
        if not self._loaded:
            raise ModelNotFoundError("Model not loaded. Call load() first.")

        if not texts:
            return []

        from src.services.context_engine import context_disambiguator

        # Get probability predictions
        probas = self.pipeline.predict_proba(texts, progress_callback=progress_callback)

        predictions: list[Prediction] = []
        for i, proba in enumerate(probas):
            text = texts[i]
            raw = raw_texts[i] if raw_texts and i < len(raw_texts) else text

            # 1. Check Adaptive Exemplar Store (Human-in-the-loop learned memory)
            adaptive_match = None
            if self.adaptive_service:
                adaptive_match = self.adaptive_service.match_exemplar(text)

            if adaptive_match:
                learned_label = adaptive_match["corrected_label"]
                base_score = self.base_scores.get(learned_label, 0)
                pred = Prediction(
                    comment_id=comment_ids[i] if i < len(comment_ids) else "",
                    predicted_label=learned_label,
                    confidence=0.96,
                    second_label="learned_correction",
                    second_confidence=0.04,
                    margin=0.92,
                    verification_status=VerificationStatus.MODEL_VERIFIED.value,
                    base_risk_score=base_score,
                )
                predictions.append(pred)
                continue

            sorted_indices = np.argsort(proba)[::-1]

            top_1_idx = sorted_indices[0]
            top_2_idx = sorted_indices[1] if len(sorted_indices) > 1 else top_1_idx

            top_1_label = self.classes[top_1_idx]
            top_1_prob = float(proba[top_1_idx])
            top_2_label = self.classes[top_2_idx]
            top_2_prob = float(proba[top_2_idx])
            margin = top_1_prob - top_2_prob

            # 2. Check Contextual Disambiguator for positive slang / praise
            ctx = context_disambiguator.analyze(raw, text)

            final_label = top_1_label
            final_prob = top_1_prob
            final_margin = margin
            verification = self._get_verification_status(final_prob, final_margin)

            if ctx.is_positive_intensifier and top_1_label in ("C1", "C2", "C3", "C4"):
                final_label = "C0"
                final_prob = max(final_prob, 0.90)
                final_margin = 0.80
                verification = VerificationStatus.MODEL_VERIFIED.value
            elif ctx.is_constructive_critique and top_1_label == "C1":
                final_label = "C0"
                final_prob = max(final_prob, 0.85)
                final_margin = 0.70
                verification = VerificationStatus.MODEL_VERIFIED.value
            else:
                # Apply standard abstention (C5) if uncertain
                if verification == VerificationStatus.UNCERTAIN.value:
                    final_label = "C5"

            mapped_final_label = self.label_mapping.get(final_label, "normal")

            # Compute base risk score
            base_score = self.base_scores.get(mapped_final_label, 0)

            pred = Prediction(
                comment_id=comment_ids[i] if i < len(comment_ids) else "",
                predicted_label=mapped_final_label,
                confidence=round(final_prob, 4),
                second_label=top_2_label,
                second_confidence=round(top_2_prob, 4),
                margin=round(final_margin, 4),
                verification_status=verification,
                base_risk_score=base_score,
            )
            predictions.append(pred)

        return predictions

    def _get_verification_status(
        self,
        confidence: float,
        margin: float,
    ) -> str:
        """Determine verification status based on confidence and margin.

        Returns:
            VerificationStatus string value.
        """
        highly = self.thresholds.get("highly_confident", 0.85)
        accepted = self.thresholds.get("accepted", 0.70)
        mandatory = self.thresholds.get("mandatory_review", 0.40)
        min_margin = self.thresholds.get("minimum_margin", 0.05)
        strong_margin = self.thresholds.get("strong_margin", 0.15)

        # Uncertain: confidence too low OR margin too small
        if confidence < mandatory or margin < min_margin:
            return VerificationStatus.UNCERTAIN.value

        # Model Verified: high confidence AND strong margin
        if confidence >= highly and margin >= strong_margin:
            return VerificationStatus.MODEL_VERIFIED.value

        # Recommended Review: moderate confidence and acceptable margin
        if confidence >= accepted and margin >= min_margin:
            return VerificationStatus.RECOMMENDED_REVIEW.value

        # Mandatory Review: between mandatory and accepted
        if confidence >= mandatory:
            return VerificationStatus.MANDATORY_REVIEW.value

        return VerificationStatus.UNCERTAIN.value

    def get_model_version(self) -> str:
        """Return model version string from metadata."""
        return self.metadata.get("model_version", "unknown")

    def get_model_info(self) -> dict[str, Any]:
        """Return model info for display."""
        return {
            "version": self.metadata.get("model_version", "unknown"),
            "name": self.metadata.get("model_name", "IndoBERT (indobenchmark/indobert-base-p1)"),
            "training_date": self.metadata.get("training_timestamp", ""),
            "classes": self.classes,
            "metrics": self.metadata.get("metrics", {}),
            "dataset_size": self.metadata.get("number_of_samples", 0),
            "sklearn_version": self.metadata.get("sklearn_version", ""),
        }
