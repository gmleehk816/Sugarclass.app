"""
Enhanced extraction pipeline with multiple libraries.
Fallback chain: trafilatura → newspaper4k → fundus → custom HTML parser

Each extractor returns (title, text, metadata) tuple.
"""
import re
import json
from typing import Optional, Tuple, Dict
from urllib.parse import urlparse


# === Extractor 1: Trafilatura (Primary) ===
try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False
    print("[Warning] trafilatura not installed")


def extract_with_trafilatura(html: str, url: str) -> Tuple[Optional[str], str, Dict]:
    """Extract using trafilatura (fast, high precision)."""
    if not HAS_TRAFILATURA:
        return None, "", {}
    
    try:
        # Extract with metadata
        result = trafilatura.extract(
            html,
            include_links=False,
            include_images=False,
            include_tables=False,
            output_format='json',
            url=url
        )
        
        if result:
            data = json.loads(result)
            title = data.get('title')
            text = data.get('text', '')
            
            metadata = {
                'author': data.get('author'),
                'date': data.get('date'),
                'description': data.get('description'),
                'sitename': data.get('sitename'),
            }
            
            if text and len(text.strip()) > 100:
                return title, text.strip(), metadata
    
    except Exception as e:
        print(f"[Trafilatura Error] {e}")
    
    return None, "", {}


# === Extractor 2: newspaper4k (Fallback) ===
try:
    import newspaper
    from newspaper import Article as Newspaper4kArticle
    HAS_NEWSPAPER4K = True
except ImportError:
    HAS_NEWSPAPER4K = False
    print("[Warning] newspaper4k not installed")


def extract_with_newspaper4k(html: str, url: str) -> Tuple[Optional[str], str, Dict]:
    """Extract using newspaper4k (async, multilingual)."""
    if not HAS_NEWSPAPER4K:
        return None, "", {}
    
    try:
        article = Newspaper4kArticle(url)
        article.set_html(html)
        article.parse()
        article.nlp()
        
        title = article.title
        text = article.text
        
        metadata = {
            'author': ', '.join(article.authors) if article.authors else None,
            'date': article.publish_date.isoformat() if article.publish_date else None,
            'summary': article.summary,
            'keywords': article.keywords,
            'top_image': article.top_image,
        }
        
        if text and len(text.strip()) > 100:
            return title, text.strip(), metadata
    
    except Exception as e:
        print(f"[Newspaper4k Error] {e}")
    
    return None, "", {}


# === Extractor 3: Fundus (Validation) ===
try:
    from fundus import PublisherCollection, Crawler
    HAS_FUNDUS = True
except ImportError:
    HAS_FUNDUS = False
    print("[Warning] fundus not installed")


def extract_with_fundus(html: str, url: str) -> Tuple[Optional[str], str, Dict]:
    """Extract using fundus (dedup + NLP tagging)."""
    if not HAS_FUNDUS:
        return None, "", {}
    
    try:
        # Fundus works best with live URLs, but we can try with HTML
        # This is a simplified version - real usage would fetch from URL
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Note: Fundus is designed for live crawling, not HTML parsing
        # This is a placeholder for future enhancement
        print(f"[Fundus] Skipping (designed for live URLs): {domain}")
        
    except Exception as e:
        print(f"[Fundus Error] {e}")
    
    return None, "", {}


# === Extractor 4: news-please (Backup) ===
try:
    from newsplease import NewsPlease
    HAS_NEWS_PLEASE = True
except ImportError:
    HAS_NEWS_PLEASE = False
    print("[Warning] news-please not installed")


def extract_with_news_please(html: str, url: str) -> Tuple[Optional[str], str, Dict]:
    """Extract using news-please (research-grade metadata)."""
    if not HAS_NEWS_PLEASE:
        return None, "", {}
    
    try:
        article = NewsPlease.from_html(html, url=url)
        
        title = article.title
        text = article.maintext
        
        metadata = {
            'author': ', '.join(article.authors) if article.authors else None,
            'date': article.date_publish.isoformat() if article.date_publish else None,
            'description': article.description,
            'source': article.source_domain,
            'language': article.language,
        }
        
        if text and len(text.strip()) > 100:
            return title, text.strip(), metadata
    
    except Exception as e:
        print(f"[NewsPlease Error] {e}")
    
    return None, "", {}


# === Extractor 5: Custom HTML Parser (Last Resort) ===
def extract_with_custom_parser(html: str, url: str) -> Tuple[Optional[str], str, Dict]:
    """Custom regex-based HTML extraction (fallback)."""
    try:
        # Extract title
        title_match = re.search(
            r'<title[^>]*>(.*?)</title>',
            html,
            flags=re.IGNORECASE | re.DOTALL
        )
        title = re.sub(r'\s+', ' ', title_match.group(1)).strip() if title_match else None
        
        # Try JSON-LD articleBody first
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
            if body and len(body.strip()) > 100:
                return title, body.strip(), {}
        
        # Fall back to paragraph extraction
        cleaned = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
        cleaned = re.sub(r'<style[\s\S]*?</style>', ' ', cleaned, flags=re.IGNORECASE)
        
        paras = re.findall(r'<p\b[^>]*>(.*?)</p>', cleaned, flags=re.IGNORECASE | re.DOTALL)
        parts = []
        seen = set()
        
        for p in paras:
            txt = re.sub(r'<[^>]+>', ' ', p)
            txt = re.sub(r'\s+', ' ', txt).strip()
            if txt and len(txt) > 20 and txt not in seen:
                parts.append(txt)
                seen.add(txt)
        
        text = '\n\n'.join(parts)
        
        if text and len(text.strip()) > 100:
            return title, text.strip(), {}
    
    except Exception as e:
        print(f"[CustomParser Error] {e}")
    
    return None, "", {}


# === Main Extraction Pipeline ===
def extract_article(
    html: str,
    url: str,
    preferred_method: Optional[str] = None
) -> Tuple[Optional[str], str, str, Dict]:
    """
    Extract article using fallback chain.
    
    Args:
        html: Raw HTML content
        url: Article URL
        preferred_method: Optional preferred extractor
    
    Returns:
        (title, text, method_used, metadata) tuple
    """
    extractors = [
        ("trafilatura", extract_with_trafilatura),
        ("newspaper4k", extract_with_newspaper4k),
        ("news-please", extract_with_news_please),
        ("custom", extract_with_custom_parser),
    ]
    
    # Try preferred method first
    if preferred_method:
        for name, func in extractors:
            if name == preferred_method:
                title, text, metadata = func(html, url)
                if text:
                    return title, text, name, metadata
    
    # Try all extractors in order
    for name, func in extractors:
        title, text, metadata = func(html, url)
        if text:
            print(f"[Extraction] Success with {name}: {len(text)} chars")
            return title, text, name, metadata
    
    # All failed
    print(f"[Extraction] All methods failed for {url}")
    return None, "", "failed", {}


# === Test Function ===
if __name__ == "__main__":
    import requests
    
    # Test URL
    test_url = "https://www.bbc.com/news/articles/c62j3y7x10no"
    
    print(f"Testing extraction pipeline on: {test_url}\n")
    
    try:
        response = requests.get(test_url, timeout=10)
        html = response.text
        
        title, text, method, metadata = extract_article(html, test_url)
        
        print(f"=== Results ===")
        print(f"Method Used: {method}")
        print(f"Title: {title}")
        print(f"Text Length: {len(text)} chars")
        print(f"Metadata: {metadata}")
        print(f"\nFirst 500 chars:\n{text[:500]}...")
    
    except Exception as e:
        print(f"Test failed: {e}")
