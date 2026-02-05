"""
Kid-focused news sources for ages 7-16.
Provides RSS feeds and web scraping configurations for educational news sites.
"""
import feedparser
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from sources.base import BaseSource, Article, CollectionResult


class BBCNewsroundSource(BaseSource):
    """
    BBC Newsround - UK news for kids (age 7-13)
    https://www.bbc.co.uk/newsround
    """
    
    def __init__(self):
        self.name = "BBC Newsround"
        self.api_source = "bbc_newsround"
        self.rss_url = "https://feeds.bbci.co.uk/newsround/rss.xml"
        self.base_url = "https://www.bbc.co.uk/newsround"
    
    def fetch_articles(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> CollectionResult:
        """Fetch articles from BBC Newsround RSS feed."""
        result = CollectionResult(
            source_name=self.name,
            api_source=self.api_source
        )
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(self.rss_url)
            
            articles = []
            for entry in feed.entries[:limit]:
                article = Article(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    description=entry.get('summary', ''),
                    source=self.name,
                    category="kids_news",
                    published_at=self._parse_date(entry.get('published')),
                    api_source=self.api_source,
                    extraction_method="rss"
                )
                articles.append(article)
            
            result.articles_found = len(articles)
            return result
        
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return result


class DogoNewsSource(BaseSource):
    """
    Dogo News - Current events for kids (age 7-12)
    https://www.dogonews.com
    """
    
    def __init__(self):
        self.name = "Dogo News"
        self.api_source = "dogo_news"
        self.rss_urls = {
            "general": "https://www.dogonews.com/rss",
            "science": "https://www.dogonews.com/category/science/rss",
            "environment": "https://www.dogonews.com/category/environment/rss",
            "social_studies": "https://www.dogonews.com/category/social-studies/rss",
        }
        self.base_url = "https://www.dogonews.com"
    
    def fetch_articles(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> CollectionResult:
        """Fetch articles from Dogo News RSS feeds."""
        result = CollectionResult(
            source_name=self.name,
            api_source=self.api_source
        )
        
        try:
            # Determine which RSS feed to use
            rss_url = self.rss_urls.get(category or "general", self.rss_urls["general"])
            
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            articles = []
            for entry in feed.entries[:limit]:
                article = Article(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    description=entry.get('summary', ''),
                    source=self.name,
                    category=category or "general",
                    published_at=self._parse_date(entry.get('published')),
                    api_source=self.api_source,
                    extraction_method="rss"
                )
                articles.append(article)
            
            result.articles_found = len(articles)
            return result
        
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return result


class TimeForKidsSource(BaseSource):
    """
    Time for Kids - News magazine for elementary/middle school
    https://www.timeforkids.com
    """
    
    def __init__(self):
        self.name = "Time for Kids"
        self.api_source = "time_for_kids"
        self.rss_urls = {
            "k1": "https://www.timeforkids.com/k1/feed/",  # Kindergarten-Grade 1
            "g2": "https://www.timeforkids.com/g2/feed/",  # Grade 2
            "g34": "https://www.timeforkids.com/g34/feed/",  # Grades 3-4
            "g56": "https://www.timeforkids.com/g56/feed/",  # Grades 5-6
        }
        self.base_url = "https://www.timeforkids.com"
    
    def fetch_articles(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> CollectionResult:
        """Fetch articles from Time for Kids RSS feeds."""
        result = CollectionResult(
            source_name=self.name,
            api_source=self.api_source
        )
        
        try:
            # Use grade level as category (default g34 for ages 7-10)
            rss_url = self.rss_urls.get(category or "g34", self.rss_urls["g34"])
            
            feed = feedparser.parse(rss_url)
            
            articles = []
            for entry in feed.entries[:limit]:
                article = Article(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    description=entry.get('summary', ''),
                    source=self.name,
                    category=category or "g34",
                    published_at=self._parse_date(entry.get('published')),
                    api_source=self.api_source,
                    extraction_method="rss"
                )
                articles.append(article)
            
            result.articles_found = len(articles)
            return result
        
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return result


class NatGeoKidsSource(BaseSource):
    """
    National Geographic Kids - Science & nature for kids
    https://kids.nationalgeographic.com
    """
    
    def __init__(self):
        self.name = "National Geographic Kids"
        self.api_source = "natgeo_kids"
        self.api_url = "https://kids.nationalgeographic.com/feed"
        self.base_url = "https://kids.nationalgeographic.com"
    
    def fetch_articles(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> CollectionResult:
        """Fetch articles from Nat Geo Kids RSS."""
        result = CollectionResult(
            source_name=self.name,
            api_source=self.api_source
        )
        
        try:
            feed = feedparser.parse(self.api_url)
            
            articles = []
            for entry in feed.entries[:limit]:
                article = Article(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    description=entry.get('summary', ''),
                    source=self.name,
                    category="science_nature",
                    published_at=self._parse_date(entry.get('published')),
                    api_source=self.api_source,
                    extraction_method="rss"
                )
                
                # Try to extract image
                if hasattr(entry, 'media_content'):
                    article.image_url = entry.media_content[0].get('url', '')
                
                articles.append(article)
            
            result.articles_found = len(articles)
            return result
        
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return result


class NewselaSource(BaseSource):
    """
    Newsela - Leveled news articles (age 11-16)
    https://newsela.com
    Note: Free tier has limited RSS access
    """
    
    def __init__(self):
        self.name = "Newsela"
        self.api_source = "newsela"
        self.base_url = "https://newsela.com"
        # Newsela requires account, but has public article URLs
    
    def fetch_articles(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> CollectionResult:
        """
        Newsela requires authentication for full access.
        This is a placeholder for future implementation.
        """
        result = CollectionResult(
            source_name=self.name,
            api_source=self.api_source
        )
        
        print(f"[{self.name}] Note: Requires account for full RSS access")
        return result


class SCMPYoungPostSource(BaseSource):
    """
    SCMP Young Post - Hong Kong news for students (age 11-18)
    https://yp.scmp.com
    """
    
    def __init__(self):
        self.name = "SCMP Young Post"
        self.api_source = "scmp_young_post"
        self.rss_url = "https://yp.scmp.com/rss/all"
        self.base_url = "https://yp.scmp.com"
    
    def fetch_articles(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> CollectionResult:
        """Fetch articles from SCMP Young Post RSS."""
        result = CollectionResult(
            source_name=self.name,
            api_source=self.api_source
        )
        
        try:
            feed = feedparser.parse(self.rss_url)
            
            articles = []
            for entry in feed.entries[:limit]:
                article = Article(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    description=entry.get('summary', ''),
                    source=self.name,
                    category=category or "hong_kong",
                    published_at=self._parse_date(entry.get('published')),
                    api_source=self.api_source,
                    extraction_method="rss"
                )
                articles.append(article)
            
            result.articles_found = len(articles)
            return result
        
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return result


# Registry of all kid-news sources
KIDS_SOURCES = {
    "bbc_newsround": BBCNewsroundSource,
    # "dogo_news": DogoNewsSource,  # Removed: RSS feed not available (404)
    "time_for_kids": TimeForKidsSource,
    # "natgeo_kids": NatGeoKidsSource,  # Removed: RSS feed not available (404)
    "newsela": NewselaSource,
    "scmp_young_post": SCMPYoungPostSource,
}


def get_kids_sources() -> Dict[str, BaseSource]:
    """Get all available kid-news sources."""
    return {name: cls() for name, cls in KIDS_SOURCES.items()}


def get_sources_by_age_group(age_group: str) -> Dict[str, BaseSource]:
    """
    Get sources appropriate for age group.

    Args:
        age_group: "7-10", "11-13", or "14-16"

    Returns:
        Dictionary of source_name: source_instance
    """
    if age_group == "7-10":
        return {
            "bbc_newsround": BBCNewsroundSource(),
            # "dogo_news": DogoNewsSource(),  # Removed: RSS feed not available (404)
            "time_for_kids": TimeForKidsSource(),
            # "natgeo_kids": NatGeoKidsSource(),  # Removed: RSS feed not available (404)
        }
    elif age_group == "11-13":
        return {
            "bbc_newsround": BBCNewsroundSource(),
            # "dogo_news": DogoNewsSource(),  # Removed: RSS feed not available (404)
            "time_for_kids": TimeForKidsSource(),
            "scmp_young_post": SCMPYoungPostSource(),
        }
    elif age_group == "14-16":
        return {
            "newsela": NewselaSource(),
            "scmp_young_post": SCMPYoungPostSource(),
        }
    else:
        return get_kids_sources()


# Test function
if __name__ == "__main__":
    print("Testing kid-news sources...\n")
    
    # Test BBC Newsround
    print("=== BBC Newsround ===")
    bbc = BBCNewsroundSource()
    result = bbc.fetch_articles(limit=5)
    print(f"Found: {result.articles_found} articles")
    
    # Test Dogo News
    print("\n=== Dogo News ===")
    dogo = DogoNewsSource()
    result = dogo.fetch_articles(category="science", limit=5)
    print(f"Found: {result.articles_found} articles")
    
    # Test Time for Kids
    print("\n=== Time for Kids ===")
    tfk = TimeForKidsSource()
    result = tfk.fetch_articles(category="g34", limit=5)
    print(f"Found: {result.articles_found} articles")
    
    # Show age-grouped sources
    print("\n=== Age Grouped Sources ===")
    for age_group in ["7-10", "11-13", "14-16"]:
        sources = get_sources_by_age_group(age_group)
        print(f"{age_group}: {', '.join(sources.keys())}")
