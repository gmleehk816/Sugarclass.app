"""
Enhanced Gemini Content Rewriter V2
===================================
Improved content rewriting with:
- Structured JSON output with schema validation
- Content length validation (input vs output)
- Retry logic with exponential backoff
- Content chunking for large chapters
- Quality metrics tracking
- Error recovery and partial saves

Features:
1. Reads raw Markdown content from database
2. Uses Gemini with structured output
3. Validates content preservation
4. Retries on failures with backoff
5. Tracks rewriting quality metrics
6. Handles large content with chunking

Author: Enhanced workflow (v2.0)
Date: 2026-01-12
"""

import requests
import json
import sqlite3
import re
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
DB_PATH = Path(__file__).parent.parent / 'database' / 'rag_content.db'

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 2  # seconds
MAX_DELAY = 30  # seconds

# Content thresholds
MAX_TOKENS_PER_REQUEST = 8000  # Approximate token limit for input
MIN_OUTPUT_RATIO = 0.5  # Minimum output/input length ratio
MAX_OUTPUT_RATIO = 5.0  # Maximum output/input length ratio (should be larger for HTML)

# JSON Schema for structured output
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "html_content": {
            "type": "string",
            "description": "The enhanced HTML content with Tailwind CSS styling"
        },
        "key_concepts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of 3-5 key learning concepts"
        },
        "learning_objectives": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of learning objectives extracted/generated"
        },
        "difficulty_level": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"],
            "description": "Estimated difficulty level of content"
        },
        "word_count": {
            "type": "integer",
            "description": "Approximate word count of main content"
        }
    },
    "required": ["html_content", "key_concepts"]
}


def load_api_config() -> Dict:
    """Load API configuration"""
    try:
        from app.api_config import get_api_config
        return get_api_config()
    except:
        # Fallback configuration
        return {
            'url': 'http://localhost:11434/api/generate',
            'model': 'gemini-2.5-flash-preview',
            'api_type': 'ollama'
        }


def exponential_backoff(attempt: int) -> float:
    """Calculate delay with exponential backoff and jitter"""
    import random
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars per token)"""
    return len(text) // 4


def chunk_content(content: str, max_tokens: int = MAX_TOKENS_PER_REQUEST) -> List[str]:
    """
    Split large content into manageable chunks.
    Tries to split at paragraph boundaries.
    """
    estimated_tokens = estimate_tokens(content)
    
    if estimated_tokens <= max_tokens:
        return [content]
    
    # Split into paragraphs
    paragraphs = content.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = estimate_tokens(para)
        
        if current_tokens + para_tokens > max_tokens and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_tokens = para_tokens
        else:
            current_chunk.append(para)
            current_tokens += para_tokens
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def validate_rewrite_output(
    raw_content: str, 
    html_content: str, 
    key_concepts: List[str]
) -> Tuple[bool, str, Dict]:
    """
    Validate that the rewrite preserved content and meets quality standards.
    
    Returns:
        (is_valid, message, metrics)
    """
    metrics = {
        'input_length': len(raw_content),
        'output_length': len(html_content),
        'ratio': len(html_content) / len(raw_content) if raw_content else 0,
        'key_concepts_count': len(key_concepts),
        'has_learning_objectives': 'learning' in html_content.lower() or 'objective' in html_content.lower(),
        'has_key_takeaways': 'takeaway' in html_content.lower() or 'summary' in html_content.lower(),
        'has_think_questions': 'think' in html_content.lower() or 'question' in html_content.lower()
    }
    
    # Check output length ratio
    if metrics['ratio'] < MIN_OUTPUT_RATIO:
        return False, f"Output too short (ratio: {metrics['ratio']:.2f})", metrics
    
    if metrics['ratio'] > MAX_OUTPUT_RATIO:
        return False, f"Output suspiciously long (ratio: {metrics['ratio']:.2f})", metrics
    
    # Check for empty or minimal content
    if len(html_content.strip()) < 100:
        return False, "Output content too minimal", metrics
    
    # Check for key concepts
    if not key_concepts or len(key_concepts) < 2:
        return False, "Insufficient key concepts extracted", metrics
    
    # Check for basic HTML structure
    if '<div' not in html_content and '<p' not in html_content:
        return False, "Missing basic HTML structure", metrics
    
    return True, "Valid", metrics


def make_api_call_with_retry(
    prompt: str,
    config: Dict,
    max_retries: int = MAX_RETRIES
) -> Tuple[Optional[str], Optional[str]]:
    """
    Make API call with retry logic and exponential backoff.
    
    Returns:
        (content, error_message)
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = exponential_backoff(attempt)
                print(f"      ⏳ Retry {attempt + 1}/{max_retries} after {delay:.1f}s...")
                time.sleep(delay)
            
            # Build request based on API type
            if config.get('api_type') == 'openai':
                response = make_openai_request(prompt, config)
            elif config.get('api_type') == 'gemini':
                response = make_gemini_request(prompt, config)
            else:
                response = make_ollama_request(prompt, config)
            
            if response:
                return response, None
                
        except requests.exceptions.Timeout:
            last_error = "Request timeout"
        except requests.exceptions.ConnectionError:
            last_error = "Connection error"
        except Exception as e:
            last_error = str(e)
    
    return None, last_error


