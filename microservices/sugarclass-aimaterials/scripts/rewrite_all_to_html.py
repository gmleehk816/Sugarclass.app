"""
Master HTML Rewriter - All Subjects
====================================
Processes all ingested content and rewrites it to educational HTML with AI-generated images.

This script:
1. Checks for unprocessed content in the database
2. Uses AI to analyze content and determine what images would be helpful
3. Generates educational images using nano-banana API
4. Rewrites markdown content into engaging HTML
5. Saves processed content for web display
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict

# Add app directory to path
APP_DIR = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

PROJECT_ROOT = APP_DIR.parent

# Import the rewriter class
from processors.content_rewriter_with_images import ContentRewriterWithImages


def get_processing_stats() -> Dict:
    """Get statistics about processed vs unprocessed content"""
    import sqlite3
    from processors.content_rewriter_with_images import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get total raw content
    cursor.execute("SELECT COUNT(*) FROM content_raw")
    total_raw = cursor.fetchone()[0]
    
    # Get total processed content
    cursor.execute("SELECT COUNT(*) FROM content_processed")
    total_processed = cursor.fetchone()[0]
    
    # Get content by subject
    cursor.execute("""
        SELECT s.name, COUNT(DISTINCT cr.id) as total, 
               COUNT(DISTINCT cp.id) as processed
        FROM subjects s
        LEFT JOIN topics t ON s.id = t.subject_id
        LEFT JOIN subtopics st ON t.id = st.topic_id
        LEFT JOIN content_raw cr ON st.id = cr.subtopic_id
        LEFT JOIN content_processed cp ON cr.id = cp.raw_id
        GROUP BY s.id, s.name
        ORDER BY s.name
    """)
    subject_stats = [{"subject": row[0], "total": row[1], "processed": row[2]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_raw": total_raw,
        "total_processed": total_processed,
        "remaining": total_raw - total_processed,
        "by_subject": subject_stats
    }


def process_all_unprocessed(limit_per_subject: int = 5, max_total: int = 50):
    """
    Process all unprocessed content for all subjects.
    
    Args:
        limit per subject: Maximum number of items to process per subject
        max_total: Maximum total items to process in this run
    """
    print("=" * 70)
    print("🎨 Master HTML Rewriter - Educational Content with AI Images")
    print("=" * 70)
    print()
    
    # Get initial stats
    stats = get_processing_stats()
    print(f"📊 Initial Status:")
    print(f"   Total content items: {stats['total_raw']}")
    print(f"   Already processed: {stats['total_processed']}")
    print(f"   Remaining to process: {stats['remaining']}")
    print()
    
    if stats['remaining'] == 0:
        print("✅ All content is already processed!")
        return
    
    rewriter = ContentRewriterWithImages()
    
    try:
        # Get all unprocessed content directly
        import sqlite3
        from processors.content_rewriter_with_images import DB_PATH
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cr.id, cr.subtopic_id, cr.title, cr.char_count, cr.markdown_content,
                   s.name as subtopic_name, t.name as topic_name, sub.name as subject_name
            FROM content_raw cr
            LEFT JOIN subtopics s ON cr.subtopic_id = s.id
            LEFT JOIN topics t ON s.topic_id = t.id
            LEFT JOIN subjects sub ON t.subject_id = sub.id
            LEFT JOIN content_processed cp ON cr.id = cp.raw_id
            WHERE cp.id IS NULL
            LIMIT ?
        """, (max_total,))
        
        all_content = [{"id": row[0], "subtopic_id": str(row[1]), "title": row[2], 
                       "char_count": row[3], "markdown_content": row[4],
                       "subtopic_name": row[5], "topic_name": row[6], "subject_name": row[7]} 
                      for row in cursor.fetchall()]
        conn.close()
        
        print(f"📝 Processing {len(all_content)} unprocessed items...")
        print("-" * 70)
        print()
        
        total_processed = 0
        results = []
        
        for i, content in enumerate(all_content, 1):
            print(f"[{i}/{len(all_content)}] {content.get('subject_name', 'Unknown')} - {content.get('title', '')[:50]}...")
            print("-" * 50)
            
            try:
                result = rewriter.process(content, force_regenerate_images=False)
                
                total_processed += 1
                results.append({
                    "subject": content.get('subject_name', 'Unknown'),
                    "subtopic": content.get('subtopic_id'),
                    "title": content.get('title', ''),
                    "status": "success",
                    "images": result.get('images_generated', 0)
                })
                
                print(f"  ✓ Processed ({result.get('images_generated', 0)} images)\n")
                
            except Exception as e:
                print(f"  ✗ Error: {e}\n")
                results.append({
                    "subject": content.get('subject_name', 'Unknown'),
                    "subtopic": content.get('subtopic_id'),
                    "title": content.get('title', ''),
                    "status": "failed",
                    "error": str(e)
                })
        
        # Final stats
        print("\n" + "=" * 70)
        print("📊 Processing Summary")
        print("=" * 70)
        
        final_stats = get_processing_stats()
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        print(f"\n✅ Successfully processed: {len(successful)} items")
        print(f"❌ Failed: {len(failed)} items")
        print(f"\n📈 Progress update:")
        print(f"   Before: {stats['total_processed']} processed")
        print(f"   After:  {final_stats['total_processed']} processed")
        print(f"   Progress: +{final_stats['total_processed'] - stats['total_processed']} items")
        print(f"   Remaining: {final_stats['remaining']} items")
        
        if successful:
            total_images = sum(r.get('images', 0) for r in successful)
            print(f"\n🖼️ Generated {total_images} educational images")
        
        if failed:
            print(f"\nFailed items:")
            for r in failed:
                print(f"  ✗ {r['subject']} - {r['subtopic']}: {r['error']}")
        else:
            print("\n🎉 All items processed successfully!")
        
        print(f"\n📄 HTML content saved to: content_processed table")
        print(f"🖼️ Images saved to: app/static/generated_images/")
        
    finally:
        rewriter.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rewrite all content to educational HTML with AI images"
    )
    parser.add_argument("--stats", action="store_true", 
                        help="Show processing statistics only, no processing")
    parser.add_argument("--limit", type=int, default=5,
                        help="Limit per subject (default: 5)")
    parser.add_argument("--max", type=int, default=50,
                        help="Maximum total items to process (default: 50)")
    parser.add_argument("--force", action="store_true",
                        help="Reprocess all content (regenerate images)")
    
    args = parser.parse_args()
    
    if args.stats:
        stats = get_processing_stats()
        print("=" * 70)
        print("📊 Content Processing Statistics")
        print("=" * 70)
        print(f"\nTotal items: {stats['total_raw']}")
        print(f"Processed: {stats['total_processed']} ({stats['total_processed']/max(stats['total_raw'],1)*100:.1f}%)")
        print(f"Remaining: {stats['remaining']}")
        print("\nBy subject:")
        print("-" * 50)
        for s in stats['by_subject']:
            if s['total'] > 0:
                pct = (s['processed'] / s['total']) * 100
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"  {s['name'][:30]:30} [{bar}] {s['processed']}/{s['total']}")
    else:
        process_all_unprocessed(
            limit_per_subject=args.limit,
            max_total=args.max
        )


if __name__ == "__main__":
    main()