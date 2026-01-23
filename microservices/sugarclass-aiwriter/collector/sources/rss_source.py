"""
RSS Source - Traditional RSS feed collection with newspaper4k extraction.
"""
import feedparser
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    import newspaper
    HAS_NEWSPAPER4K = True
except ImportError:
    HAS_NEWSPAPER4K = False

from .base import BaseSource, Article


_USER_AGENT = "Mozilla/5.0 (compatible; NewsCollect/1.0)"


class RSSSource(BaseSource):
    """RSS feed source with newspaper4k article extraction."""
    
    name = "rss"
    display_name = "RSS Feeds"
    requires_api_key = False
    free_tier_limit = 0  # Unlimited
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.rss_feeds: Dict[str, str] = {
            "cnn.com": "http://rss.cnn.com/rss/edition.rss",
            "bbc.com": "http://feeds.bbci.co.uk/news/rss.xml",
            "reuters.com": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
            "nytimes.com": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "theguardian.com": "https://www.theguardian.com/world/rss",
        }
    
    def add_feed(self, domain: str, rss_url: str) -> None:
        """Add or update an RSS feed."""
        self.rss_feeds[domain] = rss_url
    
    def fetch_articles(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
    ) -> List[Article]:
        """Fetch articles from all configured RSS feeds."""
        articles = []
        
        for domain, rss_url in self.rss_feeds.items():
            try:
                entries = self._fetch_feed(rss_url)
                for entry in entries[:limit // len(self.rss_feeds) + 1]:
                    article = Article(
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        description=entry.get("description", ""),
                        source=domain,
                        published_at=entry.get("published", ""),
                        api_source=self.name,
                    )
                    
                    # Filter by query if provided
                    if query:
                        search_text = f"{article.title} {article.description}".lower()
                        if query.lower() not in search_text:
                            continue
                    
                    articles.append(article)
                    
            except Exception as e:
                print(f"[RSS] Failed to fetch {domain}: {e}")
        
        return articles[:limit]
    
    def _fetch_feed(self, rss_url: str) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed."""
        try:
            resp = requests.get(
                rss_url,
                timeout=12,
                headers={"User-Agent": _USER_AGENT}
            )
            resp.raise_for_status()
            
            feed = feedparser.parse(resp.text)
            
            entries = []
            for entry in feed.entries:
                entries.append({
                    "title": entry.get("title", ""),
                    "description": entry.get("description", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                })
            
            return entries
        except Exception as e:
            print(f"[RSS] Error fetching {rss_url}: {e}")
            return []
    
    def extract_full_text(self, url: str) -> Optional[str]:
        """Extract full article text using newspaper4k."""
        if not HAS_NEWSPAPER4K:
            return self._extract_with_requests(url)
        
        try:
            article = newspaper.Article(url)
            article.download()
            article.parse()
            
            if article.text and len(article.text) > 100:
                return article.text
            
        except Exception as e:
            print(f"[RSS] newspaper4k failed for {url}: {e}")
        
        # Fallback to requests-based extraction
        return self._extract_with_requests(url)
    
    def _extract_with_requests(self, url: str) -> Optional[str]:
        """Fallback extraction using requests + HTML parsing."""
        import re
        
        try:
            resp = requests.get(
                url,
                timeout=15,
                headers={"User-Agent": _USER_AGENT, "Accept": "text/html"}
            )
            resp.raise_for_status()
            
            html = resp.text
            
            # Remove script/style blocks
            html = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
            html = re.sub(r'<style[\s\S]*?</style>', ' ', html, flags=re.IGNORECASE)
            
            # Extract paragraphs
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
            print(f"[RSS] Fallback extraction failed for {url}: {e}")
            return None
