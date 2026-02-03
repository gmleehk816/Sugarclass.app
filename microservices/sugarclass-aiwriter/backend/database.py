"""
Database schema and operations for newscollect system.
Stores news articles with full text, images, categories, and dates.
Supports both SQLite (development) and PostgreSQL (production).
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Tuple
from contextlib import contextmanager

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # 'sqlite' or 'postgresql'

# SQLite configuration (development)
_SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "newscollect.db")

# PostgreSQL configuration (production)
_POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "newscollect"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

# PostgreSQL connection pool
_postgres_pool = None


def _get_postgres_connection():
    """Get a PostgreSQL connection."""
    global _postgres_pool
    
    if _postgres_pool is None:
        try:
            import psycopg2
            from psycopg2 import pool
        except ImportError:
            raise ImportError("psycopg2-binary is required for PostgreSQL. Run: pip install psycopg2-binary")
        
        _postgres_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,  # min/max connections
            host=_POSTGRES_CONFIG["host"],
            port=_POSTGRES_CONFIG["port"],
            database=_POSTGRES_CONFIG["database"],
            user=_POSTGRES_CONFIG["user"],
            password=_POSTGRES_CONFIG["password"]
        )
    
    return _postgres_pool.getconn()


def _release_postgres_connection(conn):
    """Release a PostgreSQL connection back to the pool."""
    global _postgres_pool
    if _postgres_pool:
        _postgres_pool.putconn(conn)


def _get_placeholder():
    """Return the appropriate placeholder for the current database type."""
    return "%s" if DB_TYPE == "postgresql" else "?"


def _convert_placeholders(query):
    """Convert SQLite syntax to PostgreSQL if needed."""
    if DB_TYPE == "postgresql":
        query = query.replace("?", "%s")
        # Handle common SQLite-specific syntax
        if "INSERT OR IGNORE" in query:
            query = query.replace("INSERT OR IGNORE INTO", "INSERT INTO")
            # We assume the first unique column is the one to conflict on
            # This is specific to our use cases in init_db
            if "categories" in query:
                query += " ON CONFLICT (name) DO NOTHING"
            elif "sources" in query:
                query += " ON CONFLICT (domain) DO NOTHING"
            elif "api_keys" in query:
                query += " ON CONFLICT (api_name) DO NOTHING"
    return query


@contextmanager
def get_db():
    """Context manager for database connections (SQLite or PostgreSQL)."""
    if DB_TYPE == "postgresql":
        # PostgreSQL
        import psycopg2.extras
        conn = _get_postgres_connection()
        conn.autocommit = False
        try:
            # Important: yield the connection, but we also want the cursor to be RealDictCursor
            # We can't easily change the behavior of conn.cursor() globally without setting it on the conn
            # But the functions in this file call conn.cursor()
            # So we set it on the connection level
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            _release_postgres_connection(conn)
    else:
        # SQLite (default)
        conn = sqlite3.connect(_SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def health_check() -> bool:
    """Check if the database is healthy."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            # For RealDictCursor, result might be {'?column?': 1} or similar
            # For SQLite, it's (1,)
            return result is not None
    except Exception:
        return False


