"""Tests for storage service."""

from __future__ import annotations

from src.core.schemas import (
    AnalysisRun,
    AnalysisStatus,
    Cluster,
    ClusterMember,
    Review,
    ReviewDecision,
)


class TestStorageService:
    """Tests for SQLite storage operations."""

    def test_create_analysis(self, temp_db):
        """Create and retrieve an analysis run."""
        run = AnalysisRun(
            id="test_a1",
            name="Test Analysis",
            source_type="csv",
            status=AnalysisStatus.INITIALIZED.value,
        )
        temp_db.create_analysis(run)
        result = temp_db.get_analysis("test_a1")
        assert result is not None
        assert result.name == "Test Analysis"
        assert result.source_type == "csv"

    def test_update_analysis_status(self, temp_db):
        """Update analysis status."""
        run = AnalysisRun(id="test_a2", name="Test", source_type="csv")
        temp_db.create_analysis(run)
        temp_db.update_analysis_status(
            "test_a2",
            AnalysisStatus.COMPLETED.value,
            total_comments=100,
            harmful_count=5,
        )
        result = temp_db.get_analysis("test_a2")
        assert result.status == AnalysisStatus.COMPLETED.value
        assert result.total_comments == 100
        assert result.harmful_count == 5

    def test_list_analyses(self, temp_db):
        """List analyses returns correct order."""
        for i in range(3):
            run = AnalysisRun(id=f"a{i}", name=f"Test {i}", source_type="csv")
            temp_db.create_analysis(run)
        results = temp_db.list_analyses(limit=10)
        assert len(results) == 3

    def test_save_comments(self, temp_db, sample_comments):
        """Save and retrieve comments."""
        run = AnalysisRun(id="a001", name="Test", source_type="csv")
        temp_db.create_analysis(run)
        temp_db.save_comments(sample_comments)
        results = temp_db.get_comments("a001")
        assert len(results) == len(sample_comments)

    def test_get_comment(self, temp_db, sample_comments):
        """Get a single comment by ID."""
        run = AnalysisRun(id="a001", name="Test", source_type="csv")
        temp_db.create_analysis(run)
        temp_db.save_comments(sample_comments)
        result = temp_db.get_comment("c001")
        assert result is not None
        assert result.original_text == "Terima kasih informasinya."

    def test_save_predictions(self, temp_db, sample_comments, sample_predictions):
        """Save and retrieve predictions."""
        run = AnalysisRun(id="a001", name="Test", source_type="csv")
        temp_db.create_analysis(run)
        temp_db.save_comments(sample_comments)
        temp_db.save_predictions(sample_predictions)
        results = temp_db.get_predictions("a001")
        assert len(results) == len(sample_predictions)

    def test_save_review(self, temp_db, sample_comments):
        """Save and retrieve a review."""
        run = AnalysisRun(id="a001", name="Test", source_type="csv")
        temp_db.create_analysis(run)
        temp_db.save_comments(sample_comments)

        review = Review(
            comment_id="c001",
            reviewer_label="normal_konstruktif",
            reviewer_risk_level="low",
            decision=ReviewDecision.AGREE.value,
            note="Setuju dengan klasifikasi",
        )
        temp_db.save_review(review)
        reviews = temp_db.get_reviews("a001")
        assert len(reviews) == 1
        assert reviews[0]["decision"] == ReviewDecision.AGREE.value

    def test_review_overwrite(self, temp_db, sample_comments):
        """New review replaces old review for same comment."""
        run = AnalysisRun(id="a001", name="Test", source_type="csv")
        temp_db.create_analysis(run)
        temp_db.save_comments(sample_comments)

        # First review
        r1 = Review(comment_id="c001", decision="agree")
        temp_db.save_review(r1)

        # Second review overwrites
        r2 = Review(comment_id="c001", decision="false_positive")
        temp_db.save_review(r2)

        reviews = temp_db.get_reviews("a001")
        assert len(reviews) == 1
        assert reviews[0]["decision"] == "false_positive"

    def test_analysis_stats(self, temp_db, sample_comments, sample_predictions):
        """Aggregate stats are computed correctly."""
        run = AnalysisRun(id="a001", name="Test", source_type="csv")
        temp_db.create_analysis(run)
        temp_db.save_comments(sample_comments)
        temp_db.save_predictions(sample_predictions)

        stats = temp_db.get_analysis_stats("a001")
        assert stats.total_comments == 4
        assert stats.harmful_count >= 0

    def test_save_clusters(self, temp_db, sample_comments):
        """Save and retrieve clusters."""
        run = AnalysisRun(id="a001", name="Test", source_type="csv")
        temp_db.create_analysis(run)
        temp_db.save_comments(sample_comments)

        cluster = Cluster(
            id="cl1",
            analysis_id="a001",
            cluster_key="test_cluster",
            dominant_label="personal_harassment",
            comment_count=2,
            unique_author_count=2,
            average_similarity=0.85,
        )
        member = ClusterMember(
            cluster_id="cl1",
            comment_id="c002",
            similarity_score=0.85,
        )
        temp_db.save_clusters([cluster], [member])

        clusters = temp_db.get_clusters("a001")
        assert len(clusters) == 1
        assert clusters[0].cluster_key == "test_cluster"

    def test_nonexistent_analysis(self, temp_db):
        """Returns None for non-existent analysis."""
        result = temp_db.get_analysis("nonexistent")
        assert result is None

    def test_parameterized_queries(self, temp_db):
        """SQL injection is prevented."""
        run = AnalysisRun(
            id="test'; DROP TABLE analysis_runs; --",
            name="SQL Injection Test",
            source_type="csv",
        )
        # Should not crash
        temp_db.create_analysis(run)
        result = temp_db.get_analysis("test'; DROP TABLE analysis_runs; --")
        assert result is not None

    def test_delete_analysis(self, temp_db, sample_comments, sample_predictions):
        """Delete analysis cascades cleanly to comments and predictions."""
        run = AnalysisRun(id="del_01", name="To Delete", source_type="csv")
        temp_db.create_analysis(run)
        for c in sample_comments:
            c.analysis_id = "del_01"
        temp_db.save_comments(sample_comments)
        temp_db.save_predictions(sample_predictions)

        # Delete
        success = temp_db.delete_analysis("del_01")
        assert success is True
        assert temp_db.get_analysis("del_01") is None
        comments = temp_db.get_comments("del_01")
        assert len(comments) == 0

    def test_clear_all_analyses(self, temp_db):
        """Clear all analyses resets all runs."""
        temp_db.create_analysis(AnalysisRun(id="r1", name="Run 1", source_type="csv"))
        temp_db.create_analysis(AnalysisRun(id="r2", name="Run 2", source_type="csv"))

        count = temp_db.clear_all_analyses()
        assert count >= 2
        assert len(temp_db.list_analyses()) == 0
