"""CyberGuard-ID — SQLite Storage Service.

Manages the SQLite database for analysis runs, comments, predictions,
clusters, reviews, and reports. Uses parameterized queries exclusively.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.exceptions import StorageError
from src.core.logging_config import get_logger
from src.core.schemas import (
    AnalysisRun,
    AnalysisStats,
    Cluster,
    ClusterMember,
    Comment,
    Prediction,
    ReportRecord,
    Review,
)

logger = get_logger("storage")

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS analysis_runs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT DEFAULT '',
    video_id TEXT DEFAULT '',
    video_title TEXT DEFAULT '',
    channel_title TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'INITIALIZED',
    started_at TEXT,
    completed_at TEXT,
    total_comments INTEGER DEFAULT 0,
    harmful_count INTEGER DEFAULT 0,
    uncertain_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    model_version TEXT DEFAULT '',
    error_message TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    external_comment_id TEXT DEFAULT '',
    parent_id TEXT DEFAULT '',
    author_hash TEXT DEFAULT '',
    original_text TEXT DEFAULT '',
    normalized_text TEXT DEFAULT '',
    published_at TEXT DEFAULT '',
    like_count INTEGER DEFAULT 0,
    is_reply INTEGER DEFAULT 0,
    FOREIGN KEY (analysis_id) REFERENCES analysis_runs(id)
);

CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY,
    comment_id TEXT NOT NULL,
    predicted_label TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    second_label TEXT DEFAULT '',
    second_confidence REAL DEFAULT 0.0,
    margin REAL DEFAULT 0.0,
    verification_status TEXT DEFAULT 'UNCERTAIN',
    base_risk_score INTEGER DEFAULT 0,
    additional_risk_score INTEGER DEFAULT 0,
    total_risk_score INTEGER DEFAULT 0,
    risk_level TEXT DEFAULT 'low',
    FOREIGN KEY (comment_id) REFERENCES comments(id)
);

CREATE TABLE IF NOT EXISTS clusters (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    cluster_key TEXT DEFAULT '',
    dominant_label TEXT DEFAULT '',
    comment_count INTEGER DEFAULT 0,
    unique_author_count INTEGER DEFAULT 0,
    average_similarity REAL DEFAULT 0.0,
    risk_level TEXT DEFAULT 'low',
    indication_level TEXT DEFAULT 'none',
    FOREIGN KEY (analysis_id) REFERENCES analysis_runs(id)
);

CREATE TABLE IF NOT EXISTS cluster_members (
    cluster_id TEXT NOT NULL,
    comment_id TEXT NOT NULL,
    similarity_score REAL DEFAULT 0.0,
    PRIMARY KEY (cluster_id, comment_id),
    FOREIGN KEY (cluster_id) REFERENCES clusters(id),
    FOREIGN KEY (comment_id) REFERENCES comments(id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    comment_id TEXT NOT NULL,
    reviewer_label TEXT DEFAULT '',
    reviewer_risk_level TEXT DEFAULT '',
    decision TEXT DEFAULT '',
    note TEXT DEFAULT '',
    reviewed_at TEXT,
    FOREIGN KEY (comment_id) REFERENCES comments(id)
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    provider TEXT DEFAULT 'local',
    summary_json TEXT DEFAULT '{}',
    html_path TEXT DEFAULT '',
    csv_path TEXT DEFAULT '',
    json_path TEXT DEFAULT '',
    generated_at TEXT,
    FOREIGN KEY (analysis_id) REFERENCES analysis_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_comments_analysis ON comments(analysis_id);
CREATE INDEX IF NOT EXISTS idx_predictions_comment ON predictions(comment_id);
CREATE INDEX IF NOT EXISTS idx_clusters_analysis ON clusters(analysis_id);
CREATE INDEX IF NOT EXISTS idx_cluster_members_cluster ON cluster_members(cluster_id);
CREATE INDEX IF NOT EXISTS idx_reviews_comment ON reviews(comment_id);
CREATE INDEX IF NOT EXISTS idx_reports_analysis ON reports(analysis_id);
"""


def _generate_id() -> str:
    """Generate a short UUID for database records."""
    return uuid.uuid4().hex[:16]


