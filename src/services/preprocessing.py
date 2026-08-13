"""CyberGuard-ID — Text Preprocessing Service.

Membersihkan dan menormalisasi teks komentar YouTube berbahasa Indonesia
sebelum diklasifikasikan oleh model IndoBERT.

Operasi preprocessing (berurutan):
  1. Unicode normalization (NFKC) — normalisasi karakter unicode
  2. Lowercase — konversi ke huruf kecil
  3. URL replacement — ganti URL dengan token <url>
  4. Mention replacement — ganti @username dengan token <mention>
  5. Repeated char normalization — "boooooo" → "boo"
  6. Repeated punct normalization — "!!!" → "!"
  7. Slang normalization — ganti slang dengan bentuk standar (dari slang_id.yaml)
  8. Whitespace normalization — hapus spasi berlebih

Hal yang SENGAJA TIDAK dilakukan (untuk menjaga konteks ujaran):
  - Stopword removal — kata seperti "tidak", "jangan" penting untuk konteks
  - Stemming — mengubah "membunuh" menjadi "bunuh" bisa hilangkan konteks
  - Hapus profanity — kata kasar adalah fitur klasifikasi, bukan noise
"""

from __future__ import annotations

import re
import unicodedata

from src.core.logging_config import get_logger

logger = get_logger("preprocessing")

# Compiled patterns
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_PATTERN = re.compile(r"@[\w.]+")
REPEATED_PUNCT_PATTERN = re.compile(r"([!?.]){2,}")
REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{2,}")
MULTI_SPACE_PATTERN = re.compile(r"\s{2,}")
EMOJI_PATTERN = re.compile(
    r"[\U0001F600-\U0001F64F"   # Emoticons (😀–🙏)
    r"\U0001F300-\U0001F5FF"   # Misc Symbols and Pictographs
    r"\U0001F680-\U0001F6FF"   # Transport and Map
    r"\U0001F900-\U0001F9FF"   # Supplemental Symbols
    r"\U0001FA00-\U0001FA6F"   # Chess Symbols, etc.
    r"\U0001FA70-\U0001FAFF"   # Symbols and Pictographs Extended-A
    r"\U00002702-\U000027B0"   # Dingbats
    r"\U0000FE00-\U0000FE0F"   # Variation Selectors
    r"\U0000200D"               # Zero Width Joiner
    r"\U00002640-\U00002642"   # Gender symbols
    r"\U00002600-\U000026FF]+", # Misc Symbols
    flags=re.UNICODE,
)


class TextPreprocessor:
    """Preprocesses Indonesian text for comment moderation classification."""

    def __init__(self, slang_dict: dict[str, str] | None = None) -> None:
        self.slang_dict = slang_dict or {}
        logger.info("TextPreprocessor initialized with %d slang entries", len(self.slang_dict))

    def preprocess(self, text: str) -> str:
        """Apply full preprocessing pipeline to a single comment.

        Args:
            text: Raw comment text (Bahasa Indonesia).

        Returns:
            Normalized text ready for IndoBERT classification.

        Examples:
            >>> preprocessor = TextPreprocessor()
            >>> preprocessor.preprocess("Halooo kak!! Videonya kereeen 😍")
            'halooo kak! videonya kereeen'
            >>> preprocessor.preprocess("Cek link ini https://spam.com @username")
            'cek link ini <url> <mention>'
        """
        if not text or not text.strip():
            return ""

        result = text

        # Unicode normalization
        result = unicodedata.normalize("NFKC", result)

        # Lowercase
        result = result.lower()

        # Replace URLs
        result = URL_PATTERN.sub(" <url> ", result)

        # Replace mentions
        result = MENTION_PATTERN.sub(" <mention> ", result)

        # Normalize repeated characters (e.g., gooooblok -> gooblok)
        result = REPEATED_CHAR_PATTERN.sub(r"\1\1", result)

        # Normalize repeated punctuation
        result = REPEATED_PUNCT_PATTERN.sub(r"\1", result)

        # Normalize slang
        result = self._normalize_slang(result)

        # Trim and normalize whitespace
        result = MULTI_SPACE_PATTERN.sub(" ", result).strip()

        return result

    def _normalize_slang(self, text: str) -> str:
        """Replace slang words with standard forms.

        Uses word boundary matching to avoid partial replacements.
        """
        if not self.slang_dict:
            return text

        words = text.split()
        normalized = []
        for word in words:
            # Strip punctuation for lookup but preserve structure
            clean = word.strip(".,!?;:\"'()[]{}…")
            if clean in self.slang_dict:
                replacement = self.slang_dict[clean]
                # Preserve surrounding punctuation
                normalized.append(word.replace(clean, replacement, 1))
            else:
                normalized.append(word)
        return " ".join(normalized)

    def batch_preprocess(self, texts: list[str]) -> list[str]:
        """Preprocess a batch of texts.

        Args:
            texts: List of raw comment texts.

        Returns:
            List of normalized texts.
        """
        return [self.preprocess(t) for t in texts]
