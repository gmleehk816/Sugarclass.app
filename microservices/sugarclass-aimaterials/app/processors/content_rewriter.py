"""
Content Rewriter
================
Rewrites raw markdown content into enhanced educational content using AI.

Pipeline:
1. Read raw content from content_raw table
2. Send to AI for rewriting/enhancement
3. Store enhanced content in content_processed table
4. Optionally generate AI images

Usage:
    python content_rewriter.py --list          # Show unprocessed content
    python content_rewriter.py --id <id>       # Process specific content
    python content_rewriter.py --topic B1      # Process all B1 subtopics
    python content_rewriter.py --all           # Process all unprocessed
"""

import os
import re
import sqlite3
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Paths
APP_DIR = Path(__file__).parent.parent
PROJECT_ROOT = APP_DIR.parent
DB_PATH = PROJECT_ROOT / "database" / "rag_content.db"  # Database in database/ folder

# API Configuration
API_KEY = os.getenv("NANO_BANANA_API_KEY", "")
API_URL = os.getenv("NANO_BANANA_API_URL", "https://newapi.aisonnet.org/v1/chat/completions")
MODEL = os.getenv("NANO_BANANA_MODEL", "nano-banana")

# Rewriter version
PROCESSOR_VERSION = "1.0"


class ContentRewriter:
    """Rewrite raw markdown into enhanced educational content"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.api_key = API_KEY
        self.api_url = API_URL
        self.model = MODEL
    
    def get_unprocessed_content(self, limit: int = 50) -> List[Dict]:
        """Get content_raw entries that haven't been processed yet"""
        query = """
            SELECT cr.id, cr.subtopic_id, cr.title, cr.char_count, cr.markdown_content,
                   s.name as subtopic_name, t.name as topic_name, t.type as subject_type
            FROM content_raw cr
            LEFT JOIN subtopics s ON cr.subtopic_id = s.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE cr.id NOT IN (SELECT raw_id FROM content_processed)
            ORDER BY cr.id
            LIMIT ?
        """
        rows = self.conn.execute(query, (limit,)).fetchall()
        return [dict(row) for row in rows]
    
    def get_content_by_id(self, content_id: int) -> Optional[Dict]:
        """Get specific content by ID"""
        query = """
            SELECT cr.id, cr.subtopic_id, cr.title, cr.char_count, cr.markdown_content,
                   s.name as subtopic_name, t.name as topic_name, t.type as subject_type
            FROM content_raw cr
            LEFT JOIN subtopics s ON cr.subtopic_id = s.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE cr.id = ?
        """
        row = self.conn.execute(query, (content_id,)).fetchone()
        return dict(row) if row else None
    
    def get_content_by_topic(self, topic_prefix: str) -> List[Dict]:
        """Get all content for a topic (e.g., 'B1', 'C2')"""
        query = """
            SELECT cr.id, cr.subtopic_id, cr.title, cr.char_count, cr.markdown_content,
                   s.name as subtopic_name, t.name as topic_name, t.type as subject_type
            FROM content_raw cr
            LEFT JOIN subtopics s ON cr.subtopic_id = s.id
            LEFT JOIN topics t ON s.topic_id = t.id
        WHERE cr.subtopic_id LIKE ?
            AND cr.id NOT IN (SELECT raw_id FROM content_processed)
            ORDER BY cr.id
        """
        rows = self.conn.execute(query, (f"engineering_gcse_8852_E{topic_prefix}%",)).fetchall()
        return [dict(row) for row in rows]
    
    def rewrite_content(self, content: Dict) -> Dict:
        """
        Rewrite content using AI.
        
        Returns:
            Dict with html_content, summary, key_terms
        """
        markdown = content['markdown_content']
        title = content.get('title', 'Unknown')
        subject_type = content.get('subject_type', 'Science')
        
        # Create prompt for rewriting
        prompt = self._create_rewrite_prompt(markdown, title, subject_type)
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": """Convert markdown to simple HTML. Keep the ORIGINAL content - do NOT add new content.