class StorageService:
    """SQLite-backed storage for CyberGuard-ID."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """Create database and tables if they don't exist."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = self._get_connection()
            conn.executescript(CREATE_TABLES_SQL)
            conn.commit()
            logger.info("Database initialized at %s", self.db_path)
        except sqlite3.Error as e:
            raise StorageError(
                f"Failed to initialize database: {e}",
                user_message="Gagal menginisialisasi database.",
            ) from e

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a SQLite connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # --- Analysis Runs ---

    def create_analysis(self, run: AnalysisRun) -> str:
        """Create a new analysis run."""
        if not run.id:
            run.id = _generate_id()
        if not run.started_at:
            run.started_at = datetime.now(timezone.utc).isoformat()

        conn = self._get_connection()
        conn.execute(
            """INSERT INTO analysis_runs
               (id, name, source_type, source_url, video_id, video_title,
                channel_title, status, started_at, model_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run.id,
                run.name,
                run.source_type,
                run.source_url,
                run.video_id,
                run.video_title,
                run.channel_title,
                run.status,
                run.started_at,
                run.model_version,
            ),
        )
        conn.commit()
        logger.info("Created analysis %s: %s", run.id, run.name)
        return run.id

    def update_analysis_status(
        self,
        analysis_id: str,
        status: str,
        error_message: str = "",
        **kwargs: Any,
    ) -> None:
        """Update analysis run status and optional fields."""
        conn = self._get_connection()
        sets = ["status = ?"]
        vals: list[Any] = [status]

        if error_message:
            sets.append("error_message = ?")
            vals.append(error_message)

        for key in (
            "name",
            "video_title",
            "channel_title",
            "model_version",
            "total_comments",
            "harmful_count",
            "uncertain_count",
            "high_count",
            "critical_count",
            "completed_at",
        ):
            if key in kwargs:
                sets.append(f"{key} = ?")
                vals.append(kwargs[key])

        vals.append(analysis_id)
        conn.execute(
            f"UPDATE analysis_runs SET {', '.join(sets)} WHERE id = ?",
            vals,
        )
        conn.commit()

    def get_analysis(self, analysis_id: str) -> AnalysisRun | None:
        """Get a single analysis run by ID."""
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM analysis_runs WHERE id = ?", (analysis_id,)).fetchone()
        if not row:
            return None
        return self._row_to_analysis(row)

    def list_analyses(self, limit: int = 50) -> list[AnalysisRun]:
        """List recent analyses ordered by start time descending."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT * FROM analysis_runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_analysis(r) for r in rows]

    def _row_to_analysis(self, row: sqlite3.Row) -> AnalysisRun:
        return AnalysisRun(
            id=row["id"],
            name=row["name"],
            source_type=row["source_type"],
            source_url=row["source_url"] or "",
            video_id=row["video_id"] or "",
            video_title=row["video_title"] or "",
            channel_title=row["channel_title"] or "",
            status=row["status"],
            started_at=row["started_at"] or "",
            completed_at=row["completed_at"] or "",
            total_comments=row["total_comments"] or 0,
            harmful_count=row["harmful_count"] or 0,
            uncertain_count=row["uncertain_count"] or 0,
            high_count=row["high_count"] or 0,
            critical_count=row["critical_count"] or 0,
            model_version=row["model_version"] or "",
            error_message=row["error_message"] or "",
        )

    # --- Comments ---

    def save_comments(self, comments: list[Comment]) -> None:
        """Bulk insert comments."""
        conn = self._get_connection()
        for c in comments:
            if not c.id:
                c.id = _generate_id()
        data = [
            (
                c.id,
                c.analysis_id,
                c.external_comment_id,
                c.parent_id,
                c.author_hash,
                c.original_text,
                c.normalized_text,
                c.published_at,
                c.like_count,
                1 if c.is_reply else 0,
            )
            for c in comments
        ]
        conn.executemany(
            """INSERT OR REPLACE INTO comments
               (id, analysis_id, external_comment_id, parent_id, author_hash,
                original_text, normalized_text, published_at, like_count, is_reply)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            data,
        )
        conn.commit()
        logger.info("Saved %d comments", len(comments))

    def get_comments(self, analysis_id: str) -> list[Comment]:
        """Get all comments for an analysis."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT * FROM comments WHERE analysis_id = ? ORDER BY published_at",
            (analysis_id,),
        ).fetchall()
        return [self._row_to_comment(r) for r in rows]

    def get_comment(self, comment_id: str) -> Comment | None:
        """Get a single comment by ID."""
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
        return self._row_to_comment(row) if row else None

    def _row_to_comment(self, row: sqlite3.Row) -> Comment:
        return Comment(
            id=row["id"],
            analysis_id=row["analysis_id"],
            external_comment_id=row["external_comment_id"] or "",
            parent_id=row["parent_id"] or "",
            author_hash=row["author_hash"] or "",
            original_text=row["original_text"] or "",
            normalized_text=row["normalized_text"] or "",
            published_at=row["published_at"] or "",
            like_count=row["like_count"] or 0,
            is_reply=bool(row["is_reply"]),
        )

    # --- Predictions ---

    def save_predictions(self, predictions: list[Prediction]) -> None:
        """Bulk insert predictions."""
        conn = self._get_connection()
        data = [
            (
                p.id or _generate_id(),
                p.comment_id,
                p.predicted_label,
                p.confidence,
                p.second_label,
                p.second_confidence,
                p.margin,
                p.verification_status,
                p.base_risk_score,
                p.additional_risk_score,
                p.total_risk_score,
                p.risk_level,
            )
            for p in predictions
        ]
        conn.executemany(
            """INSERT OR REPLACE INTO predictions
               (id, comment_id, predicted_label, confidence, second_label,
                second_confidence, margin, verification_status, base_risk_score,
                additional_risk_score, total_risk_score, risk_level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            data,
        )
        conn.commit()
        logger.info("Saved %d predictions", len(predictions))

    def get_predictions(self, analysis_id: str) -> list[dict[str, Any]]:
        """Get predictions joined with comments for an analysis."""
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT c.*, p.predicted_label, p.confidence, p.second_label,
                      p.second_confidence, p.margin, p.verification_status,
                      p.base_risk_score, p.additional_risk_score,
                      p.total_risk_score, p.risk_level,
                      r.reviewer_label, r.reviewer_risk_level,
                      r.decision as review_decision, r.note as review_note,
                      r.reviewed_at
               FROM comments c
               JOIN predictions p ON c.id = p.comment_id
               LEFT JOIN reviews r ON c.id = r.comment_id
               WHERE c.analysis_id = ?
               ORDER BY p.total_risk_score DESC, p.confidence DESC""",
            (analysis_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_prediction_for_comment(self, comment_id: str) -> Prediction | None:
        """Get prediction for a specific comment."""
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM predictions WHERE comment_id = ?", (comment_id,)).fetchone()
        if not row:
            return None
        return Prediction(
            id=row["id"],
            comment_id=row["comment_id"],
            predicted_label=row["predicted_label"],
            confidence=row["confidence"],
            second_label=row["second_label"] or "",
            second_confidence=row["second_confidence"] or 0.0,
            margin=row["margin"] or 0.0,
            verification_status=row["verification_status"],
            base_risk_score=row["base_risk_score"] or 0,
            additional_risk_score=row["additional_risk_score"] or 0,
            total_risk_score=row["total_risk_score"] or 0,
            risk_level=row["risk_level"] or "low",
        )

    # --- Clusters ---

    def save_clusters(
        self,
        clusters: list[Cluster],
        members: list[ClusterMember],
    ) -> None:
        """Save clusters and their members."""
        conn = self._get_connection()
        for cl in clusters:
            if not cl.id:
                cl.id = _generate_id()
            conn.execute(
                """INSERT OR REPLACE INTO clusters
                   (id, analysis_id, cluster_key, dominant_label, comment_count,
                    unique_author_count, average_similarity, risk_level, indication_level)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cl.id,
                    cl.analysis_id,
                    cl.cluster_key,
                    cl.dominant_label,
                    cl.comment_count,
                    cl.unique_author_count,
                    cl.average_similarity,
                    cl.risk_level,
                    cl.indication_level,
                ),
            )

        for m in members:
            conn.execute(
                """INSERT OR REPLACE INTO cluster_members
                   (cluster_id, comment_id, similarity_score)
                   VALUES (?, ?, ?)""",
                (m.cluster_id, m.comment_id, m.similarity_score),
            )
        conn.commit()
        logger.info("Saved %d clusters with %d members", len(clusters), len(members))

    def get_clusters(self, analysis_id: str) -> list[Cluster]:
        """Get all clusters for an analysis."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT * FROM clusters WHERE analysis_id = ? ORDER BY risk_level DESC",
            (analysis_id,),
        ).fetchall()
        return [
            Cluster(
                id=r["id"],
                analysis_id=r["analysis_id"],
                cluster_key=r["cluster_key"] or "",
                dominant_label=r["dominant_label"] or "",
                comment_count=r["comment_count"] or 0,
                unique_author_count=r["unique_author_count"] or 0,
                average_similarity=r["average_similarity"] or 0.0,
                risk_level=r["risk_level"] or "low",
                indication_level=r["indication_level"] or "none",
            )
            for r in rows
        ]

    def get_cluster_members(self, cluster_id: str) -> list[dict[str, Any]]:
        """Get comments in a cluster."""
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT cm.similarity_score, c.*, p.predicted_label,
                      p.confidence, p.risk_level
               FROM cluster_members cm
               JOIN comments c ON cm.comment_id = c.id
               LEFT JOIN predictions p ON c.id = p.comment_id
               WHERE cm.cluster_id = ?
               ORDER BY cm.similarity_score DESC""",
            (cluster_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Reviews ---

    def save_review(self, review: Review) -> str:
        """Save a human review."""
        if not review.id:
            review.id = _generate_id()
        if not review.reviewed_at:
            review.reviewed_at = datetime.now(timezone.utc).isoformat()

        conn = self._get_connection()
        # Delete existing review for this comment first
        conn.execute("DELETE FROM reviews WHERE comment_id = ?", (review.comment_id,))
        conn.execute(
            """INSERT INTO reviews
               (id, comment_id, reviewer_label, reviewer_risk_level,
                decision, note, reviewed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                review.id,
                review.comment_id,
                review.reviewer_label,
                review.reviewer_risk_level,
                review.decision,
                review.note,
                review.reviewed_at,
            ),
        )
        conn.commit()
        logger.info("Saved review for comment %s", review.comment_id)
        return review.id

    def get_reviews(self, analysis_id: str) -> list[dict[str, Any]]:
        """Get all reviews for an analysis."""
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT r.*, c.original_text, c.normalized_text
               FROM reviews r
               JOIN comments c ON r.comment_id = c.id
               WHERE c.analysis_id = ?
               ORDER BY r.reviewed_at DESC""",
            (analysis_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Reports ---

    def save_report(self, report: ReportRecord) -> str:
        """Save a report record."""
        if not report.id:
            report.id = _generate_id()
        if not report.generated_at:
            report.generated_at = datetime.now(timezone.utc).isoformat()

        conn = self._get_connection()
        conn.execute(
            """INSERT OR REPLACE INTO reports
               (id, analysis_id, provider, summary_json, html_path,
                csv_path, json_path, generated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                report.id,
                report.analysis_id,
                report.provider,
                report.summary_json,
                report.html_path,
                report.csv_path,
                report.json_path,
                report.generated_at,
            ),
        )
        conn.commit()
        return report.id

    def get_reports(self, analysis_id: str) -> list[ReportRecord]:
        """Get all reports for an analysis."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT * FROM reports WHERE analysis_id = ? ORDER BY generated_at DESC",
            (analysis_id,),
        ).fetchall()
        return [
            ReportRecord(
                id=r["id"],
                analysis_id=r["analysis_id"],
                provider=r["provider"] or "local",
                summary_json=r["summary_json"] or "{}",
                html_path=r["html_path"] or "",
                csv_path=r["csv_path"] or "",
                json_path=r["json_path"] or "",
                generated_at=r["generated_at"] or "",
            )
            for r in rows
        ]

    # --- Statistics ---

    def get_analysis_stats(self, analysis_id: str) -> AnalysisStats:
        """Compute aggregate statistics for an analysis."""
        conn = self._get_connection()

        total = conn.execute(
            "SELECT COUNT(*) FROM comments WHERE analysis_id = ?",
            (analysis_id,),
        ).fetchone()[0]

        cat_rows = conn.execute(
            """SELECT p.predicted_label, COUNT(*) as cnt
               FROM predictions p
               JOIN comments c ON p.comment_id = c.id
               WHERE c.analysis_id = ?
               GROUP BY p.predicted_label""",
            (analysis_id,),
        ).fetchall()
        cat_dist = {r["predicted_label"]: r["cnt"] for r in cat_rows}

        risk_rows = conn.execute(
            """SELECT p.risk_level, COUNT(*) as cnt
               FROM predictions p
               JOIN comments c ON p.comment_id = c.id
               WHERE c.analysis_id = ?
               GROUP BY p.risk_level""",
            (analysis_id,),
        ).fetchall()
        risk_dist = {r["risk_level"]: r["cnt"] for r in risk_rows}

        ver_rows = conn.execute(
            """SELECT p.verification_status, COUNT(*) as cnt
               FROM predictions p
               JOIN comments c ON p.comment_id = c.id
               WHERE c.analysis_id = ?
               GROUP BY p.verification_status""",
            (analysis_id,),
        ).fetchall()
        ver_dist = {r["verification_status"]: r["cnt"] for r in ver_rows}

        harmful_labels = {
            "abusive",
            "hate_speech_weak",
            "hate_speech_moderate",
            "hate_speech_strong",
            "C1",
            "C2",
            "C3",
            "C4",
        }
        harmful = sum(v for k, v in cat_dist.items() if k in harmful_labels)
        uncertain = cat_dist.get("uncertain", 0)
        high = risk_dist.get("high", 0)
        critical = risk_dist.get("critical", 0)

        cluster_count = conn.execute(
            "SELECT COUNT(*) FROM clusters WHERE analysis_id = ?",
            (analysis_id,),
        ).fetchone()[0]

        reviewed = conn.execute(
            """SELECT COUNT(*) FROM reviews r
               JOIN comments c ON r.comment_id = c.id
               WHERE c.analysis_id = ?""",
            (analysis_id,),
        ).fetchone()[0]

        attack_clusters = conn.execute(
            """SELECT COUNT(*) FROM clusters
               WHERE analysis_id = ? AND indication_level IN ('moderate', 'strong', 'critical')""",
            (analysis_id,),
        ).fetchone()[0]

        return AnalysisStats(
            total_comments=total,
            category_distribution=cat_dist,
            risk_distribution=risk_dist,
            verification_distribution=ver_dist,
            harmful_count=harmful,
            uncertain_count=uncertain,
            high_count=high,
            critical_count=critical,
            cluster_count=cluster_count,
            reviewed_count=reviewed,
            repeated_attack_clusters=attack_clusters,
        )

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an analysis run and all related data from the database.

        Args:
            analysis_id: Unique identifier of the analysis run.

        Returns:
            True if deleted successfully.
        """
        conn = self._get_connection()
        # Verify existence
        row = conn.execute("SELECT id FROM analysis_runs WHERE id = ?", (analysis_id,)).fetchone()
        if not row:
            return False

        # Delete physical files
        try:
            reports = self.get_reports(analysis_id)
            for r in reports:
                for path_str in [r.html_path, r.csv_path, r.json_path]:
                    if path_str:
                        p = Path(path_str)
                        if p.exists():
                            p.unlink()
        except Exception as e:
            logger.error("Failed to delete physical files for %s: %s", analysis_id, e)

        # Cascade delete in strict order
        conn.execute(
            "DELETE FROM reviews WHERE comment_id IN (SELECT id FROM comments WHERE analysis_id = ?)",
            (analysis_id,),
        )
        conn.execute(
            "DELETE FROM cluster_members WHERE cluster_id IN (SELECT id FROM clusters WHERE analysis_id = ?)",
            (analysis_id,),
        )
        conn.execute("DELETE FROM clusters WHERE analysis_id = ?", (analysis_id,))
        conn.execute(
            "DELETE FROM predictions WHERE comment_id IN (SELECT id FROM comments WHERE analysis_id = ?)",
            (analysis_id,),
        )
        conn.execute("DELETE FROM comments WHERE analysis_id = ?", (analysis_id,))
        conn.execute("DELETE FROM reports WHERE analysis_id = ?", (analysis_id,))
        conn.execute("DELETE FROM analysis_runs WHERE id = ?", (analysis_id,))
        conn.commit()
        logger.info("Deleted analysis run %s from storage", analysis_id)
        return True

    def clear_all_analyses(self) -> int:
        """Delete all analysis records and reset history.

        Returns:
            Count of deleted analyses.
        """
        conn = self._get_connection()
        count_row = conn.execute("SELECT COUNT(*) as cnt FROM analysis_runs").fetchone()
        count = count_row["cnt"] if count_row else 0

        # Delete physical files in artifacts/reports
        try:
            reports_dir = self.db_path.parent / "reports"
            if reports_dir.exists() and reports_dir.is_dir():
                import shutil
                shutil.rmtree(reports_dir)
                reports_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to clear physical reports: %s", e)

        conn.execute("DELETE FROM reviews")
        conn.execute("DELETE FROM cluster_members")
        conn.execute("DELETE FROM clusters")
        conn.execute("DELETE FROM predictions")
        conn.execute("DELETE FROM comments")
        conn.execute("DELETE FROM reports")
        conn.execute("DELETE FROM analysis_runs")
        conn.commit()
        logger.info("Cleared all analyses history (%d records deleted)", count)
        return count
