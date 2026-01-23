# Setup Guide

Complete installation and configuration guide for the News Collector application.

---

## System Requirements

### **Minimum**
- OS: Windows 10/11 (PowerShell 5.1+)
- Python: 3.11+
- RAM: 2GB
- Disk: 500MB free space
- Internet: Stable connection for RSS feeds

### **Recommended**
- OS: Windows 11
- Python: 3.13+
- RAM: 4GB
- Disk: 2GB free space
- Internet: 10+ Mbps

### **Tested Environment**
- Windows 11 Pro
- Python 3.13.1
- PowerShell 7.4.6
- 16GB RAM

---

## Installation

### **Step 1: Install Python**

Download Python 3.13+ from [python.org](https://www.python.org/downloads/)

```powershell
# Verify installation
python --version
# Output: Python 3.13.1 (or higher)

# Verify pip
pip --version
# Output: pip 24.3.1 (or similar)
```

### **Step 2: Clone/Download Project**

```powershell
# Navigate to project directory
cd c:\SynologyDrive\coding\realtimewriter\newscollect

# Or clone from repository (if applicable)
# git clone https://github.com/yourrepo/newscollect.git
# cd newscollect
```

### **Step 3: Install Dependencies**

```powershell
# Install all required packages
pip install -r requirements.txt

# Expected packages:
# - Flask==3.1.0
# - requests==2.32.3
# - feedparser==6.0.11
# - trafilatura==2.0.2
# - newspaper4k==0.9.3
# - python-dotenv==1.0.1
# - beautifulsoup4==4.12.3
```

**Verify Installation**:
```powershell
python -c "import flask; print(flask.__version__)"
# Output: 3.1.0

python -c "import trafilatura; print(trafilatura.__version__)"
# Output: 2.0.2
```

### **Step 4: Set Up Environment Variables (Optional)**

Create `.env` file in `newscollect/` directory for LLM classification:

```env
# .env
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-flash
```

**Get Gemini API Key**:
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with Google account
3. Create new API key
4. Copy key to `.env` file

**Note**: LLM classification is optional. The app works without it using source-based classification.

### **Step 5: Initialize Database**

```powershell
# Database is auto-created on first run
# To verify schema:
python -c "import database; database.init_db(); print('Database initialized')"
```

### **Step 6: Collect Initial Articles**

```powershell
# Run collector to fetch articles from 11 sources
python simple_collector.py

# Expected output:
# Collecting from BBC News - Science...
# Saved 10 articles from BBC News - Science
# Collecting from CNN - Science...
# ...
# Total articles collected: 110
```

**First Run Takes**: 5-10 minutes (57 sources * ~10 articles each)

### **Step 7: Start Server**

```powershell
# Option A: With auto-restart (recommended)
python run_server.py

# Option B: Direct Flask (no auto-restart)
python app_enhanced.py

# Expected output:
# [2025-01-10 15:30:00] Starting server on port 7000...
# * Running on http://127.0.0.1:7000
# * Debug mode: on
```

### **Step 8: Access Application**

Open browser to: **http://127.0.0.1:7000**

You should see:
- Purple left sidebar with age buttons
- Middle content area with article grid
- Right sidebar with statistics

---

## Configuration

### **Change Port**

Edit `app_enhanced.py` (line 748):
```python
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=7000)  # Change port here
```

Edit `run_server.py` (line 16):
```python
def check_port(port=7000):  # Change port here
```

### **Adjust Collection Settings**

Edit `simple_collector.py` (line ~50):
```python
ARTICLES_PER_SOURCE = 10  # Change to fetch more/fewer articles
```

### **Add New Sources**

Edit `simple_collector.py` (line ~100+):
```python
SOURCES = [
    {
        'name': 'Your Source Name',
        'url': 'https://example.com/rss',
        'category': 'General News',
        'age_groups': ['14-16', '17+']
    },
    # ... existing sources
]
```

Then run collector:
```powershell
python simple_collector.py
```

---

## Troubleshooting

### **Problem: Port 7000 Already in Use**

**Error**:
```
OSError: [WinError 10048] Only one usage of each socket address is normally permitted
```

**Solution**:
```powershell
# Find process using port 7000
Get-NetTCPConnection -LocalPort 7000

# Kill the process
Get-Process -Id (Get-NetTCPConnection -LocalPort 7000).OwningProcess | Stop-Process -Force

# Or use different port (see Configuration section)
```

### **Problem: pip install fails**

**Error**:
```
ERROR: Could not find a version that satisfies the requirement trafilatura
```

**Solution**:
```powershell
# Update pip
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# Or install packages individually
pip install Flask requests feedparser trafilatura newspaper4k python-dotenv beautifulsoup4
```

### **Problem: No articles showing**

**Check**:
```powershell
# 1. Verify database exists
dir newscollect.db
# Should show file with size > 0KB

# 2. Check article count
python -c "import database; db = database.get_db(); print(db.execute('SELECT COUNT(*) FROM articles').fetchone()[0])"
# Should output number > 0

# 3. Run collector if count is 0
python simple_collector.py
```

### **Problem: Images not loading**

**Check**:
```javascript
// Open browser console (F12)
// Look for CORS errors or 404s

// Verify image URLs in database
fetch('/api/simple/articles')
  .then(r => r.json())
  .then(data => console.log(data.articles[0].image_url));
```

**Solution**: Some sources block external image loading. This is expected behavior.

### **Problem: LLM classification not working**

**Error**:
```
Failed to classify article: API key not found
```

**Solution**:
```powershell
# 1. Create .env file in newscollect/ directory
echo "LLM_API_KEY=your_key_here" > .env

# 2. Verify environment variable
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('LLM_API_KEY'))"
# Should output your API key

# 3. Test classification
python -c "from smart_classifier import classify_age_group; print(classify_age_group('Test article about quantum physics', 'ScienceDaily'))"
# Should output: 17+
```

### **Problem: Server keeps crashing**

**Check logs**:
```powershell
# Run without auto-restart to see errors
python app_enhanced.py

# Look for:
# - Database corruption
# - Port conflicts
# - Missing dependencies
```

**Common fixes**:
```powershell
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Reset database
mv newscollect.db newscollect.db.backup
python database.py
python simple_collector.py

# Check Python version
python --version
# Must be 3.11+
```

---

## Database Management

### **Backup Database**

```powershell
# Copy database file
cp newscollect.db "newscollect_backup_$(Get-Date -Format 'yyyy-MM-dd').db"

# Or export to SQL
sqlite3 newscollect.db .dump > backup.sql
```

### **Restore Database**

```powershell
# From backup file
cp newscollect_backup_2025-01-10.db newscollect.db

# From SQL dump
rm newscollect.db
sqlite3 newscollect.db < backup.sql
```

### **Reset Database**

```powershell
# WARNING: Deletes all articles
rm newscollect.db
python database.py  # Recreates schema
python simple_collector.py  # Refetch articles
```

### **Query Database Directly**

```powershell
# Install SQLite CLI (optional)
# Download from: https://www.sqlite.org/download.html

# Open database
sqlite3 newscollect.db

# Run queries
sqlite> SELECT COUNT(*) FROM articles;
sqlite> SELECT source_name, COUNT(*) FROM articles GROUP BY source_name;
sqlite> SELECT * FROM articles WHERE age_group = '11-13' LIMIT 5;
sqlite> .exit
```

---

## Performance Optimization

### **Database Indexes**

Already created by default:
```sql
CREATE INDEX idx_source ON articles(source_name);
CREATE INDEX idx_date ON articles(published_date);
CREATE INDEX idx_age_group ON articles(age_group);
```

### **Collection Speed**

```python
# simple_collector.py
import concurrent.futures

# Add parallel collection (advanced)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(collect_from_source, src) for src in SOURCES]
    concurrent.futures.wait(futures)
```

### **Frontend Caching**

```javascript
// static/app.js
// Add localStorage caching for articles
function loadArticles() {
  const cacheKey = 'articles_cache';
  const cached = localStorage.getItem(cacheKey);
  
  if (cached) {
    const data = JSON.parse(cached);
    if (Date.now() - data.timestamp < 300000) { // 5 min
      renderArticles(data.articles);
      return;
    }
  }
  
  fetch('/api/simple/articles')
    .then(r => r.json())
    .then(data => {
      localStorage.setItem(cacheKey, JSON.stringify({
        articles: data.articles,
        timestamp: Date.now()
      }));
      renderArticles(data.articles);
    });
}
```

---

## Deployment (Production)

### **Use Production Server**

Install Gunicorn (Linux) or Waitress (Windows):

```powershell
# Windows - Waitress
pip install waitress

# Create production_server.py
from waitress import serve
from app_enhanced import app

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=7000, threads=4)
```

Run:
```powershell
python production_server.py
```

### **Reverse Proxy with Nginx**

```nginx
# nginx.conf
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:7000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **Automatic Collection**

Windows Task Scheduler:
```powershell
# Create task to run simple_collector.py daily at 6 AM
schtasks /create /tn "NewsCollector" /tr "python c:\path\to\simple_collector.py" /sc daily /st 06:00
```

---

## Security Considerations

1. **API Key Protection**:
   - Never commit `.env` to version control
   - Use environment variables in production
   - Rotate API keys regularly

2. **Database Access**:
   - Keep `newscollect.db` in non-public directory
   - No direct database access from frontend
   - All queries through Flask API

3. **Rate Limiting**:
   - Implement Flask-Limiter for production
   - Limit API requests per IP
   - Monitor RSS feed request frequency

4. **Input Validation**:
   - Already sanitized in API endpoints
   - No SQL injection risk (parameterized queries)
   - XSS protection via JSON responses

---

## Next Steps

After successful setup:

1. **Verify all 57 sources** - Run full collection
2. **Populate categories sidebar** - Add JavaScript for category filtering
3. **Apply LLM classification** - Re-classify existing articles
4. **Add more sources** - Target 65-70 total diverse sources
5. **Set up automatic collection** - Schedule daily updates
6. **Monitor performance** - Check database size and query speed

See [DEVELOPMENT.md](DEVELOPMENT.md) for contributing guidelines.
