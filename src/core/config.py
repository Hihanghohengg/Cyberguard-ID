"""CyberGuard-ID — Configuration Manager.

Loads and validates all YAML config files and environment variables.
Provides a single AppConfig instance for the entire application.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from src.core.exceptions import ConfigurationError
from src.core.logging_config import get_logger

logger = get_logger("config")

# Project root is the parent of the src/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class APIStatus:
    """Status of external API connections."""

    youtube_available: bool = False
    gemini_available: bool = False
    model_available: bool = False
    database_ready: bool = False


@dataclass
class AppConfig:
    """Centralized application configuration."""

    # Environment
    youtube_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    use_gemini: bool = True
    anonymization_salt: str = "replace-with-random-secret"
    app_env: str = "development"
    app_port: int = 8001
    log_level: str = "INFO"

    # Loaded from YAML
    labels: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    slang_dict: dict[str, str] = field(default_factory=dict)

    # Computed
    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    api_status: APIStatus = field(default_factory=APIStatus)

    # --- Convenience accessors ---

    @property
    def db_path(self) -> Path:
        """Path to SQLite database."""
        rel = self.settings.get("paths", {}).get("database", "artifacts/cyberguard.db")
        return self.project_root / rel

    @property
    def model_path(self) -> Path:
        """Path to trained model file."""
        rel = self.settings.get("paths", {}).get("model", "models/moderation_pipeline.joblib")
        return self.project_root / rel

    @property
    def model_metadata_path(self) -> Path:
        """Path to model metadata JSON."""
        rel = self.settings.get("paths", {}).get("model_metadata", "models/model_metadata.json")
        return self.project_root / rel

    @property
    def artifacts_path(self) -> Path:
        """Path to artifacts directory."""
        rel = self.settings.get("paths", {}).get("artifacts", "artifacts")
        return self.project_root / rel

    @property
    def reports_path(self) -> Path:
        """Path to reports directory."""
        rel = self.settings.get("paths", {}).get("reports", "artifacts/reports")
        return self.project_root / rel

    @property
    def max_comments(self) -> int:
        """Default maximum comments to fetch."""
        return self.settings.get("youtube", {}).get("default_max_comments", 500)

    @property
    def max_allowed_comments(self) -> int:
        """Hard limit on comments."""
        return self.settings.get("youtube", {}).get("maximum_allowed_comments", 5000)

    @property
    def include_replies(self) -> bool:
        """Whether to include reply threads."""
        return self.settings.get("youtube", {}).get("include_replies", True)

    @property
    def confidence_thresholds(self) -> dict[str, float]:
        """Confidence threshold values."""
        return self.thresholds.get("confidence", {})

    @property
    def risk_config(self) -> dict[str, Any]:
        """Risk scoring configuration."""
        return self.thresholds.get("risk", {})

    @property
    def repetition_config(self) -> dict[str, Any]:
        """Repetition detection configuration."""
        return self.thresholds.get("repetition", {})

    @property
    def label_categories(self) -> list[dict[str, Any]]:
        """List of label category definitions."""
        return self.labels.get("categories", [])

    @property
    def training_labels(self) -> list[str]:
        """Internal names of training labels (C0-C4)."""
        return self.labels.get("training_labels", [])

    @property
    def label_to_code(self) -> dict[str, str]:
        """Mapping from internal name to code."""
        return self.labels.get("label_to_code", {})

    @property
    def code_to_label(self) -> dict[str, str]:
        """Mapping from code to internal name."""
        return {v: k for k, v in self.label_to_code.items()}

    @property
    def base_scores(self) -> dict[str, int]:
        """Base risk scores per category."""
        return self.risk_config.get("base_scores", {})

    @property
    def salt_is_default(self) -> bool:
        """Check if anonymization salt is still the default value."""
        return self.anonymization_salt in ("replace-with-random-secret", "change-me", "")

    def get_category_by_code(self, code: str) -> dict[str, Any] | None:
        """Get category definition by code (e.g., 'C0')."""
        for cat in self.label_categories:
            if cat.get("code") == code:
                return cat
        return None

    def get_category_by_name(self, name: str) -> dict[str, Any] | None:
        """Get category definition by internal name."""
        for cat in self.label_categories:
            if cat.get("internal_name") == name:
                return cat
        return None


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file safely."""
    if not path.exists():
        raise ConfigurationError(
            f"Config file not found: {path}",
            user_message=f"File konfigurasi tidak ditemukan: {path.name}",
        )
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Invalid YAML in {path}: {e}",
            user_message=f"File konfigurasi tidak valid: {path.name}",
        ) from e


def load_config() -> AppConfig:
    """Load all configuration from .env and YAML files.

    Returns:
        Fully populated AppConfig instance.
    """
    # Load .env
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        logger.warning(".env file not found — using defaults and environment variables")

    config_dir = PROJECT_ROOT / "config"

    # Load YAML configs
    labels = _load_yaml(config_dir / "labels.yaml")
    thresholds = _load_yaml(config_dir / "thresholds.yaml")
    settings = _load_yaml(config_dir / "settings.yaml")

    # Load slang dictionary
    slang_path = config_dir / "slang_id.yaml"
    slang_dict: dict[str, str] = {}
    if slang_path.exists():
        raw = _load_yaml(slang_path)
        slang_dict = {str(k): str(v) for k, v in raw.items() if not str(k).startswith("#")}

    # Build config
    cfg = AppConfig(
        youtube_api_key=os.getenv("YOUTUBE_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        use_gemini=os.getenv("USE_GEMINI", "true").lower() in ("true", "1", "yes"),
        anonymization_salt=os.getenv("ANONYMIZATION_SALT", "replace-with-random-secret"),
        app_env=os.getenv("APP_ENV", "development"),
        app_port=int(os.getenv("APP_PORT", "8001")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        labels=labels,
        thresholds=thresholds,
        settings=settings,
        slang_dict=slang_dict,
    )

    # Check API status
    cfg.api_status.youtube_available = bool(cfg.youtube_api_key)
    cfg.api_status.gemini_available = bool(cfg.gemini_api_key) and cfg.use_gemini
    cfg.api_status.model_available = cfg.model_path.exists()
    cfg.api_status.database_ready = True  # Will be set after DB init

    if cfg.salt_is_default:
        logger.warning(
            "ANONYMIZATION_SALT masih menggunakan nilai default. Ubah di file .env untuk keamanan yang lebih baik."
        )

    logger.info(
        "Config loaded — YouTube: %s, Gemini: %s, Model: %s",
        "active" if cfg.api_status.youtube_available else "inactive",
        "active" if cfg.api_status.gemini_available else "inactive",
        "available" if cfg.api_status.model_available else "not found",
    )

    return cfg
