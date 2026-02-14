"""
Generate Business Studies exercises using nano-banana
Based on the working Chemistry exercise generator
"""
import sqlite3
import requests
import json
import re
import time
import ssl
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Configuration
import os
API_KEY = os.getenv("NANO_BANANA_API_KEY", "")
API_URL = "https://newapi.pockgo.com/v1/chat/completions"
TEXT_MODEL = "nano-banana"

# Paths
SCRIPT_DIR = Path(__file__).parent
APP_DIR = SCRIPT_DIR.parent
DB_PATH = APP_DIR / "rag_content.db"

# SSL Adapter
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def generate_questions(subtopic_id, content_text, title):
    """Generate 5 MCQ questions using nano-banana"""
    session = requests.Session()
    session.mount('https://', SSLAdapter())
    
    prompt = f"""Based on this Business Studies content about "{title}", create exactly 5 multiple choice questions.

CONTENT:
{content_text[:2000]}

REQUIREMENTS:
1. Each question should test understanding of key concepts
2. Each question has 4 options (A, B, C, D)
3. Only ONE correct answer per question
4. Include a brief explanation for the correct answer

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      }},
      "correct_answer": "B",
      "explanation": "Brief explanation"
    }}
  ]
}}

Generate exactly 5 questions in valid JSON format."""

    try:
        response = session.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": TEXT_MODEL, "messages": [{"role": "user", "content": prompt}]},
            timeout=120,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('questions', [])
        else:
            print(f"    ⚠️ API Status: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:60]}")
    
    return []

def save_exercises(subtopic_id, questions):
    """Save exercises to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved = 0
    for i, q in enumerate(questions, 1):
        try:
            cursor.execute('''
                INSERT INTO exercises 
                (subtopic_id, question_num, question_text, options, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                subtopic_id,
                i,
                q.get('question', ''),
                json.dumps(q.get('options', {})),
                q.get('correct_answer', 'A'),
                q.get('explanation', '')
            ))
            saved += 1
        except Exception as e:
            print(f"    ⚠️ Error saving Q{i}: {e}")
    
    conn.commit()
    conn.close()
    return saved

def main():
    print("="*60)
    print("GENERATING BUSINESS STUDIES EXERCISES")
    print("Testing with first 10 topics")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Get first 10 processed Business Studies topics without exercises
    rows = conn.execute('''
        SELECT p.subtopic_id, p.html_content, p.summary
        FROM content_processed p
        WHERE p.subtopic_id LIKE "%business%"
        AND NOT EXISTS (
            SELECT 1 FROM exercises e 
            WHERE e.subtopic_id = p.subtopic_id
        )
        ORDER BY p.subtopic_id
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    print(f"\nGenerating for {len(rows)} topics\n")
    
    total_exercises = 0
    successful = 0
    
    for subtopic_id, html_content, summary in rows:
        print(f"\n📝 {subtopic_id}")
        print(f"   {summary[:60]}...")
        
        # Extract text from HTML
        text_content = re.sub(r'<[^>]+>', ' ', html_content)
        text_content = re.sub(r'\s+', ' ', text_content)
        
        # Generate
        print(f"   🎯 Generating 5 MCQs...")
        questions = generate_questions(subtopic_id, text_content, summary)
        
        if questions and len(questions) > 0:
            saved = save_exercises(subtopic_id, questions)
            print(f"   ✅ Saved {saved} exercises")
            total_exercises += saved
            successful += 1
        else:
            print(f"   ❌ Failed to generate")
        
        time.sleep(2)
    
    print("\n" + "="*60)
    print(f"✅ Generated {total_exercises} exercises for {successful}/{len(rows)} topics")
    print("="*60)
    
    if successful == 0:
        print("\n⚠️ Exercise generation failed!")
        print("Possible reasons:")
        print("  - nano-banana may not support text generation")
        print("  - API might need a different model")
        print("  - Need to use a dedicated text LLM")

if __name__ == "__main__":
    main()
