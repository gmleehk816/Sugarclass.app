"""
News collector module - fetches from multiple news APIs and extracts full articles.
Supports multiple extraction methods with auto-detection.

Available API Sources:
- RSS: Traditional RSS feeds + newspaper4k extraction
- NewsAPI: newsapi.org (50+ sources, 100 req/day free)
- GNews: gnews.io (Google News aggregation)
- NewsCatcher: newscatcherapi.com (60k+ sources)
"""
import os
import feedparser
import requests
import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import newspaper4k (upgraded from newspaper3k)
try:
    import newspaper
    HAS_NEWSPAPER4K = True
except ImportError:
    HAS_NEWSPAPER4K = False
    print("[Warning] newspaper4k not installed, using fallback extraction")

from backend.database import (
    insert_article,
    update_source_status,
    log_collection,
    get_sources,
    classify_age_group_from_source,
    classify_age_group_readability,
    normalize_url,
)

# Import new sources
from collector.sources import (
    BaseSource,
    RSSSource,
    NewsAPISource,
    GNewsSource,
    NewsCatcherSource,
)


# User agent for requests
_USER_AGENT = "Mozilla/5.0 (compatible; NewsCollect/1.0)"


# Initialize all available sources
def _get_available_sources() -> Dict[str, BaseSource]:
    """Get all available news sources."""
    return {
        "rss": RSSSource(),
        "newsapi": NewsAPISource(),
        "gnews": GNewsSource(),
        "newscatcher": NewsCatcherSource(),
    }


def get_all_sources_status() -> List[Dict[str, Any]]:
    """Get status of all available sources."""
    sources = _get_available_sources()
    return [source.get_status() for source in sources.values()]


# User agent for requests
_USER_AGENT = "Mozilla/5.0 (compatible; NewsCollect/1.0)"


def _generate_uuid(url: str) -> str:
    """
    Generate a UUID from normalized URL hash.
    Using normalized URL ensures consistent UUIDs for same article regardless of URL variations.
    """
    normalized = normalize_url(url)
    return hashlib.md5(normalized.encode()).hexdigest()


def _extract_text_from_html(html: str) -> Tuple[Optional[str], str]:
    """Extract title and text from HTML using multiple methods."""
    # Method 1: Try JSON-LD articleBody
    script_blocks = re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    def _walk_ld(obj) -> Optional[str]:
        if isinstance(obj, dict):
            if "articleBody" in obj and isinstance(obj.get("articleBody"), str):
                return obj.get("articleBody")
            for v in obj.values():
                found = _walk_ld(v)
                if found:
                    return found
        elif isinstance(obj, list):
            for it in obj:
                found = _walk_ld(it)
                if found:
                    return found
        return None

    for raw in script_blocks:
        raw = raw.strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            continue
        body = _walk_ld(parsed)
        if body and len(body.strip()) > 200:
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, flags=re.IGNORECASE | re.DOTALL)
            title = re.sub(r'\s+', ' ', title_match.group(1)).strip() if title_match else None
            return title, body.strip()

    # Method 2: Extract paragraphs
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, flags=re.IGNORECASE | re.DOTALL)
    title = re.sub(r'\s+', ' ', title_match.group(1)).strip() if title_match else None

    # Remove script/style blocks
    cleaned = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
    cleaned = re.sub(r'<style[\s\S]*?</style>', ' ', cleaned, flags=re.IGNORECASE)

    # Junk patterns to filter
    junk_patterns = [
        r'(?i)find any issues using dark mode',
        r'(?i)please let us know',
        r'(?i)\(?aap\)?',
        r'(?i)\(?ap\)?',
        r'(?i)advertisement',
        r'(?i)subscribe',
        r'(?i)newsletter',
        r'(?i)share this article',
        r'(?i)copy this link',
    ]

    paras = re.findall(r'<p\b[^>]*>(.*?)</p>', cleaned, flags=re.IGNORECASE | re.DOTALL)
    parts: List[str] = []
    seen = set()
    
    for p in paras:
        txt = re.sub(r'<[^>]+>', ' ', p)
        txt = re.sub(r'\s+', ' ', txt).strip()
        if not txt:
            continue
        
        # Filter junk
        is_junk = False
        for pattern in junk_patterns:
            if re.search(pattern, txt):
                is_junk = True
                break
        if is_junk:
            continue
        
        if len(txt) < 25:
            continue
        
        if txt in seen:
            continue
        seen.add(txt)
        
        parts.append(txt)

    text = '\n\n'.join(parts).strip()
    return title, text


