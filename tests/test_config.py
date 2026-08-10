"""Tests for configuration loading and validation."""

from __future__ import annotations


def test_load_config(config):
    """Config loads without errors."""
    assert config is not None
    assert config.project_root.exists()


def test_config_labels(config):
    """Label configuration is loaded."""
    assert len(config.label_categories) == 5
    assert "normal" in config.training_labels
    assert "hate_speech_strong" in config.training_labels


def test_config_label_to_code(config):
    """Label-to-code mapping is correct."""
    mapping = config.label_to_code
    assert mapping["normal"] == "C0"
    assert mapping["hate_speech_strong"] == "C4"


def test_config_thresholds(config):
    """Threshold values are loaded."""
    t = config.confidence_thresholds
    assert "highly_confident" in t
    assert "minimum_margin" in t
    assert t["highly_confident"] == 0.85
    assert t["minimum_margin"] == 0.05


def test_config_base_scores(config):
    """Base risk scores are set correctly."""
    scores = config.base_scores
    assert scores["normal"] == 0
    assert scores["abusive"] == 1
    assert scores["hate_speech_strong"] == 4


def test_config_salt_detection(config):
    """Salt default detection works."""
    # In test env, salt is set to "test-salt-value"
    assert not config.salt_is_default


def test_config_paths(config):
    """Config path properties return valid paths."""
    assert str(config.db_path).endswith(".db")
    assert str(config.model_path).endswith(".joblib")


def test_config_category_by_code(config):
    """Category lookup by code works."""
    cat = config.get_category_by_code("C0")
    assert cat is not None
    assert cat["internal_name"] == "normal"


def test_config_category_by_name(config):
    """Category lookup by name works."""
    cat = config.get_category_by_name("hate_speech_strong")
    assert cat is not None
    assert cat["code"] == "C4"
