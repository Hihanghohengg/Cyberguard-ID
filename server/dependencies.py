"""CyberGuard-ID — Shared Dependencies.

Provides singleton instances of AppConfig, StorageService, and AnalysisEngine
for dependency injection across FastAPI routes.
"""

from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path

from src.core.config import AppConfig, load_config
from src.core.logging_config import setup_logging
from src.services.storage import StorageService
from src.workflow.engine import AnalysisEngine

_lock = threading.RLock()
_storage_instance: StorageService | None = None
_engine_instance: AnalysisEngine | None = None


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and cache application config (singleton)."""
    cfg = load_config()
    setup_logging(log_level=cfg.log_level)
    return cfg


def get_storage() -> StorageService:
    """Get or create the StorageService singleton."""
    global _storage_instance
    if _storage_instance is None:
        with _lock:
            if _storage_instance is None:
                cfg = get_config()
                _storage_instance = StorageService(cfg.db_path)
                _storage_instance.initialize()
                cfg.api_status.database_ready = True
    return _storage_instance


def get_engine() -> AnalysisEngine:
    """Get or create the AnalysisEngine singleton."""
    global _engine_instance
    if _engine_instance is None:
        with _lock:
            if _engine_instance is None:
                cfg = get_config()
                storage = get_storage()
                _engine_instance = AnalysisEngine(cfg, storage)
    return _engine_instance


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent
