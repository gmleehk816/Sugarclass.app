# API Reference

All API endpoints return JSON responses. Base URL: `http://127.0.0.1:7000`

---

## Endpoints

### **GET /** 
Main application page (HTML)

**Response**: HTML page with 3-column layout

---

### **GET /api/simple/stats**
Get database statistics

**Parameters**: None

**Response**:
```json
{
  "total": 228,
  "full": 184,
  "sources": 11
}
```

**Fields**:
- `total` (int): Total number of articles in database
- `full` (int): Articles with full_text content
- `sources` (int): Number of unique sources

**Example**:
```javascript
fetch('/api/simple/stats')
  .then(r => r.json())
  .then(data => console.log(data.total));
```

---

### **GET /api/simple/sources**
Get list of all sources with article counts

**Parameters**: None

**Response**:
```json
{
  "sources": [
    {
      "name": "BBC News - Science",
      "count": 45,
      "age_groups": ["14-16", "17+"]
    },
    {
      "name": "NASA Breaking News",
      "count": 23,
      "age_groups": ["11-13", "14-16"]
    }
  ]
}
```

**Fields**:
- `sources` (array): List of source objects
  - `name` (string): Source name
  - `count` (int): Number of articles from this source
  - `age_groups` (array): Age groups this source has articles for

**Example**:
```javascript
fetch('/api/simple/sources')
  .then(r => r.json())
  .then(data => {
    data.sources.forEach(s => console.log(`${s.name}: ${s.count}`));
  });
```

---

### **GET /api/simple/articles**
Get filtered list of articles

**Parameters** (all optional):
- `source` (string): Filter by source name
- `age_group` (string): Filter by age group ("7-10", "11-13", "14-16", "17+")
- `date_from` (string): ISO date string (YYYY-MM-DD)
- `date_to` (string): ISO date string (YYYY-MM-DD)
- `search` (string): Search in title/description (case-insensitive, partial match)

**Response**:
```json
{
  "articles": [
    {
      "id": 123,
      "source_name": "BBC News - Science",
      "title": "New Discovery in Quantum Physics",
      "url": "https://bbc.com/news/science/article123",
      "published_date": "2025-01-10T14:30:00Z",
      "description": "Scientists have made a breakthrough...",
      "image_url": "https://bbc.com/images/article123.jpg",
      "categories": ["Science & Technology", "Research"],
      "age_group": "14-16",
      "has_full_text": true,
      "collected_at": "2025-01-10T15:00:00Z"
    }
  ],
  "total": 45,
  "filtered": 12
}
```

**Fields**:
- `articles` (array): List of article objects
  - `id` (int): Unique article ID
  - `source_name` (string): Source name
  - `title` (string): Article title
  - `url` (string): Full article URL
  - `published_date` (string): ISO 8601 timestamp
  - `description` (string): Article summary/excerpt
  - `image_url` (string|null): Featured image URL
  - `categories` (array): List of category strings
  - `age_group` (string|null): Age group classification
  - `has_full_text` (bool): Whether full_text is available
  - `collected_at` (string): When article was collected
- `total` (int): Total articles in database
- `filtered` (int): Articles matching filters

**Examples**:

```javascript
// Get all articles for 11-13 age group
fetch('/api/simple/articles?age_group=11-13')
  .then(r => r.json())
  .then(data => console.log(data.articles));

// Get articles from specific source
fetch('/api/simple/articles?source=BBC%20News%20-%20Science')
  .then(r => r.json())
  .then(data => console.log(data.articles));

// Get articles from date range
fetch('/api/simple/articles?date_from=2025-01-01&date_to=2025-01-10')
  .then(r => r.json())
  .then(data => console.log(data.articles));

// Search articles
fetch('/api/simple/articles?search=quantum')
  .then(r => r.json())
  .then(data => console.log(data.articles));

// Combine filters
fetch('/api/simple/articles?age_group=14-16&source=NASA&date_from=2025-01-01')
  .then(r => r.json())
  .then(data => console.log(data.articles));
```

---

### **GET /api/simple/article/<id>**
Get full article details including full text

**Parameters**:
- `id` (int): Article ID (URL path parameter)

**Response**:
```json
{
  "id": 123,
  "source_name": "BBC News - Science",
  "title": "New Discovery in Quantum Physics",
  "url": "https://bbc.com/news/science/article123",
  "published_date": "2025-01-10T14:30:00Z",
  "description": "Scientists have made a breakthrough...",
  "full_text": "Full article content here...\n\nParagraph 2...\n\nParagraph 3...",
  "image_url": "https://bbc.com/images/article123.jpg",
  "categories": ["Science & Technology", "Research"],
  "age_group": "14-16",
  "collected_at": "2025-01-10T15:00:00Z"
}
```

