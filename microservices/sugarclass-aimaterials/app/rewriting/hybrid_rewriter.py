#!/usr/bin/env python3
"""
Hybrid Content Rewriter (Option 1)

Combines markdown-to-HTML conversion (for 100% content preservation) with LLM Enhancements
(for educational features).

This is the solution to the quality issue where LLMs were summarizing content despite instructions.
"""

import sqlite3
import sys
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))  # Also add this directory

# Now import modules
from rewriting.converters.markdown_to_html import convert_markdown_to_html
from rewriting.llm_enhancer import LLMEnhancer, generate_enhancements
from rewriting.quality_tracker import RewritingQualityTracker
try:
    from _bmad.core.bmm import __all__
except:
    # If _bmad not available, skip it
    pass

# Database path
DB_PATH = str(Path(__file__).parent.parent.parent / 'database' / 'rag_content.db')


class HybridRewriter:
    """
    Hybrid rewriter that combines markdown-to-HTML conversion with LLM enhancements.
    
    Approach:
    1. Convert markdown to HTML (100% content preservation)
    2. Generate enhancements with LLM (objectives, terms, questions, takeaways)
    3. Merge enhancements into HTML
    4. Save to database with quality metrics
    """
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.tracker = RewritingQualityTracker(db_path)
        self.enhancer = LLMEnhancer()
    
    def process_subtopic(
        self,
        subtopic_id: str,
        subject_name: str,
        topic_name: str,
        markdown_content: str
    ) -> Dict:
        """
        Process a single subtopic using hybrid approach.
        
        Args:
            subtopic_id: Subtopic database ID
            subject_name: Subject name
            topic_name: Topic name  
            markdown_content: Raw markdown content
            
        Returns:
            Dictionary with results
        """
        print(f"\n🔄 Hybrid Processing: [{subject_name}] {subtopic_id}")
        
        raw_length = len(markdown_content)
        
        try:
            # Step 1: Convert markdown to HTML (100% preservation)
            print(f"   📝 Step 1: Converting markdown to HTML...")
            html_content = convert_markdown_to_html(markdown_content)
            markdown_to_html_length = len(html_content)
            
            # Verify we preserved content
            if markdown_to_html_length < raw_length * 0.5:
                print(f"   ⚠️ Warning: HTML is {(markdown_to_html_length/raw_length)*100:.1f}% of original")
            else:
                print(f"   ✅ HTML preserved {(markdown_to_html_length/raw_length)*100:.1f}% of original")
            
            # Step 2: Generate enhancements with LLM
            print(f"   🤖 Step 2: Generating enhancements with LLM...")
            enhancements = self.enhancer.extract_enhancements(
                markdown_content,
                subtopic_id,
                topic_name,
                subject_name
            )
            
            if enhancements:
                print(f"   ✅ Enhancements generated")
            else:
                print(f"   ⚠️ Using fallback enhancements")
                enhancements = self.enhancer.generate_fallback_enhancements(subtopic_id)
            
            # Step 3: Merge content
            print(f"   🔗 Step 3: Merging enhancements into HTML...")
            final_html = self._merge_enhancements(html_content, enhancements)
            
            # Step 4: Fix image paths
            final_html = self._fix_image_paths_in_html(final_html)
            
            processed_length = len(final_html)
            compression_ratio = (processed_length / raw_length * 100) if raw_length > 0 else 0
            
            print(f"   ✅ Final output: {processed_length} chars ({compression_ratio:.1f}% compression ratio)")
            
            # Step 5: Save to database with quality tracking
            self._save_to_database(
                subtopic_id,
                subject_name,
                raw_length,
                processed_length,
                compression_ratio,
                html_content,
                final_html
            )
            
            return {
                'success': True,
                'subtopic_id': subtopic_id,
                'raw_length': raw_length,
                'processed_length': processed_length,
                'compression_ratio': compression_ratio,
                'has_enhancements': enhancements is not None
            }
            
        except Exception as e:
            print(f"   ❌ Error processing: {e}")
            import traceback
            traceback.print_exc()
            
            # Record failure in quality tracker
            self.tracker.record_failure(subtopic_id, str(e))
            
            return {
                'success': False,
                'subtopic_id': subtopic_id,
                'error': str(e)
            }
    
    def _merge_enhancements(self, html_content: str, enhancements: Dict) -> str:
        """
        Merge enhancements into the HTML content.
        Add enhancement sections at the end of the content.
        """
        if not enhancements:
            return html_content
        
        # Find where to insert (after main content, before closing tags)
        # Look for the end of the prose div
        if '<div class="prose">' in html_content:
            # Insert before closing div
            insert_point = html_content.rfind('<h1>')
            if insert_point == -1:
                insert_point = html_content.rfind('</div>')
            
            if insert_point > 0:
                before = html_content[:insert_point]
                after = html_content[insert_point:]
                
                # Add title if extraction didn't include it
                title_match = ''
                if '<h1>' not in before[:insert_point]:
                    title_match = '<h1>Learning Enhancements</h1>\n\n'
                
                # Create enhancement sections
                enhancement_html = self._create_enhancement_html(enhancements)
                
                # Merge
                merged = before + enhancement_html + after
                return merged
        
        return html_content
    
    def _create_enhancement_html(self, enhancements: Dict) -> str:
        """Create HTML for enhancements."""
        html = """
    <div class="mt-8 pt-6 border-t-2 border-blue-200">
        <h2 class="text-2xl font-bold text-blue-800 mt-8 mb-4">📚 Learning Enhancements</h2>
        
        <!-- Learning Objectives -->
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6 rounded">
            <h3 class="text-lg font-semibold text-blue-900 mb-3">🎯 Learning Objectives</h3>
            <ul class="list-disc list-inside space-y-2">
"""
        
        for obj in enhancements.get('learning_objectives', []):
            html += f'                <li class="ml-4">{obj}</li>\n'
        
        html += "            </ul>\n        </div>\n"
        
        # Key Terms
        key_terms = enhancements.get('key_terms', {})
        if key_terms:
            html += """
        <div class="bg-green-50 border-l-4 border-green-400 p-4 mb-6 rounded">
            <h3 class="text-lg font-semibold text-green-900 mb-3">📖 Key Terms</h3>
            <div class="space-y-3">
"""
            
            for term, definition in key_terms.items():
                html += f'                <div class="ml-2">\n                    <strong class="text-green-900">{term}:</strong> <span class="text-green-700">{definition}</span>\n                </div>\n'
            
            html += "            </div>\n        </div>\n"
        
        # Think About It Questions
        questions = enhancements.get('think_about_it_questions', [])
        if questions:
            html += """
        <div class="bg-purple-50 border-l-4 border-purple-400 p-4 mb-6 rounded">
            <h3 class="text-lg font-semibold text-purple-900 mb-3">🤔 Think About It</h3>
            <ol class="list-decimal list-inside space-y-2">
"""
            
            for question in questions:
                html += f'                <li class="ml-4">{question}</li>\n'
            
            html += "            </ol>\n        </div>\n"
        
        # Key Takeaways
        takeaways = enhancements.get('key_takeaways', [])
        if takeaways:
            html += """
        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
            <h3 class="text-lg font-semibold text-yellow-900 mb-3">✨ Key Takeaways</h3>
            <ul class="list-disc list-inside space-y-2">
"""
            
            for takeaway in takeaways:
                html += f'                <li class="ml-4">{takeaway}</li>\n'
            
            html += "            </ul>\n        </div>\n"
        
        html += "    </div>\n"
        
        return html
    
    def _fix_image_paths_in_html(self, html_content: str) -> str:
        """Fix image paths in the converted HTML."""
        # Import locally to avoid module issues
        from rewriting.converters.markdown_to_html import fix_image_paths
        return fix_image_paths(html_content)
    
    def _save_to_database(
        self,
        subtopic_id: str,
        subject_name: str,
        raw_length: int,
        processed_length: int,
        compression_ratio: float,
        html_content: str,  # Original markdown HTML
        final_html: str  # With enhancements
    ):
        """Save processed content to database with quality tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get raw_id
            cursor.execute("""
                SELECT id FROM content_raw WHERE subtopic_id = ?
            """, (subtopic_id,))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"No raw content found for {subtopic_id}")
            
            raw_id = row[0]
            
            # Start tracking
            self.tracker.start_rewriting(subtopic_id, subject_name)
            
            # Delete old processed content if exists
            cursor.execute("DELETE FROM content_processed WHERE subtopic_id = ?", (subtopic_id,))
            
            # Insert new processed content (use final_html)
            cursor.execute("""
                INSERT INTO content_processed
                (raw_id, subtopic_id, html_content, processed_at, processor_version)
                VALUES (?, ?, ?, datetime('now'), 'hybrid-v1.0')
            """, (raw_id, subtopic_id, final_html))
            
            conn.commit()
            
            # Record success with metrics
            self.tracker.record_success(
                subtopic_id,
                raw_length=raw_length,
                processed_length=processed_length,
                html_content=final_html,
                processor_version='hybrid-v1.0'
            )
            
            print(f"   ✅ Saved to database")
            
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Database error: {e}")
            raise
        finally:
            conn.close()
    
    def process_batch(
        self,
        subject_name: Optional[str] = None,
        limit: int = 10,
        force_rewrite: bool = False
    ):
        """Process a batch of subtopics using hybrid approach."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get subtopics to process
            if subject_name:
                query = """
                    SELECT 
                        st.id as subtopic_id,
                        s.name as subject_name,
                        t.name as topic_name,
                        cr.markdown_content
                    FROM subtopics st
                    JOIN topics t ON st.topic_id = t.id
                    JOIN subjects s ON t.subject_id = s.id
                    JOIN content_raw cr ON cr.subtopic_id = st.id
                    WHERE s.name LIKE ?
                    ORDER BY st.id
                    LIMIT ?
                """
                cursor.execute(query, (f"%{subject_name}%", limit))
            else:
                query = """
                    SELECT 
                        st.id as subtopic_id,
                        s.name as subject_name,
                        t.name as topic_name,
                        cr.markdown_content
                    FROM subtopics st
                    JOIN topics t ON st.topic_id = t.id
                    JOIN subjects s ON t.subject_id = s.id
                    JOIN content_raw cr ON cr.subtopic_id = st.id
                    ORDER BY st.id
                    LIMIT ?
                """
                cursor.execute(query, (limit,))
            
            subtopics = cursor.fetchall()
            conn.close()
            
            print(f"\n🚀 Processing {len(subtopics)} subtopics with hybrid approach...")
            print("=" * 70)
            
            success_count = 0
            for i, (subtopic_id, subject_name, topic_name, markdown) in enumerate(subtopics, 1):
                if not markdown:
                    print(f"\n[{i}/{len(subtopics)}] ⚠️  No markdown content for {subtopic_id}")
                    continue
                
                print(f"\n[{i}/{len(subtopics)}]", end=" ")
                result = self.process_subtopic(
                    subtopic_id=subtopic_id,
                    subject_name=subject_name,
                    topic_name=topic_name,
                    markdown_content=markdown
                )
                
                if result['success']:
                    success_count += 1
            
            print("\n" + "=" * 70)
            print(f"✅ Successfully processed: {success_count}/{len(subtopics)}")
            
        except Exception as e:
            print(f"❌ Error in batch processing: {e}")
        finally:
            conn.close()


