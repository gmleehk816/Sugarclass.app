"""
Rewrite to HTML Function
========================
Step 2 of Content Builder Pipeline: Convert raw markdown chunks to enhanced HTML and store in content_processed table.
"""

import sqlite3
import os
import re
import time
import requests
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import ssl

# It's better to have this at the top level of the app directory
# so this import works from any script in the project.
from api_config import get_api_config

api_config = get_api_config()
CONTENT_API_KEY = api_config['key']
CONTENT_API_URL = api_config['url'].rstrip('/') + "/v1/chat/completions"
MODEL = api_config['model']


class SSLAdapter(HTTPAdapter):
    """An SSL adapter that ignores SSL verification errors."""
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


def rewrite_to_html(
    subtopic_id: Optional[str] = None,
    raw_id: Optional[int] = None,
    subject_id: Optional[str] = None,
    chapter: Optional[int] = None,
    limit: int = 10,
    force: bool = False,
    db_path: Optional[Path | str] = None,
    system_prompt: Optional[str] = None,
    user_prompt_template: Optional[str] = None,
    processor_version: str = "v7.0-universal"
) -> Dict:
    """
    Rewrite raw markdown content to enhanced HTML using AI.
    """
    if db_path is None:
        # Assume the script is run from the root directory
        db_path = Path.cwd() / "app" / "rag_content.db"
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        return {'success': False, 'errors': [f"Database not found at {db_path}"]}

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    try:
        query_parts = []
        params = []

        if subtopic_id:
            query_parts.append("r.subtopic_id = ?")
            params.append(subtopic_id)
        elif raw_id:
            query_parts.append("r.id = ?")
            params.append(raw_id)
        elif subject_id:
            query_parts.append("r.subtopic_id LIKE ?")
            params.append(f"{subject_id}_%")
            if chapter:
                query_parts.append("r.subtopic_id LIKE ?")
                params.append(f"%_Ch{chapter}.%")

        if not query_parts:
            return {'success': False, 'errors': ['No valid criteria specified.']}

        base_query = "SELECT r.id, r.subtopic_id, r.title, r.markdown_content FROM content_raw r"
        if not force:
            base_query += " LEFT JOIN content_processed p ON p.subtopic_id = r.subtopic_id"
            query_parts.append("p.subtopic_id IS NULL")

        query = base_query + " WHERE " + " AND ".join(query_parts) + " ORDER BY r.subtopic_id LIMIT ?"
        params.append(limit)
        
        rows = cur.execute(query, tuple(params)).fetchall()
        
        if not rows:
            return {'success': True, 'processed': 0, 'failed': 0, 'errors': ['No content found matching criteria']}
        
        print("Found " + str(len(rows)) + " subtopics to process")
        
        processed, failed, errors = 0, 0, []
        
        for raw_id_val, subtopic_id_val, title, markdown in rows:
            try:
                _process_one_subtopic(cur, raw_id_val, subtopic_id_val, title or subtopic_id_val, markdown or "", system_prompt, user_prompt_template, processor_version)
                conn.commit()
                processed += 1
            except Exception as e:
                conn.rollback()
                error_msg = f"Failed to process {subtopic_id_val}: {e}"
                print("   " + error_msg)
                errors.append(error_msg)
                failed += 1
        
        return {'success': True, 'processed': processed, 'failed': failed, 'errors': errors}
    
    finally:
        conn.close()


def _process_one_subtopic(cur, raw_id, subtopic_id, title, markdown, custom_system_prompt, custom_user_prompt, processor_version):
    """Process a single subtopic."""
    print("Processing: " + subtopic_id)
    print("   Title: " + title[:80])
    
    from .process_math_comprehensive import extract_math_expressions, extract_images, extract_tables, restore_math_expressions, restore_images, restore_tables, clean_markdown_for_ai
    
    images, md_no_images = extract_images(markdown)
    print("   Found " + str(len(images)) + " images to preserve")
    
    tables, md_no_tables = extract_tables(md_no_images)
    print("   Found " + str(len(tables)) + " tables to preserve")
    
    math_expressions, cleaned_md = extract_math_expressions(md_no_tables)
    cleaned_md = clean_markdown_for_ai(cleaned_md)
    print("   Found " + str(len(math_expressions)) + " math expressions to preserve")
    
    system_prompt = custom_system_prompt or _get_default_system_prompt()
    user_prompt = custom_user_prompt or _get_default_user_prompt(title, cleaned_md[:8000], "", "")

    session = requests.Session()
    session.mount('https://', SSLAdapter())
    
    html_content = None
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    
    try:
        response = session.post(
            CONTENT_API_URL,
            headers={"Authorization": "Bearer " + CONTENT_API_KEY, "Content-Type": "application/json"},
            json={"model": MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 8000},
            timeout=180,
            verify=False,
        )
        if response.status_code == 200:
            result = response.json()
            html_content = result['choices'][0]['message']['content']
            html_content = html_content.replace("```html", "").replace("```", "").strip()
            print("   HTML generated")
        else:
            print("   API call failed with status: " + str(response.status_code))
    except Exception as e:
        print("   API call error: " + str(e))

    if not html_content:
        from .process_math_comprehensive import create_fallback_html
        html_content = create_fallback_html(title, cleaned_md, math_expressions, None, None)
    
    html_content = restore_math_expressions(html_content, math_expressions)
    html_content = restore_images(html_content, images)
    html_content = restore_tables(html_content, tables)
    
    if 'MathJax' not in html_content:
        mathjax_script = '<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>'
        html_content += mathjax_script
    
    summary = title[:200]
    
    cur.execute("DELETE FROM content_processed WHERE subtopic_id = ?", (subtopic_id,))
    cur.execute(
        "INSERT OR REPLACE INTO content_processed (subtopic_id, raw_id, html_content, summary, processor_version) VALUES (?, ?, ?, ?, ?)",
        (subtopic_id, raw_id, html_content, summary, processor_version),
    )
    print("   Saved to database (" + str(len(html_content)) + " chars)")


def _get_default_system_prompt():
    return "You are an expert educational content designer..."

def _get_default_user_prompt(title, content, image_placeholders, table_placeholders):
    return f"Transform this content about '{title}':

{content}"

if __name__ == "__main__":
    # Simplified for direct call, not CLI
    pass