"""
News sources module - provides different API sources for news collection.

Available sources:
- RSS: Traditional RSS feed collection with newspaper4k extraction
- NewsAPI: newsapi.org - 50+ sources, 100 req/day free tier
- GNews: gnews.io - Google News aggregation
- NewsCatcher: newscatcherapi.com - 60k+ sources
"""

from .base import BaseSource
from .rss_source import RSSSource
from .newsapi_source import NewsAPISource
from .gnews_source import GNewsSource
from .newscatcher_source import NewsCatcherSource

__all__ = [
    "BaseSource",
    "RSSSource",
    "NewsAPISource",
    "GNewsSource",
    "NewsCatcherSource",
]
