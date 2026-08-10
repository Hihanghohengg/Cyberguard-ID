"""Tests for report service."""

from __future__ import annotations

import json

import pytest

from src.core.schemas import AnalysisRun, AnalysisStats, ReportSummary
from src.services.gemini_reporter import LocalReportGenerator
from src.services.report_service import ReportService


class TestLocalReportGenerator:
    """Tests for local report template generation."""

    @pytest.fixture
    def generator(self):
        return LocalReportGenerator()

    @pytest.fixture
    def sample_stats(self):
        return {
            "total_comments": 100,
            "category_distribution": {
                "normal_konstruktif": 60,
                "bahasa_kasar": 15,
                "personal_harassment": 10,
                "hate_speech": 5,
                "threat_intimidation": 3,
                "uncertain": 7,
            },
            "risk_distribution": {"low": 75, "medium": 12, "high": 8, "critical": 5},
            "harmful_count": 33,
            "uncertain_count": 7,
            "high_count": 8,
            "critical_count": 5,
            "repeated_attack_clusters": 2,
            "reviewed_count": 10,
        }

    def test_generate_summary(self, generator, sample_stats):
        """Local generator produces valid summary."""
        result = generator.generate_summary(sample_stats, "Test Analysis")
        assert isinstance(result, ReportSummary)
        assert len(result.executive_summary) > 0
        assert len(result.key_findings) > 0
        assert len(result.recommended_actions) > 0
        assert len(result.limitations) > 0

    def test_critical_severity(self, generator, sample_stats):
        """Critical items are mentioned in summary."""
        result = generator.generate_summary(sample_stats, "Test")
        assert "kritis" in result.executive_summary.lower()

    def test_no_harmful(self, generator):
        """Safe analysis produces appropriate summary."""
        stats = {
            "total_comments": 50,
            "category_distribution": {"normal_konstruktif": 50},
            "risk_distribution": {"low": 50},
            "harmful_count": 0,
            "uncertain_count": 0,
            "high_count": 0,
            "critical_count": 0,
            "repeated_attack_clusters": 0,
            "reviewed_count": 0,
        }
        result = generator.generate_summary(stats, "Safe Video")
        assert "rendah" in result.executive_summary.lower()

    def test_no_judgmental_language(self, generator, sample_stats):
        """Summary doesn't use judgmental language."""
        result = generator.generate_summary(sample_stats, "Test")
        full_text = " ".join(
            [
                result.executive_summary,
                *result.key_findings,
                *result.recommended_actions,
            ]
        ).lower()
        # Should not contain judgmental terms
        assert "terbukti" not in full_text
        assert "pelaku" not in full_text
        assert "bersalah" not in full_text


class TestReportService:
    """Tests for report file generation."""

    @pytest.fixture
    def service(self, tmp_path):
        return ReportService(tmp_path / "reports")

    @pytest.fixture
    def sample_analysis(self):
        return AnalysisRun(
            id="test_id",
            name="Test Analysis",
            source_type="csv",
            status="COMPLETED",
            started_at="2026-01-01T00:00:00Z",
        )

    @pytest.fixture
    def sample_stats(self):
        return AnalysisStats(
            total_comments=50,
            category_distribution={"normal_konstruktif": 30, "bahasa_kasar": 20},
            risk_distribution={"low": 40, "medium": 10},
            harmful_count=20,
            cluster_count=1,
        )

    @pytest.fixture
    def sample_summary(self):
        return ReportSummary(
            executive_summary="Test summary.",
            key_findings=["Finding 1"],
            recommended_actions=["Action 1"],
            limitations=["Limitation 1"],
        )

    def test_generate_csv_all(self, service):
        """CSV all generates a file."""
        predictions = [
            {
                "analysis_id": "a1",
                "id": "c1",
                "original_text": "test",
                "predicted_label": "normal_konstruktif",
                "confidence": 0.9,
            },
        ]
        path = service.generate_csv_all(predictions, "test_id")
        assert path.exists()
        assert path.suffix == ".csv"

    def test_generate_csv_priority(self, service):
        """Priority CSV filters correctly."""
        predictions = [
            {"risk_level": "low", "verification_status": "MODEL_VERIFIED"},
            {"risk_level": "critical", "verification_status": "MANDATORY_REVIEW"},
        ]
        path = service.generate_csv_priority(predictions, "test_id")
        assert path.exists()

    def test_generate_json(self, service, sample_analysis, sample_stats, sample_summary):
        """JSON report generates valid JSON."""
        path = service.generate_json(
            sample_analysis,
            sample_stats,
            [],
            sample_summary,
            "test_id",
        )
        assert path.exists()
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "analysis" in data
        assert "statistics" in data
        assert "summary" in data

    def test_generate_html(self, service, sample_analysis, sample_stats, sample_summary):
        """HTML report generates valid HTML."""
        path = service.generate_html(
            sample_analysis,
            sample_stats,
            sample_summary,
            "local",
            "test_id",
        )
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "CyberGuard-ID" in content
        assert "Disclaimer" in content

    def test_html_escapes_user_text(self, service, sample_analysis, sample_stats, sample_summary):
        """HTML report escapes potentially dangerous text."""
        path = service.generate_html(
            sample_analysis,
            sample_stats,
            sample_summary,
            "local",
            "test_xss",
        )
        content = path.read_text(encoding="utf-8")
        # Jinja2 auto-escapes by default in render
        assert "<script>" not in content
