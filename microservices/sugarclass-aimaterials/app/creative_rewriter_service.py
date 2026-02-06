"""
Creative Content Rewriter Service
Uses LLM to rewrite content for educational purposes
"""

import sqlite3
import json
import os
import re
from pathlib import Path
from openai import OpenAI

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "rag_content.db"

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not set in environment variables")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_subtopic_content(subtopic_id):
    """Get raw content for a subtopic"""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT s.id, s.name, s.description, s.topic_id,
               t.name as topic_name,
               cp.chapter_number, cp.markdown_content
        FROM subtopics s
        LEFT JOIN topics t ON s.topic_id = t.id
        LEFT JOIN content_processed cp ON s.id = cp.subtopic_id
        WHERE s.id = ?
    """, (subtopic_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_rewrite_prompt(content_data):
    """Create a detailed prompt for LLM to rewrite content"""
    
    prompt = f"""You are an expert engineering educator creating engaging, textbook-style content for GCSE Engineering (AQA 9-1). Your audience is students aged 14-16 and their trainers.

**Chapter:** {content_data['topic_name']}
**Subtopic:** {content_data['name']}

**Original Content:**
{content_data['markdown_content']}

## Your Task

Rewrite this content to make it more engaging and educational while maintaining technical accuracy.

## Requirements

### Style & Tone
- Educational, encouraging, and inspiring
- Professional yet accessible for GCSE students
- Use real-world examples and applications
- Explain complex concepts with analogies

### Structure
1. **Learning Objectives** - Start with "## Learning Objectives" listing 3-5 key points students will learn
2. **Engaging Introduction** - Hook the reader with a real-world scenario or question
3. **Clear Explanations** - Break down concepts step by step with examples
4. **Visual References** - Keep all images in their original positions (![](images/filename.jpg))
5. **Key Takeaways** - End with "## Key Takeaways" summarizing 3-5 main points
6. **Practice Questions** - Add 2-3 thought-provoking questions

### Format
- Use Markdown with proper headers (##, ###)
- Use bullet points for lists
- Use bold for emphasis
- Include spacing for readability

## Guidelines
- Preserve all technical information and data
- Explain terms on first use
- Connect content to engineering careers
- Add context about why this matters in the real world
- Maintain all image references exactly as they appear
- Keep content at similar length (±20%)

Start your rewrite immediately with ## Learning Objectives. Do not include any meta-commentary or introduction text."""

    return prompt

def rewrite_with_llm(content_data):
    """Use OpenAI API to rewrite content"""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")
    
    prompt = create_rewrite_prompt(content_data)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using smaller model for cost efficiency
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert engineering educator who creates engaging, textbook-style content for GCSE students. You write clear, inspiring, and technically accurate educational materials."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        rewritten_content = response.choices[0].message.content
        model_used = response.model
        
        # Extract learning objectives
        learning_obj_match = re.search(r'## Learning Objectives\s*(.*?)(?=##|$)', rewritten_content, re.DOTALL)
        learning_objectives = learning_obj_match.group(1).strip() if learning_obj_match else ""
        
        # Extract key takeaways
        takeaways_match = re.search(r'## Key Takeaways\s*(.*?)(?=##|$)', rewritten_content, re.DOTALL)
        key_takeaways = takeaways_match.group(1).strip() if takeaways_match else ""
        
        return {
            'rewritten_content': rewritten_content,
            'learning_objectives': learning_objectives,
            'key_takeaways': key_takeaways,
            'model_used': model_used
        }
        
    except Exception as e:
        raise Exception(f"LLM rewrite failed: {str(e)}")

def save_rewrite(subtopic_id, raw_content, rewrite_result, chapter_number=None):
    """Save rewritten content to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO content_rewritten 
            (subtopic_id, chapter_number, rewrite_version, raw_content, 
             rewritten_content, learning_objectives, key_takeaways, ai_model)
            VALUES (?, ?, 'v1', ?, ?, ?, ?, ?)
        """, (
            subtopic_id,
            chapter_number,
            raw_content,
            rewrite_result['rewritten_content'],
            rewrite_result['learning_objectives'],
            rewrite_result['key_takeaways'],
            rewrite_result['model_used']
        ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving rewrite: {e}")
        return False
    finally:
        conn.close()

def get_rewritten_content(subtopic_id):
    """Get rewritten content from database"""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT * FROM content_rewritten 
        WHERE subtopic_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (subtopic_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def rewrite_subtopic(subtopic_id):
    """Complete workflow to rewrite a subtopic"""
    print(f"Rewriting subtopic: {subtopic_id}")
    
    # 1. Get original content
    content_data = get_subtopic_content(subtopic_id)
    if not content_data:
        raise ValueError(f"Subtopic {subtopic_id} not found")
    
    print(f"  - Original content: {len(content_data['markdown_content'] or '')} words")
    
    # 2. Check if already rewritten
    existing = get_rewritten_content(subtopic_id)
    if existing:
        print(f"  - Already exists (version {existing['rewrite_version']})")
        return existing
    
    # 3. Rewrite with LLM
    print("  - Generating rewrite with LLM...")
    rewrite_result = rewrite_with_llm(content_data)
    
    # 4. Save to database
    print("  - Saving to database...")
    saved = save_rewrite(
        subtopic_id,
        content_data['markdown_content'],
        rewrite_result,
        content_data['chapter_number']
    )
    
    if saved:
        print(f"  ✓ Rewrite complete!")
        return {'id': subtopic_id, **rewrite_result}
    else:
        raise Exception("Failed to save rewrite")

if __name__ == "__main__":
    # Test with Chapter 1 subtopics
    print("Creative Content Rewriter Service")
    print("="*80)
    
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export OPENAI_API_KEY='your-key-here'")
        exit(1)
    
    # List Chapter 1 subtopics
    conn = get_db_connection()
    ch1_subs = conn.execute("""
        SELECT id, name FROM subtopics 
        WHERE topic_id = 'engineering_gcse_8852_ch1'
        ORDER BY id
    """).fetchall()
    conn.close()
    
    print("\nChapter 1 Subtopics available to rewrite:")
    for i, sub in enumerate(ch1_subs, 1):
        print(f"  {i}. {sub['id']}: {sub['name']}")
    
    print("\nTo rewrite a subtopic:")
    print("  python -c \"from app.creative_rewriter_service import rewrite_subtopic; rewrite_subtopic('engineering_gcse_8852_1.1')\"")