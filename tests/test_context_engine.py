"""Tests for Contextual Slang & Sentiment Disambiguation Engine."""

import pytest

from src.services.context_engine import ContextDisambiguator


@pytest.fixture
def disambiguator():
    return ContextDisambiguator()


class TestContextDisambiguator:
    """Test suite for contextual slang understanding."""

    def test_positive_slang_anjir_bagus(self, disambiguator):
        """'anjirrr mobilnya bagus banget' should be identified as positive intensifier."""
        res = disambiguator.analyze(
            raw_text="anjirrr, mobilnya bagus banget",
            normalized_text="anjir mobilnya bagus banget",
        )
        assert res.is_positive_intensifier is True
        assert res.is_direct_attack is False
        assert res.suggested_label == "normal_konstruktif"
        assert res.risk_adjustment < 0

    def test_positive_slang_mahal_cok(self, disambiguator):
        """'sepatunya mahal kali cok' should be identified as positive/wonder intensifier."""
        res = disambiguator.analyze(
            raw_text="sepatunya mahal kali cok",
            normalized_text="sepatunya mahal kali cok",
        )
        assert res.is_positive_intensifier is True
        assert res.is_direct_attack is False
        assert res.suggested_label == "normal_konstruktif"

    def test_positive_slang_gila_keren(self, disambiguator):
        """'gila keren parah videonya' should be positive."""
        res = disambiguator.analyze(
            raw_text="gila keren parah videonya",
            normalized_text="gila keren parah videonya",
        )
        assert res.is_positive_intensifier is True
        assert res.suggested_label == "normal_konstruktif"

    def test_direct_attack_dasar_anjing(self, disambiguator):
        """'dasar anjing lu' must be flagged as direct attack, not praise."""
        res = disambiguator.analyze(
            raw_text="dasar anjing lu",
            normalized_text="dasar anjing kamu",
        )
        assert res.is_direct_attack is True
        assert res.is_positive_intensifier is False
        assert res.suggested_label is None

    def test_direct_attack_muka_jelek_cok(self, disambiguator):
        """'muka lu jelek bgt cok' must be flagged as attack."""
        res = disambiguator.analyze(
            raw_text="muka lu jelek bgt cok",
            normalized_text="muka kamu jelek banget cok",
        )
        assert res.is_direct_attack is True
        assert res.is_positive_intensifier is False

    def test_constructive_critique(self, disambiguator):
        """'saran ya bang audionya agak kurang jelas' should be constructive critique."""
        res = disambiguator.analyze(
            raw_text="saran ya bang audionya agak kurang jelas",
            normalized_text="saran ya bang audionya agak kurang jelas",
        )
        assert res.is_constructive_critique is True
        assert res.suggested_label == "kritik_wajar"
