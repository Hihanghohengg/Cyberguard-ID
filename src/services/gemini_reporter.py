"""CyberGuard-ID — Gemini Reporter Service.

Generates narrative report summaries using Gemini API.
Only sends aggregate statistics — never raw comments or usernames.
Falls back to local template if Gemini is unavailable.
"""

from __future__ import annotations

import json
from typing import Any

from src.core.exceptions import GeminiAPIError
from src.core.logging_config import get_logger
from src.core.schemas import ReportSummary

logger = get_logger("gemini_reporter")


GEMINI_SYSTEM_PROMPT = """Anda adalah asisten analis moderasi konten.
Tugas Anda adalah membuat ringkasan eksekutif, temuan utama, rekomendasi tindak lanjut,
dan keterbatasan berdasarkan data statistik analisis moderasi komentar.

PENTING:
- Gunakan Bahasa Indonesia yang formal dan profesional.
- Jangan membuat vonis atau tuduhan.
- Gunakan istilah "indikasi" dan "potensi", bukan "terbukti" atau "pasti".
- Jangan menyebutkan nama pengguna atau identitas individu.
- Fokus pada pola dan statistik, bukan pada komentar individual.
- Tekankan bahwa hasil ini adalah alat bantu yang memerlukan verifikasi manusia.

Berikan output dalam format JSON berikut:
{
    "executive_summary": "...",
    "key_findings": ["...", "..."],
    "recommended_actions": ["...", "..."],
    "limitations": ["...", "..."]
}
"""


def _build_stats_prompt(stats: dict[str, Any], analysis_name: str = "") -> str:
    """Build a prompt from aggregate statistics."""
    return f"""Analisis: {analysis_name}

Data Statistik:
- Total komentar: {stats.get("total_comments", 0)}
- Distribusi kategori: {json.dumps(stats.get("category_distribution", {}), indent=2)}
- Distribusi risiko: {json.dumps(stats.get("risk_distribution", {}), indent=2)}
- Komentar berbahaya: {stats.get("harmful_count", 0)}
- Komentar tidak pasti: {stats.get("uncertain_count", 0)}
- Risiko tinggi: {stats.get("high_count", 0)}
- Risiko kritis: {stats.get("critical_count", 0)}
- Kluster serangan berulang: {stats.get("repeated_attack_clusters", 0)}
- Sudah direview: {stats.get("reviewed_count", 0)}

Buatkan ringkasan eksekutif, temuan utama, rekomendasi tindak lanjut, dan keterbatasan."""


