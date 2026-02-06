#!/usr/bin/env python3
"""
Hybrid Content Processing Orchestrator

Combines markdown-to-HTML conversion (100% content preservation) 
with LLM-generated educational enhancements.

This solves the critical content loss issue while maintaining educational value.
"""

import sys
from pathlib import Path
import sqlite3
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.rewriting.converters.markdown_to_html import (
    convert_markdown_to_html,
    add_enhancements_to_html,
    get_content_statistics
)
from app.rewriting.generate_llm_enhancements import (
    generate_enhancements,
    validate_enhancements
)

DB_PATH = str(Path(__file__).parent.parent.parent / 'database' / 'rag_content.db')


def process_content_hybrid(
    markdown_content: str,
    title: str = "",
    subtopic_id: str = "",
    enhance_with_llm: bool = True,
    llm_model: str = "gemini-1.5-flash",
    theme: str = "default"
) -> dict:
    """
    Process content using hybrid approach:
    1. Convert markdown to HTML (100% preservation)
    2. Optionally generate LLM enhancements
    3. Merge enhancements with preserved content
    
    Args:
        markdown_content: Raw markdown content
        title: Content title
        subtopic_id: Subtopic ID for tracking
        enhance_with_llm: Whether to add LLM enhancements
        llm_model: LLM model for enhancements
        theme: HTML theme (default, clean, modern)
    
    Returns:
        Dictionary with results:
        {
            'html_content': str,
            'enhancements': dict,
            'statistics': dict,
            'quality_metrics': dict,
            'success': bool,
            'error': str (if any)
        }
    """
    result = {
        'html_content': None,
        'enhancements': {},
        'statistics': {},
        'quality_metrics': {},
        'success': False,
        'error': None
    }
    
    try:
        # Step 1: Get content statistics
        stats = get_content_statistics(markdown_content)
        result['statistics'] = stats
        
        print(f"Processing: {title or subtopic_id}")
        print(f"  Raw content: {stats['char_count']:,} chars")
        
        # Step 2: Convert markdown to HTML (100% preservation guaranteed)
        print(f"  Converting to HTML...")
        html = convert_markdown_to_html(
            markdown_text=markdown_content,
            add_toc=True,
            theme=theme
        )
        
        print(f"  HTML output: {len(html):,} chars")
        
        # Step 3: Generate LLM enhancements (optional)
        enhancements = {}
        enhancement_score = 0
        
        if enhance_with_llm:
            print(f"  Generating LLM enhancements...")
            enhancements = generate_enhancements(
                content=markdown_content,
                title=title,
                model=llm_model
            )
            
            # Validate enhancements
            validation = validate_enhancements(enhancements)
            enhancement_score = validation['score']
            result['quality_metrics'] = validation
            
            print(f"  Enhancement score: {enhancement_score}/100")
            
            if validation['issues']:
                print(f"  ⚠️  Enhancement issues: {len(validation['issues'])}")
            
            # Step 4: Merge enhancements with HTML
            if enhancements and any(enhancements.values()):
                print(f"  Merging enhancements...")
                html = add_enhancements_to_html(
                    html_content=html,
                    learning_objectives=enhancements.get('learning_objectives'),
                    key_terms=enhancements.get('key_terms'),
                    questions=enhancements.get('questions'),
                    takeaways=enhancements.get('takeaways')
                )
                print(f"  Final HTML: {len(html):,} chars")
        
        result['html_content'] = html
        result['enhancements'] = enhancements
        result['success'] = True
        
        # Calculate compression ratio (should be > 80% for success)
        compression_ratio = len(html) / stats['char_count'] * 100
        result['quality_metrics']['compression_ratio'] = compression_ratio
        result['quality_metrics']['content_preserved'] = compression_ratio >= 80
        
        print(f"  Compression ratio: {compression_ratio:.1f}%")
        print(f"  Status: {'✅ PASS' if compression_ratio >= 80 else '❌ FAIL'}")
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        result['success'] = False
        print(f"  ❌ Error: {e}")
        return result


