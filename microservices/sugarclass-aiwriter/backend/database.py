"""
Database schema and operations for newscollect system.
Stores news articles with full text, images, categories, and dates.
Supports both SQLite (development) and PostgreSQL (production).
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
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
        ]
        
        for domain, name, rss_url in default_sources:
            cursor.execute(_convert_placeholders("""
                INSERT OR IGNORE INTO sources (domain, name, rss_url)
                VALUES (?, ?, ?)
            """), (domain, name, rss_url))


def insert_article(article: Dict[str, Any]) -> Optional[int]:
    """Insert or update an article in the database. Returns article ID if successful."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Calculate word count
        full_text = article.get("full_text") or ""
        word_count = len(full_text.split()) if full_text else 0
        
        # Determine if we have full article
        has_full_article = 1 if word_count > 100 else 0
        
        # Determine extraction status
        extraction_status = "success" if has_full_article else "partial"
        
        try:
            sql = """
                INSERT INTO articles (
                    uuid, title, description, full_text, url, image_url,
                    source, category, published_at, collected_at,
                    extraction_status, extraction_method, word_count, has_full_article,
                    api_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    api_source = excluded.api_source
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
                article.get("api_source", "rss")
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
    milestone_message: str = None
) -> int:
    """Save user's news writing work."""
    with get_db() as conn:
        cursor = conn.cursor()

        sql = """
            INSERT INTO user_writings (
                user_id, article_id, title, content, content_html, content_json, word_count, year_level, milestone_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(_convert_placeholders(sql), (
            user_id, article_id, title, content, content_html, content_json, word_count, year_level, milestone_message
        ))

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
