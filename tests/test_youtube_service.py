"""Tests for YouTube service URL extraction."""

from __future__ import annotations

import pytest

from src.services.youtube_service import extract_video_id


class TestExtractVideoId:
    """Tests for YouTube URL parsing."""

    def test_standard_url(self):
        """Standard watch URL works."""
        vid = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_short_url(self):
        """youtu.be URL works."""
        vid = extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        """Shorts URL works."""
        vid = extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        """URL with additional parameters works."""
        vid = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120")
        assert vid == "dQw4w9WgXcQ"

    def test_invalid_url(self):
        """Invalid URL raises ValueError."""
        with pytest.raises(ValueError):
            extract_video_id("not-a-url")

    def test_non_youtube_url(self):
        """Non-YouTube URL raises ValueError."""
        with pytest.raises(ValueError):
            extract_video_id("https://example.com/watch?v=test")

    def test_empty_url(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError):
            extract_video_id("")
