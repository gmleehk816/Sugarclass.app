#!/usr/bin/env python
"""
Quick script to populate the database with articles from RSS sources.
Run this when you need to add articles to the database.

Usage: python backend/populate_db.py (from project root)
"""
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from collector.collector import collect_all
from database import get_stats

def main():
    print("=" * 60)
    print("NewsCollect - Database Population Script")
    print("=" * 60)
    print()
    
    # Check current stats
    print("Current database status:")
    stats = get_stats()
    print(f"  Total articles: {stats['total_articles']}")
    print(f"  Full articles: {stats['full_articles']}")
    print()
    
    # Collect articles from all RSS sources
    print("Starting collection from RSS sources...")
    print("-" * 60)
    
    try:
        results = collect_all(limit_per_source=20)
        
        print()
        print("-" * 60)
        print("Collection complete!")
        print()
        
        # Summary
        total_stored = sum(r.get('articles_stored', 0) for r in results)
        total_failed = sum(r.get('articles_failed', 0) for r in results)
        
        print(f"Articles stored: {total_stored}")
        print(f"Articles failed: {total_failed}")
        print()
        
        # New stats
        print("New database status:")
        stats = get_stats()
        print(f"  Total articles: {stats['total_articles']}")
        print(f"  Full articles: {stats['full_articles']}")
        print()
        
        if stats['total_articles'] > 0:
            print("✅ Success! Articles are now available in the database.")
            print("   You can now access them via the API at /articles")
        else:
            print("⚠️  Warning: No articles were stored.")
            print("   Check the error messages above.")
        
    except Exception as e:
        print(f"❌ Error during collection: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
