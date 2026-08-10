"""CyberGuard-ID — CSV Data Service.

Handles reading, validating, and importing comments from CSV files.
"""

from __future__ import annotations

import hashlib
import io
import uuid
from pathlib import Path

import pandas as pd

from src.core.exceptions import InvalidDatasetError
from src.core.logging_config import get_logger
from src.core.schemas import Comment

logger = get_logger("csv_service")

# Expected/optional columns
REQUIRED_COLUMNS = {"text"}
OPTIONAL_COLUMNS = {
    "id",
    "author",
    "author_hash",
    "published_at",
    "like_count",
    "parent_id",
    "is_reply",
    "label",
    "external_comment_id",
}


def anonymize_author(display_name: str, salt: str) -> str:
    """Anonymize an author name using salted SHA-256."""
    h = hashlib.sha256(f"{salt}:{display_name}".encode()).hexdigest()
    return f"USER_{h[:6].upper()}"


class CSVService:
    """Service for reading and validating CSV comment files."""

    def __init__(
        self,
        salt: str = "default-salt",
        max_file_size_mb: int = 50,
        max_rows: int = 10000,
    ) -> None:
        self.salt = salt
        self.max_file_size_mb = max_file_size_mb
        self.max_rows = max_rows

    def read_csv(
        self,
        file_path: str | Path | None = None,
        file_content: bytes | None = None,
        analysis_id: str = "",
    ) -> list[Comment]:
        """Read and validate a CSV file, returning Comment objects.

        Args:
            file_path: Path to CSV file.
            file_content: Raw bytes of uploaded CSV.
            analysis_id: Analysis run ID to associate comments with.

        Returns:
            List of Comment objects.

        Raises:
            InvalidDatasetError: If the CSV is malformed or missing required columns.
        """
        try:
            if file_content is not None:
                # Check file size
                size_mb = len(file_content) / (1024 * 1024)
                if size_mb > self.max_file_size_mb:
                    raise InvalidDatasetError(
                        f"File size {size_mb:.1f}MB exceeds limit of {self.max_file_size_mb}MB",
                        user_message=f"Ukuran file terlalu besar (maks {self.max_file_size_mb}MB).",
                    )
                df = pd.read_csv(io.BytesIO(file_content), encoding="utf-8")
            elif file_path is not None:
                path = Path(file_path)
                if not path.exists():
                    raise InvalidDatasetError(
                        f"CSV file not found: {path}",
                        user_message="File CSV tidak ditemukan.",
                    )
                size_mb = path.stat().st_size / (1024 * 1024)
                if size_mb > self.max_file_size_mb:
                    raise InvalidDatasetError(
                        f"File size {size_mb:.1f}MB exceeds limit",
                        user_message=f"Ukuran file terlalu besar (maks {self.max_file_size_mb}MB).",
                    )
                df = pd.read_csv(path, encoding="utf-8")
            else:
                raise InvalidDatasetError(
                    "No file path or content provided",
                    user_message="Tidak ada file yang diberikan.",
                )
        except InvalidDatasetError:
            raise
        except Exception as e:
            raise InvalidDatasetError(
                f"Failed to read CSV: {e}",
                user_message="Gagal membaca file CSV. Pastikan format file benar.",
            ) from e

        return self._process_dataframe(df, analysis_id)

    def _process_dataframe(self, df: pd.DataFrame, analysis_id: str) -> list[Comment]:
        """Validate and convert DataFrame to Comment objects."""
        if df.empty:
            raise InvalidDatasetError(
                "CSV file is empty",
                user_message="File CSV kosong.",
            )

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        # Check required columns
        if "text" not in df.columns:
            # Try to find text column by common aliases
            text_aliases = ["comment", "komentar", "content", "comment_text", "teks"]
            found = False
            for alias in text_aliases:
                if alias in df.columns:
                    df = df.rename(columns={alias: "text"})
                    found = True
                    break
            if not found:
                raise InvalidDatasetError(
                    f"CSV missing 'text' column. Found: {list(df.columns)}",
                    user_message="CSV harus memiliki kolom 'text' untuk komentar.",
                )

        # Enforce row limit
        if len(df) > self.max_rows:
            logger.warning("CSV has %d rows, limiting to %d", len(df), self.max_rows)
            df = df.head(self.max_rows)

        # Drop rows with empty text
        df = df.dropna(subset=["text"])  # type: ignore
        df = df[df["text"].str.strip().astype(bool)]  # type: ignore

        if df.empty:
            raise InvalidDatasetError(
                "CSV has no valid text entries",
                user_message="File CSV tidak berisi komentar yang valid.",
            )

        comments: list[Comment] = []
        for _, row in df.iterrows():
            text = str(row["text"]).strip()
            if not text:
                continue

            # Author anonymization
            author = str(row.get("author", "")) if "author" in row.index else ""
            if author and author != "nan":
                author_hash = anonymize_author(author, self.salt)
            elif "author_hash" in row.index and str(row.get("author_hash", "")) != "nan":
                author_hash = str(row["author_hash"])
            else:
                author_hash = f"USER_{uuid.uuid4().hex[:6].upper()}"

            comment = Comment(
                id=uuid.uuid4().hex[:16],
                analysis_id=analysis_id,
                external_comment_id=str(row.get("external_comment_id", row.get("id", ""))),
                parent_id=str(row.get("parent_id", "")) if "parent_id" in row.index else "",
                author_hash=author_hash,
                original_text=text,
                published_at=str(row.get("published_at", "")) if "published_at" in row.index else "",
                like_count=int(row.get("like_count", 0)) if "like_count" in row.index else 0,  # type: ignore
                is_reply=bool(row.get("is_reply", False)) if "is_reply" in row.index else False,  # type: ignore
            )
            # Clean nan values
            if comment.parent_id == "nan":
                comment.parent_id = ""
            if comment.published_at == "nan":
                comment.published_at = ""
            if comment.external_comment_id == "nan":
                comment.external_comment_id = ""

            comments.append(comment)

        logger.info("Loaded %d comments from CSV", len(comments))
        return comments
