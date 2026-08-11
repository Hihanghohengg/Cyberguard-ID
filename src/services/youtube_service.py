"""CyberGuard-ID — YouTube Data Service.

Fetches comments and metadata from YouTube videos using the YouTube Data API v3.
Handles pagination, error codes, and comment thread replies.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from src.core.exceptions import (
    CommentsDisabledError,
    InvalidURLError,
    QuotaExceededError,
    VideoNotFoundError,
    YouTubeAPIError,
)
from src.core.logging_config import get_logger
from src.core.schemas import Comment, VideoMetadata

logger = get_logger("youtube")

# Supported URL formats
YOUTUBE_URL_PATTERNS = [
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})"),
]


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from a URL.

    Args:
        url: YouTube video URL.

    Returns:
        11-character video ID.

    Raises:
        InvalidURLError: If the URL format is not recognized.
    """
    url = url.strip()
    for pattern in YOUTUBE_URL_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    raise InvalidURLError(url)


def anonymize_author(display_name: str, salt: str) -> str:
    """Anonymize an author name using salted SHA-256.

    Args:
        display_name: Original YouTube display name.
        salt: Salt value for hashing.

    Returns:
        Anonymized identifier like 'USER_3F8A12'.
    """
    h = hashlib.sha256(f"{salt}:{display_name}".encode()).hexdigest()
    return f"USER_{h[:6].upper()}"