# Convenience function
def process_subtopic_hybrid(subtopic_id: str):
    """Process a single subtopic with hybrid approach."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            st.id as subtopic_id,
            s.name as subject_name,
            t.name as topic_name,
            cr.markdown_content
        FROM subtopics st
        JOIN topics t ON st.topic_id = t.id
        JOIN subjects s ON t.subject_id = s.id
        JOIN content_raw cr ON cr.subtopic_id = st.id
        WHERE st.id = ?
    """, (subtopic_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        rewriter = HybridRewriter()
        return rewriter.process_subtopic(
            subtopic_id=row[0],
            subject_name=row[1],
            topic_name=row[2],
            markdown_content=row[3]
        )
    else:
        print(f"❌ Subtopic {subtopic_id} not found")
        return None


if __name__ == "__main__":
    import json
    """
    Test the hybrid rewriter with Business Studies sample
    """
    print("Testing Hybrid Rewriter...")
    print("=" * 70)
    
    # Test with first Business Studies subtopic
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            cr.markdown_content,
            s.name as subject_name,
            t.name as topic_name,
            st.id as subtopic_id
        FROM content_raw cr
        JOIN subtopics st ON cr.subtopic_id = st.id
        JOIN topics t ON st.topic_id = t.id
        JOIN subjects s ON t.subject_id = s.id
        WHERE s.name LIKE '%Business%'
        LIMIT 3
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    rewriter = HybridRewriter()
    
    results = []
    for i, (markdown, subject_name, topic_name, subtopic_id) in enumerate(rows, 1):
        print(f"\nTest {i}/{len(rows)}:")
        result = rewriter.process_subtopic(subtopic_id, subject_name, topic_name, markdown)
        results.append(result)
    
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        if result['success']:
            print(f"\n{i}. {result['subtopic_id']}")
            print(f"   Raw: {result['raw_length']:,d} chars")
            print(f"   Processed: {result['processed_length']:,d} chars")
            print(f"   Compression: {result['compression_ratio']:.1f}%")
            print(f"   Has Enhancements: {'Yes' if result.get('has_enhancements') else 'No'}")
        else:
            print(f"\n{i}. {result['subtopic_id']} - FAILED")
            print(f"   Error: {result.get('error', 'Unknown')}")
    
    # Save results to JSON
    with open('hybrid_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: hybrid_test_results.json")