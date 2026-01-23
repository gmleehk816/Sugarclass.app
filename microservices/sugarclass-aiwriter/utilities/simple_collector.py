# -*- coding: utf-8 -*-
"""
Simple RSS Collector - Collects articles from free RSS sources
No complex dependencies, direct database access
"""
import sys
import os
import time

# Set UTF-8 encoding for stdout on Windows (only if not already wrapped)
if sys.platform == "win32" and not isinstance(sys.stdout, type(sys.stdin)):
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass  # Already wrapped or unavailable

import feedparser
import requests
import sqlite3
import hashlib
import uuid as uuid_lib
from datetime import datetime
from contextlib import contextmanager

# Add smart classifier
try:
    from smart_classifier import classify_article_with_llm, extract_failed_content_with_llm
    SMART_CLASSIFICATION = True
except ImportError:
    SMART_CLASSIFICATION = False
    print("Warning: smart_classifier not available, using fallback classification")

# Configuration
ARTICLES_PER_SOURCE = 10
DB_PATH = "newscollect.db"

SOURCES = [
    # Kids News
    {
        "name": "BBC Newsround",
        "rss_url": "https://feeds.bbci.co.uk/newsround/rss.xml",
        "category": "kids_news",
    },
    {
        "name": "Dogo News",
        "rss_url": "https://www.dogonews.com/rss",
        "category": "kids_news",
    },
    {
        "name": "Time for Kids",
        "rss_url": "https://www.timeforkids.com/g34/feed/",
        "category": "kids_news",
    },
    
    # General News
    {
        "name": "CNN News",
        "rss_url": "http://rss.cnn.com/rss/edition.rss",
        "category": "general",
    },
    {
        "name": "BBC World News",
        "rss_url": "http://feeds.bbci.co.uk/news/rss.xml",
        "category": "general",
    },
    
    # Science & Space
    {
        "name": "NASA",
        "rss_url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "category": "science",
    },
    {
        "name": "NASA Space Station",
        "rss_url": "https://www.nasa.gov/rss/dyn/shuttle_station.rss",
        "category": "science",
    },
    {
        "name": "NASA Image of the Day",
        "rss_url": "https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss",
        "category": "science",
    },
    {
        "name": "National Geographic",
        "rss_url": "https://www.nationalgeographic.com/pages/article/feeds/all",
        "category": "science",
    },
    {
        "name": "Smithsonian Magazine",
        "rss_url": "https://www.smithsonianmag.com/rss/latest_articles/",
        "category": "science",
    },
    {
        "name": "Live Science",
        "rss_url": "https://www.livescience.com/feeds/all",
        "category": "science",
    },
    {
        "name": "Space.com",
        "rss_url": "https://www.space.com/feeds/all",
        "category": "science",
    },
    {
        "name": "EarthSky",
        "rss_url": "https://earthsky.org/feed",
        "category": "science",
    },
    
    # Educational
    {
        "name": "Smithsonian Science",
        "rss_url": "https://www.smithsonianmag.com/rss/science/",
        "category": "education",
    },
    {
        "name": "TED Blog",
        "rss_url": "https://blog.ted.com/feed/",
        "category": "education",
    },
    {
        "name": "Khan Academy Blog",
        "rss_url": "https://blog.khanacademy.org/feed/",
        "category": "education",
    },
    
    # Research & Academic (Open Access)
    {
        "name": "ScienceDaily",
        "rss_url": "https://www.sciencedaily.com/rss/all.xml",
        "category": "research",
    },
    {
        "name": "Phys.org",
        "rss_url": "https://phys.org/rss-feed/",
        "category": "research",
    },
    {
        "name": "MIT News",
        "rss_url": "https://news.mit.edu/rss/feed",
        "category": "research",
    },
    {
        "name": "Stanford News",
        "rss_url": "https://news.stanford.edu/feed/",
        "category": "research",
    },
    {
        "name": "The Conversation",
        "rss_url": "https://theconversation.com/articles.atom",
        "category": "research",
    },
    {
        "name": "Ars Technica Science",
        "rss_url": "https://feeds.arstechnica.com/arstechnica/science",
        "category": "tech",
    },
    
    # Environment & Nature
    {
        "name": "Climate Central",
        "rss_url": "https://www.climatecentral.org/feed",
        "category": "environment",
    },
    {
        "name": "Mongabay",
        "rss_url": "https://news.mongabay.com/feed/",
        "category": "environment",
    },
    {
        "name": "Treehugger",
        "rss_url": "https://www.treehugger.com/feeds/rss",
        "category": "environment",
    },
    
    # Technology & Innovation
    {
        "name": "The Verge Science",
        "rss_url": "https://www.theverge.com/rss/science/index.xml",
        "category": "tech",
    },
    {
        "name": "Wired Science",
        "rss_url": "https://www.wired.com/feed/category/science/latest/rss",
        "category": "tech",
    },
    
    # History & Culture
    {
        "name": "History.com",
        "rss_url": "https://www.history.com/rss",
        "category": "history",
    },
    {
        "name": "Smithsonian History",
        "rss_url": "https://www.smithsonianmag.com/rss/history/",
        "category": "history",
    },
    {
        "name": "Atlas Obscura",
        "rss_url": "https://www.atlasobscura.com/feeds/latest",
        "category": "culture",
    },
    
    # Health & Wellness (Age-appropriate)
    {
        "name": "NIH News",
        "rss_url": "https://www.nih.gov/news-events/news-releases/rss",
        "category": "health",
    },
    {
        "name": "Mayo Clinic News",
        "rss_url": "https://newsnetwork.mayoclinic.org/feed/",
        "category": "health",
    },
    
    # NEW DIVERSE SOURCES - General News for All Ages
    {
        "name": "NPR News",
        "rss_url": "https://feeds.npr.org/1001/rss.xml",
        "category": "general",
    },
    {
        "name": "NPR World News",
        "rss_url": "https://feeds.npr.org/1004/rss.xml",
        "category": "general",
    },
    {
        "name": "The Guardian World",
        "rss_url": "https://www.theguardian.com/world/rss",
        "category": "general",
    },
    {
        "name": "The Guardian Culture",
        "rss_url": "https://www.theguardian.com/culture/rss",
        "category": "culture",
    },
    {
        "name": "Vox",
        "rss_url": "https://www.vox.com/rss/index.xml",
        "category": "general",
    },
    # Removed: The Atlantic (paywall)
    {
        "name": "ProPublica",
        "rss_url": "https://www.propublica.org/feeds/propublica/main",
        "category": "general",
    },
    {
        "name": "Reuters World News",
        "rss_url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "category": "general",
    },
    {
        "name": "Al Jazeera",
        "rss_url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "general",
    },
    
    # Entertainment & Gaming (11-13, 14-16)
    {
        "name": "Polygon",
        "rss_url": "https://www.polygon.com/rss/index.xml",
        "category": "entertainment",
    },
    {
        "name": "IGN All",
        "rss_url": "http://feeds.ign.com/ign/all",
        "category": "entertainment",
    },
    # Removed: Rolling Stone (paywall)
    {
        "name": "Pitchfork",
        "rss_url": "https://pitchfork.com/rss/news/",
        "category": "entertainment",
    },
    
    # Sports (All Ages)
    {
        "name": "ESPN",
        "rss_url": "https://www.espn.com/espn/rss/news",
        "category": "sports",
    },
    {
        "name": "ESPN Soccer",
        "rss_url": "https://www.espn.com/espn/rss/soccer/news",
        "category": "sports",
    },
    
    # Arts & Design (14-16, 17+)
    {
        "name": "Artnet News",
        "rss_url": "https://news.artnet.com/feed",
        "category": "arts",
    },
    {
        "name": "Hyperallergic",
        "rss_url": "https://hyperallergic.com/feed/",
        "category": "arts",
    },
    
    # Higher Education (17+)
    {
        "name": "Inside Higher Ed",
        "rss_url": "https://www.insidehighered.com/rss.xml",
        "category": "education",
    },
    
    # === NEW SOURCES FOR BETTER COVERAGE ===
    
    # Nature & Environment (Critical Gap - 10 sources)
    {
        "name": "Earth.com",
        "rss_url": "https://www.earth.com/news/feed/",
        "category": "environment",
    },
    {
        "name": "MongabayKids",
        "rss_url": "https://kids.mongabay.com/feed/",
        "category": "environment",
    },
    {
        "name": "NASA Climate Kids",
        "rss_url": "https://climatekids.nasa.gov/feed/",
        "category": "environment",
    },
    {
        "name": "National Geographic Kids Animals",
        "rss_url": "https://www.natgeokids.com/uk/category/discover/animals/feed/",
        "category": "environment",
    },
    {
        "name": "EcoWatch",
        "rss_url": "https://www.ecowatch.com/feed",
        "category": "environment",
    },
    {
        "name": "TreeHugger",
        "rss_url": "https://www.treehugger.com/feeds/rss",
        "category": "environment",
    },
    {
        "name": "Science Daily Environment",
        "rss_url": "https://www.sciencedaily.com/rss/earth_climate/environment.xml",
        "category": "environment",
    },
    {
        "name": "Our Planet Today",
        "rss_url": "https://ourplanettoday.com/feed/",
        "category": "environment",
    },
    {
        "name": "Climate Change News",
        "rss_url": "https://www.climatechangenews.com/feed/",
        "category": "environment",
    },
    {
        "name": "Ocean Conservancy News",
        "rss_url": "https://oceanconservancy.org/blog/feed/",
        "category": "environment",
    },
    
    # History & Geography (Critical Gap - 8 sources)
    {
        "name": "History.com News",
        "rss_url": "https://www.history.com/news/rss",
        "category": "history",
    },
    {
        "name": "Ancient Origins",
        "rss_url": "https://www.ancient-origins.net/rss.xml",
        "category": "history",
    },
    {
        "name": "Archaeology Magazine",
        "rss_url": "https://www.archaeology.org/feed",
        "category": "history",
    },
    {
        "name": "National Geographic History",
        "rss_url": "https://www.nationalgeographic.com/history/rss",
        "category": "history",
    },
    {
        "name": "Smithsonian History",
        "rss_url": "https://www.smithsonianmag.com/rss/history/",
        "category": "history",
    },
    {
        "name": "World History Encyclopedia",
        "rss_url": "https://www.worldhistory.org/rss/articles/",
        "category": "history",
    },
    {
        "name": "National Geographic Travel",
        "rss_url": "https://www.nationalgeographic.com/travel/rss",
        "category": "history",
    },
    {
        "name": "Lonely Planet News",
        "rss_url": "https://www.lonelyplanet.com/news/rss",
        "category": "history",
    },
    
    # Lifestyle (Critical Gap - 6 sources)
    {
        "name": "TeenVogue Lifestyle",
        "rss_url": "https://www.teenvogue.com/feed/category/lifestyle/rss",
        "category": "lifestyle",
    },
    {
        "name": "Seventeen Lifestyle",
        "rss_url": "https://www.seventeen.com/rss/lifestyle.xml",
        "category": "lifestyle",
    },
    {
        "name": "Girls Life",
        "rss_url": "https://www.girlslife.com/feed/",
        "category": "lifestyle",
    },
    {
        "name": "KidsHealth",
        "rss_url": "https://kidshealth.org/rss/recent-articles.xml",
        "category": "lifestyle",
    },
    {
        "name": "Rookie Mag",
        "rss_url": "https://www.rookiemag.com/feed/",
        "category": "lifestyle",
    },
    {
        "name": "The Art of Simple",
        "rss_url": "https://theartofsimple.net/feed/",
        "category": "lifestyle",
    },
    
    # Social Issues (Moderate Gap - 5 sources)
    {
        "name": "PBS Kids News",
        "rss_url": "https://www.pbs.org/newshour/extra/feed/",
        "category": "social",
    },
    {
        "name": "Scholastic News",
        "rss_url": "https://www.scholastic.com/feed/",
        "category": "social",
    },
    {
        "name": "ACLU News",
        "rss_url": "https://www.aclu.org/news/feed",
        "category": "social",
    },
    {
        "name": "Facing History",
        "rss_url": "https://www.facinghistory.org/feed",
        "category": "social",
    },
    {
        "name": "Learning for Justice",
        "rss_url": "https://www.learningforjustice.org/rss.xml",
        "category": "social",
    },
    
    # Education (Moderate Gap - 3 sources - Khan Academy already exists)
    {
        "name": "Edutopia",
        "rss_url": "https://www.edutopia.org/rss.xml",
        "category": "education",
    },
    {
        "name": "TeachThought",
        "rss_url": "https://www.teachthought.com/feed/",
        "category": "education",
    },
    {
        "name": "Education Week",
        "rss_url": "https://www.edweek.org/rss/blogs.rss",
        "category": "education",
    },
    
    # Business & Economics (Moderate Gap - 5 sources)
    {
        "name": "Young Money",
        "rss_url": "https://youngmoney.com/feed/",
        "category": "business",
    },
    {
        "name": "EconEdLink",
        "rss_url": "https://www.econedlink.org/feed/",
        "category": "business",
    },
    {
        "name": "BizKid$",
        "rss_url": "https://bizkids.com/feed/",
        "category": "business",
    },
    {
        "name": "Junior Achievement Blog",
        "rss_url": "https://www.juniorachievement.org/web/ja-usa/blog/-/blogs/rss",
        "category": "business",
    },
    {
        "name": "The Mint",
        "rss_url": "https://themint.org/feed/",
        "category": "business",
    },
    
    # Removed: Harvard Business Review (paywall)
]

