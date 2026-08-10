"""Tests for workflow state machine and engine."""

from __future__ import annotations

from src.core.schemas import AnalysisStatus
from src.workflow.state import is_valid_transition


class TestWorkflowState:
    """Tests for workflow state transitions."""

    def test_valid_initial_transition(self):
        """INITIALIZED -> VALIDATING_INPUT is valid."""
        assert is_valid_transition(
            AnalysisStatus.INITIALIZED.value,
            AnalysisStatus.VALIDATING_INPUT.value,
        )

    def test_valid_collection_transition(self):
        """VALIDATING_INPUT -> COLLECTING_COMMENTS is valid."""
        assert is_valid_transition(
            AnalysisStatus.VALIDATING_INPUT.value,
            AnalysisStatus.COLLECTING_COMMENTS.value,
        )

    def test_valid_failure_transition(self):
        """Any state -> FAILED is valid."""
        assert is_valid_transition(
            AnalysisStatus.CLASSIFYING.value,
            AnalysisStatus.FAILED.value,
        )

    def test_valid_complete_transition(self):
        """GENERATING_REPORT -> COMPLETED is valid."""
        assert is_valid_transition(
            AnalysisStatus.GENERATING_REPORT.value,
            AnalysisStatus.COMPLETED.value,
        )

    def test_completed_no_data(self):
        """COLLECTING_COMMENTS -> COMPLETED_NO_DATA is valid."""
        assert is_valid_transition(
            AnalysisStatus.COLLECTING_COMMENTS.value,
            AnalysisStatus.COMPLETED_NO_DATA.value,
        )


class TestAnalysisStatusEnum:
    """Tests for AnalysisStatus enum values."""

    def test_all_states_defined(self):
        """All required workflow states exist."""
        states = [s.value for s in AnalysisStatus]
        required = [
            "INITIALIZED",
            "VALIDATING_INPUT",
            "COLLECTING_COMMENTS",
            "PREPROCESSING",
            "CLASSIFYING",
            "DETECTING_REPETITION",
            "SCORING_RISK",
            "VERIFYING",
            "WAITING_HUMAN_REVIEW",
            "GENERATING_REPORT",
            "COMPLETED",
            "COMPLETED_NO_DATA",
            "FAILED",
        ]
        for r in required:
            assert r in states, f"Missing state: {r}"
