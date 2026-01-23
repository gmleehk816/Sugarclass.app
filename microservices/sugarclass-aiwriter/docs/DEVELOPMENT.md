# Development Guide

Guidelines for contributing to the News Collector project.

---

## Getting Started

### **Prerequisites**
- Python 3.13+
- Git (for version control)
- Code editor (VS Code recommended)
- Basic knowledge of Flask, SQLite, HTML/CSS/JavaScript

### **Setup Development Environment**

```powershell
# 1. Clone repository
cd c:\SynologyDrive\coding\realtimewriter\newscollect

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run in development mode
python run_server.py
```

---

## Project Code Style

### **Python Code Style**

Follow guidelines in [AGENTS.md](../AGENTS.md):

```python
# Good
def fetch_article(url: str, timeout: int = 10) -> dict | None:
    """Fetch article from URL with timeout."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return {'text': resp.text, 'url': url}
    except requests.RequestException as e:
        print(f'Error fetching {url}: {e}')
        return None

# Bad
def fetchArticle(url):  # Missing type hints, camelCase
    resp = requests.get(url)  # No error handling, no timeout
    return resp.text  # Wrong return type
```

**Key Rules**:
- Use 4-space indentation
- Type hints for all functions
- snake_case for functions/variables
- Maximum line length: 100 characters
- f-strings for string formatting

### **JavaScript Code Style**

Follow guidelines in [AGENTS.md](../AGENTS.md):

```javascript
// Good
async function loadArticles(sources, ageGroup) {
  try {
    const params = new URLSearchParams();
    if (sources.length > 0) params.append('source', sources[0]);
    if (ageGroup) params.append('age_group', ageGroup);
    
    const resp = await fetch(`/api/simple/articles?${params}`);
    const json = await resp.json();
    return json.articles;
  } catch (e) {
    console.error('Failed to load articles:', e);
    return [];
  }
}

// Bad
function loadArticles(sources, ageGroup) {  // Not async
  fetch(`/api/simple/articles?source=${sources[0]}&age_group=${ageGroup}`)  // No error handling
    .then(r => r.json())
    .then(data => renderArticles(data.articles));  // Side effect in function
}
```

**Key Rules**:
- Use 2-space indentation
- No semicolons
- async/await for asynchronous operations
- const/let (never var)
- Maximum line length: 100 characters

---

## Adding New Sources

### **Step 1: Research Source**

Check if source meets criteria:
- ✅ Has RSS/Atom feed
- ✅ Provides full articles (not just headlines)
- ✅ Free to access (no paywall)
- ✅ Age-appropriate content
- ✅ Regular updates (daily/weekly)
- ✅ Reliable publisher

**Find RSS Feed**:
```powershell
# Method 1: Look for RSS icon on website
# Method 2: Check common paths
curl https://example.com/rss
curl https://example.com/feed
curl https://example.com/rss.xml

# Method 3: View page source, search for "rss" or "atom"
```

### **Step 2: Test Feed Parsing**

```python
# test_source.py
import feedparser

feed_url = 'https://example.com/rss'
d = feedparser.parse(feed_url)

print(f'Feed Title: {d.feed.title}')
print(f'Entry Count: {len(d.entries)}')

if len(d.entries) > 0:
    entry = d.entries[0]
    print(f'First Article:')
    print(f'  Title: {entry.title}')
    print(f'  Link: {entry.link}')
    print(f'  Published: {entry.get("published", "N/A")}')
```

### **Step 3: Test Article Extraction**

```python
# test_extraction.py
import requests
from trafilatura import fetch_url, extract
from newspaper import Article

url = 'https://example.com/article123'

# Test trafilatura
print('Testing trafilatura...')
downloaded = fetch_url(url)
if downloaded:
    text = extract(downloaded)
    print(f'Success: {len(text)} characters extracted')
else:
    print('Failed')

# Test newspaper4k
print('\nTesting newspaper4k...')
article = Article(url)
article.download()
article.parse()
print(f'Success: {len(article.text)} characters extracted')
print(f'Has image: {bool(article.top_image)}')
```

### **Step 4: Add to simple_collector.py**

```python
# simple_collector.py
SOURCES = [
    {
        'name': 'Your Source Name',
        'url': 'https://example.com/rss',
        'category': 'General News',  # See CATEGORIES.md
        'age_groups': ['14-16', '17+']  # Target age groups
    },
    # ... existing sources
]
```

### **Step 5: Collect and Verify**

```powershell
# Run collector
python simple_collector.py

# Check database
python -c "
import database
db = database.get_db()
count = db.execute('SELECT COUNT(*) FROM articles WHERE source_name = ?', ('Your Source Name',)).fetchone()[0]
print(f'Articles collected: {count}')
"

# View in browser
python run_server.py
# Open http://127.0.0.1:7000
```

---

## Modifying the UI

### **Changing Layout**

All layout code is in [app_enhanced.py](../app_enhanced.py):