# Note: Economist also removed (paywall) - was not in this list

USER_AGENT = "Mozilla/5.0 (compatible; NewsCollect/2.0)"


@contextmanager
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database if needed"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                title TEXT,
                url TEXT UNIQUE,
                source TEXT,
                description TEXT,
                full_text TEXT,
                has_full_article INTEGER DEFAULT 0,
                published_at TEXT,
                collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                image_url TEXT,
                word_count INTEGER DEFAULT 0,
                extraction_method TEXT,
                category TEXT,
                age_group TEXT,
                readability_score REAL,
                grade_level REAL,
                quality_score INTEGER,
                quality_check_status TEXT,
                quality_check_at TEXT
            )
        """)
        print("Database initialized")


def extract_text_simple(html: str) -> str:
    """Simple HTML text extraction"""
    import re
    # Remove scripts and styles
    cleaned = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
    cleaned = re.sub(r'<style[\s\S]*?</style>', ' ', cleaned, flags=re.IGNORECASE)
    
    # Extract paragraphs
    paras = re.findall(r'<p\b[^>]*>(.*?)</p>', cleaned, flags=re.IGNORECASE | re.DOTALL)
    parts = []
    for p in paras:
        txt = re.sub(r'<[^>]+>', ' ', p)
        txt = re.sub(r'\s+', ' ', txt).strip()
        if txt and len(txt) > 20:
            parts.append(txt)
    
    return '\n\n'.join(parts)


def fetch_full_article(url: str) -> tuple[str, str]:
    """Fetch and extract article text with multiple fallback methods"""
    
    # Method 1: trafilatura (best for modern sites like Wired, Guardian, etc.)
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            if text and len(text) > 300:
                print(f"    [OK] trafilatura: {len(text)} chars")
                return text, "trafilatura"
    except Exception as e:
        print(f"    [WARN] trafilatura failed: {str(e)[:60]}...")
    
    # Method 2: newspaper4k
    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=12)
        response.raise_for_status()
        
        from newspaper import Article as NewsArticle
        article = NewsArticle(url)
        article.download(input_html=response.text)
        article.parse()
        if article.text and len(article.text) > 300:
            print(f"    [OK] newspaper4k: {len(article.text)} chars")
            return article.text, "newspaper4k"
    except Exception as e:
        print(f"    [WARN] newspaper4k failed: {str(e)[:60]}...")
    
    # Method 3: Simple HTML parser (fallback)
    try:
        if 'response' not in locals():
            response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=12)
            response.raise_for_status()
        
        text = extract_text_simple(response.text)
        if text and len(text) > 300:
            print(f"    [OK] html_parser: {len(text)} chars")
            return text, "html_parser"
    except Exception as e:
        print(f"    [WARN] html_parser failed: {str(e)[:60]}...")

        
        return "", "failed"
    
    except Exception as e:
        return "", "error"


def insert_article_simple(conn, article_data):
    """Insert article into database with smart classification"""
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT id FROM articles WHERE url = ?", (article_data['url'],))
    if cursor.fetchone():
        return None  # Already exists
    
    # Use smart classifier if available
    if SMART_CLASSIFICATION and article_data.get('full_text'):
        try:
            classification = classify_article_with_llm(
                article_data.get('title', ''),
                article_data.get('description', ''),
                article_data.get('full_text', ''),
                article_data.get('source', '')
            )
            article_data['age_group'] = classification.get('age_group', '14-16')
            article_data['quality_score'] = classification.get('quality_score', 7)
            article_data['readability_score'] = classification.get('quality_score', 7) * 10
        except Exception as e:
            print(f"      Classification error: {e}")
            # Use fallback based on source
            article_data['age_group'] = _guess_age_group(article_data.get('source', ''))
    else:
        article_data['age_group'] = _guess_age_group(article_data.get('source', ''))
    
    # Generate UUID for the article
    article_uuid = str(uuid_lib.uuid4())
    
    cursor.execute("""
        INSERT INTO articles (
            uuid, title, url, source, category, description,
            full_text, has_full_article, published_at, 
            image_url, word_count, extraction_method,
            age_group, quality_score, readability_score, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        article_uuid,
        article_data.get('title', ''),
        article_data['url'],
        article_data.get('source', ''),
        article_data.get('category', ''),
        article_data.get('description', ''),
        article_data.get('full_text', ''),
        article_data.get('has_full_article', 0),
        article_data.get('published_at', datetime.now().isoformat()),
        article_data.get('image_url', ''),
        article_data.get('word_count', 0),
        article_data.get('extraction_method', 'rss'),
        article_data.get('age_group', '14-16'),
        article_data.get('quality_score', 7),
        article_data.get('readability_score', 70.0),
        datetime.now().isoformat(),  # collected_at
    ))
    
    return cursor.lastrowid


