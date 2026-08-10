"""Tests for CSV service."""

from __future__ import annotations

import pytest

from src.core.exceptions import InvalidDatasetError
from src.services.csv_service import CSVService, anonymize_author


class TestAnonymizeAuthor:
    """Tests for author anonymization."""

    def test_anonymize_produces_hash(self):
        """Anonymization produces USER_ prefix."""
        result = anonymize_author("John Doe", "test-salt")
        assert result.startswith("USER_")
        assert len(result) == 11  # "USER_" + 6 hex chars

    def test_different_salt_different_hash(self):
        """Different salts produce different hashes."""
        h1 = anonymize_author("John", "salt1")
        h2 = anonymize_author("John", "salt2")
        assert h1 != h2

    def test_same_input_same_hash(self):
        """Same input+salt produces same hash."""
        h1 = anonymize_author("John", "salt")
        h2 = anonymize_author("John", "salt")
        assert h1 == h2


class TestCSVService:
    """Tests for CSVService."""

    @pytest.fixture
    def service(self):
        return CSVService(salt="test-salt", max_rows=100)

    def test_valid_csv(self, service):
        """Valid CSV with text column is parsed correctly."""
        csv_bytes = b"text,author\nhello world,alice\ntest comment,bob\n"
        comments = service.read_csv(file_content=csv_bytes, analysis_id="a1")
        assert len(comments) == 2
        assert comments[0].original_text == "hello world"
        assert comments[0].author_hash.startswith("USER_")

    def test_missing_text_column(self, service):
        """CSV without text column raises error."""
        csv_bytes = b"id,value\n1,100\n"
        with pytest.raises(InvalidDatasetError):
            service.read_csv(file_content=csv_bytes)

    def test_text_aliases(self, service):
        """Text aliases (comment, komentar, content) are accepted."""
        csv_bytes = b"komentar,label\nhalo dunia,normal_konstruktif\n"
        comments = service.read_csv(file_content=csv_bytes, analysis_id="a1")
        assert len(comments) == 1
        assert comments[0].original_text == "halo dunia"

    def test_empty_csv(self, service):
        """Empty CSV raises error."""
        csv_bytes = b"text\n"
        with pytest.raises(InvalidDatasetError):
            service.read_csv(file_content=csv_bytes)

    def test_row_limit(self, service):
        """Row limit is enforced."""
        rows = "text\n" + "\n".join([f"comment_{i}" for i in range(200)])
        comments = service.read_csv(file_content=rows.encode(), analysis_id="a1")
        assert len(comments) <= 100

    def test_nan_cleanup(self, service):
        """NaN values in parent_id are cleaned to empty string."""
        csv_bytes = b"text,parent_id\nhello,\nworld,\n"
        comments = service.read_csv(file_content=csv_bytes, analysis_id="a1")
        for c in comments:
            assert c.parent_id != "nan"

    def test_no_content_provided(self, service):
        """No file or content raises error."""
        with pytest.raises(InvalidDatasetError):
            service.read_csv()

    def test_file_size_limit(self, service):
        """Oversized file raises error."""
        service.max_file_size_mb = 0.001  # ~1KB limit
        big_content = b"text\n" + (b"x" * 2000) + b"\n"
        with pytest.raises(InvalidDatasetError):
            service.read_csv(file_content=big_content)