class YouTubeService:
    """Service for fetching YouTube video data and comments."""

    def __init__(self, api_key: str, salt: str = "default-salt") -> None:
        self.api_key = api_key
        self.salt = salt
        self._service: Any = None

    def _get_service(self) -> Any:
        """Lazily build the YouTube API service."""
        if self._service is None:
            try:
                from googleapiclient.discovery import build

                self._service = build(
                    "youtube",
                    "v3",
                    developerKey=self.api_key,
                    cache_discovery=False,
                )
            except Exception as e:
                raise YouTubeAPIError(
                    f"Failed to build YouTube service: {e}",
                    user_message="Gagal terhubung ke YouTube API. Periksa API key.",
                ) from e
        return self._service

    def get_video_metadata(self, video_id: str) -> VideoMetadata:
        """Fetch video metadata.

        Args:
            video_id: YouTube video ID.

        Returns:
            VideoMetadata with title, channel, etc.

        Raises:
            VideoNotFoundError: If video is not found or is private.
        """
        try:
            service = self._get_service()
            response = (
                service.videos()
                .list(
                    part="snippet,statistics",
                    id=video_id,
                )
                .execute()
            )

            items = response.get("items", [])
            if not items:
                raise VideoNotFoundError(video_id)

            snippet = items[0]["snippet"]
            stats = items[0].get("statistics", {})

            return VideoMetadata(
                video_id=video_id,
                title=snippet.get("title", ""),
                channel_title=snippet.get("channelTitle", ""),
                published_at=snippet.get("publishedAt", ""),
                comment_count=int(stats.get("commentCount", 0)),
            )
        except VideoNotFoundError:
            raise
        except Exception as e:
            self._handle_api_error(e, video_id)
            raise  # Should not reach here

    def fetch_comments(
        self,
        video_id: str,
        max_comments: int = 500,
        include_replies: bool = True,
        analysis_id: str = "",
        store_original_username: bool = False,
    ) -> list[Comment]:
        """Fetch all comments and replies for a video.

        Args:
            video_id: YouTube video ID.
            max_comments: Maximum number of top-level comments to fetch.
            include_replies: Whether to fetch replies.
            analysis_id: Analysis ID for association.
            store_original_username: If False, do not store display names.

        Returns:
            List of Comment objects with anonymized authors.
        """
        comments: list[Comment] = []
        page_token: str | None = None
        fetched_top = 0

        service = self._get_service()

        logger.info("Fetching comments for video %s (max: %d)", video_id, max_comments)

        try:
            while fetched_top < max_comments:
                batch_size = min(100, max_comments - fetched_top)
                request = service.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=batch_size,
                    pageToken=page_token,
                    textFormat="plainText",
                    order="time",
                )
                response = request.execute()

                items = response.get("items", [])
                if not items:
                    break

                for item in items:
                    top_snippet = item["snippet"]["topLevelComment"]["snippet"]
                    author_name = top_snippet.get("authorDisplayName", "Anonymous")
                    if store_original_username:
                        author_hash = author_name
                    else:
                        author_hash = anonymize_author(author_name, self.salt)

                    comment = Comment(
                        analysis_id=analysis_id,
                        external_comment_id=item["snippet"]["topLevelComment"]["id"],
                        parent_id="",
                        author_hash=author_hash,
                        original_text=top_snippet.get("textDisplay", ""),
                        published_at=top_snippet.get("publishedAt", ""),
                        like_count=int(top_snippet.get("likeCount", 0)),
                        is_reply=False,
                    )
                    comments.append(comment)
                    fetched_top += 1

                    # Fetch replies if requested
                    if include_replies:
                        reply_count = item["snippet"].get("totalReplyCount", 0)
                        if reply_count > 0:
                            replies = self._fetch_replies(
                                item,
                                service,
                                analysis_id,
                                store_original_username,
                            )
                            comments.extend(replies)

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

        except (VideoNotFoundError, CommentsDisabledError, QuotaExceededError):
            raise
        except Exception as e:
            self._handle_api_error(e, video_id)

        logger.info("Fetched %d total comments (including replies)", len(comments))
        return comments

    def _fetch_replies(
        self,
        thread_item: dict,
        service: Any,
        analysis_id: str,
        store_original_username: bool = False,
    ) -> list[Comment]:
        """Fetch replies within a comment thread."""
        replies: list[Comment] = []
        parent_id = thread_item["snippet"]["topLevelComment"]["id"]

        # First check inline replies
        inline = thread_item.get("replies", {}).get("comments", [])
        for reply_item in inline:
            snippet = reply_item["snippet"]
            author_name = snippet.get("authorDisplayName", "Anonymous")
            if store_original_username:
                author_hash = author_name
            else:
                author_hash = anonymize_author(author_name, self.salt)

            reply = Comment(
                analysis_id=analysis_id,
                external_comment_id=reply_item["id"],
                parent_id=parent_id,
                author_hash=author_hash,
                original_text=snippet.get("textDisplay", ""),
                published_at=snippet.get("publishedAt", ""),
                like_count=int(snippet.get("likeCount", 0)),
                is_reply=True,
            )
            replies.append(reply)

        # If there are more replies, paginate
        total_reply_count = thread_item["snippet"].get("totalReplyCount", 0)
        if total_reply_count > len(inline):
            try:
                page_token = None
                while True:
                    req = service.comments().list(
                        part="snippet",
                        parentId=parent_id,
                        maxResults=100,
                        pageToken=page_token,
                        textFormat="plainText",
                    )
                    resp = req.execute()
                    for item in resp.get("items", []):
                        snippet = item["snippet"]
                        author_name = snippet.get("authorDisplayName", "Anonymous")
                        if store_original_username:
                            author_hash = author_name
                        else:
                            author_hash = anonymize_author(author_name, self.salt)
                        # Skip if already in inline replies
                        if any(r.external_comment_id == item["id"] for r in replies):
                            continue
                        reply = Comment(
                            analysis_id=analysis_id,
                            external_comment_id=item["id"],
                            parent_id=parent_id,
                            author_hash=author_hash,
                            original_text=snippet.get("textDisplay", ""),
                            published_at=snippet.get("publishedAt", ""),
                            like_count=int(snippet.get("likeCount", 0)),
                            is_reply=True,
                        )
                        replies.append(reply)
                    page_token = resp.get("nextPageToken")
                    if not page_token:
                        break
            except Exception as e:
                logger.warning("Failed to fetch additional replies for %s: %s", parent_id, e)

        return replies

    def _handle_api_error(self, error: Exception, video_id: str = "") -> None:
        """Convert API exceptions to CyberGuard exceptions."""
        error_str = str(error)

        if "commentsDisabled" in error_str or "disabled comments" in error_str.lower():
            raise CommentsDisabledError(video_id) from error
        if "quotaExceeded" in error_str or "dailyLimitExceeded" in error_str:
            raise QuotaExceededError() from error
        if "videoNotFound" in error_str or "404" in error_str:
            raise VideoNotFoundError(video_id) from error

        raise YouTubeAPIError(
            f"YouTube API error for video {video_id}: {error}",
            user_message=f"Terjadi kesalahan saat mengakses YouTube API: {error_str[:200]}",
        ) from error
