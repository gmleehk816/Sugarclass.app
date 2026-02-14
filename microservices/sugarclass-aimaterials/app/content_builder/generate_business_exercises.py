"""
Generate MCQ exercises for Business Studies
- Creates 5 questions per topic
- Uses nano-banana API
- Validates output
- Saves to exercises table
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

def generate_exercises(subtopic_id, content_text):
    """Generate 5 MCQ exercises using nano-banana"""
    session = requests.Session()
    session.mount('https://', SSLAdapter())
    
    prompt = f"""Create 5 multiple choice questions for IGCSE Business Studies based on this content:

{content_text[:1500]}

Format each question as:
Q1: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct: [A/B/C/D]
Explanation: [Why this is correct]

Make questions test understanding, not just memorization."""

    try:
        response = session.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",  # Use text model, not image model
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60,
            verify=False
        )
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            return parse_exercises(content)
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    return []

def parse_exercises(text):
    """Parse exercise text into structured format"""
    exercises = []
    
    # Split by question numbers
    questions = re.split(r'Q\d+:', text)
    
    for q_text in questions[1:]:  # Skip first empty split
        try:
            # Extract question
            q_match = re.search(r'^(.+?)\n[A-D]\)', q_text, re.DOTALL)
            if not q_match:
                continue
            question = q_match.group(1).strip()
            
            # Extract options
            options = {}
            for letter in ['A', 'B', 'C', 'D']:
                opt_match = re.search(rf'{letter}\)\s*(.+?)(?:\n[A-D]\)|\nCorrect:|\n\n|$)', q_text, re.DOTALL)
                if opt_match:
                    options[letter] = opt_match.group(1).strip()
            
            # Extract correct answer
            correct_match = re.search(r'Correct:\s*([A-D])', q_text)
            correct = correct_match.group(1) if correct_match else 'A'
            
            # Extract explanation
            exp_match = re.search(r'Explanation:\s*(.+?)(?:\n\n|$)', q_text, re.DOTALL)
            explanation = exp_match.group(1).strip() if exp_match else ''
            
            if question and len(options) == 4:
                exercises.append({
                    'question': question,
                    'options': options,
                    'correct': correct,
                    'explanation': explanation
                })
        except Exception as e:
            continue
    
    return exercises

def save_exercises(subtopic_id, exercises):
    """Save exercises to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved = 0
    for i, ex in enumerate(exercises, 1):
        try:
            cursor.execute('''
                INSERT INTO exercises 
                (subtopic_id, question_num, question_text, options, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                subtopic_id,
                i,
                ex['question'],
                json.dumps(ex['options']),
                ex['correct'],
                ex['explanation']
            ))
            saved += 1
        except Exception as e:
            print(f"    ⚠️ Error saving exercise {i}: {e}")
    
    conn.commit()
    conn.close()
    return saved

def main():
    print("="*60)
    print("GENERATING BUSINESS STUDIES EXERCISES")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Get processed Business Studies topics (limit to first 20 for now)
    rows = conn.execute('''
        SELECT p.subtopic_id, p.html_content, p.summary
        FROM content_processed p
        WHERE p.subtopic_id LIKE "%business%"
        AND NOT EXISTS (
            SELECT 1 FROM exercises e 
            WHERE e.subtopic_id = p.subtopic_id
        )
        ORDER BY p.subtopic_id
        LIMIT 20
    ''').fetchall()
    
    conn.close()
    
    print(f"\nGenerating exercises for {len(rows)} topics\n")
    
    total_exercises = 0
    
    for subtopic_id, html_content, summary in rows:
        print(f"\n📝 {subtopic_id}")
        print(f"   {summary[:60]}...")
        
        # Extract text from HTML
        text_content = re.sub(r'<[^>]+>', ' ', html_content)
        text_content = re.sub(r'\s+', ' ', text_content)[:2000]
        
        # Generate exercises
        print(f"   🎯 Generating 5 MCQs...")
        exercises = generate_exercises(subtopic_id, text_content)
        
        if exercises:
            saved = save_exercises(subtopic_id, exercises)
            print(f"   ✅ Saved {saved} exercises")
            total_exercises += saved
        else:
            print(f"   ❌ Failed to generate exercises")
        
        time.sleep(2)  # Rate limiting
    
    print("\n" + "="*60)
    print(f"✅ Generated {total_exercises} total exercises")
    print("="*60)

if __name__ == "__main__":
    main()