**Fields**: Same as `/api/simple/articles` but includes:
- `full_text` (string|null): Complete article text content

**Error Response** (404):
```json
{
  "error": "Article not found"
}
```

**Example**:
```javascript
// Get full article by ID
fetch('/api/simple/article/123')
  .then(r => r.json())
  .then(article => {
    console.log(article.full_text);
  });
```

---

## Error Responses

All endpoints may return standard HTTP error codes:

### **400 Bad Request**
```json
{
  "error": "Invalid parameter: age_group must be one of 7-10, 11-13, 14-16, 17+"
}
```

### **404 Not Found**
```json
{
  "error": "Article not found"
}
```

### **500 Internal Server Error**
```json
{
  "error": "Database error",
  "details": "Error message here"
}
```

---

## Frontend Integration

### **Age Group Filtering**
```javascript
function selectAgeGroup(age) {
  const ageToSources = {
    '7-10': ['BBC Newsround', 'NASA Kids', 'National Geographic Kids'],
    '11-13': ['NASA Breaking News', 'CNN Science', 'BBC News - Science'],
    '14-16': ['BBC News', 'CNN', 'Reuters', 'NPR', 'Guardian'],
    '17+': ['ScienceDaily', 'Nature News', 'Wired', 'Ars Technica']
  };
  
  const sources = ageToSources[age] || [];
  loadArticles(sources, age);
}

function loadArticles(sources, ageGroup) {
  const params = new URLSearchParams();
  if (sources.length > 0) params.append('source', sources[0]);
  if (ageGroup) params.append('age_group', ageGroup);
  
  fetch(`/api/simple/articles?${params}`)
    .then(r => r.json())
    .then(data => renderArticles(data.articles));
}
```

### **Search and Filter**
```javascript
function applyFilters() {
  const params = new URLSearchParams();
  
  const search = document.getElementById('searchInput').value;
  if (search) params.append('search', search);
  
  const dateFrom = document.getElementById('dateFrom').value;
  if (dateFrom) params.append('date_from', dateFrom);
  
  const dateTo = document.getElementById('dateTo').value;
  if (dateTo) params.append('date_to', dateTo);
  
  fetch(`/api/simple/articles?${params}`)
    .then(r => r.json())
    .then(data => renderArticles(data.articles));
}
```

### **Statistics Dashboard**
```javascript
async function updateStats() {
  const stats = await fetch('/api/simple/stats').then(r => r.json());
  document.getElementById('totalArticles').textContent = stats.total;
  document.getElementById('fullTextArticles').textContent = stats.full;
  document.getElementById('totalSources').textContent = stats.sources;
}
```

---

## Rate Limiting

Currently **no rate limiting** is implemented. For production use, consider:
- 100 requests/minute per IP
- 10 requests/second per endpoint
- Use Flask-Limiter extension

---

## CORS Policy

Currently **localhost only** (127.0.0.1:7000).

To enable CORS for external access:
```python
# app_enhanced.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow all origins
```

Or restrict to specific domains:
```python
CORS(app, resources={r"/api/*": {"origins": ["https://yourdomain.com"]}})
```

---

## Data Freshness

Articles are collected by running `simple_collector.py` manually. No automatic refresh.

To update articles:
```powershell
cd c:\SynologyDrive\coding\realtimewriter\newscollect
python simple_collector.py
```

Consider adding cron job (Linux) or Task Scheduler (Windows) for automatic updates.

---

## Performance Notes

- **Database**: SQLite with indexes on `source_name`, `published_date`, `age_group`
- **Query Speed**: <10ms for most queries (228 articles)
- **Scalability**: Tested up to 10,000 articles without issues
- **Image Loading**: Images loaded lazily in frontend
- **Full Text**: Not included in list view to reduce payload size

---

## Future API Enhancements

Planned for Phase 2:
- `POST /api/simple/classify` - Re-classify article age group
- `GET /api/simple/categories` - Get category taxonomy
- `POST /api/simple/collect` - Trigger collection for specific source
- `DELETE /api/simple/article/<id>` - Remove article
- `GET /api/simple/sources/<name>/articles` - Get all articles from source
- WebSocket support for real-time updates
