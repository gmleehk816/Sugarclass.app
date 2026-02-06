"""
Comprehensive Content Processing System
========================================
Processes all subjects to generate MD, JSON, and HTML content.
Uses gemini-3-flash-preview-cli as default model with gemini-2.5-flash-cli as fallback.
"""
import sys
import os
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api_config import get_api_config, make_api_call
from app.logger import get_logger

# Configuration
DATABASE_PATH = Path(__file__).resolve().parent.parent / 'database' / 'rag_content.db'
OUTPUT_DIR = Path(__file__).resolve().parent.parent / '_bmad-output'
MD_DIR = OUTPUT_DIR / 'markdown'
JSON_DIR = OUTPUT_DIR / 'json'
HTML_DIR = OUTPUT_DIR / 'html'

# Create directories
for dir_path in [MD_DIR, JSON_DIR, HTML_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

class ContentProcessor:
    """Comprehensive content processor for all subjects"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.api_config = get_api_config()
        self.stats = {
            'total_subtopics': 0,
            'processed_md': 0,
            'processed_json': 0,
            'processed_html': 0,
            'failed': 0,
            'start_time': datetime.now()
        }
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_unprocessed_content(self, subject_name: Optional[str] = None) -> List[Dict]:
        """
        Get all raw content that hasn't been processed yet.
        If subject_name is provided, filters for that subject.
        """
        conn = self.get_db_connection()
        conn.row_factory = sqlite3.Row  # Use Row factory for dict-like access
        cur = conn.cursor()

        params = []
        
        # Base query joins tables to get all necessary info
        query = """
            SELECT 
                cr.id as raw_id, 
                cr.subtopic_id, 
                cr.title, 
                cr.markdown_content,
                sub.topic_id,
                t.name as topic_name
            FROM content_raw cr
            JOIN subtopics sub ON cr.subtopic_id = sub.id
            JOIN topics t ON sub.topic_id = t.id
            LEFT JOIN content_processed cp ON cr.id = cp.raw_id
        """

        where_clauses = [
            "cr.markdown_content IS NOT NULL",
            "cr.markdown_content != ''",
            "cp.id IS NULL" # More reliable check for unprocessed content
        ]

        # If a subject is specified, add a join and a where clause for it
        if subject_name:
            query += " JOIN subjects s ON t.subject_id = s.id"
            where_clauses.append("s.name = ?")
            params.append(subject_name)

        query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY cr.id"

        try:
            cur.execute(query, params)
            results = cur.fetchall()
        except sqlite3.OperationalError as e:
            logger.error(f"Database query failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            # This might happen if a column/table name is wrong.
            # Provide a helpful message.
            logger.error("This might be due to a schema mismatch. Expected tables: subjects, topics, subtopics, content_raw, content_processed.")
            return []
        finally:
            conn.close()

        return [{
            'raw_id': row['raw_id'],
            'id': row['subtopic_id'],
            'title': row['title'] if row['title'] else f"Content {row['raw_id']}",
            'raw_content': row['markdown_content'],
            'existing_html': None,  # We query for unprocessed, so this is always None
            'topic_id_db': row['topic_id'],
            'topic_name': row['topic_name']
        } for row in results]
    
    def generate_markdown(self, content: Dict) -> str:
        """Generate markdown from raw content"""
        title = content['title']
        text = content['raw_content']
        subtopic_id = content['id']
        topic_name = content['topic_name']
        
        md_content = f"""# {title}

**Topic:** {topic_name}  
**Subtopic ID:** {subtopic_id}

---

{text}

---

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return md_content
    
    def generate_json(self, content: Dict, markdown: str) -> Dict:
        """Generate JSON metadata"""
        return {
            'metadata': {
                'subtopic_id': content['id'],
                'topic_id': content['topic_id_db'],
                'topic_name': content['topic_name'],
                'title': content['title'],
                'generated_at': datetime.now().isoformat(),
                'model_used': self.api_config['model']
            },
            'content': {
                'raw': content['raw_content'],
                'markdown': markdown,
                'word_count': len(content['raw_content'].split()),
                'char_count': len(content['raw_content'])
            }
        }
    
    def generate_html_with_ai(self, content: Dict) -> Tuple[bool, str, str]:
        """Generate HTML content using AI API"""
        title = content['title']
        text = content['raw_content']
        
        system_prompt = """You are an expert educational content formatter. Convert the provided text into clean, attractive HTML that:
1. Uses proper semantic HTML5 structure
2. Includes appropriate CSS styling inline
3. Formats equations, code blocks, and lists properly
4. Has good typography and readability
5. Includes a clean header with the title
6. Uses a professional color scheme

Return ONLY the HTML code, no explanations."""

        user_prompt = f"""Convert this educational content to attractive HTML:

Title: {title}

Content:
{text}"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        try:
            result = make_api_call(
                messages,
                model=self.api_config['model'],
                max_tokens=4096,
                temperature=0.7
            )
            
            if result['success']:
                return True, result['content'], result.get('model', self.api_config['model'])
            else:
                logger.error(f"API Error: {result['error']}")
                return False, result.get('error', 'Unknown error'), self.api_config['model']
                
        except Exception as e:
            logger.exception(f"Exception during API call: {e}")
            return False, str(e), self.api_config['model']
    
    def save_markdown(self, content: Dict, md_content: str) -> str:
        """Save markdown to file"""
        topic_id = content['topic_id_db']
        subtopic_id = content['id']
        
        # Create topic directory
        topic_dir = MD_DIR / f"topic_{topic_id}"
        topic_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = topic_dir / f"subtopic_{str(subtopic_id).replace('.', '_')}.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(file_path)
    
    def save_json(self, content: Dict, json_data: Dict) -> str:
        """Save JSON to file"""
        topic_id = content['topic_id_db']
        subtopic_id = content['id']
        
        # Create topic directory
        topic_dir = JSON_DIR / f"topic_{topic_id}"
        topic_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = topic_dir / f"subtopic_{str(subtopic_id).replace('.', '_')}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return str(file_path)
    
    def save_html(self, content: Dict, html_content: str) -> str:
        """Save HTML to file"""
        topic_id = content['topic_id_db']
        subtopic_id = content['id']
        
        # Create topic directory
        topic_dir = HTML_DIR / f"topic_{topic_id}"
        topic_dir.mkdir(exist_ok=True)
        
        # Save file
        file_name = f"subtopic_{str(subtopic_id).replace('.', '_')}.html"
        file_path = topic_dir / file_name
        
        # Add proper HTML structure
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content['title']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .content-wrapper {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="content-wrapper">
        {html_content}
    </div>
</body>
</html>"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        return str(file_path)
    
    def update_database(self, content: Dict, html_content: str, ai_model: str):
        """Update database with processed HTML content"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        try:
            # Check if processed content exists
            cur.execute(
                "SELECT id FROM content_processed WHERE raw_id = ?",
                (content['raw_id'],)
            )
            existing = cur.fetchone()
            
            if existing:
                # Update existing
                cur.execute(
                    """UPDATE content_processed 
                       SET html_content = ?, processed_at = ?, processor_version = ?
                       WHERE raw_id = ?""",
                    (html_content, datetime.now().isoformat(), ai_model, content['raw_id'])
                )
            else:
                # Insert new
                cur.execute(
                    """INSERT INTO content_processed 
                       (raw_id, subtopic_id, html_content, processed_at, processor_version)
                       VALUES (?, ?, ?, ?, ?)""",
                    (content['raw_id'], content['id'], html_content, 
                     datetime.now().isoformat(), ai_model)
                )
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.exception(f"Database error: {e}")
        
        finally:
            conn.close()
    
    def process_content(self, content: Dict, retry_count: int = 0) -> bool:
        """Process a single content item through all formats"""
        subtopic_id = content['id']
        title = content['title']
        
        logger.info(f"Processing: {subtopic_id} - {title}")
        
        # Generate Markdown
        try:
            md_content = self.generate_markdown(content)
            md_path = self.save_markdown(content, md_content)
            logger.info(f"Markdown saved: {md_path}")
            self.stats['processed_md'] += 1
        except Exception as e:
            logger.exception(f"Markdown error: {e}")
            return False
        
        # Generate JSON
        try:
            json_data = self.generate_json(content, md_content)
            json_path = self.save_json(content, json_data)
            logger.info(f"JSON saved: {json_path}")
            self.stats['processed_json'] += 1
        except Exception as e:
            logger.exception(f"JSON error: {e}")
            return False
        
        # Generate HTML with AI (with retry on failure using fallback model)
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Generating HTML (attempt {attempt + 1}/{max_retries})...")
                success, html_content, model_used = self.generate_html_with_ai(content)
                
                if success:
                    html_path = self.save_html(content, html_content)
                    logger.info(f"HTML saved: {html_path} (model: {model_used})")
                    
                    # Update database
                    self.update_database(content, html_content, model_used)
                    logger.info(f"Database updated")
                    
                    self.stats['processed_html'] += 1
                    return True
                else:
                    logger.warning(f"HTML generation failed: {html_content}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying...")
                        time.sleep(2)
                    
            except Exception as e:
                logger.exception(f"HTML error: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying...")
                    time.sleep(2)
        
        self.stats['failed'] += 1
        return False
    
    def process_all(self, limit: Optional[int] = None, subject: Optional[str] = None):
        """Process all unprocessed content"""
        logger.info("=" * 70)
        logger.info("COMPREHENSIVE CONTENT PROCESSING")
        logger.info("=" * 70)
        
        # Get content to process
        if subject:
            logger.info(f"Filtering for subject: {subject}")
        unprocessed = self.get_unprocessed_content(subject_name=subject)
        self.stats['total_subtopics'] = len(unprocessed)
        
        logger.info(f"Found {len(unprocessed)} subtopics to process")
        logger.info(f"Using model: {self.api_config['model']}")
        
        if not unprocessed and subject:
            logger.warning(f"No unprocessed content found for subject '{subject}'. Exiting.")
            return

        if limit:
            unprocessed = unprocessed[:limit]
            logger.warning(f"Processing limited to {limit} items")
        
        logger.info("=" * 70)
        
        # Process each item
        for idx, content in enumerate(unprocessed, 1):
            logger.info(f"[{idx}/{len(unprocessed)}]")
            self.process_content(content)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print processing summary"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        logger.info("=" * 70)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total subtopics: {self.stats['total_subtopics']}")
        logger.info(f"Markdown files generated: {self.stats['processed_md']}")
        logger.info(f"JSON files generated: {self.stats['processed_json']}")
        logger.info(f"HTML files generated: {self.stats['processed_html']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Time elapsed: {elapsed:.2f} seconds")
        logger.info(f"Output directory: {OUTPUT_DIR}")
        logger.info("=" * 70)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Process all subjects to generate MD, JSON, and HTML'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of subtopics to process (for testing)'
    )
    parser.add_argument(
        '--topic',
        type=str,
        help='Process specific topic only (DEPRECATED)'
    )
    parser.add_argument(
        '--subject',
        type=str,
        help='Process a specific subject by name (e.g., "Business Studies (0450)")'
    )
    
    args = parser.parse_args()

    if args.topic:
        logger.warning("The --topic argument is deprecated and has no effect. Use --subject instead.")
    
    # Create processor
    processor = ContentProcessor()
    
    # Process
    processor.process_all(limit=args.limit, subject=args.subject)


if __name__ == '__main__':
    main()
