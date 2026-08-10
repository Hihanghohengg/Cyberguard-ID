import sys
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
sys.path.append(str(Path.cwd()))

from src.services.youtube_service import YouTubeService

api_key = os.getenv("YOUTUBE_API_KEY")
service = YouTubeService(api_key)

video_id = "bnA5cEsY0Oc"
print(f"Fetching comments for video_id={video_id}")

try:
    # We temporarily patch the method to use order='relevance' to test the hypothesis
    def _fetch_comments_relevance():
        comments = []
        page_token = None
        fetched_top = 0
        while fetched_top < 5000:
            request = service._get_service().commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                pageToken=page_token,
                textFormat="plainText",
                order="relevance",
            )
            response = request.execute()
            items = response.get("items", [])
            if not items:
                break
            for item in items:
                fetched_top += 1
                comments.append(item)
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return comments
    
    comments = _fetch_comments_relevance()
    print(f"Total top comments with relevance: {len(comments)}")
    
except Exception as e:
    print(f"Error: {e}")
