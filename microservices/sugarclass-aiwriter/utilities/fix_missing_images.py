"""
Fix Missing Images in Articles Database

This script attempts to fetch og:image meta tags from article URLs
and update the database with the found images.
"""
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import re

DB_PATH = 'newscollect.db'

def get_og_image(url):
    """Extract og:image from a webpage"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try different image sources
        # 1. og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # 2. twitter:image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
        
        # 3. First large image in content
        for img in soup.find_all('img'):
            src = img.get('src', '')
            # Skip small icons, logos
            if any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'button', 'sprite']):
                continue
            # Check if it has reasonable size attributes
            width = img.get('width', '0')
            height = img.get('height', '0')
            try:
                if int(width) > 200 or int(height) > 200:
                    return src
            except:
                pass
            # If no size, check for content-related classes
            if 'article' in str(img.get('class', '')).lower() or 'featured' in str(img.get('class', '')).lower():
                return src
        
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def fix_images_for_source(source_name=None, limit=10):
    """Fix missing images for a specific source or all sources"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get articles with missing images
    query = """
        SELECT id, title, url, source
        FROM articles 
        WHERE (image_url IS NULL OR image_url = '')
    """
    params = []
    
    if source_name:
        query += " AND source = ?"
        params.append(source_name)
    
    query += " LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    articles = cur.fetchall()
    
    print(f"\nFound {len(articles)} articles with missing images")
    print("=" * 60)
    
    fixed_count = 0
    
    for article_id, title, url, source in articles:
        print(f"\n[{source}] {title[:50]}...")
        print(f"  URL: {url}")
        
        image_url = get_og_image(url)
        
        if image_url:
            print(f"  ✅ Found: {image_url[:60]}...")
            
            # Update database
            cur.execute(
                "UPDATE articles SET image_url = ? WHERE id = ?",
                (image_url, article_id)
            )
            fixed_count += 1
        else:
            print(f"  ❌ No image found")
        
        # Be polite to servers
        time.sleep(0.5)
    
    conn.commit()
    conn.close()
    
    print(f"\n{'=' * 60}")
    print(f"Fixed {fixed_count} out of {len(articles)} articles")
    return fixed_count


def show_image_stats():
    """Show image statistics by source"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT source, 
               COUNT(*) as total,
               SUM(CASE WHEN image_url IS NULL OR image_url = '' THEN 1 ELSE 0 END) as no_image
        FROM articles
        GROUP BY source
        ORDER BY no_image DESC
    ''')
    
    print("\nImage Statistics by Source:")
    print("=" * 60)
    print(f"{'Source':<30} {'Missing':<10} {'Total':<10}")
    print("-" * 60)
    
    for source, total, no_img in cur.fetchall():
        pct = int(no_img/total*100) if total > 0 else 0
        status = "⚠️" if pct > 50 else "✅" if pct == 0 else "🔶"
        print(f"{status} {source:<28} {no_img:<10} {total:<10} ({pct}%)")
    
    conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--stats":
            show_image_stats()
        elif sys.argv[1] == "--all":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            fix_images_for_source(limit=limit)
        else:
            # Fix specific source
            source = sys.argv[1]
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            fix_images_for_source(source, limit)
    else:
        print("Usage:")
        print("  python fix_missing_images.py --stats          # Show stats")
        print("  python fix_missing_images.py --all [limit]    # Fix all sources")
        print("  python fix_missing_images.py 'NASA' [limit]   # Fix specific source")
        print()
        show_image_stats()
