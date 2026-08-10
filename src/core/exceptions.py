"""CyberGuard-ID — Custom Exceptions.

Semua exception yang digunakan di seluruh aplikasi.
Log detail teknis ke file; tampilkan pesan sederhana ke user.
"""


class CyberGuardError(Exception):
    """Base exception untuk CyberGuard-ID."""

    def __init__(self, message: str, user_message: str | None = None):
        super().__init__(message)
        self.user_message = user_message or message


class ConfigurationError(CyberGuardError):
    """Konfigurasi tidak valid atau file config tidak ditemukan."""


class YouTubeAPIError(CyberGuardError):
    """Kesalahan saat berkomunikasi dengan YouTube Data API."""


class QuotaExceededError(YouTubeAPIError):
    """Kuota YouTube API telah habis."""

    def __init__(self) -> None:
        super().__init__(
            "YouTube API quota exceeded",
            user_message="Kuota YouTube API telah habis. Coba lagi besok atau gunakan CSV.",
        )


class CommentsDisabledError(YouTubeAPIError):
    """Komentar pada video dinonaktifkan."""

    def __init__(self, video_id: str = "") -> None:
        super().__init__(
            f"Comments disabled for video {video_id}",
            user_message="Komentar pada video ini dinonaktifkan. Gunakan video lain atau unggah CSV.",
        )


class VideoNotFoundError(YouTubeAPIError):
    """Video tidak ditemukan atau bersifat private."""

    def __init__(self, video_id: str = "") -> None:
        super().__init__(
            f"Video not found: {video_id}",
            user_message="Video tidak ditemukan. Periksa URL atau pastikan video bersifat publik.",
        )


class InvalidURLError(YouTubeAPIError, ValueError):
    """URL YouTube tidak valid."""

    def __init__(self, url: str = "") -> None:
        super().__init__(
            f"Invalid YouTube URL: {url}",
            user_message="URL tidak valid. Gunakan format: https://www.youtube.com/watch?v=VIDEO_ID",
        )


class ModelNotFoundError(CyberGuardError):
    """Model machine learning tidak ditemukan."""

    def __init__(self, path: str = "") -> None:
        super().__init__(
            f"Model not found at: {path}",
            user_message=(
                "Model belum tersedia. Jalankan 'python run.py --train' untuk melatih model terlebih dahulu."
            ),
        )


class InvalidDatasetError(CyberGuardError):
    """Dataset tidak valid atau tidak memenuhi persyaratan."""


class ReportGenerationError(CyberGuardError):
    """Gagal membuat laporan."""


class StorageError(CyberGuardError):
    """Gagal mengakses atau memanipulasi storage/database."""


class GeminiAPIError(CyberGuardError):
    """Kesalahan saat berkomunikasi dengan Gemini API."""

    def __init__(self, message: str = "") -> None:
        super().__init__(
            f"Gemini API error: {message}",
            user_message="Gemini tidak tersedia. Laporan akan menggunakan template lokal.",
        )
