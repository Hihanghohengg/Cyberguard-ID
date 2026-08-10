"""Tests for text preprocessing."""

from __future__ import annotations


class TestPreprocessor:
    """Tests for TextPreprocessor."""

    def test_empty_input(self, preprocessor):
        """Empty input returns empty string."""
        assert preprocessor.preprocess("") == ""
        assert preprocessor.preprocess("   ") == ""
        assert preprocessor.preprocess(None) == ""

    def test_lowercase(self, preprocessor):
        """Text is lowercased."""
        assert preprocessor.preprocess("HALO DUNIA") == "halo dunia"

    def test_url_replacement(self, preprocessor):
        """URLs are replaced with <URL> token."""
        text = "Cek https://example.com ini"
        result = preprocessor.preprocess(text)
        assert "<url>" in result
        assert "https://" not in result

    def test_mention_replacement(self, preprocessor):
        """Mentions are replaced with <MENTION> token."""
        text = "Hei @username lihat ini"
        result = preprocessor.preprocess(text)
        assert "<mention>" in result
        assert "@username" not in result

    def test_repeated_chars(self, preprocessor):
        """Repeated characters are normalized."""
        result = preprocessor.preprocess("gooooblok")
        assert result == "gooblok"

    def test_repeated_punctuation(self, preprocessor):
        """Repeated punctuation is normalized."""
        result = preprocessor.preprocess("apa!!!")
        assert result == "apa!"

    def test_whitespace_normalization(self, preprocessor):
        """Multiple spaces are normalized."""
        result = preprocessor.preprocess("terlalu    banyak    spasi")
        assert "  " not in result

    def test_slang_normalization(self, preprocessor):
        """Slang is replaced with standard form."""
        result = preprocessor.preprocess("gw mau pergi")
        assert "saya" in result
        assert "gw" not in result

    def test_preserves_negation(self, preprocessor):
        """Negation words are preserved."""
        result = preprocessor.preprocess("Tidak bagus sama sekali")
        assert "tidak" in result

    def test_preserves_profanity(self, preprocessor):
        """Profanity words are preserved for classification."""
        result = preprocessor.preprocess("Anjir apa ini")
        assert "anjir" in result

    def test_unicode_normalization(self, preprocessor):
        """Unicode is normalized to NFKC."""
        # Full-width characters should be normalized
        result = preprocessor.preprocess("Ｈａｌｏ")
        assert "halo" in result.lower()

    def test_batch_preprocess(self, preprocessor):
        """Batch preprocessing works."""
        texts = ["HALO", "https://example.com", ""]
        results = preprocessor.batch_preprocess(texts)
        assert len(results) == 3
        assert results[0] == "halo"
        assert results[2] == ""