class GeminiReporter:
    """Generates report narratives using Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.timeout = timeout
        self._client: Any = None

    def _get_client(self) -> Any:
        """Initialize Gemini client lazily."""
        if self._client is None:
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                raise GeminiAPIError(f"Failed to initialize Gemini client: {e}") from e
        return self._client

    def generate_summary(
        self,
        stats: dict[str, Any],
        analysis_name: str = "",
    ) -> ReportSummary:
        """Generate a report summary using Gemini.

        Args:
            stats: Aggregate analysis statistics (no raw comments).
            analysis_name: Name of the analysis.

        Returns:
            Structured ReportSummary.

        Raises:
            GeminiAPIError: If Gemini fails after retries.
        """
        prompt = _build_stats_prompt(stats, analysis_name)

        for attempt in range(self.max_retries):
            try:
                client = self._get_client()
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        "system_instruction": GEMINI_SYSTEM_PROMPT,
                        "temperature": self.temperature,
                    },
                )

                # Parse response
                text = response.text.strip()
                # Try to extract JSON from response
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()

                data = json.loads(text)
                return ReportSummary(
                    executive_summary=data.get("executive_summary", ""),
                    key_findings=data.get("key_findings", []),
                    recommended_actions=data.get("recommended_actions", []),
                    limitations=data.get("limitations", []),
                )

            except json.JSONDecodeError as err:
                logger.warning(
                    "Gemini returned non-JSON response (attempt %d/%d)",
                    attempt + 1,
                    self.max_retries,
                )
                if attempt == self.max_retries - 1:
                    raise GeminiAPIError("Gemini returned invalid JSON") from err
            except GeminiAPIError:
                raise
            except Exception as e:
                logger.warning(
                    "Gemini request failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                if attempt == self.max_retries - 1:
                    raise GeminiAPIError(str(e)) from e

        raise GeminiAPIError("All retry attempts exhausted")


class LocalReportGenerator:
    """Generates report summaries using local templates (no API needed)."""

    def generate_summary(
        self,
        stats: dict[str, Any],
        analysis_name: str = "",
    ) -> ReportSummary:
        """Generate a template-based report summary.

        Args:
            stats: Aggregate analysis statistics.
            analysis_name: Name of the analysis.

        Returns:
            Structured ReportSummary from template.
        """
        if hasattr(stats, "__dataclass_fields__"):
            import dataclasses

            stats = dataclasses.asdict(stats)  # type: ignore
        elif not isinstance(stats, dict):
            stats = getattr(stats, "__dict__", {})

        total = stats.get("total_comments", 0)
        harmful = stats.get("harmful_count", 0)
        uncertain = stats.get("uncertain_count", 0)
        high = stats.get("high_count", 0)
        critical = stats.get("critical_count", 0)
        clusters = stats.get("repeated_attack_clusters", 0)
        reviewed = stats.get("reviewed_count", 0)
        cat_dist = stats.get("category_distribution", {})

        # Determine severity narrative
        if critical > 0:
            severity = "kritis"
            severity_desc = f"Ditemukan {critical} komentar dengan risiko kritis yang memerlukan perhatian segera."
        elif high > 0:
            severity = "tinggi"
            severity_desc = f"Ditemukan {high} komentar dengan risiko tinggi."
        elif harmful > 0:
            severity = "sedang"
            severity_desc = f"Ditemukan {harmful} komentar yang terindikasi bermasalah."
        else:
            severity = "rendah"
            severity_desc = "Tidak ditemukan komentar dengan indikasi risiko signifikan."

        # Executive summary
        exec_summary = (
            f"Analisis '{analysis_name}' telah memproses {total} komentar. "
            f"{severity_desc} "
            f"Tingkat risiko keseluruhan dinilai: {severity}. "
        )
        if clusters > 0:
            exec_summary += f"Terdeteksi {clusters} kluster indikasi serangan berulang. "
        if uncertain > 0:
            exec_summary += f"Terdapat {uncertain} komentar yang memerlukan verifikasi manual."

        # Key findings
        findings: list[str] = []
        if harmful > 0:
            pct = round(harmful / total * 100, 1) if total > 0 else 0
            findings.append(f"{harmful} komentar ({pct}%) terindikasi mengandung konten bermasalah.")

        for cat, count in sorted(cat_dist.items(), key=lambda x: x[1], reverse=True):
            if cat not in ("normal_konstruktif", "kritik_wajar", "uncertain") and count > 0:
                findings.append(f"Kategori '{cat}': {count} komentar.")

        if clusters > 0:
            findings.append(f"Ditemukan {clusters} pola serangan berulang yang perlu diperhatikan.")
        if uncertain > 0:
            findings.append(f"{uncertain} komentar belum dapat diklasifikasikan dengan keyakinan cukup.")

        # Recommended actions
        actions: list[str] = []
        if critical > 0:
            actions.append("Segera tinjau komentar dengan risiko kritis dan simpan bukti.")
        if high > 0:
            actions.append("Prioritaskan review komentar dengan risiko tinggi.")
        if clusters > 0:
            actions.append("Periksa kluster serangan berulang untuk indikasi cyberbullying.")
        if uncertain > 0:
            actions.append("Lakukan verifikasi manual pada komentar yang tidak pasti.")
        if reviewed < harmful:
            unreviewed = harmful - reviewed
            actions.append(f"Masih terdapat {unreviewed} komentar bermasalah yang belum direview.")
        if not actions:
            actions.append("Tidak ada tindakan mendesak yang diperlukan saat ini.")

        # Limitations
        limitations = [
            "Hasil klasifikasi merupakan prediksi model dan bukan keputusan final.",
            "Model mungkin tidak menangkap seluruh konteks percakapan.",
            "Indikasi cyberbullying memerlukan verifikasi manusia sebelum tindak lanjut.",
            "Slang atau bahasa daerah tertentu mungkin tidak tercakup dalam model.",
        ]

        return ReportSummary(
            executive_summary=exec_summary,
            key_findings=findings,
            recommended_actions=actions,
            limitations=limitations,
        )
