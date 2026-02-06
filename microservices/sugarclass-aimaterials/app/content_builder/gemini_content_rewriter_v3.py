"""
Gemini Content Rewriter with Retry Logic
========================================
Enhanced version with automatic retry on failures
"""

import requests
import json
import sqlite3
import re
import sys
import importlib.util
import time
import random
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for api_config import
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import api_config
spec = importlib.util.spec_from_file_location("api_config", str(Path(__file__).parent.parent / "api_config.py"))
api_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_config)
make_api_call = api_config.make_api_call
get_api_config = api_config.get_api_config

# Database path (use absolute path)
import os
DB_PATH = Path(r"E:\BaiduSyncdisk\code\rag\database\rag_content.db")


class GeminiContentRewriterV3:
    """Content rewriter with retry logic and automatic rate limit handling."""
    
    def __init__(self, db_path: Optional[Path] = None, max_retries: int = 3, retry_delay: int = 20):
        """
        Initialize rewriter
        
        Args:
            db_path: Optional custom database path
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 20)
        """
        self.db_path = db_path or DB_PATH
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Use centralized API config
        config = get_api_config()
        self.api_config = config
        print(f"🔧 Using API: {config['model']} @ {config['url']}")
        print(f"🔄 Retry settings: max_retries={max_retries}, delay={retry_delay}s")
    
    def rewrite_content_with_retry(
        self, 
        raw_content: str, 
        subtopic_name: str,
        topic_name: str,
        subject_name: str = "Engineering"
    ) -> Optional[Dict]:
        """
        Rewrite raw content with automatic retry on failure
        
        Args:
            raw_content: Original markdown/text content
            subtopic_name: Name of the subtopic
            topic_name: Parent topic name
            subject_name: Subject name for context
            
        Returns:
            Dictionary with enhanced content or None if all retries fail
        """
        
        # Professional educational prompt
        prompt = f"""You are an expert educational content designer for IGCSE/GCSE {subject_name} students (ages 14-16).

Transform this textbook content into engaging, comprehensive HTML that PRESERVES ALL information while making it more accessible and educational.

## Topic: {topic_name} > {subtopic_name}

## Source Content:
{raw_content}

## CRITICAL Requirements:

1. **PRESERVE ALL CONTENT** - Do NOT summarize or skip any information. Every concept, definition, example, and detail from the source MUST appear in your output.

2. **Educational Structure**:
   - Start with clear Learning Objectives (from "What will I learn?" section)
   - Organize content with clear headings and subheadings
   - Add helpful explanations to complex concepts
   - Highlight KEY TERMS in bold or with special styling
   - Include any tables, lists, or formulas from the original

3. **Visual Enhancement**:
   - Use Tailwind CSS classes for professional styling
   - Add visual hierarchy with colors (blue for objectives, gray for content, green for examples)
   - Use icons or emojis sparingly for engagement (📚 💡 ⚠️ ✓)
   - Create info boxes for important concepts
   - Use bullet points and numbered lists appropriately

4. **Educational Additions** (at the end):
   - Add 3-5 "Think About It" questions to test understanding
   - Add a "Key Takeaways" summary box (5-8 bullet points)
   - Suggest 1-2 real-world applications if relevant

5. **HTML Guidelines**:
   - Use semantic HTML (h1, h2, h3, p, ul, ol, table)
   - Apply Tailwind classes: bg-*, text-*, p-*, m-*, rounded-*, shadow-*, border-*
   - Wrap everything in a container div

Return ONLY valid JSON (no markdown code blocks):
{{"html_content": "<div class='max-w-4xl mx-auto p-6 bg-white'>YOUR COMPLETE HTML HERE</div>", "key_concepts": ["concept1", "concept2", "concept3"]}}"""

        # Retry loop
        for attempt in range(1, self.max_retries + 1):
            try:
                # Use centralized make_api_call with automatic fallback
                messages = [{"role": "user", "content": prompt}]
                result = make_api_call(
                    messages=messages,
                    max_tokens=16000,
                    temperature=0.3,
                    auto_fallback=True
                )
                
                if result['success']:
                    content = result['content']
                    print(f"   ✅ API Success (attempt {attempt}/{self.max_retries}): {result['model']}")
                    
                    # Parse JSON response
                    try:
                        if content.strip().startswith('{'):
                            enhanced_content = json.loads(content.strip())
                            return enhanced_content
                    except:
                        pass
                    
                    # Extract JSON from code blocks
                    json_match = re.search(r'```json?\s*\n?(.*?)```', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1).strip()
                    else:
                        # Try to find raw JSON object with html_content
                        brace_match = re.search(r'\{[^{}]*"html_content"[^{}]*\}', content, re.DOTALL)
                        if brace_match:
                            content = brace_match.group(0)
                        elif '{' in content:
                            start = content.index('{')
                            end = content.rfind('}')
                            if end > start:
                                content = content[start:end+1]
                    
                    # Parse JSON
                    enhanced_content = json.loads(content)
                    return enhanced_content
                else:
                    error_msg = result.get('error', 'Unknown error')
                    status_code = result.get('status_code', 'N/A')
                    print(f"   ❌ API Error (attempt {attempt}/{self.max_retries}): Status {status_code} - {error_msg}")
                    
                    # If not last attempt, wait and retry
                    if attempt < self.max_retries:
                        print(f"   ⏳ Waiting {self.retry_delay}s before retry...")
                        time.sleep(self.retry_delay)
                    else:
                        return None
                        
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON Parse Error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    print(f"   ⏳ Waiting {self.retry_delay}s before retry...")
                    time.sleep(self.retry_delay)
                else:
                    return None
                    
            except Exception as e:
                print(f"   ❌ Exception on API call (attempt {attempt}/{self.max_retries}): {type(e).__name__} - {e}")
                if attempt < self.max_retries:
                    print(f"   ⏳ Waiting {self.retry_delay}s before retry...")
                    time.sleep(self.retry_delay)
                else:
                    return None
        
        return None
    
    def process_subtopic(self, subtopic_id: str) -> bool:
        """
        Process a single subtopic with retry logic
        
        Args:
            subtopic_id: Database ID of subtopic to process
            
        Returns:
            Success boolean
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get subtopic data
            cursor.execute("""
                SELECT 
                    st.id, st.name as subtopic_name,
                    t.name as topic_name,
                    s.name as subject_name,
                    cr.id as raw_id,
                    cr.markdown_content
                FROM subtopics st
                JOIN topics t ON t.id = st.topic_id
                JOIN subjects s ON s.id = t.subject_id
                LEFT JOIN content_raw cr ON cr.subtopic_id = st.id
                WHERE st.id = ?
            """, (subtopic_id,))
            
            row = cursor.fetchone()
            if not row:
                print(f"❌ Subtopic {subtopic_id} not found")
                return False
            
            if not row['markdown_content']:
                print(f"⚠️ No raw content for subtopic {subtopic_id}")
                return False
            
            raw_id = row['raw_id']
            if not raw_id:
                print(f"❌ No raw content ID for subtopic {subtopic_id}")
                return False
            
            print(f"\n🔄 Processing: [{row['subject_name']}] {row['topic_name']} → {row['subtopic_name']}")
            
            # Rewrite content with retry
            enhanced = self.rewrite_content_with_retry(
                raw_content=row['markdown_content'],
                subtopic_name=row['subtopic_name'],
                topic_name=row['topic_name'],
                subject_name=row['subject_name']
            )
            
            if not enhanced:
                print(f"❌ Rewriting failed after {self.max_retries} retries")
                return False
            
            # Save to content_processed table
            cursor.execute("""
                INSERT OR REPLACE INTO content_processed 
                (raw_id, subtopic_id, html_content, processed_at, processor_version)
                VALUES (?, ?, ?, datetime('now'), ?)
            """, (
                raw_id,
                subtopic_id,
                enhanced.get('html_content', ''),
                'gemini-v3-retry'
            ))
            
            conn.commit()
            print(f"✅ Saved enhanced content ({len(enhanced.get('html_content', ''))} chars)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing subtopic: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


def rewrite_chemistry_with_retry():
    """Rewrite all chemistry content with retry logic and delays between requests"""
    
    print("🧪 CHEMISTRY REWRITE PIPELINE V3 (WITH RETRY + DELAYS)")
    print("=" * 80)
    
    # Initialize rewriter with retry settings
    rewriter = GeminiContentRewriterV3(max_retries=3, retry_delay=20)
    
    print(f"\n⏱️  Delay Strategy: 3-5s between all requests to prevent rate limiting")
    
    # Get chemistry subtopics
    conn = sqlite3.connect(rewriter.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT st.id, st.name as subtopic_name, t.name as topic_name
        FROM subtopics st
        JOIN topics t ON t.id = st.topic_id
        WHERE t.subject_id = '3'
        AND st.id IN (
            SELECT subtopic_id FROM content_raw
        )
        ORDER BY t.order_num, st.order_num
    """)
    
    subtopics = cursor.fetchall()
    conn.close()
    
    print(f"\n📊 Found {len(subtopics)} chemistry subtopics to process")
    
    # Process each subtopic
    success_count = 0
    failed_subtopics = []
    
    for i, (subtopic_id, subtopic_name, topic_name) in enumerate(subtopics, 1):
        print(f"\n[{i}/{len(subtopics)}] Processing: {topic_name} → {subtopic_name}")
        
        try:
            success = rewriter.process_subtopic(subtopic_id)
            
            # If failed, retry the same subtopic after 60s delay
            if not success:
                print(f"   ❌ First attempt failed, waiting 60s before retry...")
                time.sleep(60)
                print(f"   🔄 Retrying same subtopic after 60s recovery...")
                
                # Retry the same subtopic
                success = rewriter.process_subtopic(subtopic_id)
                
                if success:
                    success_count += 1
                    print(f"   ✅ Recovery successful! Success rate: {success_count}/{len(subtopics)} ({success_count/len(subtopics)*100:.1f}%)")
                else:
                    failed_subtopics.append((subtopic_id, subtopic_name))
                    print(f"   ❌ Subtopic failed even after 60s retry")
            else:
                success_count += 1
                print(f"   ✅ Success rate: {success_count}/{len(subtopics)} ({success_count/len(subtopics)*100:.1f}%)")
                
        except Exception as e:
            failed_subtopics.append((subtopic_id, subtopic_name))
            print(f"   ❌ Error: {e}")
        
        # Add delay between requests (not after last one)
        # Use standard 3-5s delay for all successful or finally-failed subtopics
        if i < len(subtopics):
            delay = random.uniform(3, 5)
            print(f"   ⏳ Waiting {delay:.1f}s before next request to prevent rate limiting...")
            time.sleep(delay)
    
    # Summary
    print("\n" + "=" * 80)
    print("REWRITE SUMMARY")
    print("=" * 80)
    print(f"Total Subtopics: {len(subtopics)}")
    print(f"Successfully Rewritten: {success_count}")
    print(f"Failed: {len(failed_subtopics)}")
    print(f"Success Rate: {success_count/len(subtopics)*100:.1f}%")
    
    if failed_subtopics:
        print(f"\n❌ Failed Subtopics:")
        for sub_id, sub_name in failed_subtopics:
            print(f"  - {sub_name} (ID: {sub_id})")
    
    return {
        'total': len(subtopics),
        'success': success_count,
        'failed': len(failed_subtopics)
    }


if __name__ == "__main__":
    rewrite_chemistry_with_retry()