def _guess_age_group(source: str) -> str:
    """Fallback age group classification based on source"""
    kids_sources = ["BBC Newsround", "Time for Kids", "Dogo News", "KidsHealth", "Girls Life"]
    science_middle = ["NASA", "NASA Space Station", "NASA Image of the Day", "Khan Academy"]
    high_school = ["Space.com", "Live Science", "Smithsonian Magazine", "EarthSky", "CNN", "BBC", "ESPN", "Polygon"]
    
    if source in kids_sources:
        return "7-10"
    elif source in science_middle:
        return "11-14"  # Changed from 11-13
    elif source in high_school:
        return "15-18"  # Changed from 14-16
    else:
        return "11-14"  # Default middle school


def insert_article_simple_old(conn, article_data):
    """OLD VERSION - Insert article into database"""
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT id FROM articles WHERE url = ?", (article_data['url'],))
    if cursor.fetchone():
        return None  # Already exists
    
    cursor.execute("""
        INSERT INTO articles (
            title, url, source, category, description,
            full_text, has_full_article, published_at, 
            image_url, word_count, extraction_method
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        article_data.get('title', ''),
        article_data['url'],
        article_data.get('source', ''),
        article_data.get('category', ''),
        article_data.get('description', ''),
        article_data.get('full_text', ''),
        article_data.get('has_full_article', 0),
        article_data.get('published_at', datetime.now().isoformat()),
        article_data.get('image_url', ''),
        article_data.get('word_count', 0),
        article_data.get('extraction_method', 'rss'),
    ))
    
    return cursor.lastrowid


def collect_from_source(source):
    """Collect articles from one RSS source"""
    print(f"\n{source['name']}")
    print(f"   URL: {source['rss_url']}")
    
    stored = 0
    skipped = 0
    
    try:
        # Fetch RSS feed
        feed = feedparser.parse(source['rss_url'])
        
        if not feed.entries:
            print(f"   No entries found")
            return
        
        print(f"   Found {len(feed.entries)} articles")
        
        with get_db() as conn:
            for entry in feed.entries[:ARTICLES_PER_SOURCE]:
                try:
                    # Extract basic info
                    title = entry.get('title', 'Untitled')
                    url = entry.get('link', '')
                    description = entry.get('summary', '')
                    image_url = entry.get('media_thumbnail', [{}])[0].get('url', '') if 'media_thumbnail' in entry else ''
                    
                    if not url:
                        continue
                    
                    # Fetch full article
                    full_text, method = fetch_full_article(url)
                    word_count = len(full_text.split()) if full_text else 0
                    has_full_article = 1 if word_count > 100 else 0
                    
                    article_data = {
                        'title': title,
                        'url': url,
                        'source': source['name'],
                        'category': source['category'],
                        'description': description,
                        'full_text': full_text,
                        'has_full_article': has_full_article,
                        'published_at': entry.get('published', datetime.now().isoformat()),
                        'image_url': image_url,
                        'word_count': word_count,
                        'extraction_method': method,
                    }
                    
                    article_id = insert_article_simple(conn, article_data)
                    if article_id:
                        print(f"   Stored: {title[:50]}...")
                        stored += 1
                    else:
                        skipped += 1
                    
                    time.sleep(0.5)  # Rate limiting
                
                except Exception as e:
                    print(f"   Error: {e}")
                    skipped += 1
        
        print(f"   Result: {stored} stored, {skipped} skipped")
    
    except Exception as e:
        print(f"   Failed: {e}")


def main():
    """Main collection function"""
    print("\n" + "=" * 70)
    print("NewsCollect - Simple RSS Collector")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sources: {len(SOURCES)}")
    print(f"Articles per source: {ARTICLES_PER_SOURCE}")
    print("=" * 70)
    
    init_db()
    
    for source in SOURCES:
        collect_from_source(source)
    
    # Show stats
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM articles WHERE has_full_article = 1")
        full = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
        sources = cursor.fetchone()[0]
    
    print("\n" + "=" * 70)
    print("Collection Complete")
    print("=" * 70)
    print(f"Total articles: {total}")
    print(f"Full articles: {full}")
    print(f"Sources: {sources}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
