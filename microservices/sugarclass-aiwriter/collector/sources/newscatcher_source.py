"""
NewsCatcher Source - Integration with newscatcherapi.com
- 60,000+ news sources
- Full-text articles available
- Free tier: 100 requests/day
- API Key: https://newscatcherapi.com/
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


_NEWSCATCHER_BASE_URL = "https://api.newscatcherapi.com/v2"
_USER_AGENT = "Mozilla/5.0 (compatible; NewsCollect/1.0)"


# NewsCatcher supported topics
NEWSCATCHER_TOPICS = [
    "news",
    "sport",
    "tech",
    "world",
    "finance",
    "politics",
    "business",
    "economics",
    "entertainment",
    "beauty",
    "travel",
    "music",
    "food",
    "science",
    "gaming",
    "energy",
]

# NewsCatcher supported languages
NEWSCATCHER_LANGUAGES = [
    "en", "de", "es", "fr", "it", "pt", "ru", "nl", "zh", "ar",
    "ja", "ko", "he", "uk", "tr", "pl", "sv", "no", "da", "fi",
]


class NewsCatcherSource(BaseSource):
    """
    NewsCatcher API source - Large scale news aggregation.
    
    Features:
    - 60,000+ news sources worldwide
    - Full-text articles
    - Multiple languages
    - Topic filtering
    - Advanced search capabilities
    
    API Key: Get at https://newscatcherapi.com/
    Free tier: 100 requests/day, 100 articles per request
    """
    
    name = "newscatcher"
    display_name = "NewsCatcher"
    requires_api_key = True
    free_tier_limit = 100  # requests per day
    
    def __init__(self, api_key: Optional[str] = None):
        # Try to get API key from environment if not provided
        if not api_key:
            api_key = os.getenv("NEWSCATCHER_KEY") or os.getenv("NEWSCATCHER_API_KEY")
        super().__init__(api_key)
    
    def fetch_articles(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
    ) -> List[Article]:
        """
        Fetch articles from NewsCatcher API.
        
        Uses search endpoint for queries, latest-headlines for browsing.
        """
        if not self.api_key:
            print("[NewsCatcher] No API key configured")
            return []
        
        articles = []
        
        try:
            if query:
                # Use search endpoint
                data = self._search(query, language, limit)
            else:
                # Use latest-headlines endpoint
                data = self._latest_headlines(category, language, limit)
            
            if not data or "articles" not in data:
                return []
            
            for item in data["articles"]:
                # NewsCatcher provides rich article data
                article = Article(
                    title=item.get("title", "") or "",
                    url=item.get("link", "") or "",
                    description=item.get("summary", "") or item.get("excerpt", "") or "",
                    full_text=item.get("content", "") or "",  # NewsCatcher often has full content
                    image_url=item.get("media", "") or "",
                    source=item.get("clean_url", "") or item.get("rights", "") or "",
                    category=item.get("topic", "") or "general",
                    published_at=item.get("published_date", "") or "",
                    authors=item.get("authors", []) or [],
                    keywords=item.get("keywords", []) or [],
                    api_source=self.name,
                    extraction_method="newscatcher",
                )
                articles.append(article)
            
            self._request_count += 1
            
        except Exception as e:
            print(f"[NewsCatcher] Error fetching articles: {e}")
        
        return articles[:limit]
    
    def _latest_headlines(
        self,
        topic: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
    ) -> Optional[dict]:
        """Fetch latest headlines from NewsCatcher."""
        headers = {
            "x-api-key": self.api_key,
            "User-Agent": _USER_AGENT,
        }
        
        params = {
            "lang": language if language in NEWSCATCHER_LANGUAGES else "en",
            "page_size": min(limit, 100),
        }
        
        if topic and topic in NEWSCATCHER_TOPICS:
            params["topic"] = topic
        else:
            params["topic"] = "news"  # Default to general news
        
        try:
            resp = requests.get(
                f"{_NEWSCATCHER_BASE_URL}/latest_headlines",
                params=params,
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[NewsCatcher] latest_headlines error: {e}")
            return None
    
    def _search(
        self,
        query: str,
        language: str = "en",
        limit: int = 20,
    ) -> Optional[dict]:
        """Search articles with NewsCatcher search endpoint."""
        headers = {
            "x-api-key": self.api_key,
            "User-Agent": _USER_AGENT,
        }
        
        params = {
            "q": query,
            "lang": language if language in NEWSCATCHER_LANGUAGES else "en",
            "page_size": min(limit, 100),
            "sort_by": "date",  # Sort by most recent
        }
        
        try:
            resp = requests.get(
                f"{_NEWSCATCHER_BASE_URL}/search",
                params=params,
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[NewsCatcher] search error: {e}")
            return None
    
    def extract_full_text(self, url: str) -> Optional[str]:
        """
        Extract full article text from URL.
        
        NewsCatcher often provides full content, but we use newspaper4k as backup.
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
            print(f"[NewsCatcher] newspaper4k failed for {url}: {e}")
        
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
            print(f"[NewsCatcher] Fallback extraction failed: {e}")
            return None
    
    def get_sources(self, language: str = "en") -> Optional[dict]:
        """Get available news sources from NewsCatcher."""
        if not self.api_key:
            return None
        
        headers = {
            "x-api-key": self.api_key,
        }
        
        try:
            resp = requests.get(
                f"{_NEWSCATCHER_BASE_URL}/sources",
                params={"lang": language},
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[NewsCatcher] get_sources error: {e}")
            return None
    
    def get_available_topics(self) -> List[str]:
        """Get available NewsCatcher topics."""
        return NEWSCATCHER_TOPICS.copy()
    
    def get_available_languages(self) -> List[str]:
        """Get available NewsCatcher languages."""
        return NEWSCATCHER_LANGUAGES.copy()
