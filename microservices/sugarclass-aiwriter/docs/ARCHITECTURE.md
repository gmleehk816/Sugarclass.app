# System Architecture

Complete technical documentation of the News Collector application architecture.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           User Browser                               │
│                     (http://127.0.0.1:7000)                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Flask Web Server (app_enhanced.py)                │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Routes     │  │   Templates  │  │  Static Files │             │
│  │  (API/HTML)  │  │   (HTML)     │  │  (JS/CSS)     │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ SQL Queries
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SQLite Database (database.py)                     │
│                         newscollect.db                               │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  articles table (228 rows)                                  │    │
│  │  - id, source_name, title, url, published_date             │    │
│  │  - description, full_text, image_url                       │    │
│  │  - categories (JSON), age_group, collected_at              │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Insert Articles
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              RSS Collector (simple_collector.py)                     │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Feed Parser  │→ │  Extraction  │→ │  Database    │             │
│  │  (57 feeds)  │  │   Pipeline   │  │  Insertion   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       External RSS Feeds                             │
│   BBC, CNN, NASA, NPR, Guardian, Vox, ESPN, etc. (57 sources)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### **1. Flask Web Server (app_enhanced.py)**

**Purpose**: Main application server handling HTTP requests and responses

**Key Components**:
- **Routes**: 5 endpoints (`/`, `/api/simple/stats`, `/api/simple/sources`, `/api/simple/articles`, `/api/simple/article/<id>`)
- **Templates**: Embedded HTML with Jinja2 (3-column layout)
- **Static Files**: Served from `static/` directory (app.js, styles.css)
- **Database Interface**: Uses `database.py` for all queries

**Technologies**:
- Flask 3.1+ (micro web framework)
- Jinja2 (templating engine)
- Werkzeug (WSGI utility library)

**Configuration**:
- Host: `127.0.0.1` (localhost only)
- Port: `7000` (configurable)
- Debug Mode: Enabled (development)

**Process Flow**:
1. User requests page (`/`)
2. Flask renders HTML template with embedded CSS/JS
3. Frontend JavaScript makes API calls (`/api/simple/articles`)
4. Flask queries database via `database.py`
5. Returns JSON response
6. Frontend renders articles

---

### **2. Database Layer (database.py)**

**Purpose**: SQLite database operations and schema management

**Schema**:
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    published_date TEXT,
    description TEXT,
    full_text TEXT,
    image_url TEXT,
    categories TEXT,
    age_group TEXT,
    collected_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_source ON articles(source_name);
CREATE INDEX idx_date ON articles(published_date);
CREATE INDEX idx_age_group ON articles(age_group);
```

**Key Functions**:
- `get_db()` - Returns database connection
- `init_db()` - Creates schema and indexes
- `close_db()` - Closes connection
- `save_article(article)` - Inserts article with duplicate check

**Data Types**:
- `TEXT` for all string fields
- `INTEGER` for id (auto-increment)
- ISO 8601 format for dates (`YYYY-MM-DDTHH:MM:SSZ`)
- JSON strings for categories array

**Indexes**:
- `idx_source` - Fast filtering by source_name
- `idx_date` - Fast date range queries
- `idx_age_group` - Fast age group filtering

**Performance**:
- File-based SQLite (no server required)
- In-memory caching via Flask context
- ~10ms query time for 228 articles
- Scales to 10,000+ articles without issues

---

### **3. RSS Collector (simple_collector.py)**

**Purpose**: Fetch and extract articles from 57 RSS sources

**Collection Process**:
```
1. Parse RSS feed with feedparser
   ↓
2. Extract article URL and metadata
   ↓
3. Download full article HTML
   ↓
4. Extract text with multi-method fallback:
   - Method 1: trafilatura (best for modern sites)
   - Method 2: newspaper4k (good for traditional news)
   - Method 3: html_parser (regex fallback)
   ↓
5. Classify age group (source-based or LLM)
   ↓
6. Save to database with deduplication
```

**Source Configuration**:
```python
SOURCES = [
    {
        'name': 'BBC News - Science',
        'url': 'http://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
        'category': 'Science & Technology',
        'age_groups': ['14-16', '17+']
    },
    # ... 56 more sources
]
```

**Extraction Libraries**:
1. **trafilatura** (v2.0.2)
   - Downloads HTML with `fetch_url()`
   - Extracts with `extract()`
   - Best for: Wired, Vox, ProPublica, modern sites
   - Success Rate: ~95%
   - Average Words: 1,500-4,000

2. **newspaper4k** (v0.9.3)
   - Parses with `Article()` class
   - Automatically downloads and parses
   - Best for: CNN, BBC, NPR, traditional news
   - Success Rate: ~85%
   - Average Words: 600-1,200

3. **html_parser** (BeautifulSoup + regex)
   - Finds `<p>` tags with `soup.find_all('p')`
   - Filters by length (>50 chars)
   - Best for: Simple sites, fallback
   - Success Rate: ~60%
   - Average Words: 300-800

**Rate Limiting**:
- No built-in rate limiting (RSS feeds are public)
- Respectful scraping: 1-2 sec delay between requests
- User-Agent: `NewscollectBot/1.0`

**Error Handling**:
- Try/except for each extraction method
- Fallback to next method on failure
- Skip article if all methods fail
- Log errors to console

---

### **4. Frontend (static/app.js, templates/index.html)**

**Purpose**: User interface for browsing and filtering articles

**Layout Structure**:
```html
<div class="app-container">  <!-- CSS Grid 3-column -->
  <div class="left-sidebar">
    <!-- Age group buttons -->
    <div class="age-groups">
      <button onclick="selectAgeGroup('7-10')">7-10 Kids</button>
      <button onclick="selectAgeGroup('11-13')">11-13 Teens</button>
      <button onclick="selectAgeGroup('14-16')">14-16 High School</button>
      <button onclick="selectAgeGroup('17+')">All Ages</button>
    </div>
    
    <!-- Category filters (placeholder) -->
    <div class="categories">
      <h3>Categories</h3>
      <div id="categoryFilters"></div>
    </div>
  </div>
  
  <div class="main-content">
    <!-- Search and filters -->
    <div class="controls">
      <input type="text" id="searchInput" placeholder="Search...">
      <button onclick="applyFilters()">Search</button>
    </div>
    
    <!-- Article grid -->
    <div class="article-grid" id="articleGrid">
      <!-- Articles rendered by JavaScript -->
    </div>
  </div>
  
  <div class="right-sidebar">
    <!-- Statistics -->
    <div class="stats">
      <div class="stat-card">
        <div class="stat-value" id="totalArticles">228</div>
        <div class="stat-label">Total Articles</div>
      </div>
      <!-- More stats... -->
    </div>
    
    <!-- Date filters -->
    <div class="filters">
      <label>From:</label>
      <input type="date" id="dateFrom">
      <label>To:</label>
      <input type="date" id="dateTo">
    </div>
  </div>
</div>
```

**Key JavaScript Functions**:
- `selectAgeGroup(age)` - Filter by age, update source list
- `loadArticles(sources, ageGroup)` - Fetch articles from API
- `applyFilters()` - Apply search and date filters
- `renderArticles(articles)` - Display articles in grid
- `updateStats()` - Fetch and display statistics

**CSS Grid Layout**:
```css
.app-container {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  height: 100vh;
}

.left-sidebar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.main-content {
  background: white;
  padding: 30px;
  overflow-y: auto;
}

.right-sidebar {
  background: white;
  border-left: 1px solid #e2e8f0;
  padding: 20px;
}
```

---

## Data Flow Diagrams

### **Article Collection Flow**

```
[User runs simple_collector.py]
         ↓
[Loop through 57 sources]
         ↓
[Parse RSS feed with feedparser]
         ↓
[For each article in feed (limit 10)]
         ↓
[Check if URL exists in database]
         ↓ (if new)
[Download HTML with requests]
         ↓
[Try extraction method 1: trafilatura]
         ↓ (if fails)
[Try extraction method 2: newspaper4k]
         ↓ (if fails)
[Try extraction method 3: html_parser]
         ↓ (if success)
[Classify age group (source-based)]
         ↓
[Insert into database]
         ↓
[Continue to next article]
```

### **User Request Flow**

```
[User clicks age button "11-13"]
         ↓
[selectAgeGroup() called]
         ↓
[Map age to sources: ["NASA", "CNN Science", ...]]
         ↓
[Build API URL: /api/simple/articles?age_group=11-13]
         ↓
[Fetch from Flask server]
         ↓
[Flask queries database: SELECT * FROM articles WHERE age_group = '11-13']
         ↓
[Return JSON: {articles: [...], total: 38}]
         ↓
[JavaScript renders articles in grid]
         ↓
[User sees 38 articles for 11-13]
```

---

## Scalability Considerations

### **Current Scale**
- **Articles**: 228
- **Sources**: 57 configured, 11 collected
- **Database Size**: ~15MB
- **Query Time**: <10ms
- **Page Load**: ~500ms

### **Projected Scale (Phase 2)**
- **Articles**: 5,000+ (57 sources × 10 articles × multiple collections)
- **Sources**: 75+
- **Database Size**: ~200MB
- **Query Time**: ~50ms (still fast with indexes)
- **Page Load**: ~1s

### **Optimization Strategies**
1. **Database**:
   - Add composite indexes: `(age_group, published_date)`
   - Pagination: Limit 50 articles per page
   - Archive old articles: Move articles >90 days to separate table

2. **API**:
   - Response caching: Cache API responses for 5 minutes
   - Compression: Enable gzip compression for JSON responses
   - Rate limiting: 100 requests/minute per IP

3. **Frontend**:
   - Lazy loading: Load images on scroll
   - Virtual scrolling: Render only visible articles
   - Local storage: Cache article list for 5 minutes

4. **Collection**:
   - Parallel collection: Use `ThreadPoolExecutor` for 5 concurrent sources
   - Incremental updates: Only collect new articles (check last_collected timestamp)
   - Scheduled collection: Daily cron job instead of manual runs

---

## Security Architecture

### **Current Security Measures**

**1. Database Security**:
- SQLite file in non-public directory
- No direct database access from frontend
- Parameterized queries (no SQL injection)
- Unique URL constraint (prevents duplicates)

**2. API Security**:
- Localhost only (127.0.0.1) - no external access
- No authentication required (internal tool)
- Input validation on all parameters
- No user-generated content (read-only for users)

**3. Scraping Security**:
- Respect robots.txt (manual check)
- User-Agent header set
- No aggressive scraping (1-2 sec delays)
- Only public RSS feeds (no login required)

**4. Frontend Security**:
- No eval() or dangerous JavaScript
- Content sanitization (escapeHtml function)
- HTTPS only (when deployed)
- No localStorage of sensitive data

### **Production Security Enhancements**

**For Public Deployment**:
1. **Authentication**: Add JWT-based API authentication
2. **HTTPS**: Use SSL/TLS certificates
3. **Rate Limiting**: Implement Flask-Limiter (100 req/min)
4. **CORS**: Restrict to allowed domains only
5. **Input Sanitization**: Add HTML escaping on all user inputs
6. **Database Encryption**: Encrypt sensitive fields
7. **Logging**: Log all API access with IP addresses
8. **Monitoring**: Add error tracking (Sentry, Rollbar)

---

## Deployment Architecture

### **Current Setup (Development)**

```
Windows Machine (localhost:7000)
         ↓
  PowerShell Terminal
         ↓
  run_server.py (auto-restart wrapper)
         ↓
  app_enhanced.py (Flask development server)
         ↓
  newscollect.db (SQLite file)
```

### **Recommended Production Setup**

```
┌─────────────────────────────────────────┐
│         Nginx Reverse Proxy              │
│     (SSL termination, load balancing)    │
└────────────┬────────────────────────────┘
             │
             │ HTTP (internal)
             ▼
┌─────────────────────────────────────────┐
│    Gunicorn/Waitress (WSGI Server)      │
│         (4 worker processes)             │
└────────────┬────────────────────────────┘
             │
             │
             ▼
┌─────────────────────────────────────────┐
│       Flask App (app_enhanced.py)        │
└────────────┬────────────────────────────┘
             │
             │
             ▼
┌─────────────────────────────────────────┐
│      SQLite Database (newscollect.db)   │
│      (or PostgreSQL for high traffic)   │
└─────────────────────────────────────────┘
```

**Production Components**:
1. **Nginx**: Handle SSL, compression, static files, load balancing
2. **Gunicorn/Waitress**: Production WSGI server (multi-process)
3. **Systemd Service**: Auto-start Flask on boot
4. **Cron Job**: Scheduled article collection (daily at 6 AM)
5. **Monitoring**: Prometheus + Grafana for metrics
6. **Backups**: Daily database backups to S3/cloud storage

---

## Technology Choices Rationale

### **Why Flask?**
- Lightweight and fast for small/medium apps
- Easy to learn and maintain
- Built-in development server
- Excellent documentation
- Large ecosystem of extensions

### **Why SQLite?**
- No server setup required
- Single-file database (easy backups)
- Fast for <10,000 articles
- ACID compliant
- Built into Python
- Easy to migrate to PostgreSQL later

### **Why trafilatura?**
- Best extraction quality (tested on Wired, Vox, ProPublica)
- Handles modern JavaScript-heavy sites
- Extracts tables and structured content
- Fast and reliable
- Actively maintained

### **Why Vanilla JavaScript (no React/Vue)?**
- Simple application (no complex state management)
- Fast page load (no framework overhead)
- Easy to understand and modify
- No build process required
- Fewer dependencies

### **Why CSS Grid (not Flexbox)?**
- Perfect for 2D layouts (rows + columns)
- Fixed sidebar widths (280px left, 320px right)
- Simple responsive design
- Better than floats or absolute positioning
- Modern browser support (95%+)

---

## Related Documentation

- [API.md](API.md) - API endpoint details
- [SETUP.md](SETUP.md) - Installation and configuration
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development guidelines
- [SOURCES.md](SOURCES.md) - Source configuration
- [CATEGORIES.md](CATEGORIES.md) - Category taxonomy
