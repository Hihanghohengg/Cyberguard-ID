"""CyberGuard-ID — Workflow State Machine.

Defines valid analysis states and transitions.
"""

from __future__ import annotations

from src.core.schemas import AnalysisStatus

# Valid state transitions
TRANSITIONS: dict[str, list[str]] = {
    AnalysisStatus.INITIALIZED.value: [
        AnalysisStatus.VALIDATING_INPUT.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.VALIDATING_INPUT.value: [
        AnalysisStatus.COLLECTING_COMMENTS.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.COLLECTING_COMMENTS.value: [
        AnalysisStatus.PREPROCESSING.value,
        AnalysisStatus.COMPLETED_NO_DATA.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.PREPROCESSING.value: [
        AnalysisStatus.CLASSIFYING.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.CLASSIFYING.value: [
        AnalysisStatus.DETECTING_REPETITION.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.DETECTING_REPETITION.value: [
        AnalysisStatus.SCORING_RISK.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.SCORING_RISK.value: [
        AnalysisStatus.VERIFYING.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.VERIFYING.value: [
        AnalysisStatus.WAITING_HUMAN_REVIEW.value,
        AnalysisStatus.GENERATING_REPORT.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.WAITING_HUMAN_REVIEW.value: [
        AnalysisStatus.GENERATING_REPORT.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.GENERATING_REPORT.value: [
        AnalysisStatus.COMPLETED.value,
        AnalysisStatus.FAILED.value,
    ],
    AnalysisStatus.COMPLETED.value: [],
    AnalysisStatus.COMPLETED_NO_DATA.value: [],
    AnalysisStatus.FAILED.value: [],
}

# Human-readable labels
STATE_LABELS: dict[str, str] = {
    AnalysisStatus.INITIALIZED.value: "Inisialisasi",
    AnalysisStatus.VALIDATING_INPUT.value: "Memvalidasi sumber",
    AnalysisStatus.COLLECTING_COMMENTS.value: "Mengambil komentar",
    AnalysisStatus.PREPROCESSING.value: "Menyiapkan teks",
    AnalysisStatus.CLASSIFYING.value: "Menjalankan klasifikasi",
    AnalysisStatus.DETECTING_REPETITION.value: "Mendeteksi pola",
    AnalysisStatus.SCORING_RISK.value: "Menghitung risiko",
    AnalysisStatus.VERIFYING.value: "Memverifikasi hasil",
    AnalysisStatus.WAITING_HUMAN_REVIEW.value: "Menunggu review manual",
    AnalysisStatus.GENERATING_REPORT.value: "Membuat laporan",
    AnalysisStatus.COMPLETED.value: "Selesai",
    AnalysisStatus.COMPLETED_NO_DATA.value: "Selesai — Tidak ada data",
    AnalysisStatus.FAILED.value: "Gagal",
}

# Ordered steps for progress stepper
WORKFLOW_STEPS = [
    AnalysisStatus.VALIDATING_INPUT.value,
    AnalysisStatus.COLLECTING_COMMENTS.value,
    AnalysisStatus.PREPROCESSING.value,
    AnalysisStatus.CLASSIFYING.value,
    AnalysisStatus.DETECTING_REPETITION.value,
    AnalysisStatus.SCORING_RISK.value,
    AnalysisStatus.VERIFYING.value,
    AnalysisStatus.GENERATING_REPORT.value,
    AnalysisStatus.COMPLETED.value,
]


def is_valid_transition(current: str, target: str) -> bool:
    """Check if a state transition is valid."""
    valid_targets = TRANSITIONS.get(current, [])
    return target in valid_targets


def get_step_index(status: str) -> int:
    """Get the 0-based index of a status in the workflow."""
    try:
        return WORKFLOW_STEPS.index(status)
    except ValueError:
        return -1
