"""
NewsAPI Source - Integration with newsapi.org
- 50+ news sources
- Free tier: 100 requests/day
- Requires API key from https://newsapi.org/
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


_NEWSAPI_BASE_URL = "https://newsapi.org/v2"
_USER_AGENT = "Mozilla/5.0 (compatible; NewsCollect/1.0)"


# Category mapping for NewsAPI
NEWSAPI_CATEGORIES = [
    "business",
    "entertainment", 
    "general",
    "health",
    "science",
    "sports",
    "technology",
]


class NewsAPISource(BaseSource):
    """
    NewsAPI.org source - Popular news API with 50+ sources.
    
    Features:
    - Top headlines from major sources
    - Everything endpoint for comprehensive search
    - Category filtering
    - Source filtering (e.g., bbc-news, cnn, reuters)
    
    API Key: Get free at https://newsapi.org/register
    Free tier: 100 requests/day, developer use only
    """
    
    name = "newsapi"
    display_name = "NewsAPI.org"
    requires_api_key = True
    free_tier_limit = 100  # requests per day
    
    def __init__(self, api_key: Optional[str] = None):
        # Try to get API key from environment if not provided
        if not api_key:
            api_key = os.getenv("NEWSAPI_KEY") or os.getenv("NEWSAPI_API_KEY")
        super().__init__(api_key)
    
    def fetch_articles(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
    ) -> List[Article]:
        """
        Fetch articles from NewsAPI.
        
        Uses top-headlines for category browsing, everything for search.
        """
        if not self.api_key:
            print("[NewsAPI] No API key configured")
            return []
        
        articles = []
        
        try:
            if query:
                # Use everything endpoint for search
                data = self._fetch_everything(query, language, limit)
            else:
                # Use top-headlines for browsing
                data = self._fetch_top_headlines(category, language, limit)
            
            if not data or "articles" not in data:
                return []
            
            for item in data["articles"]:
                article = Article(
                    title=item.get("title", "") or "",
                    url=item.get("url", "") or "",
                    description=item.get("description", "") or "",
                    full_text=item.get("content", "") or "",  # NewsAPI provides truncated content
                    image_url=item.get("urlToImage", "") or "",
                    source=item.get("source", {}).get("name", "") or "",
                    published_at=item.get("publishedAt", "") or "",
                    authors=[item.get("author", "")] if item.get("author") else [],
                    api_source=self.name,
                    extraction_method="newsapi",
                )
                articles.append(article)
            
            self._request_count += 1
            
        except Exception as e:
            print(f"[NewsAPI] Error fetching articles: {e}")
        
        return articles[:limit]
    
    def _fetch_top_headlines(
        self,
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
    ) -> Optional[dict]:
        """Fetch top headlines from NewsAPI."""
        params = {
            "apiKey": self.api_key,
            "language": language,
            "pageSize": min(limit, 100),
        }
        
        # Need either category, sources, or country
        if category and category in NEWSAPI_CATEGORIES:
            params["category"] = category
            params["country"] = "us"  # Required with category
        else:
            params["country"] = "us"
        
        try:
            resp = requests.get(
                f"{_NEWSAPI_BASE_URL}/top-headlines",
                params=params,
                timeout=15,
                headers={"User-Agent": _USER_AGENT}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[NewsAPI] top-headlines error: {e}")
            return None
    
    def _fetch_everything(
        self,
        query: str,
        language: str = "en",
        limit: int = 20,
    ) -> Optional[dict]:
        """Search all articles with NewsAPI everything endpoint."""
        params = {
            "apiKey": self.api_key,
            "q": query,
            "language": language,
            "pageSize": min(limit, 100),
            "sortBy": "publishedAt",
        }
        
        try:
            resp = requests.get(
                f"{_NEWSAPI_BASE_URL}/everything",
                params=params,
                timeout=15,
                headers={"User-Agent": _USER_AGENT}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[NewsAPI] everything error: {e}")
            return None
    
    def extract_full_text(self, url: str) -> Optional[str]:
        """
        Extract full article text from URL.
        
        NewsAPI only provides truncated content, so we need to fetch full text.
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
            print(f"[NewsAPI] newspaper4k failed for {url}: {e}")
        
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
            print(f"[NewsAPI] Fallback extraction failed: {e}")
            return None
    
    def get_sources(self) -> List[dict]:
        """Get available news sources from NewsAPI."""
        if not self.api_key:
            return []
        
        try:
            resp = requests.get(
                f"{_NEWSAPI_BASE_URL}/top-headlines/sources",
                params={"apiKey": self.api_key},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("sources", [])
        except Exception as e:
            print(f"[NewsAPI] get_sources error: {e}")
            return []
