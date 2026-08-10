"""CyberGuard-ID — Contextual Slang & Sentiment Disambiguation Engine.

Differentiates emotional slang/vulgar intensifiers used in positive/admiration
contexts (e.g. "anjir mobilnya bagus banget", "sepatunya mahal kali cok") from
actual aggressive insults or hate speech (e.g. "dasar anjing lu").
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.core.logging_config import get_logger

logger = get_logger("context_engine")

# Common slang tokens that frequently act as emotional intensifiers
INTENSIFIER_TOKENS = {
    "anjir",
    "anjirr",
    "anjirrr",
    "anjirrrr",
    "anjing",
    "anjingg",
    "anjinggg",
    "anying",
    "anjrit",
    "anjay",
    "cok",
    "cuk",
    "cukz",
    "coook",
    "cukk",
    "jancok",
    "jancuk",
    "gila",
    "gilaa",
    "gilaaa",
    "gile",
    "gokil",
    "buset",
    "busett",
    "busettt",
    "astaga",
    "astagfirullah",
    "edan",
    "edann",
    "sialan",
    "babi",
    "kampret",
}

# Positive sentiment and admiration descriptors
POSITIVE_KEYWORDS = {
    "bagus",
    "bagus bgt",
    "bagus banget",
    "cakep",
    "cakep bgt",
    "cantik",
    "ganteng",
    "keren",
    "keren bgt",
    "keren parah",
    "mantap",
    "mantul",
    "mantap bgt",
    "mantapp",
    "mahal",
    "mahal kali",
    "mahal bgt",
    "mewah",
    "enak",
    "enak bgt",
    "enak parah",
    "lezat",
    "kece",
    "kece bgt",
    "lucu",
    "lucu bgt",
    "imut",
    "juara",
    "top",
    "salut",
    "hebat",
    "jago",
    "berbakat",
    "rapi",
    "mulus",
    "indah",
    "seru",
    "asik",
    "asik bgt",
    "terbaik",
    "the best",
    "estetik",
    "aesthetic",
    "sukses",
    "berkelas",
    "adem",
    "menarik",
    "suka",
    "suka bgt",
    "cinta",
    "cinta bgt",
    "apik",
    "jos",
    "top markotop",
    "legend",
    "nagih",
    "puas",
    "bersih",
    "ramah",
    "terharu",
    "merinding",
    "spektakuler",
}

# Explicit aggressive attack targeting patterns
ATTACK_TARGET_PATTERNS = [
    re.compile(r"\b(dasar|dasarr)\b", re.IGNORECASE),
    re.compile(
        r"\b(lu|loe|kamu|elu|lo)\s+(jelek|bego|tolol|goblok|mati|kontol|sampah|cacat|anjing|babi|bangsat)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(mati\s+aja|bunuh|hajar|bakar|usir|mampus|mampuz)\b", re.IGNORECASE),
    re.compile(
        r"\b(muka|wajah|keluarga|otak)\s+(lu|kamu|lo|mu)\s+(jelek|cacat|rusak|bego|tolol|goblok|sampah)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(lonte|pelacur|bencong|banci|homo|kafir|pribumi|cina|anjing\s+lu|babi\s+lu)\b", re.IGNORECASE),
]

# Constructive critique markers
CRITIQUE_MARKERS = {
    "kritik",
    "masukan",
    "saran",
    "kurang",
    "sedikit",
    "agak",
    "tapi",
    "namun",
    "evaluasi",
    "perbaiki",
    "ditingkatkan",
    "disarankan",
    "lebih baik",
}


@dataclass
class ContextAnalysisResult:
    """Result of contextual disambiguation analysis."""

    is_positive_intensifier: bool = False
    is_constructive_critique: bool = False
    is_direct_attack: bool = False
    context_note: str = ""
    suggested_label: str | None = None
    risk_adjustment: int = 0


class ContextDisambiguator:
    """Analyzes Indonesian comment semantics to prevent false positives."""

    def __init__(self) -> None:
        logger.info("ContextDisambiguator initialized")

    def analyze(self, raw_text: str, normalized_text: str) -> ContextAnalysisResult:
        """Analyze text context to identify positive intensifiers vs real attacks.

        Args:
            raw_text: Original raw comment.
            normalized_text: Preprocessed text.

        Returns:
            ContextAnalysisResult with classification guidance.
        """
        text = (normalized_text or raw_text).lower().strip()
        if not text:
            return ContextAnalysisResult()

        tokens = set(re.findall(r"\b\w+\b", text))

        # Check for direct hostile attacks first
        is_attack = False
        for pattern in ATTACK_TARGET_PATTERNS:
            if pattern.search(text):
                is_attack = True
                break

        if is_attack:
            return ContextAnalysisResult(
                is_direct_attack=True,
                context_note="Terdeteksi serangan verbal langsung terhadap individu/kelompok.",
                suggested_label=None,  # Keep ML attack prediction
                risk_adjustment=0,
            )

        # Check for presence of slang intensifiers
        has_intensifier = bool(tokens.intersection(INTENSIFIER_TOKENS))

        # Check for presence of positive keywords
        has_positive = any(kw in text for kw in POSITIVE_KEYWORDS)

        # Check for constructive critique
        has_critique = any(cm in text for cm in CRITIQUE_MARKERS)

        # Case 1: Slang word used strictly as emotional praise/wonder
        # (e.g. "anjir mobilnya bagus banget", "sepatunya mahal kali cok", "gila keren parah")
        if has_intensifier and has_positive and not is_attack:
            return ContextAnalysisResult(
                is_positive_intensifier=True,
                context_note="💡 Slang/kata seru digunakan sebagai ekspresi kekaguman atau pujian (bukan serangan).",
                suggested_label="normal_konstruktif",
                risk_adjustment=-5,
            )

        # Case 2: Constructive polite critique
        if has_critique and not is_attack and ("kurang" in text or "saran" in text or "masukan" in text):
            return ContextAnalysisResult(
                is_constructive_critique=True,
                context_note="💡 Masukan atau kritik membangun yang disampaikan secara wajar.",
                suggested_label="kritik_wajar",
                risk_adjustment=-2,
            )

        # Case 3: Pure praise without any hostility
        if has_positive and not is_attack and not has_intensifier:
            return ContextAnalysisResult(
                is_positive_intensifier=False,
                context_note="Apresiasi positif atau komentar konstruktif.",
                suggested_label="normal_konstruktif",
                risk_adjustment=-5,
            )

        return ContextAnalysisResult()


# Global singleton instance
context_disambiguator = ContextDisambiguator()