```python
# HTML structure (line ~50-150)
<div class="app-container">
  <div class="left-sidebar">...</div>
  <div class="main-content">...</div>
  <div class="right-sidebar">...</div>
</div>

# CSS Grid (line ~200-250)
.app-container {
  display: grid;
  grid-template-columns: 280px 1fr 320px;  # Left | Middle | Right
}
```

**Example: Add 4th Column**

```python
# Change grid template
.app-container {
  grid-template-columns: 280px 1fr 320px 200px;  # Add 200px column
}

# Add 4th div in HTML
<div class="app-container">
  <div class="left-sidebar">...</div>
  <div class="main-content">...</div>
  <div class="right-sidebar">...</div>
  <div class="extra-sidebar">...</div>  # New column
</div>
```

### **Adding New Filters**

```javascript
// static/app.js (embedded in app_enhanced.py)

// 1. Add HTML control
<select id="categoryFilter" onchange="applyFilters()">
  <option value="">All Categories</option>
  <option value="Science & Technology">Science & Technology</option>
  <option value="Entertainment">Entertainment</option>
</select>

// 2. Add JavaScript filter logic
function applyFilters() {
  const params = new URLSearchParams();
  
  const category = document.getElementById('categoryFilter').value;
  if (category) params.append('category', category);
  
  // ... existing filters
  
  fetch(`/api/simple/articles?${params}`)
    .then(r => r.json())
    .then(data => renderArticles(data.articles));
}
```

### **Changing Colors**

```css
/* app_enhanced.py CSS section */

/* Change left sidebar gradient */
.left-sidebar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  /* Replace with your colors, e.g., #ff6b6b to #4ecdc4 */
}

/* Change button hover color */
.age-btn:hover {
  background: rgba(255, 255, 255, 0.2);  /* Adjust opacity */
}

/* Change article card background */
.article-item {
  background: white;  /* Change to #f8f9fa for light gray */
}
```

---

## API Development

### **Adding New Endpoint**

```python
# app_enhanced.py

@app.get('/api/simple/categories')
def api_categories():
    """Get list of all categories with article counts."""
    db = get_db()
    
    # Query database
    rows = db.execute('''
        SELECT categories, COUNT(*) as count
        FROM articles
        WHERE categories IS NOT NULL
        GROUP BY categories
        ORDER BY count DESC
    ''').fetchall()
    
    # Process results
    category_counts = {}
    for row in rows:
        cats = json.loads(row['categories'] or '[]')
        for cat in cats:
            category_counts[cat] = category_counts.get(cat, 0) + row['count']
    
    return jsonify({
        'categories': [
            {'name': name, 'count': count}
            for name, count in category_counts.items()
        ]
    })
```

### **Testing API Endpoint**

```powershell
# Test with curl
curl http://127.0.0.1:7000/api/simple/categories

# Or with PowerShell
Invoke-RestMethod -Uri http://127.0.0.1:7000/api/simple/categories
```

---

## Database Modifications

### **Adding New Column**

```python
# 1. Create migration script (e.g., add_author_column.py)
import sqlite3

conn = sqlite3.connect('newscollect.db')
cursor = conn.cursor()

# Add column
cursor.execute('ALTER TABLE articles ADD COLUMN author TEXT')

# Update existing rows (optional)
cursor.execute('UPDATE articles SET author = "Unknown" WHERE author IS NULL')

conn.commit()
conn.close()
print('Migration complete')
```

```powershell
# 2. Run migration
python add_author_column.py

# 3. Verify
python -c "
import sqlite3
conn = sqlite3.connect('newscollect.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(articles)')
for row in cursor.fetchall():
    print(row)
"
```

### **Adding Index**

```python
# database.py
def init_db():
    # ... existing code
    
    # Add new index
    db.execute('CREATE INDEX IF NOT EXISTS idx_category ON articles(categories)')
    db.commit()
```

---

## Testing

### **Manual Testing Checklist**

**Frontend**:
- [ ] Age buttons filter correctly
- [ ] Search filters articles
- [ ] Date range filters work
- [ ] Articles display with images
- [ ] Statistics update correctly
- [ ] Responsive layout on different screen sizes

**API**:
- [ ] `/api/simple/stats` returns correct counts
- [ ] `/api/simple/sources` lists all sources
- [ ] `/api/simple/articles` filters by age group
- [ ] `/api/simple/articles` filters by date range
- [ ] `/api/simple/article/<id>` returns full text

**Collection**:
- [ ] `simple_collector.py` runs without errors
- [ ] Articles saved to database
- [ ] No duplicate URLs
- [ ] Full text extracted successfully
- [ ] Images extracted when available

### **Automated Testing**

```python
# test_api.py
import requests

BASE_URL = 'http://127.0.0.1:7000'

def test_stats():
    resp = requests.get(f'{BASE_URL}/api/simple/stats')
    assert resp.status_code == 200
    data = resp.json()
    assert 'total' in data
    assert 'full' in data
    assert 'sources' in data
    print('✓ Stats endpoint working')

def test_articles():
    resp = requests.get(f'{BASE_URL}/api/simple/articles?age_group=11-13')
    assert resp.status_code == 200
    data = resp.json()
    assert 'articles' in data
    assert len(data['articles']) > 0
    print('✓ Articles endpoint working')

if __name__ == '__main__':
    test_stats()
    test_articles()
    print('All tests passed!')
```

