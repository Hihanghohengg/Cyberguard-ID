"""CyberGuard-ID — Adaptive Continuous Learning Service.

Records human-in-the-loop corrections and feedback, building an exemplar memory
that sharpens AI classification over time and prevents repeating false positive /
false negative mistakes.
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.core.logging_config import get_logger

logger = get_logger("adaptive_learning")

CREATE_ADAPTIVE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS adaptive_exemplars (
    id TEXT PRIMARY KEY,
    text_hash TEXT NOT NULL UNIQUE,
    original_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    corrected_label TEXT NOT NULL,
    original_predicted_label TEXT NOT NULL,
    reviewer_decision TEXT NOT NULL,
    note TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    applied_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_adaptive_hash ON adaptive_exemplars(text_hash);
"""


class AdaptiveLearningService:
    """Manages continuous active learning and human feedback memory."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._initialized = False

    def initialize(self) -> None:
        """Initialize database table for adaptive exemplars."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.executescript(CREATE_ADAPTIVE_TABLE_SQL)
                conn.commit()
            self._initialized = True
            logger.info("AdaptiveLearningService initialized at %s", self.db_path)
        except Exception as e:
            logger.error("Failed to initialize AdaptiveLearningService: %s", e)

    def _hash_text(self, text: str) -> str:
        """Compute SHA-256 hash of normalized text."""
        clean = " ".join(text.lower().strip().split())
        return hashlib.sha256(clean.encode("utf-8")).hexdigest()

    def record_human_correction(
        self,
        original_text: str,
        normalized_text: str,
        corrected_label: str,
        original_predicted_label: str,
        reviewer_decision: str = "CONFIRMED",
        note: str = "",
    ) -> bool:
        """Record human review correction to adaptive memory."""
        if not self._initialized:
            self.initialize()

        text_hash = self._hash_text(normalized_text or original_text)
        created_at = datetime.now(UTC).isoformat()
        exemplar_id = f"lrn_{text_hash[:12]}"

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """INSERT INTO adaptive_exemplars
                       (id, text_hash, original_text, normalized_text,
                        corrected_label, original_predicted_label,
                        reviewer_decision, note, created_at, applied_count)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                       ON CONFLICT(text_hash) DO UPDATE SET
                        corrected_label=excluded.corrected_label,
                        reviewer_decision=excluded.reviewer_decision,
                        note=excluded.note,
                        created_at=excluded.created_at""",
                    (
                        exemplar_id,
                        text_hash,
                        original_text,
                        normalized_text,
                        corrected_label,
                        original_predicted_label,
                        reviewer_decision,
                        note,
                        created_at,
                    ),
                )
                conn.commit()
            logger.info("Learned exemplar recorded: '%s' -> %s", original_text[:40], corrected_label)
            return True
        except Exception as e:
            logger.error("Failed to record human correction: %s", e)
            return False

    def match_exemplar(self, text: str) -> dict[str, Any] | None:
        """Check if a text matches any previously learned human correction."""
        if not self._initialized:
            self.initialize()

        text_hash = self._hash_text(text)
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM adaptive_exemplars WHERE text_hash = ?",
                    (text_hash,),
                ).fetchone()

                if row:
                    # Increment applied count
                    conn.execute(
                        "UPDATE adaptive_exemplars SET applied_count = applied_count + 1 WHERE text_hash = ?",
                        (text_hash,),
                    )
                    conn.commit()
                    return dict(row)
        except Exception as e:
            logger.warning("Error querying adaptive exemplars: %s", e)

        return None

    def get_stats(self) -> dict[str, Any]:
        """Return statistics on continuous learning."""
        if not self._initialized:
            self.initialize()

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                total_learned = conn.execute("SELECT COUNT(*) as cnt FROM adaptive_exemplars").fetchone()["cnt"]
                total_applied = conn.execute(
                    "SELECT COALESCE(SUM(applied_count), 0) as sm FROM adaptive_exemplars"
                ).fetchone()["sm"]

                # Breakdown by label
                rows = conn.execute(
                    "SELECT corrected_label, COUNT(*) as cnt FROM adaptive_exemplars GROUP BY corrected_label"
                ).fetchall()
                by_label = {r["corrected_label"]: r["cnt"] for r in rows}

                return {
                    "total_learned_exemplars": total_learned,
                    "total_applied_corrections": total_applied,
                    "corrections_by_category": by_label,
                    "status": "Active & Learning",
                }
        except Exception as e:
            logger.warning("Error querying adaptive stats: %s", e)
            return {
                "total_learned_exemplars": 0,
                "total_applied_corrections": 0,
                "corrections_by_category": {},
                "status": "Ready",
            }
