#!/usr/bin/env python3
"""
Run the news collector to populate the database.
Usage: python run_collector.py [options]

Options:
  --limit N          Limit articles per source (default: 10)
  --source DOMAIN    Collect from specific source only (e.g., cnn.com)
  --url URL          Collect a single article by URL
"""
import sys
import argparse

# Add parent directory to path for imports
sys.path.insert(0, '/app')

from collector.collector import (
    collect_all,
    collect_from_source,
    collect_single_article,
    get_all_sources_status
)

def main():
    parser = argparse.ArgumentParser(description='Run news collector')
    parser.add_argument('--limit', type=int, default=10, help='Articles per source')
    parser.add_argument('--source', type=str, help='Specific source domain (e.g., cnn.com)')
    parser.add_argument('--url', type=str, help='Collect single article by URL')
    parser.add_argument('--status', action='store_true', help='Show sources status')
    
    args = parser.parse_args()
    
    if args.status:
        print("\n=== Available Sources ===")
        for source in get_all_sources_status():
            status = "✅ Available" if source.get('available', False) else "❌ Not configured"
            print(f"  {source.get('name', 'Unknown')}: {status}")
        return
    
    if args.url:
        print(f"\n=== Collecting article: {args.url} ===")
        result = collect_single_article(args.url)
        print(f"Result: {result}")
        return
    
    if args.source:
        print(f"\n=== Collecting from {args.source} (limit: {args.limit}) ===")
        result = collect_from_source(args.source, limit=args.limit)
        print(f"\nResult:")
        print(f"  Articles found: {result.get('articles_found', 0)}")
        print(f"  Articles stored: {result.get('articles_stored', 0)}")
        print(f"  Articles failed: {result.get('articles_failed', 0)}")
        if result.get('error'):
            print(f"  Error: {result['error']}")
        return
    
    # Default: collect from all sources
    print(f"\n=== Collecting from ALL sources (limit: {args.limit} per source) ===")
    results = collect_all(limit_per_source=args.limit)
    
    print("\n=== Collection Summary ===")
    total_found = 0
    total_stored = 0
    total_failed = 0
    
    for result in results:
        domain = result.get('domain', 'Unknown')
        found = result.get('articles_found', 0)
        stored = result.get('articles_stored', 0)
        failed = result.get('articles_failed', 0)
        
        total_found += found
        total_stored += stored
        total_failed += failed
        
        status = "✅" if stored > 0 else "⚠️" if found > 0 else "❌"
        print(f"  {status} {domain}: {stored}/{found} stored")
    
    print(f"\n  TOTAL: {total_stored} articles stored ({total_found} found, {total_failed} failed)")


if __name__ == "__main__":
    main()