---

## Debugging

### **Common Issues**

**Issue**: Server won't start
```powershell
# Check port availability
Get-NetTCPConnection -LocalPort 7000

# Kill process using port
Get-Process -Id (Get-NetTCPConnection -LocalPort 7000).OwningProcess | Stop-Process -Force
```

**Issue**: Articles not displaying
```javascript
// Open browser console (F12)
// Check for JavaScript errors

// Check API response
fetch('/api/simple/articles')
  .then(r => r.json())
  .then(data => console.log(data));
```

**Issue**: Extraction failing
```python
# Test extraction manually
from trafilatura import fetch_url, extract

url = 'https://problem-url.com/article'
downloaded = fetch_url(url)
print(f'Downloaded: {len(downloaded)} bytes')

text = extract(downloaded)
print(f'Extracted: {len(text)} characters')
```

### **Logging**

```python
# app_enhanced.py - add logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.get('/api/simple/articles')
def api_articles():
    logger.debug(f'Request args: {request.args}')
    # ... existing code
    logger.debug(f'Returning {len(articles)} articles')
    return jsonify({'articles': articles})
```

---

## Git Workflow

### **Branching Strategy**

```bash
# Main branch (stable)
main

# Feature branches
feature/add-category-filter
feature/improve-extraction

# Bug fix branches
fix/article-display-bug
fix/date-filter-issue
```

### **Making Changes**

```powershell
# 1. Create feature branch
git checkout -b feature/add-category-filter

# 2. Make changes
# Edit files...

# 3. Test changes
python run_server.py
# Test in browser

# 4. Commit changes
git add .
git commit -m "Add category filter to sidebar"

# 5. Push to remote
git push origin feature/add-category-filter

# 6. Create pull request (if using GitHub)
# Or merge to main (if working solo)
git checkout main
git merge feature/add-category-filter
```

---

## Performance Optimization

### **Database Query Optimization**

```python
# Bad: N+1 query problem
for source in sources:
    articles = db.execute('SELECT * FROM articles WHERE source_name = ?', (source,)).fetchall()

# Good: Single query with IN clause
placeholders = ','.join('?' * len(sources))
articles = db.execute(f'SELECT * FROM articles WHERE source_name IN ({placeholders})', sources).fetchall()
```

### **Frontend Optimization**

```javascript
// Bad: Re-render entire list on filter
function applyFilters() {
  const articles = await loadArticles();
  document.getElementById('articleGrid').innerHTML = '';  // Clear all
  articles.forEach(article => renderArticle(article));  // Re-render all
}

// Good: Only update changed articles
function applyFilters() {
  const articles = await loadArticles();
  const grid = document.getElementById('articleGrid');
  
  // Remove articles not in new list
  const existingIds = new Set(articles.map(a => a.id));
  grid.querySelectorAll('.article-item').forEach(el => {
    if (!existingIds.has(parseInt(el.dataset.id))) {
      el.remove();
    }
  });
  
  // Add new articles only
  articles.forEach(article => {
    if (!grid.querySelector(`[data-id="${article.id}"]`)) {
      renderArticle(article);
    }
  });
}
```

---

## Release Process

### **Versioning**

Follow Semantic Versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., database schema change)
- **MINOR**: New features (e.g., add category filter)
- **PATCH**: Bug fixes (e.g., fix extraction error)

### **Release Checklist**

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number bumped
- [ ] Database migration (if needed)
- [ ] Backup database before deployment
- [ ] Deploy to production
- [ ] Verify deployment
- [ ] Tag release in Git

---

## Getting Help

### **Resources**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [trafilatura Documentation](https://trafilatura.readthedocs.io/)
- [newspaper4k Documentation](https://newspaper4k.readthedocs.io/)

### **Common Questions**

**Q: How do I change the port?**
A: Edit `app_enhanced.py` line 748 and `run_server.py` line 16

**Q: How do I add a new category?**
A: Add to `CATEGORIES` list in [CATEGORIES.md](CATEGORIES.md), no code changes needed

**Q: How do I backup the database?**
A: Copy `newscollect.db` file to backup location

**Q: How do I reset the database?**
A: Delete `newscollect.db`, run `python database.py`, then `python simple_collector.py`

---

## Contributing Guidelines

1. **Code Style**: Follow [AGENTS.md](../AGENTS.md) guidelines
2. **Testing**: Test all changes manually before committing
3. **Documentation**: Update docs for any API/UI changes
4. **Commit Messages**: Use clear, descriptive messages
5. **Pull Requests**: Include description of changes and testing done

---

## Related Documentation

- [README.md](../README.md) - Project overview
- [API.md](API.md) - API reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [AGENTS.md](../AGENTS.md) - Code style guide
