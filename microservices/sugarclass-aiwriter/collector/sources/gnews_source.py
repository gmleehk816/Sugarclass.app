"""
GNews Source - Integration with gnews.io
- Google News aggregation
- Free tier available
- Good international coverage
- API Key: https://gnews.io/
"""
import os
import requests
from typing import List, Optional
from datetime import datetime

try:
    import newspaper
    HAS_NEWSPAPER4K = True
except ImportError:
    HAS_NEWSPAPER4K = False

from .base import BaseSource, Article


_GNEWS_BASE_URL = "https://gnews.io/api/v4"
_USER_AGENT = "Mozilla/5.0 (compatible; NewsCollect/1.0)"


# GNews supported categories
GNEWS_CATEGORIES = [
    "general",
    "world",
    "nation",
    "business",
    "technology",
    "entertainment",
    "sports",
    "science",
    "health",
]

# GNews supported languages
GNEWS_LANGUAGES = [
    "ar", "zh", "nl", "en", "fr", "de", "el", "he", "hi", "it",
    "ja", "ml", "mr", "no", "pt", "ro", "ru", "es", "sv", "ta",
    "te", "uk",
]


class GNewsSource(BaseSource):
    """
    GNews.io source - Google News aggregation API.
    
    Features:
    - Google News aggregation
    - Multiple languages support
    - Category filtering
    - Search by keywords
    - Article full content extraction
    
    API Key: Get at https://gnews.io/
    Free tier: 100 requests/day, 10 articles per request
    """
    
    name = "gnews"
    display_name = "GNews.io"
    requires_api_key = True
    free_tier_limit = 100  # requests per day
    
    def __init__(self, api_key: Optional[str] = None):
        # Try to get API key from environment if not provided
        if not api_key:
            api_key = os.getenv("GNEWS_KEY") or os.getenv("GNEWS_API_KEY")
        super().__init__(api_key)
    
    def fetch_articles(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
    ) -> List[Article]:
        """
        Fetch articles from GNews API.
        
        Uses search endpoint for queries, top-headlines for browsing.
        """
        if not self.api_key:
            print("[GNews] No API key configured")
            return []
        
        articles = []
        
        try:
            if query:
                # Use search endpoint
                data = self._search(query, language, limit)
            else:
                # Use top-headlines endpoint
                data = self._top_headlines(category, language, limit)
            
            if not data or "articles" not in data:
                return []
            
            for item in data["articles"]:
                article = Article(
                    title=item.get("title", "") or "",
                    url=item.get("url", "") or "",
                    description=item.get("description", "") or "",
                    full_text=item.get("content", "") or "",
                    image_url=item.get("image", "") or "",
                    source=item.get("source", {}).get("name", "") or "",
                    published_at=item.get("publishedAt", "") or "",
                    api_source=self.name,
                    extraction_method="gnews",
                )
                articles.append(article)
            
            self._request_count += 1
            
        except Exception as e:
            print(f"[GNews] Error fetching articles: {e}")
        
        return articles[:limit]
    
    def _top_headlines(
        self,
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 10,
    ) -> Optional[dict]:
        """Fetch top headlines from GNews."""
        params = {
            "token": self.api_key,
            "lang": language if language in GNEWS_LANGUAGES else "en",
            "max": min(limit, 10),  # Free tier max 10 per request
        }
        
        if category and category in GNEWS_CATEGORIES:
            params["topic"] = category
        
        try:
            resp = requests.get(
                f"{_GNEWS_BASE_URL}/top-headlines",
                params=params,
                timeout=15,
                headers={"User-Agent": _USER_AGENT}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[GNews] top-headlines error: {e}")
            return None
    
    def _search(
        self,
        query: str,
        language: str = "en",
        limit: int = 10,
    ) -> Optional[dict]:
        """Search articles with GNews search endpoint."""
        params = {
            "token": self.api_key,
            "q": query,
            "lang": language if language in GNEWS_LANGUAGES else "en",
            "max": min(limit, 10),  # Free tier max 10 per request
        }
        
        try:
            resp = requests.get(
                f"{_GNEWS_BASE_URL}/search",
                params=params,
                timeout=15,
                headers={"User-Agent": _USER_AGENT}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[GNews] search error: {e}")
            return None
    
    def extract_full_text(self, url: str) -> Optional[str]:
        """
        Extract full article text from URL.
        
        GNews provides partial content, so we need newspaper4k for full text.
        """
        if not HAS_NEWSPAPER4K:
            return self._extract_with_requests(url)
        
        try:
            article = newspaper.Article(url)
            article.download()
            article.parse()
            
            if article.text and len(article.text) > 100:
                return article.text
                
        except Exception as e:
            print(f"[GNews] newspaper4k failed for {url}: {e}")
        
        return self._extract_with_requests(url)
    
    def _extract_with_requests(self, url: str) -> Optional[str]:
        """Fallback text extraction using requests."""
        import re
        
        try:
            resp = requests.get(
                url,
                timeout=15,
                headers={"User-Agent": _USER_AGENT}
            )
            resp.raise_for_status()
            
            html = resp.text
            html = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
            html = re.sub(r'<style[\s\S]*?</style>', ' ', html, flags=re.IGNORECASE)
            
            paras = re.findall(r'<p\b[^>]*>(.*?)</p>', html, flags=re.IGNORECASE | re.DOTALL)
            parts = []
            
            for p in paras:
                txt = re.sub(r'<[^>]+>', ' ', p)
                txt = re.sub(r'\s+', ' ', txt).strip()
                if len(txt) > 25:
                    parts.append(txt)
            
            text = '\n\n'.join(parts)
            return text if len(text) > 100 else None
            
        except Exception as e:
            print(f"[GNews] Fallback extraction failed: {e}")
            return None
    
    def get_available_topics(self) -> List[str]:
        """Get available GNews topics/categories."""
        return GNEWS_CATEGORIES.copy()
    
    def get_available_languages(self) -> List[str]:
        """Get available GNews languages."""
        return GNEWS_LANGUAGES.copy()