def process_from_database(
    limit: int = None,
    reprocess_all: bool = False,
    enhance_with_llm: bool = True,
    llm_model: str = "gemini-1.5-flash",
    theme: str = "default"
) -> dict:
    """
    Process content from database using hybrid approach.
    
    Args:
        limit: Maximum number of items to process (None = all)
        reprocess_all: Whether to reprocess already processed items
        enhance_with_llm: Whether to add LLM enhancements
        llm_model: LLM model for enhancements
        theme: HTML theme
    
    Returns:
        Dictionary with batch processing results
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get raw content items
    if reprocess_all:
        query = "SELECT id, subtopic_id, title, markdown_content FROM content_raw"
        params = []
    else:
        query = """
        SELECT cr.id, cr.subtopic_id, cr.title, cr.markdown_content
        FROM content_raw cr
        LEFT JOIN content_processed cp ON cr.subtopic_id = cp.subtopic_id
        WHERE cp.subtopic_id IS NULL
        """
        params = []
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    cursor.execute(query, params)
    items = cursor.fetchall()
    conn.close()
    
    total = len(items)
    print(f"\n{'='*80}")
    print(f"HYBRID PROCESSING: {total} items to process")
    print(f"{'='*80}\n")
    
    results = {
        'total': total,
        'success': 0,
        'failed': 0,
        'high_quality': 0,
        'items': []
    }
    
    for i, (raw_id, subtopic_id, title, markdown_content) in enumerate(items, 1):
        print(f"\n[{i}/{total}] Processing: {title or subtopic_id}")
        print("-" * 80)
        
        result = process_content_hybrid(
            markdown_content=markdown_content,
            title=title,
            subtopic_id=subtopic_id,
            enhance_with_llm=enhance_with_llm,
            llm_model=llm_model,
            theme=theme
        )
        
        if result['success']:
            results['success'] += 1
            
            # Save to database
            save_result = save_processed_content(
                raw_id=raw_id,
                subtopic_id=subtopic_id,
                html_content=result['html_content'],
                enhancements=result['enhancements'],
                quality_metrics=result['quality_metrics'],
                processor_version=f"hybrid-{llm_model}",
                title=title
            )
            
            if save_result and result['quality_metrics'].get('content_preserved'):
                results['high_quality'] += 1
                
                item_result = {
                    'subtopic_id': subtopic_id,
                    'title': title,
                    'success': True,
                    'compression': result['quality_metrics'].get('compression_ratio', 0),
                    'enhancement_score': result['quality_metrics'].get('score', 0)
                }
                results['items'].append(item_result)
            else:
                results['failed'] += 1
                results['items'].append({
                    'subtopic_id': subtopic_id,
                    'title': title,
                    'success': False,
                    'error': 'Failed to save or quality check failed'
                })
        else:
            results['failed'] += 1
            results['items'].append({
                'subtopic_id': subtopic_id,
                'title': title,
                'success': False,
                'error': result['error']
            })
    
    print(f"\n{'='*80}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"Total:        {results['total']}")
    print(f"✅ Success:    {results['success']}")
    print(f"❌ Failed:     {results['failed']}")
    print(f"⭐ High Quality: {results['high_quality']}")
    
    success_rate = (results['success'] / results['total'] * 100) if results['total'] > 0 else 0
    quality_rate = (results['high_quality'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    print(f"Quality Rate: {quality_rate:.1f}%")
    
    return results


def save_processed_content(
    raw_id: int,
    subtopic_id: str,
    html_content: str,
    enhancements: dict,
    quality_metrics: dict,
    processor_version: str = "hybrid",
    title: str = ""
) -> bool:
    """
    Save processed content to database.
    
    Args:
        raw_id: Raw content ID
        subtopic_id: Subtopic ID
        html_content: Processed HTML content
        enhancements: Enhancement dictionary
        quality_metrics: Quality metrics dictionary
        processor_version: Processor version identifier
    
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Prepare enhancement strings for storage
        summary = '; '.join(enhancements.get('takeaways', []))
        key_terms_json = str(enhancements.get('key_terms', []))
        
        # Check if already exists
        cursor.execute(
            "SELECT id FROM content_processed WHERE subtopic_id = ?",
            (subtopic_id,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute("""
                UPDATE content_processed
                SET html_content = ?,
                    summary = ?,
                    key_terms = ?,
                    processed_at = ?,
                    processor_version = ?
                WHERE subtopic_id = ?
            """, (
                html_content,
                summary,
                key_terms_json,
                datetime.now().isoformat(),
                processor_version,
                subtopic_id
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO content_processed
                (raw_id, subtopic_id, html_content, summary, key_terms, processed_at, processor_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                raw_id,
                subtopic_id,
                html_content,
                summary,
                key_terms_json,
                datetime.now().isoformat(),
                processor_version
            ))
        
        # Get raw content for length comparison
        cursor.execute("SELECT markdown_content FROM content_raw WHERE id = ?", (raw_id,))
        raw_content_row = cursor.fetchone()
        raw_content_length = len(raw_content_row[0]) if raw_content_row else 0
        
        # Update or insert quality metrics
        cursor.execute("""
            INSERT OR REPLACE INTO rewriting_quality
            (subtopic_id, subject_name, status, raw_length, processed_length,
             compression_ratio, has_learning_objectives, has_key_terms,
             has_questions, has_takeaways, processor_version, quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            subtopic_id,
            title or "Unknown",
            "rewritten",
            raw_content_length,
            len(html_content),
            quality_metrics.get('compression_ratio', 0),
            bool(enhancements.get('learning_objectives')),
            bool(enhancements.get('key_terms')),
            bool(enhancements.get('questions')),
            bool(enhancements.get('takeaways')),
            processor_version,
            quality_metrics.get('score', 0)
        ))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("HYBRID CONTENT PROCESSING - TEST MODE")
    print("=" * 80)
    print()
    
    # Test with a sample from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, subtopic_id, title, markdown_content
        FROM content_raw
        LIMIT 1
    """)
    item = cursor.fetchone()
    conn.close()
    
    if item:
        raw_id, subtopic_id, title, content = item
        
        print(f"Testing with: {title or subtopic_id}")
        print()
        
        result = process_content_hybrid(
            markdown_content=content,
            title=title,
            subtopic_id=subtopic_id,
            enhance_with_llm=True,
            theme="default"
        )
        
        print("\n" + "=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        print(f"Success: {result['success']}")
        print(f"Compression Ratio: {result['quality_metrics'].get('compression_ratio', 0):.1f}%")
        print(f"Enhancement Score: {result['quality_metrics'].get('score', 0)}/{result['quality_metrics'].get('max_score', 100)}")
        
        if result.get('error'):
            print(f"Error: {result['error']}")
    else:
        print("No content found in database")