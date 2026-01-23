"""
Base source class - abstract interface for all news sources.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    """Standardized article data structure."""
    title: str
    url: str
    description: str = ""
    full_text: str = ""
    image_url: str = ""
    source: str = ""
    category: str = "general"
    published_at: str = ""
    authors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    extraction_method: str = ""
    api_source: str = ""  # Which API provided this article
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "full_text": self.full_text,
            "image_url": self.image_url,
            "source": self.source,
            "category": self.category,
            "published_at": self.published_at,
            "authors": self.authors,
            "keywords": self.keywords,
            "extraction_method": self.extraction_method,
            "api_source": self.api_source,
        }


@dataclass
class CollectionResult:
    """Result of a collection operation."""
    source_name: str
    api_source: str
    articles_found: int = 0
    articles_stored: int = 0
    articles_failed: int = 0
    started_at: str = ""
    completed_at: str = ""
    error: Optional[str] = None
    articles: List[Article] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "api_source": self.api_source,
            "articles_found": self.articles_found,
            "articles_stored": self.articles_stored,
            "articles_failed": self.articles_failed,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


class BaseSource(ABC):
    """Abstract base class for all news sources."""
    
    # Source name identifier
    name: str = "base"
    
    # Display name for UI
    display_name: str = "Base Source"
    
    # Whether this source requires an API key
    requires_api_key: bool = False
    
    # Free tier limits (requests per day)
    free_tier_limit: int = 0
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the source with optional API key."""
        self.api_key = api_key
        self._request_count = 0
    
    @abstractmethod
    def fetch_articles(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
    ) -> List[Article]:
        """
        Fetch articles from the source.
        
        Args:
            query: Search query (optional)
            category: News category (optional)
            language: Language code (default: "en")
            limit: Maximum number of articles to fetch
            
        Returns:
            List of Article objects
        """
        pass
    
    @abstractmethod
    def extract_full_text(self, url: str) -> Optional[str]:
        """
        Extract full article text from URL.
        
        Args:
            url: Article URL
            
        Returns:
            Full article text or None if extraction failed
        """
        pass
    
    def collect(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
        extract_full_text: bool = True,
    ) -> CollectionResult:
        """
        Full collection workflow: fetch articles and optionally extract full text.
        
        Args:
            query: Search query (optional)
            category: News category (optional)
            language: Language code
            limit: Maximum articles to fetch
            extract_full_text: Whether to extract full article text
            
        Returns:
            CollectionResult with statistics
        """
        started_at = datetime.utcnow().isoformat()
        result = CollectionResult(
            source_name=self.display_name,
            api_source=self.name,
            started_at=started_at,
        )
        
        try:
            # Fetch articles from API
            articles = self.fetch_articles(
                query=query,
                category=category,
                language=language,
                limit=limit,
            )
            result.articles_found = len(articles)
            
            # Extract full text if requested
            if extract_full_text:
                for article in articles:
                    if not article.full_text:
                        try:
                            full_text = self.extract_full_text(article.url)
                            if full_text:
                                article.full_text = full_text
                                article.extraction_method = self.name
                        except Exception as e:
                            print(f"[{self.name}] Failed to extract {article.url}: {e}")
            
            result.articles = articles
            result.articles_stored = len([a for a in articles if a.full_text])
            result.articles_failed = len([a for a in articles if not a.full_text])
            
        except Exception as e:
            result.error = str(e)
            print(f"[{self.name}] Collection error: {e}")
        
        result.completed_at = datetime.utcnow().isoformat()
        return result
    
    def is_available(self) -> bool:
        """Check if this source is available (API key configured if required)."""
        if self.requires_api_key:
            return bool(self.api_key)
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get source status information."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "available": self.is_available(),
            "requires_api_key": self.requires_api_key,
            "free_tier_limit": self.free_tier_limit,
            "request_count": self._request_count,
        }