def make_ollama_request(prompt: str, config: Dict) -> Optional[str]:
    """Make request to Ollama API"""
    response = requests.post(
        config['url'],
        json={
            'model': config['model'],
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.3,
                'num_predict': 16000
            }
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json().get('response', '')


def make_openai_request(prompt: str, config: Dict) -> Optional[str]:
    """Make request to OpenAI-compatible API"""
    headers = {
        'Content-Type': 'application/json'
    }
    if config.get('api_key'):
        headers['Authorization'] = f"Bearer {config['api_key']}"
    
    response = requests.post(
        config['url'],
        headers=headers,
        json={
            'model': config['model'],
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.3,
            'max_tokens': 16000,
            'response_format': {'type': 'json_object'}  # Request JSON output
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']


def make_gemini_request(prompt: str, config: Dict) -> Optional[str]:
    """Make request to Gemini API"""
    import google.generativeai as genai
    
    genai.configure(api_key=config.get('api_key'))
    model = genai.GenerativeModel(config['model'])
    
    response = model.generate_content(
        prompt,
        generation_config={
            'temperature': 0.3,
            'max_output_tokens': 16000,
            'response_mime_type': 'application/json'  # Request JSON
        }
    )
    return response.text


def parse_json_response(content: str) -> Optional[Dict]:
    """
    Parse JSON from LLM response with multiple strategies.
    """
    if not content:
        return None
    
    content = content.strip()
    
    # Strategy 1: Direct parse (clean JSON)
    try:
        if content.startswith('{'):
            return json.loads(content)
    except:
        pass
    
    # Strategy 2: Extract from code blocks
    patterns = [
        r'```json\s*\n?(.*?)```',
        r'```\s*\n?(.*?)```',
        r'\{[\s\S]*"html_content"[\s\S]*\}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                json_str = match.group(1) if '```' in pattern else match.group(0)
                return json.loads(json_str.strip())
            except:
                continue
    
    # Strategy 3: Extract HTML content manually
    html_match = re.search(r'"html_content"\s*:\s*"((?:[^"\\]|\\.)*)"\s*[,}]', content, re.DOTALL)
    if html_match:
        html = html_match.group(1)
        html = html.replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/')
        return {'html_content': html, 'key_concepts': []}
    
    return None


class EnhancedContentRewriter:
    """Enhanced content rewriter with all improvements"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.api_config = load_api_config()
        print(f"🔧 Using API: {self.api_config.get('model', 'unknown')}")
    
    def get_rewrite_prompt(
        self,
        raw_content: str,
        subtopic_name: str,
        topic_name: str,
        subject_name: str,
        is_chunk: bool = False,
        chunk_num: int = 0,
        total_chunks: int = 1
    ) -> str:
        """Generate the rewrite prompt"""
        
        chunk_context = ""
        if is_chunk:
            chunk_context = f"""
**Note**: This is part {chunk_num + 1} of {total_chunks} for this subtopic.
Please process this section while maintaining consistency with the overall topic.
"""
        
        prompt = f"""You are an expert educational content designer for IGCSE/GCSE {subject_name} students (ages 14-16).

Transform this textbook content into engaging, comprehensive HTML that PRESERVES ALL information.
{chunk_context}
## Topic: {topic_name} > {subtopic_name}

## Source Content:
{raw_content}

## CRITICAL Requirements:

1. **PRESERVE ALL CONTENT** - Every concept, definition, example MUST appear in output.

2. **Educational Structure**:
   - Clear Learning Objectives at the start
   - Organized with headings and subheadings
   - KEY TERMS highlighted with styling
   - Tables, lists, formulas preserved

3. **Visual Enhancement** (Tailwind CSS):
   - Use bg-*, text-*, p-*, m-*, rounded-*, shadow-* classes
   - Blue for objectives, gray for content, green for examples
   - Use emojis sparingly: 📚 💡 ⚠️ ✓
   - Info boxes for important concepts

4. **Educational Additions**:
   - 3-5 "Think About It" questions
   - "Key Takeaways" summary (5-8 points)
   - Real-world applications where relevant

5. **HTML Guidelines**:
   - Use semantic HTML (h1, h2, h3, p, ul, ol, table)
   - Wrap everything in a container div with max-w-4xl

## Output Format (STRICT JSON):
Return ONLY valid JSON with this structure:
{{
    "html_content": "<div class='max-w-4xl mx-auto p-6 bg-white'>YOUR HTML</div>",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "learning_objectives": ["objective1", "objective2"],
    "difficulty_level": "intermediate",
    "word_count": 500
}}

IMPORTANT: Output ONLY the JSON object, no markdown code blocks."""
        
        return prompt
    
    def rewrite_content(
        self,
        raw_content: str,
        subtopic_name: str,
        topic_name: str,
        subject_name: str
    ) -> Tuple[Optional[Dict], Dict]:
        """
        Rewrite content with chunking support and validation.
        
        Returns:
            (result_dict, metrics)
        """
        metrics = {
            'input_length': len(raw_content),
            'chunks': 1,
            'retries': 0,
            'validation': None,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # Check if content needs chunking
        chunks = chunk_content(raw_content)
        metrics['chunks'] = len(chunks)
        
        if len(chunks) > 1:
            print(f"      📦 Content split into {len(chunks)} chunks")
            return self._process_chunks(chunks, subtopic_name, topic_name, subject_name, metrics)
        
        # Single chunk processing
        prompt = self.get_rewrite_prompt(raw_content, subtopic_name, topic_name, subject_name)
        
        response, error = make_api_call_with_retry(prompt, self.api_config)
        
        if error:
            metrics['error'] = error
            return None, metrics
        
        result = parse_json_response(response)
        
        if not result:
            metrics['error'] = 'Failed to parse JSON response'
            return None, metrics
        
        # Validate output
        is_valid, message, validation_metrics = validate_rewrite_output(
            raw_content,
            result.get('html_content', ''),
            result.get('key_concepts', [])
        )
        
        metrics['validation'] = validation_metrics
        metrics['processing_time'] = time.time() - start_time
        
        if not is_valid:
            metrics['validation_error'] = message
            # Still return result, but flag it
            result['_validation_warning'] = message
        
        return result, metrics
    
    def _process_chunks(
        self,
        chunks: List[str],
        subtopic_name: str,
        topic_name: str,
        subject_name: str,
        metrics: Dict
    ) -> Tuple[Optional[Dict], Dict]:
        """Process content in chunks and merge results"""
        
        html_parts = []
        all_concepts = []
        all_objectives = []
        
        for i, chunk in enumerate(chunks):
            print(f"      🔄 Processing chunk {i + 1}/{len(chunks)}...")
            
            prompt = self.get_rewrite_prompt(
                chunk, subtopic_name, topic_name, subject_name,
                is_chunk=True, chunk_num=i, total_chunks=len(chunks)
            )
            
            response, error = make_api_call_with_retry(prompt, self.api_config)
            
            if error:
                print(f"      ❌ Chunk {i + 1} failed: {error}")
                continue
            
            result = parse_json_response(response)
            
            if result:
                html_parts.append(result.get('html_content', ''))
                all_concepts.extend(result.get('key_concepts', []))
                all_objectives.extend(result.get('learning_objectives', []))
        
        if not html_parts:
            return None, metrics
        
        # Merge results
        merged_html = self._merge_html_chunks(html_parts)
        
        merged_result = {
            'html_content': merged_html,
            'key_concepts': list(set(all_concepts))[:5],
            'learning_objectives': list(set(all_objectives))[:5],
            'difficulty_level': 'intermediate',
            'word_count': len(merged_html.split())
        }
        
        return merged_result, metrics
    
    def _merge_html_chunks(self, html_parts: List[str]) -> str:
        """Merge multiple HTML chunks into cohesive content"""
        # Extract inner content from each part
        merged_content = []
        
        for part in html_parts:
            # Try to extract content from container div
            match = re.search(r"<div[^>]*class=['\"][^'\"]*max-w[^'\"]*['\"][^>]*>(.*?)</div>\s*$", part, re.DOTALL)
            if match:
                merged_content.append(match.group(1))
            else:
                merged_content.append(part)
        
        # Wrap in container
        return f"""<div class='max-w-4xl mx-auto p-6 bg-white'>
    {chr(10).join(merged_content)}
</div>"""
    
    def process_subtopic(self, subtopic_id: str) -> Tuple[bool, Dict]:
        """
        Process a single subtopic with full error handling.
        
        Returns:
            (success, metrics)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        metrics = {'subtopic_id': subtopic_id}
        
        try:
            # Get subtopic data
            cursor.execute("""
                SELECT 
                    st.id, st.name as subtopic_name,
                    t.name as topic_name,
                    s.name as subject_name,
                    cr.id as raw_id,
                    cr.markdown_content,
                    cr.content_hash as input_hash
                FROM subtopics st
                JOIN topics t ON t.id = st.topic_id
                JOIN subjects s ON s.id = t.subject_id
                LEFT JOIN content_raw cr ON cr.subtopic_id = st.id
                WHERE st.id = ?
            """, (subtopic_id,))
            
            row = cursor.fetchone()
            if not row:
                return False, {'error': 'Subtopic not found'}
            
            if not row['markdown_content']:
                return False, {'error': 'No raw content'}
            
            raw_id = row['raw_id']
            if not raw_id:
                return False, {'error': 'No raw content ID'}
            
            print(f"\n🔄 Processing: [{row['subject_name']}] {row['topic_name']}")
            print(f"   → {row['subtopic_name']}")
            
            # Rewrite content
            result, rewrite_metrics = self.rewrite_content(
                raw_content=row['markdown_content'],
                subtopic_name=row['subtopic_name'],
                topic_name=row['topic_name'],
                subject_name=row['subject_name']
            )
            
            metrics.update(rewrite_metrics)
            
            if not result:
                return False, metrics
            
            html_content = result.get('html_content', '')
            
            # Compute output hash
            output_hash = hashlib.md5(html_content.encode('utf-8')).hexdigest()
            
            # Save to database
            cursor.execute("""
                INSERT OR REPLACE INTO content_processed 
                (raw_id, subtopic_id, html_content, processed_at, processor_version, 
                 input_hash, output_hash, key_concepts, processing_metrics)
                VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?, ?)
            """, (
                raw_id,
                subtopic_id,
                html_content,
                'gemini-enhanced-v2',
                row.get('input_hash', ''),
                output_hash,
                json.dumps(result.get('key_concepts', [])),
                json.dumps(metrics)
            ))
            
            conn.commit()
            
            # Log to rewriting_quality
            self._log_quality_metrics(conn, subtopic_id, row['subject_name'], metrics)
            
            print(f"   ✅ Saved ({len(html_content)} chars)")
            
            if metrics.get('validation', {}).get('has_learning_objectives'):
                print(f"   📚 Learning objectives: ✓")
            if metrics.get('validation', {}).get('has_key_takeaways'):
                print(f"   🎯 Key takeaways: ✓")
            
            return True, metrics
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            traceback.print_exc()
            metrics['error'] = str(e)
            return False, metrics
        finally:
            conn.close()
    
    def _log_quality_metrics(self, conn, subtopic_id: str, subject_name: str, metrics: Dict):
        """Log quality metrics to rewriting_quality table"""
        try:
            validation = metrics.get('validation', {})
            
            conn.execute("""
                INSERT OR REPLACE INTO rewriting_quality
                (subtopic_id, subject_name, status, raw_length, processed_length,
                 compression_ratio, has_objectives, has_takeaways, has_questions,
                 processing_time, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                subtopic_id,
                subject_name,
                'success',
                metrics.get('input_length', 0),
                validation.get('output_length', 0),
                validation.get('ratio', 0),
                1 if validation.get('has_learning_objectives') else 0,
                1 if validation.get('has_key_takeaways') else 0,
                1 if validation.get('has_think_questions') else 0,
                metrics.get('processing_time', 0)
            ))
            conn.commit()
        except Exception as e:
            # Table might have different schema
            pass
    
    def process_batch(
        self, 
        limit: int = 10, 
        skip_processed: bool = True,
        subject_filter: Optional[str] = None
    ) -> Dict:
        """
        Process multiple subtopics in batch.
        
        Returns:
            Summary statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        if skip_processed:
            query = """
                SELECT st.id 
                FROM subtopics st
                JOIN topics t ON t.id = st.topic_id
                JOIN subjects s ON s.id = t.subject_id
                LEFT JOIN content_processed cp ON cp.subtopic_id = st.id
                WHERE cp.id IS NULL
                AND EXISTS (SELECT 1 FROM content_raw cr WHERE cr.subtopic_id = st.id)
            """
            params = []
            
            if subject_filter:
                query += " AND s.name LIKE ?"
                params.append(f"%{subject_filter}%")
            
            query += " LIMIT ?"
            params.append(limit)
        else:
            query = """
                SELECT st.id 
                FROM subtopics st
                WHERE EXISTS (SELECT 1 FROM content_raw cr WHERE cr.subtopic_id = st.id)
                LIMIT ?
            """
            params = [limit]
        
        cursor.execute(query, params)
        subtopic_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"\n🚀 Processing {len(subtopic_ids)} subtopics...")
        print("=" * 70)
        
        stats = {
            'total': len(subtopic_ids),
            'success': 0,
            'failed': 0,
            'total_time': 0,
            'errors': []
        }
        
        for i, subtopic_id in enumerate(subtopic_ids, 1):
            print(f"\n[{i}/{len(subtopic_ids)}]", end="")
            
            success, metrics = self.process_subtopic(subtopic_id)
            
            if success:
                stats['success'] += 1
                stats['total_time'] += metrics.get('processing_time', 0)
            else:
                stats['failed'] += 1
                stats['errors'].append({
                    'subtopic_id': subtopic_id,
                    'error': metrics.get('error', 'Unknown')
                })
        
        print("\n" + "=" * 70)
        print(f"✅ Completed: {stats['success']}/{stats['total']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"⏱️  Total time: {stats['total_time']:.1f}s")
        
        return stats


def ensure_schema_updates(conn):
    """Ensure content_processed has enhanced columns"""
    try:
        cursor = conn.execute("PRAGMA table_info(content_processed)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = [
            ('input_hash', 'TEXT'),
            ('output_hash', 'TEXT'),
            ('key_concepts', 'TEXT'),
            ('processing_metrics', 'TEXT')
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                conn.execute(f"ALTER TABLE content_processed ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Added {col_name} column")
        
        conn.commit()
    except Exception as e:
        print(f"  ⚠️  Schema update warning: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Gemini Content Rewriter V2")
    parser.add_argument('--limit', type=int, default=10, help='Number of subtopics to process')
    parser.add_argument('--subtopic-id', type=str, help='Process specific subtopic ID')
    parser.add_argument('--subject', type=str, help='Filter by subject name')
    parser.add_argument('--skip-processed', action='store_true', default=True,
                       help='Skip already processed subtopics')
    parser.add_argument('--force', action='store_true', help='Reprocess all')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🤖 Enhanced Gemini Content Rewriter V2")
    print("=" * 70)
    print("\nFeatures:")
    print("  ✅ Structured JSON output")
    print("  ✅ Content validation")
    print("  ✅ Retry with exponential backoff")
    print("  ✅ Content chunking for large chapters")
    print("  ✅ Quality metrics tracking")
    print()
    
    # Ensure schema
    conn = sqlite3.connect(DB_PATH)
    ensure_schema_updates(conn)
    conn.close()
    
    rewriter = EnhancedContentRewriter()
    
    if args.subtopic_id:
        success, metrics = rewriter.process_subtopic(args.subtopic_id)
        print(f"\n{'✅ Success' if success else '❌ Failed'}")
        print(f"Metrics: {json.dumps(metrics, indent=2)}")
    else:
        stats = rewriter.process_batch(
            limit=args.limit,
            skip_processed=not args.force,
            subject_filter=args.subject
        )


if __name__ == "__main__":
    main()
