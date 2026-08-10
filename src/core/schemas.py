"""CyberGuard-ID — Data Schemas.

Dataclass definitions for comments, predictions, clusters, reviews, and reports.
These are the canonical data structures used across all modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class VerificationStatus(StrEnum):
    """Verification status for a prediction."""

    MODEL_VERIFIED = "MODEL_VERIFIED"
    RECOMMENDED_REVIEW = "RECOMMENDED_REVIEW"
    MANDATORY_REVIEW = "MANDATORY_REVIEW"
    UNCERTAIN = "UNCERTAIN"
    HUMAN_VERIFIED = "HUMAN_VERIFIED"


class RiskLevel(StrEnum):
    """Risk level classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisStatus(StrEnum):
    """Status of an analysis run."""

    INITIALIZED = "INITIALIZED"
    VALIDATING_INPUT = "VALIDATING_INPUT"
    COLLECTING_COMMENTS = "COLLECTING_COMMENTS"
    PREPROCESSING = "PREPROCESSING"
    CLASSIFYING = "CLASSIFYING"
    DETECTING_REPETITION = "DETECTING_REPETITION"
    SCORING_RISK = "SCORING_RISK"
    VERIFYING = "VERIFYING"
    WAITING_HUMAN_REVIEW = "WAITING_HUMAN_REVIEW"
    GENERATING_REPORT = "GENERATING_REPORT"
    COMPLETED = "COMPLETED"
    COMPLETED_NO_DATA = "COMPLETED_NO_DATA"
    FAILED = "FAILED"


class ReviewDecision(StrEnum):
    """Possible decisions for human review."""

    AGREE = "agree"
    CHANGE_CATEGORY = "change_category"
    CHANGE_RISK = "change_risk"
    FALSE_POSITIVE = "false_positive"
    KEEP = "keep"
    RECOMMEND_HIDE = "recommend_hide"
    RECOMMEND_REPORT = "recommend_report"


class IndicationLevel(StrEnum):
    """Cyberbullying indication levels."""

    NONE = "none"
    EARLY = "early"
    MODERATE = "moderate"
    STRONG = "strong"
    CRITICAL = "critical"


@dataclass
class Comment:
    """A single comment from YouTube or CSV."""

    id: str = ""
    analysis_id: str = ""
    external_comment_id: str = ""
    parent_id: str = ""
    author_hash: str = ""
    original_text: str = ""
    normalized_text: str = ""
    published_at: str = ""
    like_count: int = 0
    is_reply: bool = False


@dataclass
class Prediction:
    """Classification prediction for a comment."""

    id: str = ""
    comment_id: str = ""
    predicted_label: str = ""
    confidence: float = 0.0
    second_label: str = ""
    second_confidence: float = 0.0
    margin: float = 0.0
    verification_status: str = VerificationStatus.UNCERTAIN.value
    base_risk_score: int = 0
    additional_risk_score: int = 0
    total_risk_score: int = 0
    risk_level: str = RiskLevel.LOW.value


@dataclass
class Cluster:
    """A cluster of similar comments targeting the same entity."""

    id: str = ""
    analysis_id: str = ""
    cluster_key: str = ""
    dominant_label: str = ""
    comment_count: int = 0
    unique_author_count: int = 0
    average_similarity: float = 0.0
    risk_level: str = RiskLevel.LOW.value
    indication_level: str = IndicationLevel.NONE.value


@dataclass
class ClusterMember:
    """Membership of a comment in a cluster."""

    cluster_id: str = ""
    comment_id: str = ""
    similarity_score: float = 0.0


@dataclass
class Review:
    """Human review record for a comment."""

    id: str = ""
    comment_id: str = ""
    reviewer_label: str = ""
    reviewer_risk_level: str = ""
    decision: str = ""
    note: str = ""
    reviewed_at: str = ""


@dataclass
class AnalysisRun:
    """A complete analysis session."""

    id: str = ""
    name: str = ""
    source_type: str = ""  # "youtube" or "csv"
    source_url: str = ""
    video_id: str = ""
    video_title: str = ""
    channel_title: str = ""
    status: str = AnalysisStatus.INITIALIZED.value
    started_at: str = ""
    completed_at: str = ""
    total_comments: int = 0
    harmful_count: int = 0
    uncertain_count: int = 0
    high_count: int = 0
    critical_count: int = 0
    model_version: str = ""
    error_message: str = ""


@dataclass
class ReportRecord:
    """Record of a generated report."""

    id: str = ""
    analysis_id: str = ""
    provider: str = ""  # "gemini" or "local"
    summary_json: str = ""
    html_path: str = ""
    csv_path: str = ""
    json_path: str = ""
    generated_at: str = ""


@dataclass
class ReportSummary:
    """Structured report summary."""

    executive_summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class VideoMetadata:
    """YouTube video metadata."""

    video_id: str = ""
    title: str = ""
    channel_title: str = ""
    published_at: str = ""
    comment_count: int = 0


@dataclass
class AnalysisStats:
    """Aggregate statistics for an analysis."""

    total_comments: int = 0
    category_distribution: dict[str, int] = field(default_factory=dict)
    risk_distribution: dict[str, int] = field(default_factory=dict)
    verification_distribution: dict[str, int] = field(default_factory=dict)
    harmful_count: int = 0
    uncertain_count: int = 0
    high_count: int = 0
    critical_count: int = 0
    cluster_count: int = 0
    reviewed_count: int = 0
    repeated_attack_clusters: int = 0
