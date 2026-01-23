#!/usr/bin/env python3
"""Fetch real images from Girls Life articles"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import re

def fetch_girlslife_image(url):
    """Try multiple methods to get image from Girls Life article"""
    # Use curl user agent - Girls Life blocks browser user agents but allows curl!
    headers = {
        'User-Agent': 'curl/7.68.0',
        'Accept': '*/*'
    }
    
    try:
        print(f"  Fetching: {url[:60]}...")
        r = requests.get(url, headers=headers, timeout=15)
        print(f"  Status: {r.status_code}")
        
        if r.status_code != 200:
            return None
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Method 1: og:image
        og = soup.find('meta', property='og:image')
        if og and og.get('content'):
            img_url = og['content']
            if img_url and not img_url.startswith('data:'):
                print(f"  ✅ Found og:image: {img_url[:60]}...")
                return img_url
        
        # Method 2: twitter:image
        tw = soup.find('meta', attrs={'name': 'twitter:image'})
        if tw and tw.get('content'):
            img_url = tw['content']
            if img_url and not img_url.startswith('data:'):
                print(f"  ✅ Found twitter:image: {img_url[:60]}...")
                return img_url
        
        # Method 3: Look for article/post image
        article = soup.find('article') or soup.find(class_=re.compile(r'article|post|content', re.I))
        if article:
            img = article.find('img')
            if img:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src and not src.startswith('data:'):
                    print(f"  ✅ Found article image: {src[:60]}...")
                    return src
        
        # Method 4: Look for any featured image
        featured = soup.find(class_=re.compile(r'featured|hero|main-image|post-thumbnail', re.I))
        if featured:
            img = featured.find('img') if featured.name != 'img' else featured
            if img:
                src = img.get('src') or img.get('data-src')
                if src and not src.startswith('data:'):
                    print(f"  ✅ Found featured image: {src[:60]}...")
                    return src
        
        # Method 5: First large image in content
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and not src.startswith('data:') and 'logo' not in src.lower() and 'icon' not in src.lower():
                width = img.get('width', '0')
                height = img.get('height', '0')
                try:
                    if int(width) > 200 or int(height) > 150:
                        print(f"  ✅ Found large image: {src[:60]}...")
                        return src
                except:
                    pass
        
        # Method 6: Any image with meaningful size in src
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and not src.startswith('data:'):
                if 'logo' not in src.lower() and 'icon' not in src.lower() and 'avatar' not in src.lower():
                    # Check if it looks like a content image
                    if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        print(f"  ✅ Found content image: {src[:60]}...")
                        return src
        
        print("  ❌ No image found")
        return None
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def main():
    conn = sqlite3.connect('newscollect.db')
    cur = conn.cursor()
    
    # Get Girls Life articles with placeholder images
    cur.execute('''
        SELECT id, title, url, image_url 
        FROM articles 
        WHERE source = 'Girls Life'
    ''')
    articles = cur.fetchall()
    
    print(f"Found {len(articles)} Girls Life articles\n")
    
    updated = 0
    for article_id, title, url, current_img in articles:
        print(f"\n[{article_id}] {title[:50]}...")
        
        # Try to fetch the real image
        new_img = fetch_girlslife_image(url)
        
        if new_img and new_img != current_img:
            cur.execute('UPDATE articles SET image_url = ? WHERE id = ?', (new_img, article_id))
            conn.commit()
            updated += 1
            print(f"  ✅ Updated!")
        elif not new_img:
            print(f"  ⚠️ Keeping placeholder: {current_img[:40]}...")
    
    print(f"\n\nSummary: Updated {updated}/{len(articles)} articles")
    conn.close()

if __name__ == '__main__':
    main()