RULES:
1. Keep original text exactly as is
2. Convert markdown headings (#) to HTML headings (h2, h3)
3. Convert paragraphs to <p> tags
4. Convert image references ![](path) to <img src="path">
5. Bold key terms that are defined
6. NO fancy cards, NO flip cards, NO interactive elements
7. NO mnemonics, NO extra explanations
8. Just clean, simple HTML conversion"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 4000
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Parse the response
                result = self._parse_ai_response(ai_response, markdown)
                return result
            else:
                print(f"   ⚠️ API error: {response.status_code}")
                return self._fallback_processing(markdown, title)
                
        except Exception as e:
            print(f"   ⚠️ Rewrite error: {e}")
            return self._fallback_processing(markdown, title)
    
    def _create_rewrite_prompt(self, markdown: str, title: str, subject_type: str) -> str:
        """Create the rewrite prompt"""
        # Truncate if too long
        if len(markdown) > 8000:
            markdown = markdown[:8000] + "\n\n[Content truncated...]"
        
        return f"""Convert this markdown to simple HTML. Keep the original content exactly.

Title: {title}

Markdown:
{markdown}

Output format:
---HTML---
[Simple HTML conversion - keep original text]
---SUMMARY---
[One sentence summary]
---KEY_TERMS---
[key terms from the content, comma-separated]
"""
    
    def _parse_ai_response(self, response: str, original: str) -> Dict:
        """Parse AI response into structured data"""
        result = {
            "html_content": "",
            "summary": "",
            "key_terms": "[]"
        }
        
        # Try to parse structured response
        if "---HTML---" in response:
            parts = response.split("---")
            for i, part in enumerate(parts):
                if "HTML" in part and i + 1 < len(parts):
                    result["html_content"] = parts[i + 1].strip()
                elif "SUMMARY" in part and i + 1 < len(parts):
                    result["summary"] = parts[i + 1].strip()
                elif "KEY_TERMS" in part and i + 1 < len(parts):
                    terms = parts[i + 1].strip()
                    # Convert to JSON array
                    term_list = [t.strip() for t in terms.split(",") if t.strip()]
                    result["key_terms"] = json.dumps(term_list)
        else:
            # Fallback: use entire response as HTML
            result["html_content"] = response
        
        # If no HTML content, use fallback
        if not result["html_content"]:
            result = self._fallback_processing(original, "")
        
        return result
    
    def _fallback_processing(self, markdown: str, title: str) -> Dict:
        """Fallback: convert markdown to basic HTML"""
        import html
        
        # Basic markdown to HTML conversion
        content = html.escape(markdown)
        content = re.sub(r'^# (.+)$', r'<h2 class="text-2xl font-bold mb-4">\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h3 class="text-xl font-semibold mb-3">\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'<h4 class="text-lg font-medium mb-2">\1</h4>', content, flags=re.MULTILINE)
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
        content = re.sub(r'\n\n', '</p><p class="mb-4">', content)
        content = f'<p class="mb-4">{content}</p>'
        
        return {
            "html_content": content,
            "summary": f"Content about {title}" if title else "Educational content",
            "key_terms": "[]"
        }
    
    def save_processed_content(self, raw_id: int, subtopic_id: str, result: Dict) -> int:
        """Save processed content to database"""
        cursor = self.conn.execute("""
            INSERT INTO content_processed 
            (raw_id, subtopic_id, html_content, summary, key_terms, processor_version)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            raw_id,
            subtopic_id,
            result["html_content"],
            result["summary"],
            result["key_terms"],
            PROCESSOR_VERSION
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def process_content(self, content: Dict) -> Dict:
        """Full pipeline: rewrite and save"""
        print(f"   📝 Rewriting: {content['title'][:50]}...")
        
        # Rewrite
        result = self.rewrite_content(content)
        
        # Save
        processed_id = self.save_processed_content(
            content['id'],
            content['subtopic_id'],
            result
        )
        
        return {
            "raw_id": content['id'],
            "processed_id": processed_id,
            "subtopic_id": content['subtopic_id'],
            "html_length": len(result["html_content"]),
            "summary": result["summary"][:100] + "..." if len(result["summary"]) > 100 else result["summary"]
        }
    
    def close(self):
        self.conn.close()


def list_unprocessed():
    """List content that hasn't been processed yet"""
    rewriter = ContentRewriter()
    content = rewriter.get_unprocessed_content(limit=20)
    rewriter.close()
    
    print(f"\n📋 Unprocessed Content ({len(content)} items):")
    print("-" * 60)
    for c in content:
        print(f"  [{c['id']}] {c['subtopic_id']}")
        print(f"      {c['title'][:50]}... ({c['char_count']} chars)")
    
    return content


def process_by_id(content_id: int):
    """Process specific content by ID"""
    rewriter = ContentRewriter()
    content = rewriter.get_content_by_id(content_id)
    
    if not content:
        print(f"❌ Content ID {content_id} not found")
        return
    
    print(f"\n🔄 Processing content ID {content_id}...")
    result = rewriter.process_content(content)
    rewriter.close()
    
    print("\n✅ Result:")
    print(json.dumps(result, indent=2))


def process_by_topic(topic_prefix: str, limit: int = 5):
    """Process all content for a topic"""
    rewriter = ContentRewriter()
    content_list = rewriter.get_content_by_topic(topic_prefix)
    
    if not content_list:
        print(f"❌ No unprocessed content found for topic '{topic_prefix}'")
        return
    
    print(f"\n🔄 Processing {min(len(content_list), limit)} items for topic '{topic_prefix}'...")
    
    results = []
    for content in content_list[:limit]:
        result = rewriter.process_content(content)
        results.append(result)
        print(f"   ✅ Processed: {content['subtopic_id']}")
    
    rewriter.close()
    
    print(f"\n✅ Processed {len(results)} items")
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Rewrite content using AI")
    parser.add_argument("--list", action="store_true", help="List unprocessed content")
    parser.add_argument("--id", type=int, help="Process specific content ID")
    parser.add_argument("--topic", type=str, help="Process all content for a topic (e.g., B1, C2)")
    parser.add_argument("--limit", type=int, default=5, help="Max items to process")
    parser.add_argument("--all", action="store_true", help="Process all unprocessed content")
    
    args = parser.parse_args()
    
    if args.list:
        list_unprocessed()
    elif args.id:
        process_by_id(args.id)
    elif args.topic:
        process_by_topic(args.topic, args.limit)
    elif args.all:
        rewriter = ContentRewriter()
        content_list = rewriter.get_unprocessed_content(limit=args.limit)
        
        print(f"\n🔄 Processing {len(content_list)} items...")
        for content in content_list:
            result = rewriter.process_content(content)
            print(f"   ✅ {content['subtopic_id']}")
        
        rewriter.close()
        print(f"\n✅ Done!")
    else:
        # Default: show help
        parser.print_help()
