"""CyberGuard-ID — System API Routes.

Endpoints for system health checks, model info, and label schema.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from server.dependencies import get_config, get_engine

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
def get_system_status() -> dict[str, Any]:
    """Get system health status."""
    config = get_config()

    model_info = {}
    try:
        engine = get_engine()
        model_info = engine.classifier.get_model_info()
    except Exception:
        pass

    return {
        "status": "healthy",
        "version": config.settings.get("app", {}).get("version", "2.0.0"),
        "api_status": {
            "youtube_available": config.api_status.youtube_available,
            "gemini_available": config.api_status.gemini_available,
            "model_available": config.api_status.model_available,
            "database_ready": config.api_status.database_ready,
        },
        "model": model_info,
        "config": {
            "max_comments": config.max_comments,
            "max_allowed_comments": config.max_allowed_comments,
            "include_replies": config.include_replies,
            "gemini_model": config.gemini_model if config.api_status.gemini_available else None,
        },
    }


@router.get("/labels")
def get_label_schema() -> dict[str, Any]:
    """Get the label categories schema."""
    config = get_config()
    categories = config.label_categories

    return {
        "categories": [
            {
                "code": cat.get("code", ""),
                "internal_name": cat.get("internal_name", ""),
                "display_name": cat.get("display_name", ""),
                "definition": cat.get("definition", "").strip(),
                "base_score": cat.get("base_score", 0),
                "color_token": cat.get("color_token", ""),
                "recommended_action": cat.get("recommended_action", ""),
            }
            for cat in categories
        ],
        "training_labels": config.training_labels,
        "label_to_code": config.label_to_code,
    }