def _extract_with_newspaper(url: str) -> Dict[str, Any]:
    """Extract article using newspaper4k library (upgraded from newspaper3k)."""
    if not HAS_NEWSPAPER4K:
        return {"error": "newspaper4k not installed", "url": url}
    
    try:
        article = newspaper.Article(url)
        article.download()
        article.parse()
        
        return {
            "title": article.title,
            "text": article.text,
            "authors": article.authors,
            "publish_date": article.publish_date,
            "top_image": article.top_image,
            "keywords": getattr(article, 'keywords', []),
            "summary": getattr(article, 'summary', ''),
        }
    except Exception as e:
        return {
            "error": f"newspaper4k failed: {str(e)}",
            "url": url,
        }


def _extract_with_requests(url: str) -> Dict[str, Any]:
    """Extract article using requests + HTML parsing."""
    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": _USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        )
        resp.raise_for_status()
        
        title, text = _extract_text_from_html(resp.text)
        
        # Try to extract image
        image_match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            resp.text,
            flags=re.IGNORECASE
        )
        image_url = image_match.group(1) if image_match else None
        
        return {
            "title": title,
            "text": text,
            "top_image": image_url,
        }
    except Exception as e:
        return {
            "error": f"Requests extraction failed: {str(e)}",
            "url": url,
        }


def _extract_full_article(url: str) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    """
    Extract full article with auto-detection of best method.
    Returns: (title, text, image_url, method_used)
    """
    # Try newspaper4k first (most reliable)
    result = _extract_with_newspaper(url)
    if "error" not in result and result.get("text") and len(result["text"]) > 100:
        return (
            result.get("title"),
            result.get("text"),
            result.get("top_image"),
            "newspaper4k"
        )
    
    # Fallback to requests + HTML parsing
    result = _extract_with_requests(url)
    if "error" not in result and result.get("text") and len(result["text"]) > 100:
        return (
            result.get("title"),
            result.get("text"),
            result.get("top_image"),
            "html_parser"
        )
    
    # Both methods failed
    return None, None, None, "failed"


