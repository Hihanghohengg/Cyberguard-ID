"""CyberGuard-ID — Repetition Detector Service.

Detects clusters of similar harmful comments, repeat attacks against the same
targets, and potential cyberbullying patterns using TF-IDF cosine similarity.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.core.logging_config import get_logger
from src.core.schemas import (
    Cluster,
    ClusterMember,
    Comment,
    IndicationLevel,
    Prediction,
    RiskLevel,
)

logger = get_logger("repetition")

# Labels considered harmful
HARMFUL_LABELS = {
    "bahasa_kasar",
    "personal_harassment",
    "hate_speech",
    "sexual_harassment",
    "threat_intimidation",
}

# High-risk labels
HIGH_RISK_LABELS = {"threat_intimidation", "sexual_harassment", "hate_speech"}


class RepetitionDetector:
    """Detects repeated attack patterns and similar comment clusters."""

    def __init__(
        self,
        similarity_threshold: float = 0.80,
        min_harmful_comments: int = 3,
        min_unique_authors: int = 3,
        time_window_hours: int = 24,
    ) -> None:
        self.similarity_threshold = similarity_threshold
        self.min_harmful_comments = min_harmful_comments
        self.min_unique_authors = min_unique_authors
        self.time_window_hours = time_window_hours
        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 1),
            min_df=1,
            use_idf=False,
            norm="l2",
            max_features=10000,
        )

    def detect(
        self,
        comments: list[Comment],
        predictions: list[Prediction],
        analysis_id: str,
    ) -> tuple[list[Cluster], list[ClusterMember]]:
        """Detect repetition and cluster patterns.

        Args:
            comments: List of comments.
            predictions: List of predictions aligned with comments.
            analysis_id: Current analysis ID.

        Returns:
            Tuple of (clusters, cluster_members).
        """
        if len(comments) < 2:
            logger.info("Too few comments for repetition detection")
            return [], []

        # Build lookup
        pred_map = {p.comment_id: p for p in predictions}

        # Filter to harmful comments only
        harmful_comments = []
        harmful_preds = []
        for c in comments:
            p = pred_map.get(c.id)
            if p and p.predicted_label in HARMFUL_LABELS:
                harmful_comments.append(c)
                harmful_preds.append(p)

        if len(harmful_comments) < 2:
            logger.info("Fewer than 2 harmful comments — skipping clustering")
            return [], []

        logger.info(
            "Running repetition detection on %d harmful comments",
            len(harmful_comments),
        )

        # Group by reply thread (parent_id) and by target
        thread_groups = self._group_by_thread(harmful_comments, harmful_preds)

        # Build TF-IDF matrix for similarity
        texts = [c.normalized_text or c.original_text for c in harmful_comments]

        try:
            tfidf_matrix = self._vectorizer.fit_transform(texts)
        except ValueError:
            logger.warning("TF-IDF failed — possibly empty texts")
            return [], []

        # Compute pairwise similarity
        sim_matrix = cosine_similarity(tfidf_matrix)

        # Find clusters via greedy merging
        clusters_raw = self._greedy_cluster(
            harmful_comments,
            harmful_preds,
            sim_matrix,
        )

        # Merge thread groups
        for thread_key, members in thread_groups.items():
            if len(members) >= 2:
                # Check if any member already in a cluster
                existing = None
                for cl in clusters_raw:
                    if any(m.id in {cm.id for cm in cl["members"]} for m in members):
                        existing = cl
                        break
                if existing is None:
                    clusters_raw.append(
                        {
                            "key": f"thread_{thread_key}",
                            "members": members,
                            "preds": [pred_map[m.id] for m in members if m.id in pred_map],
                        }
                    )

        # Build Cluster objects
        all_clusters: list[Cluster] = []
        all_members: list[ClusterMember] = []

        for cl_data in clusters_raw:
            if len(cl_data["members"]) < 2:
                continue

            cluster_comments = cl_data["members"]
            cluster_preds = cl_data.get("preds", [])
            if not cluster_preds:
                cluster_preds = [pred_map[c.id] for c in cluster_comments if c.id in pred_map]

            # Compute stats
            unique_authors = len({c.author_hash for c in cluster_comments})
            labels = [p.predicted_label for p in cluster_preds]
            dominant_label = max(set(labels), key=labels.count) if labels else ""

            # Average similarity within cluster
            member_indices = []
            for mc in cluster_comments:
                for i, hc in enumerate(harmful_comments):
                    if hc.id == mc.id:
                        member_indices.append(i)
                        break

            avg_sim = 0.0
            if len(member_indices) > 1:
                sims = []
                for i in range(len(member_indices)):
                    for j in range(i + 1, len(member_indices)):
                        sims.append(sim_matrix[member_indices[i], member_indices[j]])
                avg_sim = float(np.mean(sims)) if sims else 0.0

            # Determine indication level
            indication = self._determine_indication(
                cluster_comments,
                cluster_preds,
                unique_authors,
            )

            # Determine risk level
            risk = self._cluster_risk_level(indication)

            cluster_id = uuid.uuid4().hex[:16]
            cluster = Cluster(
                id=cluster_id,
                analysis_id=analysis_id,
                cluster_key=cl_data.get("key", f"cluster_{cluster_id[:8]}"),
                dominant_label=dominant_label,
                comment_count=len(cluster_comments),
                unique_author_count=unique_authors,
                average_similarity=round(avg_sim, 4),
                risk_level=risk,
                indication_level=indication,
            )
            all_clusters.append(cluster)

            # Create members
            for mc in cluster_comments:
                idx = None
                for i, hc in enumerate(harmful_comments):
                    if hc.id == mc.id:
                        idx = i
                        break

                sim_score = avg_sim  # Default
                if idx is not None and member_indices:
                    relevant_sims = [sim_matrix[idx, j] for j in member_indices if j != idx]
                    sim_score = float(np.mean(relevant_sims)) if relevant_sims else avg_sim

                all_members.append(
                    ClusterMember(
                        cluster_id=cluster_id,
                        comment_id=mc.id,
                        similarity_score=round(sim_score, 4),
                    )
                )

        logger.info("Detected %d clusters", len(all_clusters))
        return all_clusters, all_members

    def _group_by_thread(
        self,
        comments: list[Comment],
        predictions: list[Prediction],
    ) -> dict[str, list[Comment]]:
        """Group comments by reply thread."""
        groups: dict[str, list[Comment]] = defaultdict(list)
        for c in comments:
            if c.parent_id:
                groups[c.parent_id].append(c)
            else:
                groups[c.external_comment_id or c.id].append(c)
        return dict(groups)

    def _greedy_cluster(
        self,
        comments: list[Comment],
        predictions: list[Prediction],
        sim_matrix: np.ndarray,
    ) -> list[dict[str, Any]]:
        """Greedy clustering based on similarity threshold."""
        n = len(comments)
        visited = [False] * n
        clusters: list[dict[str, Any]] = []

        for i in range(n):
            if visited[i]:
                continue

            cluster_members = [comments[i]]
            cluster_preds = [predictions[i]] if i < len(predictions) else []
            visited[i] = True

            for j in range(i + 1, n):
                if visited[j]:
                    continue
                if sim_matrix[i, j] >= (self.similarity_threshold - 1e-5):
                    cluster_members.append(comments[j])
                    if j < len(predictions):
                        cluster_preds.append(predictions[j])
                    visited[j] = True

            if len(cluster_members) >= 2:
                clusters.append(
                    {
                        "key": f"sim_{comments[i].id[:8]}",
                        "members": cluster_members,
                        "preds": cluster_preds,
                    }
                )

        return clusters

    def _determine_indication(
        self,
        comments: list[Comment],
        predictions: list[Prediction],
        unique_authors: int,
    ) -> str:
        """Determine cyberbullying indication level for a cluster."""
        harmful_count = len(comments)
        has_threats = any(p.predicted_label in ("threat_intimidation",) for p in predictions)

        # Critical: threats or doxxing repeated
        if has_threats and harmful_count >= 2:
            return IndicationLevel.CRITICAL.value

        # Strong: >= 5 harmful from >= 3 authors
        if harmful_count >= 5 and unique_authors >= self.min_unique_authors:
            return IndicationLevel.STRONG.value

        # Moderate: >= 3 harmful
        if harmful_count >= self.min_harmful_comments:
            return IndicationLevel.MODERATE.value

        # Early: 1-2 harmful
        if harmful_count >= 1:
            return IndicationLevel.EARLY.value

        return IndicationLevel.NONE.value

    def _cluster_risk_level(self, indication: str) -> str:
        """Map indication level to risk level."""
        mapping = {
            IndicationLevel.CRITICAL.value: RiskLevel.CRITICAL.value,
            IndicationLevel.STRONG.value: RiskLevel.HIGH.value,
            IndicationLevel.MODERATE.value: RiskLevel.MEDIUM.value,
            IndicationLevel.EARLY.value: RiskLevel.LOW.value,
            IndicationLevel.NONE.value: RiskLevel.LOW.value,
        }
        return mapping.get(indication, RiskLevel.LOW.value)