def init_db():
    """Initialize database with required tables. Supports SQLite and PostgreSQL."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # SQLite-specific optimizations (only for SQLite)
        if DB_TYPE == "sqlite":
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        
        # Articles table
        if DB_TYPE == "postgresql":
            # PostgreSQL syntax
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    uuid TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    full_text TEXT,
                    url TEXT UNIQUE NOT NULL,
                    image_url TEXT,
                    source TEXT NOT NULL,
                    category TEXT,
                    published_at TIMESTAMP WITH TIME ZONE,
                    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    extraction_status TEXT DEFAULT 'pending',
                    extraction_method TEXT,
                    api_source TEXT DEFAULT 'rss',
                    word_count INTEGER DEFAULT 0,
                    has_full_article INTEGER DEFAULT 0,
                    age_group TEXT DEFAULT NULL,
                    readability_score REAL DEFAULT NULL,
                    grade_level REAL DEFAULT NULL,
                    quality_score REAL DEFAULT NULL,
                    quality_check_status TEXT DEFAULT 'pending',
                    quality_check_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # SQLite syntax
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    full_text TEXT,
                    url TEXT UNIQUE NOT NULL,
                    image_url TEXT,
                    source TEXT NOT NULL,
                    category TEXT,
                    published_at TEXT,
                    collected_at TEXT NOT NULL,
                    extraction_status TEXT DEFAULT 'pending',
                    extraction_method TEXT,
                    api_source TEXT DEFAULT 'rss',
                    word_count INTEGER DEFAULT 0,
                    has_full_article INTEGER DEFAULT 0,
                    age_group TEXT DEFAULT NULL,
                    readability_score REAL DEFAULT NULL,
                    grade_level REAL DEFAULT NULL,
                    quality_score REAL DEFAULT NULL,
                    quality_check_status TEXT DEFAULT 'pending',
                    quality_check_at TEXT DEFAULT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Try to add missing columns if they don't exist (migrations)
        if DB_TYPE == "postgresql":
            # api_source
            cursor.execute("ALTER TABLE articles ADD COLUMN IF NOT EXISTS api_source TEXT DEFAULT 'rss'")
            
            # quality/age columns
            quality_columns = [
                ("age_group", "TEXT DEFAULT NULL"),
                ("readability_score", "REAL DEFAULT NULL"),
                ("grade_level", "REAL DEFAULT NULL"),
                ("quality_score", "REAL DEFAULT NULL"),
                ("quality_check_status", "TEXT DEFAULT 'pending'"),
                ("quality_check_at", "TIMESTAMP WITH TIME ZONE"),
            ]
            for col_name, col_type in quality_columns:
                cursor.execute(f"ALTER TABLE articles ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
        else:
            # SQLite - try-except is safer here since it doesn't support IF NOT EXISTS for ADD COLUMN
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN api_source TEXT DEFAULT 'rss'")
            except Exception:
                pass
            
            quality_columns = [
                ("age_group", "TEXT DEFAULT NULL"),
                ("readability_score", "REAL DEFAULT NULL"),
                ("grade_level", "REAL DEFAULT NULL"),
                ("quality_score", "REAL DEFAULT NULL"),
                ("quality_check_status", "TEXT DEFAULT 'pending'"),
                ("quality_check_at", "TEXT DEFAULT NULL"),
            ]
            for col_name, col_type in quality_columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass
        
        # Categories table
        if DB_TYPE == "postgresql":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Sources table
        if DB_TYPE == "postgresql":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id SERIAL PRIMARY KEY,
                    domain TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    rss_url TEXT,
                    status TEXT DEFAULT 'unknown',
                    last_check TIMESTAMP WITH TIME ZONE,
                    last_success TIMESTAMP WITH TIME ZONE,
                    error_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    rss_url TEXT,
                    status TEXT DEFAULT 'unknown',
                    last_check TEXT,
                    last_success TEXT,
                    error_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # API Keys table
        if DB_TYPE == "postgresql":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    api_name TEXT UNIQUE NOT NULL,
                    api_key TEXT,
                    is_active INTEGER DEFAULT 1,
                    daily_limit INTEGER DEFAULT 0,
                    requests_today INTEGER DEFAULT 0,
                    last_reset TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT UNIQUE NOT NULL,
                    api_key TEXT,
                    is_active INTEGER DEFAULT 1,
                    daily_limit INTEGER DEFAULT 0,
                    requests_today INTEGER DEFAULT 0,
                    last_reset TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Collection logs table
        if DB_TYPE == "postgresql":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection_logs (
                    id SERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    articles_found INTEGER DEFAULT 0,
                    articles_stored INTEGER DEFAULT 0,
                    articles_failed INTEGER DEFAULT 0,
                    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    error_message TEXT
                )
            """)
            
            # User writings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_writings (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    article_id INTEGER REFERENCES articles(id),
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_html TEXT,
                    content_json TEXT,
                    word_count INTEGER DEFAULT 0,
                    year_level TEXT,
                    milestone_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    articles_found INTEGER DEFAULT 0,
                    articles_stored INTEGER DEFAULT 0,
                    articles_failed INTEGER DEFAULT 0,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT
                )
            """)
            
            # User writings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_writings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    article_id INTEGER REFERENCES articles(id),
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_html TEXT,
                    content_json TEXT,
                    word_count INTEGER DEFAULT 0,
                    year_level TEXT,
                    milestone_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Migrations for user_writings table (add content_html and content_json if missing)
        if DB_TYPE == "postgresql":
            # PostgreSQL supports IF NOT EXISTS for ALTER TABLE
            cursor.execute("ALTER TABLE user_writings ADD COLUMN IF NOT EXISTS content_html TEXT")
            cursor.execute("ALTER TABLE user_writings ADD COLUMN IF NOT EXISTS content_json TEXT")
        else:
            # SQLite - use try-except since it doesn't support IF NOT EXISTS for ADD COLUMN
            try:
                cursor.execute("ALTER TABLE user_writings ADD COLUMN content_html TEXT")
            except Exception:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE user_writings ADD COLUMN content_json TEXT")
            except Exception:
                pass  # Column already exists

        # Create indexes for better query performance (only for columns that exist)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_collected ON articles(collected_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_method ON articles(extraction_method)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_age_group ON articles(age_group)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_quality ON articles(quality_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_readability ON articles(readability_score)")
        
        # Insert default categories
        default_categories = [
            ("general", "General News"),
            ("politics", "Politics"),
            ("business", "Business"),
            ("technology", "Technology"),
            ("science", "Science"),
            ("health", "Health"),
            ("sports", "Sports"),
            ("entertainment", "Entertainment"),
            ("world", "World News"),
        ]
        
        for name, display_name in default_categories:
            cursor.execute(_convert_placeholders("""
                INSERT OR IGNORE INTO categories (name, display_name)
                VALUES (?, ?)
            """), (name, display_name))
        
        # Insert default sources
        default_sources = [
            ("cnn.com", "CNN", "https://rss.cnn.com/rss/edition.rss"),
            ("bbc.com", "BBC", "https://feeds.bbci.co.uk/news/rss.xml"),
            ("reuters.com", "Reuters", "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"),
            ("cnbc.com", "CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
            ("theguardian.com", "The Guardian", "https://www.theguardian.com/world/rss"),
            ("phys.org", "Phys.org", "https://phys.org/rss-feed/"),
            ("sciencenewsforstudents.org", "Science News Explores", "https://www.snexplores.org/feed"),
            # Kid-friendly news sources (age-appropriate content)
            ("bbc.co.uk", "BBC Newsround", "https://feeds.bbci.co.uk/newsround/rss.xml"),
            ("dogonews.com", "Dogo News", "https://www.dogonews.com/rss"),
            ("timeforkids.com", "Time for Kids", "https://www.timeforkids.com/g34/feed/"),
            ("kids.nationalgeographic.com", "Nat Geo Kids", "https://kids.nationalgeographic.com/feed"),
        ]
        
        for domain, name, rss_url in default_sources:
            cursor.execute(_convert_placeholders("""
                INSERT OR IGNORE INTO sources (domain, name, rss_url)
                VALUES (?, ?, ?)
            """), (domain, name, rss_url))


# ============================================================================
# DUPLICATE PREVENTION
# ============================================================================

def normalize_url(url: str) -> str:
    """
    Normalize URL for duplicate detection.

    Removes:
    - Tracking parameters (utm_*, fbclid, gclid, etc.)
    - Session IDs
    - Protocol variations (force https)
    - www prefix
    - Trailing slashes

    Args:
        url: URL to normalize

    Returns:
        Normalized URL suitable for duplicate comparison
    """
    if not url:
        return ""

    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

    try:
        # Parse URL
        parsed = urlparse(url.strip())

        # Force https and remove www
        scheme = "https"
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Remove tracking parameters
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        tracking_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "fbclid", "gclid", "msclkid", "ncid", "cid", "ref",
            "share", "utm_reader", "utm_referrer", "utm_social", "ei",
            "fb", "ig", "tw", "_ga", "_gid", "mc_cid", "mc_eid",
            "WT.mc_id", "s", "source", "trk", "trkCampaign",
        }

        # Keep only non-tracking params
        clean_params = {k: v for k, v in query_params.items() if k not in tracking_params}

        # Rebuild query string
        query = urlencode(clean_params, doseq=True) if clean_params else ""

        # Remove trailing slash from path
        path = parsed.path.rstrip("/")

        # Rebuild URL
        normalized = urlunparse((scheme, netloc, path, parsed.params, query, parsed.fragment))

        return normalized

    except Exception as e:
        print(f"[URL Normalization Error] {e}")
        return url.strip().lower()


def check_duplicate_before_insert(
    url: str,
    title: str,
    source: str,
    conn=None
) -> Optional[Dict[str, Any]]:
    """
    Check if an article already exists before insertion.

    Checks in order:
    1. Exact URL match (normalized)
    2. Title + Source match (for same article from different URLs)
    3. Similar title match (fuzzy matching)

    Args:
        url: Article URL
        title: Article title
        source: Article source/domain
        conn: Optional database connection (creates new if None)

    Returns:
        Existing article dict if duplicate found, None otherwise
    """
    from . import database as db_module  # Import at runtime to avoid circular import

    should_close = False
    if conn is None:
        conn = db_module.get_db().__enter__()
        should_close = True

    try:
        cursor = conn.cursor()

        # Normalize URL for comparison
        normalized_url = normalize_url(url)

        # Check 1: Exact URL match (normalized)
        # First check by exact match
        cursor.execute(_convert_placeholders("""
            SELECT * FROM articles WHERE url = ?
        """), (url,))
        existing = cursor.fetchone()

        if existing:
            return dict(existing)

        # Check normalized URLs by getting all and comparing in Python
        # (SQLite doesn't support regex replace, so we do this in Python)
        cursor.execute(_convert_placeholders("""
            SELECT id, url, title, source FROM articles WHERE source = ?
            LIMIT 100
        """), (source,))

        rows = cursor.fetchall()

        for row in rows:
            row_dict = dict(row)
            existing_url = row_dict.get("url", "")
            existing_normalized = normalize_url(existing_url)

            if existing_normalized == normalized_url:
                # Found duplicate by normalized URL - fetch full article
                cursor.execute(_convert_placeholders("""
                    SELECT * FROM articles WHERE id = ?
                """), (row_dict["id"],))
                return dict(cursor.fetchone())

        # Check 2: Title + Source match
        # Normalize titles for comparison (remove extra whitespace, lower case)
        normalized_title = " ".join(title.lower().split())

        cursor.execute(_convert_placeholders("""
            SELECT * FROM articles
            WHERE source = ?
            AND LOWER(TRIM(title)) = ?
            LIMIT 1
        """), (source, normalized_title))

        existing = cursor.fetchone()
        if existing:
            return dict(existing)

        # Check 3: Similar title match (using simple similarity)
        # Check if title is very similar to any existing title from same source
        cursor.execute(_convert_placeholders("""
            SELECT id, url, title, source FROM articles
            WHERE source = ?
            ORDER BY id DESC
            LIMIT 50
        """), (source,))

        rows = cursor.fetchall()

        for row in rows:
            row_dict = dict(row)
            existing_title = row_dict.get("title", "")

            # Calculate similarity using simple character matching
            similarity = _calculate_title_similarity(normalized_title, existing_title.lower())

            if similarity >= 0.85:  # 85% similarity threshold
                # Found highly similar title - likely a duplicate
                cursor.execute(_convert_placeholders("""
                    SELECT * FROM articles WHERE id = ?
                """), (row_dict["id"],))
                return dict(cursor.fetchone())

        # No duplicate found
        return None

    finally:
        if should_close:
            conn.__exit__(None, None, None)


def _calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate similarity between two titles using a simple algorithm.

    Args:
        title1: First title (already normalized)
        title2: Second title

    Returns:
        Similarity score between 0 and 1
    """
    if not title1 or not title2:
        return 0.0

    # Quick check: if one is contained in the other, high similarity
    if title1 in title2 or title2 in title1:
        return 0.9

    # Word-based similarity (Jaccard index)
    words1 = set(title1.split())
    words2 = set(title2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    if not union:
        return 0.0

    return len(intersection) / len(union)


def insert_article(article: Dict[str, Any], check_duplicate: bool = True) -> Optional[int]:
    """
    Insert or update an article in the database. Returns article ID if successful.

    Args:
        article: Article data dictionary
        check_duplicate: Whether to check for duplicates before inserting (default: True)

    Returns:
        Article ID if successful, None if duplicate found or error occurred
    """
    try:
        # Pre-insert duplicate check (before expensive operations)
        if check_duplicate:
            url = article.get("url", "")
            title = article.get("title", "")
            source = article.get("source", "")

            existing = check_duplicate_before_insert(url, title, source)
            if existing:
                # Update existing article with new data if it has better content
                existing_id = existing.get("id")
                existing_full_text = existing.get("full_text", "")
                new_full_text = article.get("full_text", "")

                # Only update if new content is better (longer/more complete)
                if new_full_text and len(new_full_text) > len(existing_full_text):
                    print(f"[Duplicate Update] Improving existing article: {title[:50]}...")
                    # This will be handled by ON CONFLICT below
                else:
                    print(f"[Duplicate Skipped] Article already exists: {title[:50]}...")
                    return existing_id

        with get_db() as conn:
            cursor = conn.cursor()

            # Calculate word count
            full_text = article.get("full_text") or ""
            word_count = len(full_text.split()) if full_text else 0

            # Determine if we have full article
            has_full_article = 1 if word_count > 100 else 0

            # Determine extraction status
            extraction_status = "success" if has_full_article else "partial"

            sql = """
                INSERT INTO articles (
                    uuid, title, description, full_text, url, image_url,
                    source, category, published_at, collected_at,
                    extraction_status, extraction_method, word_count, has_full_article,
                    api_source, age_group
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    full_text = excluded.full_text,
                    image_url = excluded.image_url,
                    category = excluded.category,
                    published_at = excluded.published_at,
                    extraction_status = excluded.extraction_status,
                    extraction_method = excluded.extraction_method,
                    word_count = excluded.word_count,
                    has_full_article = excluded.has_full_article,
                    api_source = excluded.api_source,
                    age_group = excluded.age_group
            """
            # Prepare article data, handling empty strings for PostgreSQL timestamp compatibility
            published_at = article.get("published_at")
            if not published_at:
                published_at = None

            collected_at = article.get("collected_at")
            if not collected_at:
                collected_at = datetime.utcnow().isoformat()

            params = (
                article.get("uuid"),
                article.get("title"),
                article.get("description"),
                article.get("full_text"),
                article.get("url"),
                article.get("image_url"),
                article.get("source"),
                article.get("category"),
                published_at,
                collected_at,
                extraction_status,
                article.get("extraction_method"),
                word_count,
                has_full_article,
                article.get("api_source", "rss"),
                article.get("age_group")  # NEW: age_group parameter
            )

            if DB_TYPE == "postgresql":
                sql += " RETURNING id"
                cursor.execute(_convert_placeholders(sql), params)
                row = cursor.fetchone()
                article_id = row["id"] if row else None
            else:
                cursor.execute(_convert_placeholders(sql), params)
                article_id = cursor.lastrowid

            # Trigger WebSocket broadcast after successful insert
            try:
                from app_enhanced import broadcast_update
                broadcast_update('collection')
            except ImportError:
                pass  # Server not running, skip broadcast

            return article_id
    except Exception as e:
        print(f"[DB Error] Failed to insert article: {e}")
        return None


def get_articles(
    source: Optional[str] = None,
    category: Optional[str] = None,
    age_group: Optional[str] = None,
    extraction_method: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get articles with optional filters."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if age_group:
            # Include NULL age_group values as they belong to the default "11-14" group
            # This ensures older articles (collected before age_group feature) appear in filters
            if age_group == "11-14":
                query += " AND (age_group = ? OR age_group IS NULL)"
                params.append(age_group)
            else:
                query += " AND age_group = ?"
                params.append(age_group)
        
        if extraction_method:
            query += " AND extraction_method = ?"
            params.append(extraction_method)
        
        if date_from:
            query += " AND published_at >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND published_at <= ?"
            params.append(date_to)
        
        # Order by collected_at (most recently collected first) as it's always set
        # Fall back to id DESC for articles with same collection time
        query += f" ORDER BY collected_at DESC, id DESC LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(_convert_placeholders(query), params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


def get_article_by_id(article_id: int) -> Optional[Dict[str, Any]]:
    """Get a single article by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_convert_placeholders("SELECT * FROM articles WHERE id = ?"), (article_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_article_by_uuid(uuid: str) -> Optional[Dict[str, Any]]:
    """Get a single article by UUID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_convert_placeholders("SELECT * FROM articles WHERE uuid = ?"), (uuid,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_sources() -> List[Dict[str, Any]]:
    """Get all news sources."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_categories() -> List[Dict[str, Any]]:
    """Get all categories."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY display_name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_source_status(domain: str, status: str, error_message: Optional[str] = None) -> None:
    """Update source health status."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if status == "success":
            cursor.execute(_convert_placeholders("""
                UPDATE sources
                SET status = 'working', last_success = ?, last_check = ?, error_count = 0
                WHERE domain = ?
            """), (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), domain))
        else:
            cursor.execute(_convert_placeholders("""
                UPDATE sources
                SET status = ?, last_check = ?, error_count = error_count + 1
                WHERE domain = ?
            """), (status, datetime.utcnow().isoformat(), domain))


def log_collection(
    source: str,
    articles_found: int,
    articles_stored: int,
    articles_failed: int,
    started_at: str,
    completed_at: Optional[str] = None,
    error_message: Optional[str] = None
) -> None:
    """Log a collection run."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_convert_placeholders("""
            INSERT INTO collection_logs (
                source, articles_found, articles_stored, articles_failed,
                started_at, completed_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """), (source, articles_found, articles_stored, articles_failed,
              started_at, completed_at, error_message))


def get_collection_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent collection logs."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_convert_placeholders("""
            SELECT * FROM collection_logs
            ORDER BY started_at DESC
            LIMIT ?
        """), (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_stats() -> Dict[str, Any]:
    """Get database statistics."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total articles
        cursor.execute("SELECT COUNT(*) as count FROM articles")
        total_articles = cursor.fetchone()["count"]
        
        # Articles with full text
        cursor.execute("SELECT COUNT(*) as count FROM articles WHERE has_full_article = 1")
        full_articles = cursor.fetchone()["count"]
        
        # Articles by source
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM articles
            GROUP BY source
            ORDER BY count DESC
        """)
        by_source = {row["source"]: row["count"] for row in cursor.fetchall()}
        
        # Articles by category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM articles
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """)
        by_category = {row["category"]: row["count"] for row in cursor.fetchall()}
        
        # Articles by extraction method
        cursor.execute("""
            SELECT extraction_method, COUNT(*) as count
            FROM articles
            WHERE extraction_method IS NOT NULL
            GROUP BY extraction_method
            ORDER BY count DESC
        """)
        by_method = {row["extraction_method"]: row["count"] for row in cursor.fetchall()}
        
        # Latest collection
        cursor.execute("""
            SELECT * FROM collection_logs
            ORDER BY started_at DESC
            LIMIT 1
        """)
        latest_log = cursor.fetchone()
        
        return {
            "total_articles": total_articles,
            "full_articles": full_articles,
            "partial_articles": total_articles - full_articles,
            "by_source": by_source,
            "by_category": by_category,
            "by_method": by_method,
            "latest_collection": dict(latest_log) if latest_log else None
        }


def delete_old_articles(days: int = 30) -> int:
    """Delete articles older than specified days."""
    with get_db() as conn:
        cursor = conn.cursor()
        if DB_TYPE == "postgresql":
            cursor.execute("""
                DELETE FROM articles
                WHERE collected_at < NOW() - INTERVAL '1 day' * %s
            """, (days,))
        else:
            cursor.execute("""
                DELETE FROM articles
                WHERE collected_at < datetime('now', '-' || ? || ' days')
            """, (days,))
        return cursor.rowcount


def get_api_keys() -> List[Dict[str, Any]]:
    """Get all API key configurations."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT api_name, api_key, is_active, daily_limit, requests_today, last_reset
            FROM api_keys
            ORDER BY api_name
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def save_api_key(
    api_name: str,
    api_key: str,
    is_active: bool = True,
    daily_limit: int = 100
) -> None:
    """Save or update an API key configuration."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        sql = """
            INSERT INTO api_keys (api_name, api_key, is_active, daily_limit, last_reset)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(api_name) DO UPDATE SET
                api_key = excluded.api_key,
                is_active = excluded.is_active,
                daily_limit = excluded.daily_limit
        """
        
        cursor.execute(_convert_placeholders(sql), (
            api_name,
            api_key,
            1 if is_active else 0,
            daily_limit,
            datetime.utcnow().isoformat()
        ))


def increment_api_requests(api_name: str) -> bool:
    """Increment the request count for an API. Returns True if under limit."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if we need to reset the counter (new day)
        if DB_TYPE == "postgresql":
            cursor.execute(_convert_placeholders("""
                UPDATE api_keys
                SET requests_today = 0, last_reset = ?
                WHERE api_name = ? 
                AND (last_reset IS NULL OR last_reset::date < CURRENT_DATE)
            """), (datetime.utcnow().isoformat(), api_name))
        else:
            cursor.execute(_convert_placeholders("""
                UPDATE api_keys
                SET requests_today = 0, last_reset = ?
                WHERE api_name = ? 
                AND (last_reset IS NULL OR date(last_reset) < date('now'))
            """), (datetime.utcnow().isoformat(), api_name))
        
        # Get current count and limit
        cursor.execute(_convert_placeholders("""
            SELECT daily_limit, requests_today
            FROM api_keys
            WHERE api_name = ? AND is_active = 1
        """), (api_name,))
        row = cursor.fetchone()
        
        if not row:
            return False
        
        daily_limit = row['daily_limit']
        requests_today = row['requests_today']
        
        # Check if under limit
        if daily_limit > 0 and requests_today >= daily_limit:
            return False
        
        # Increment counter
        cursor.execute(_convert_placeholders("""
            UPDATE api_keys
            SET requests_today = requests_today + 1
            WHERE api_name = ?
        """), (api_name,))
        
        return True


def get_api_key_value(api_name: str) -> str | None:
    """Get the actual API key value for a given API name."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_convert_placeholders("""
            SELECT api_key
            FROM api_keys
            WHERE api_name = ? AND is_active = 1
        """), (api_name,))
        row = cursor.fetchone()
        return row['api_key'] if row else None


def save_user_writing(
    user_id: str,
    article_id: int,
    title: str,
    content: str,
    content_html: str = None,
    content_json: str = None,
    word_count: int = 0,
    year_level: str = None,
    milestone_message: str = None,
    writing_id: int = None
) -> int:
    """Save or update user's news writing work.

    If writing_id is provided, updates that specific writing.
    Otherwise, checks for existing writing for this user+article and updates it,
    or creates a new one if none exists.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # If writing_id is provided, update that specific writing
        if writing_id:
            sql = """
                UPDATE user_writings
                SET title = ?, content = ?, content_html = ?, content_json = ?,
                    word_count = ?, year_level = ?, milestone_message = ?,
                    updated_at = ?
                WHERE id = ? AND user_id = ?
            """
            cursor.execute(_convert_placeholders(sql), (
                title, content, content_html, content_json,
                word_count, year_level, milestone_message,
                datetime.utcnow().isoformat() if DB_TYPE == "postgresql" else datetime.utcnow().isoformat(),
                writing_id, user_id
            ))
            conn.commit()
            return writing_id

        # No writing_id - check for existing writing for this user+article
        cursor.execute(_convert_placeholders("""
            SELECT id FROM user_writings
            WHERE user_id = ? AND article_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """), (user_id, article_id))

        existing = cursor.fetchone()

        if existing:
            # Update existing writing
            existing_id = existing["id"]
            sql = """
                UPDATE user_writings
                SET title = ?, content = ?, content_html = ?, content_json = ?,
                    word_count = ?, year_level = ?, milestone_message = ?,
                    updated_at = ?
                WHERE id = ? AND user_id = ?
            """
            cursor.execute(_convert_placeholders(sql), (
                title, content, content_html, content_json,
                word_count, year_level, milestone_message,
                datetime.utcnow().isoformat() if DB_TYPE == "postgresql" else datetime.utcnow().isoformat(),
                existing_id, user_id
            ))
            conn.commit()
            return existing_id
        else:
            # Insert new writing
            sql = """
                INSERT INTO user_writings (
                    user_id, article_id, title, content, content_html, content_json, word_count, year_level, milestone_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(_convert_placeholders(sql), (
                user_id, article_id, title, content, content_html, content_json, word_count, year_level, milestone_message
            ))
            conn.commit()

            if DB_TYPE == "postgresql":
                cursor.execute("SELECT LASTVAL() as id")
                row = cursor.fetchone()
                return row["id"] if row else None
            else:
                return cursor.lastrowid


def get_user_writings(user_id: str) -> List[Dict[str, Any]]:
    """Get all writings for a specific user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_convert_placeholders("""
            SELECT * FROM user_writings WHERE user_id = ? ORDER BY created_at DESC
        """), (user_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_user_writing(writing_id: int, user_id: str) -> bool:
    """Delete a specific writing for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_convert_placeholders("""
            DELETE FROM user_writings WHERE id = ? AND user_id = ?
        """), (writing_id, user_id))
        conn.commit()
        return cursor.rowcount > 0


def get_user_writing(writing_id: int, user_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific writing for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_convert_placeholders("""
            SELECT * FROM user_writings WHERE id = ? AND user_id = ?
        """), (writing_id, user_id))
        row = cursor.fetchone()
        return dict(row) if row else None


# Initialize database on import
init_db()


# ============================================================================
# AGE GROUP CLASSIFICATION HELPER
# ============================================================================

# Kids news sources that produce age-appropriate content
# Maps both domain names and display names to age groups
KIDS_SOURCES = {
    # Display names
    "BBC Newsround": "7-10",
    "Dogo News": "7-10",
    "Time for Kids": "7-10",
    "National Geographic Kids": "7-10",
    "Nat Geo Kids": "7-10",
    "Newsela": "11-14",
    "SCMP Young Post": "11-14",
    # Domain names (for matching source domain)
    "bbc.co.uk": "7-10",
    "dogonews.com": "7-10",
    "timeforkids.com": "7-10",
    "kids.nationalgeographic.com": "7-10",
    "newsela.com": "11-14",
    "yp.scmp.com": "11-14",
    # Educational sources
    "sciencenewsforstudents.org": "7-10",
    "snexplores.org": "7-10",
}

# Default age group for unknown sources (middle range)
DEFAULT_AGE_GROUP = "11-14"


def classify_age_group_from_source(source: str, full_text: str = "", word_count: int = 0) -> str:
    """
    Classify article age group based on source and content.

    Priority:
    1. Known kids news sources → specific age groups
    2. Word count analysis → shorter = younger audience
    3. Default to middle group (11-14)

    Args:
        source: Article source name
        full_text: Full article text (for fallback classification)
        word_count: Word count of article (for fallback classification)

    Returns:
        Age group: "7-10", "11-14", or "15-18"
    """
    # Check known kids sources first
    for kids_source, age_group in KIDS_SOURCES.items():
        if kids_source.lower() in source.lower():
            return age_group

    # Fallback: classify by word count if available
    if word_count > 0 or full_text:
        if not word_count:
            word_count = len(full_text.split()) if full_text else 0

        # Simple word count classification
        if word_count < 300:
            return "7-10"  # Shorter articles for younger kids
        elif word_count < 700:
            return "11-14"  # Medium length for middle school
        else:
            return "15-18"  # Longer articles for high school

    # Default to middle group
    return DEFAULT_AGE_GROUP


def classify_age_group_readability(text: str) -> Tuple[Optional[str], Optional[float], Optional[float]]:
    """
    Classify age group using readability scores.
    Requires textstat library for accurate results.

    Args:
        text: Article text to analyze

    Returns:
        (age_group, readability_score, grade_level) tuple
    """
    try:
        from textstat import flesch_reading_ease, flesch_kincaid_grade

        # Calculate readability scores
        readability_score = flesch_reading_ease(text)
        grade_level = flesch_kincaid_grade(text)

        # Classify by Flesch Reading Ease (higher = easier)
        if readability_score >= 80:
            age_group = "7-10"  # Very easy to read
        elif readability_score >= 60:
            age_group = "11-14"  # Standard readability
        else:
            age_group = "15-18"  # More complex text

        return age_group, readability_score, grade_level

    except ImportError:
        # textstat not available, use simple word count classification
        word_count = len(text.split()) if text else 0
        if word_count < 300:
            return "7-10", None, None
        elif word_count < 700:
            return "11-14", None, None
        else:
            return "15-18", None, None
    except Exception as e:
        print(f"[Age Classification Error] {e}")
        return DEFAULT_AGE_GROUP, None, None


# ============================================================================
# DUPLICATE CLEANUP UTILITIES
# ============================================================================

def find_and_remove_duplicates(dry_run: bool = True) -> Dict[str, Any]:
    """
    Find and optionally remove duplicate articles from the database.

    Duplicates are identified by:
    1. Normalized URL matching
    2. Title + source matching

    Args:
        dry_run: If True, only report duplicates without removing them

    Returns:
        Dictionary with duplicate statistics and list of duplicates found
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get all articles
        cursor.execute(_convert_placeholders("""
            SELECT id, url, title, source, full_text, collected_at
            FROM articles
            ORDER BY collected_at DESC
        """))

        all_articles = cursor.fetchall()
        duplicates_found = []
        duplicates_to_remove = []
        seen_urls = {}  # normalized_url -> (article_id, title)
        seen_title_source = {}  # (normalized_title, source) -> article_id

        for article in all_articles:
            article_dict = dict(article)
            article_id = article_dict["id"]
            url = article_dict.get("url", "")
            title = article_dict.get("title", "")
            source = article_dict.get("source", "")

            # Check by normalized URL
            normalized_url = normalize_url(url)
            if normalized_url in seen_urls:
                # Found duplicate by URL
                original_id, original_title = seen_urls[normalized_url]
                duplicate_info = {
                    "id": article_id,
                    "duplicate_of": original_id,
                    "reason": "url",
                    "url": url,
                    "normalized_url": normalized_url,
                    "title": title,
                    "original_title": original_title,
                }
                duplicates_found.append(duplicate_info)
                duplicates_to_remove.append(article_id)
            else:
                seen_urls[normalized_url] = (article_id, title)

            # Check by title + source
            normalized_title = " ".join(title.lower().split())
            title_source_key = (normalized_title, source)
            if title_source_key in seen_title_source and title_source_key[0]:  # Skip empty titles
                # Found duplicate by title + source
                original_id = seen_title_source[title_source_key]
                if original_id != article_id:  # Not already marked as duplicate
                    duplicate_info = {
                        "id": article_id,
                        "duplicate_of": original_id,
                        "reason": "title_source",
                        "url": url,
                        "title": title,
                        "source": source,
                    }
                    # Avoid adding if already in list
                    if not any(d["id"] == article_id for d in duplicates_found):
                        duplicates_found.append(duplicate_info)
                        if article_id not in duplicates_to_remove:
                            duplicates_to_remove.append(article_id)
            else:
                seen_title_source[title_source_key] = article_id

        # Remove duplicates if not dry run
        removed_count = 0
        if not dry_run and duplicates_to_remove:
            placeholders = ",".join("?" * len(duplicates_to_remove))
            cursor.execute(_convert_placeholders(f"""
                DELETE FROM articles WHERE id IN ({placeholders})
            """), duplicates_to_remove)
            removed_count = cursor.rowcount
            conn.commit()

        return {
            "total_articles": len(all_articles),
            "duplicates_found": len(duplicates_found),
            "duplicates_to_remove": len(duplicates_to_remove),
            "removed_count": removed_count,
            "dry_run": dry_run,
            "duplicates": duplicates_found[:100],  # Return first 100 for inspection
        }


def get_duplicate_summary() -> Dict[str, Any]:
    """
    Get a summary of duplicate articles without removing them.

    Returns:
        Dictionary with duplicate statistics grouped by source
    """
    result = find_and_remove_duplicates(dry_run=True)

    # Group duplicates by source
    duplicates_by_source = {}
    for dup in result["duplicates"]:
        source = dup.get("source", "unknown")
        if source not in duplicates_by_source:
            duplicates_by_source[source] = 0
        duplicates_by_source[source] += 1

    return {
        "total_articles": result["total_articles"],
        "total_duplicates": result["duplicates_found"],
        "duplicates_by_source": duplicates_by_source,
        "sample_duplicates": result["duplicates"][:20],  # First 20 for inspection
    }