def _infer_category(title: str, description: str, source: str) -> str:
    """Infer category from title and description."""
    text = f"{title} {description}".lower()
    
    category_keywords = {
        "technology": ["tech", "technology", "digital", "software", "ai", "gadget", "computer", "app", "cyber", "internet"],
        "business": ["business", "market", "stock", "economy", "finance", "company", "trade", "startup", "economic"],
        "science": ["science", "research", "study", "discovery", "scientist", "experiment", "space", "climate"],
        "health": ["health", "medical", "doctor", "disease", "hospital", "medicine", "patient", "vaccine", "covid"],
        "sports": ["sport", "team", "game", "player", "coach", "championship", "league", "match", "score", "olympic"],
        "entertainment": ["entertainment", "movie", "music", "celebrity", "film", "actor", "show", "tv", "hollywood"],
        "politics": ["politics", "government", "election", "president", "congress", "senate", "vote", "policy", "political"],
        "world": ["world", "global", "international", "country", "nation", "war", "conflict", "diplomacy"],
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            return category
    
    return "general"


def fetch_rss_feed(rss_url: str) -> List[Dict[str, Any]]:
    """Fetch and parse RSS feed."""
    try:
        resp = requests.get(rss_url, timeout=12, headers={"User-Agent": _USER_AGENT})
        resp.raise_for_status()
        
        feed = feedparser.parse(resp.text)
        
        entries = []
        for entry in feed.entries:
            entries.append({
                "title": entry.get("title", ""),
                "description": entry.get("description", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "image": entry.get("image", ""),
            })
        
        return entries
    except Exception as e:
        print(f"[RSS Error] Failed to fetch {rss_url}: {e}")
        return []


def collect_from_source(domain: str, limit: int = 12) -> Dict[str, Any]:
    """
    Collect news from a single source.
    Returns collection statistics.
    """
    sources = get_sources()
    source_info = next((s for s in sources if s["domain"] == domain), None)
    
    if not source_info:
        return {
            "error": f"Source {domain} not configured",
            "domain": domain,
        }
    
    rss_url = source_info.get("rss_url")
    if not rss_url:
        return {
            "error": f"No RSS URL configured for {domain}",
            "domain": domain,
        }
    
    started_at = datetime.utcnow().isoformat()
    articles_found = 0
    articles_stored = 0
    articles_failed = 0
    error_message = None
    
    try:
        # Fetch RSS feed
        entries = fetch_rss_feed(rss_url)
        articles_found = len(entries)
        
        if not entries:
            error_message = "No articles found in RSS feed"
            update_source_status(domain, "no_feed", error_message)
            return {
                "domain": domain,
                "articles_found": 0,
                "articles_stored": 0,
                "articles_failed": 0,
                "error": error_message,
            }
        
        # Process each article
        for entry in entries[:limit]:
            url = entry.get("link")
            if not url:
                continue
            
            try:
                # Extract full article
                title, full_text, image_url, method = _extract_full_article(url)
                
                # Use RSS data as fallback
                if not title:
                    title = entry.get("title", "")
                if not image_url:
                    image_url = entry.get("image", "")
                
                # Infer category
                category = _infer_category(
                    title or "",
                    entry.get("description", ""),
                    domain
                )

                # Classify age group based on source and content
                word_count = len(full_text.split()) if full_text else 0
                age_group = classify_age_group_from_source(domain, full_text or "", word_count)

                # Prepare article data
                article_data = {
                    "uuid": _generate_uuid(url),
                    "title": title,
                    "description": entry.get("description", ""),
                    "full_text": full_text or "",
                    "url": url,
                    "image_url": image_url,
                    "source": domain,
                    "category": category,
                    "published_at": entry.get("published", ""),
                    "collected_at": datetime.utcnow().isoformat(),
                    "extraction_method": method,
                    "age_group": age_group,  # NEW: Add age group classification
                }
                
                # Store in database
                article_id = insert_article(article_data)
                if article_id:
                    articles_stored += 1
                    print(f"[Collect] Stored: {title[:50]}... ({method})")
                else:
                    articles_failed += 1
                    
            except Exception as e:
                articles_failed += 1
                print(f"[Collect Error] Failed to process {url}: {e}")
        
        # Update source status
        if articles_stored > 0:
            update_source_status(domain, "success")
        else:
            update_source_status(domain, "no_articles")
        
    except Exception as e:
        error_message = str(e)
        update_source_status(domain, "error", error_message)
        print(f"[Collect Error] Failed to collect from {domain}: {e}")
    
    completed_at = datetime.utcnow().isoformat()
    
    # Log collection
    log_collection(
        source=domain,
        articles_found=articles_found,
        articles_stored=articles_stored,
        articles_failed=articles_failed,
        started_at=started_at,
        completed_at=completed_at,
        error_message=error_message
    )
    
    return {
        "domain": domain,
        "articles_found": articles_found,
        "articles_stored": articles_stored,
        "articles_failed": articles_failed,
        "started_at": started_at,
        "completed_at": completed_at,
        "error": error_message,
    }


def collect_all(limit_per_source: int = 12) -> List[Dict[str, Any]]:
    """Collect news from all configured sources."""
    sources = get_sources()
    results = []
    
    for source in sources:
        domain = source["domain"]
        print(f"\n[Collect] Starting collection from {domain}...")
        result = collect_from_source(domain, limit=limit_per_source)
        results.append(result)
        print(f"[Collect] Completed {domain}: {result.get('articles_stored', 0)} articles stored")
    
    return results


def collect_single_article(url: str) -> Optional[Dict[str, Any]]:
    """Collect a single article by URL."""
    try:
        title, full_text, image_url, method = _extract_full_article(url)
        
        if not title:
            return {"error": "Failed to extract article"}
        
        # Infer category from title
        category = _infer_category(title, "", "manual")

        # Get domain from URL
        parsed = urlparse(url)
        domain = parsed.hostname or "unknown"

        # Classify age group
        word_count = len(full_text.split()) if full_text else 0
        age_group = classify_age_group_from_source(domain, full_text or "", word_count)

        article_data = {
            "uuid": _generate_uuid(url),
            "title": title,
            "description": "",
            "full_text": full_text or "",
            "url": url,
            "image_url": image_url,
            "source": domain,
            "category": category,
            "published_at": datetime.utcnow().isoformat(),
            "collected_at": datetime.utcnow().isoformat(),
            "extraction_method": method,
            "age_group": age_group,  # NEW: Add age group classification
        }
        
        article_id = insert_article(article_data)
        if article_id:
            return {
                "success": True,
                "article_id": article_id,
                "uuid": article_data["uuid"],
                "title": title,
                "extraction_method": method,
            }
        else:
            return {"error": "Failed to store article"}
            
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# New API-based Collection Functions
# =============================================================================

def collect_from_api(
    api_source: str,
    query: Optional[str] = None,
    category: Optional[str] = None,
    language: str = "en",
    limit: int = 12,
    extract_full_text: bool = True,
) -> Dict[str, Any]:
    """
    Collect news from a specific API source.
    
    Args:
        api_source: One of 'newsapi', 'gnews', 'newscatcher', 'rss'
        query: Search query (optional)
        category: News category (optional)
        language: Language code (default: 'en')
        limit: Maximum articles to fetch
        extract_full_text: Whether to extract full article text
        
    Returns:
        Collection result with statistics
    """
    sources = _get_available_sources()
    
    if api_source not in sources:
        return {
            "error": f"Unknown API source: {api_source}",
            "available_sources": list(sources.keys()),
        }
    
    source = sources[api_source]
    
    if not source.is_available():
        return {
            "error": f"API source {api_source} is not configured (missing API key)",
            "api_source": api_source,
        }
    
    started_at = datetime.utcnow().isoformat()
    articles_stored = 0
    articles_failed = 0
    
    try:
        # Collect from API source
        result = source.collect(
            query=query,
            category=category,
            language=language,
            limit=limit,
            extract_full_text=extract_full_text,
        )
        
        # Store articles in database
        for article in result.articles:
            try:
                # Classify age group
                word_count = len(article.full_text.split()) if article.full_text else 0
                age_group = classify_age_group_from_source(article.source, article.full_text or "", word_count)

                article_data = {
                    "uuid": _generate_uuid(article.url),
                    "title": article.title,
                    "description": article.description,
                    "full_text": article.full_text,
                    "url": article.url,
                    "image_url": article.image_url,
                    "source": article.source,
                    "category": article.category or _infer_category(
                        article.title, article.description, article.source
                    ),
                    "published_at": article.published_at,
                    "collected_at": datetime.utcnow().isoformat(),
                    "extraction_method": article.extraction_method or api_source,
                    "api_source": api_source,
                    "age_group": age_group,  # NEW: Add age group classification
                }
                
                article_id = insert_article(article_data)
                if article_id:
                    articles_stored += 1
                    print(f"[{api_source}] Stored: {article.title[:50]}...")
                else:
                    articles_failed += 1
                    
            except Exception as e:
                articles_failed += 1
                print(f"[{api_source}] Failed to store article: {e}")
        
        completed_at = datetime.utcnow().isoformat()
        
        # Log collection
        log_collection(
            source=api_source,
            articles_found=result.articles_found,
            articles_stored=articles_stored,
            articles_failed=articles_failed,
            started_at=started_at,
            completed_at=completed_at,
            error_message=result.error,
        )
        
        return {
            "api_source": api_source,
            "query": query,
            "category": category,
            "articles_found": result.articles_found,
            "articles_stored": articles_stored,
            "articles_failed": articles_failed,
            "started_at": started_at,
            "completed_at": completed_at,
            "error": result.error,
        }
        
    except Exception as e:
        return {
            "api_source": api_source,
            "error": str(e),
        }


def collect_from_all_apis(
    query: Optional[str] = None,
    category: Optional[str] = None,
    language: str = "en",
    limit_per_source: int = 12,
) -> List[Dict[str, Any]]:
    """
    Collect news from all available API sources.
    
    Args:
        query: Search query (optional)
        category: News category (optional)
        language: Language code
        limit_per_source: Max articles per API source
        
    Returns:
        List of collection results from each source
    """
    results = []
    sources = _get_available_sources()
    
    for api_name, source in sources.items():
        if not source.is_available():
            print(f"[{api_name}] Skipping - not configured")
            results.append({
                "api_source": api_name,
                "error": "Not configured (missing API key)",
                "articles_found": 0,
                "articles_stored": 0,
            })
            continue
        
        print(f"\n[Collect] Starting collection from {source.display_name}...")
        result = collect_from_api(
            api_source=api_name,
            query=query,
            category=category,
            language=language,
            limit=limit_per_source,
        )
        results.append(result)
        print(f"[Collect] Completed {api_name}: {result.get('articles_stored', 0)} articles stored")
    
    return results


def search_all_apis(
    query: str,
    language: str = "en",
    limit_per_source: int = 12,
) -> Dict[str, Any]:
    """
    Search for news across all available API sources.
    
    Args:
        query: Search query
        language: Language code
        limit_per_source: Max articles per API source
        
    Returns:
        Combined search results with source breakdown
    """
    all_articles = []
    source_stats = []
    
    sources = _get_available_sources()
    
    for api_name, source in sources.items():
        if not source.is_available():
            source_stats.append({
                "api_source": api_name,
                "available": False,
                "articles_found": 0,
            })
            continue
        
        try:
            articles = source.fetch_articles(
                query=query,
                language=language,
                limit=limit_per_source,
            )
            
            for article in articles:
                article.api_source = api_name
                all_articles.append(article.to_dict())
            
            source_stats.append({
                "api_source": api_name,
                "available": True,
                "articles_found": len(articles),
            })
            
        except Exception as e:
            source_stats.append({
                "api_source": api_name,
                "available": True,
                "articles_found": 0,
                "error": str(e),
            })
    
    return {
        "query": query,
        "total_articles": len(all_articles),
        "articles": all_articles,
        "source_breakdown": source_stats,
    }
