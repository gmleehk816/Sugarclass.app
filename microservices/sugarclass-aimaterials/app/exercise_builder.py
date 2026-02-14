"""
Exercise Builder - Generate multiple choice questions with AI images
Uses nano-banana API to create questions and images for each subtopic
"""
import sqlite3
import requests
import json
import re
import os
import time
from pathlib import Path
from PIL import Image
from io import BytesIO

# Configuration
APP_DIR = Path(__file__).parent
DB_PATH = Path(os.getenv("DB_PATH", APP_DIR / "rag_content.db"))
EXERCISE_IMAGES_DIR = Path(__file__).parent / "exercise_images"
EXERCISE_IMAGES_DIR.mkdir(exist_ok=True)

# Use same API settings as content_rewriter_with_images.py
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get("LLM_API_KEY", os.environ.get("NANO_BANANA_API_KEY", ""))
API_URL = os.environ.get("LLM_API_URL", os.environ.get("NANO_BANANA_API_URL", "https://newapi.pockgo.com/v1/chat/completions"))
if API_URL and not API_URL.endswith('/chat/completions'):
    API_URL = API_URL.rstrip('/') + '/chat/completions'
TEXT_MODEL = os.environ.get("LLM_MODEL", "nano-banana")
IMAGE_MODEL = os.environ.get("LLM_IMAGE_MODEL", "nano-banana")


def get_subtopic_content(subtopic_id, db_path=None):
    """Get raw content for a subtopic"""
    effective_db_path = db_path if db_path else DB_PATH
    conn = sqlite3.connect(str(effective_db_path))
    conn.row_factory = sqlite3.Row
    
    row = conn.execute("""
        SELECT s.id, s.name, s.topic_id, cr.markdown_content, t.name as topic_name, t.type
        FROM subtopics s
        LEFT JOIN content_raw cr ON cr.subtopic_id = s.id
        LEFT JOIN topics t ON t.id = s.topic_id
        WHERE s.id = ?
    """, (subtopic_id,)).fetchone()
    
    conn.close()
    return dict(row) if row else None


def generate_questions(subtopic_data, count=5, max_retries=3):
    """Generate multiple choice questions using AI"""
    content = subtopic_data['markdown_content'] or ''
    name = subtopic_data['name']
    topic_type = subtopic_data['type'] or 'Science'
    
    prompt = f"""Based on this {topic_type} content about "{name}", create exactly {count} multiple choice questions.

CONTENT:
{content[:8000]}

REQUIREMENTS:
1. Each question should test understanding of key concepts
2. Each question has 4 options (A, B, C, D)
3. Only ONE correct answer per question
4. Include a brief explanation for the correct answer
5. Questions should range from easy to challenging

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
      "explanation": "Brief explanation of why B is correct",
      "image_prompt": "A simple educational diagram showing [specific concept] for students"
    }}
  ]
}}

Generate exactly {count} questions in valid JSON format."""

    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": TEXT_MODEL,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get('questions', [])
            else:
                print(f"  ⚠️ API error: {response.status_code}, retrying...")
                
        except Exception as e:
            print(f"  ⚠️ Attempt {attempt + 1}/{max_retries} failed: {str(e)[:50]}...")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
    
    print(f"  ❌ Failed after {max_retries} attempts")
    return []


def generate_image(prompt, filename, max_retries=2):
    """Generate an educational image using nano-banana"""
    print(f"  🎨 Generating image: {prompt[:50]}...")
    
    # Prepend "Generate an image:" to trigger image generation
    full_prompt = f"Generate an image: {prompt}"
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": IMAGE_MODEL,
                    "messages": [{"role": "user", "content": full_prompt}]
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract image URL from markdown format
                match = re.search(r'!\[.*?\]\((https://[^)]+)\)', content)
                if match:
                    url = match.group(1)
                    
                    # Download and save
                    img_response = requests.get(url, timeout=30)
                    if img_response.status_code == 200:
                        img_path = EXERCISE_IMAGES_DIR / filename
                        
                        # Save image
                        img = Image.open(BytesIO(img_response.content))
                        if img.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[-1])
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        img.save(img_path, 'JPEG', quality=90)
                        print(f"  ✅ Saved: {filename}")
                        return filename
            else:
                print(f"  ⚠️ Image API error: {response.status_code}")
                    
        except Exception as e:
            print(f"  ⚠️ Image attempt {attempt + 1}/{max_retries} failed: {str(e)[:40]}...")
            if attempt < max_retries - 1:
                time.sleep(3)
    
    return None


def save_exercises_to_db(subtopic_id, questions, topic_id=None, db_path=None):
    """Save generated exercises to database"""
    effective_db_path = db_path if db_path else DB_PATH
    conn = sqlite3.connect(str(effective_db_path))
    
    # Create exercises table if not exists (with topic_id for compatibility)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id TEXT NOT NULL,
            topic_id TEXT,
            question_num INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            image_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(subtopic_id, question_num)
        )
    """)
    
    # Delete existing exercises for this subtopic
    conn.execute("DELETE FROM exercises WHERE subtopic_id = ?", (subtopic_id,))
    
    # Insert new exercises
    for i, q in enumerate(questions, 1):
        conn.execute("""
            INSERT INTO exercises (subtopic_id, topic_id, question_num, question_text, options, correct_answer, explanation, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            subtopic_id,
            topic_id,
            i,
            q['question'],
            json.dumps(q['options']),
            q['correct_answer'],
            q.get('explanation', ''),
            q.get('image_path')
        ))
    
    conn.commit()
    conn.close()
    print(f"  💾 Saved {len(questions)} exercises to database")


def build_exercises_for_subtopic(subtopic_id, generate_images=True, count=5, db_path=None):
    """Build exercises for a single subtopic"""
    global DB_PATH
    if db_path:
        DB_PATH = Path(db_path)
    print(f"\n📚 Building exercises for {subtopic_id}...")
    
    # Get content
    data = get_subtopic_content(subtopic_id, db_path=DB_PATH)
    if not data or not data.get('markdown_content'):
        print(f"  ⚠️ No content found for {subtopic_id}")
        return False
    
    print(f"  📖 Topic: {data['name']}")
    print(f"  📄 Content: {len(data['markdown_content'])} chars")
    
    # Generate questions
    print(f"  🤖 Generating {count} questions...")
    questions = generate_questions(data, count=count)
    
    if not questions:
        print("  ❌ Failed to generate questions")
        return False
    
    print(f"  ✅ Generated {len(questions)} questions")
    
    # Generate images for each question
    if generate_images:
        for i, q in enumerate(questions, 1):
            if q.get('image_prompt'):
                filename = f"{subtopic_id.replace('/', '_')}_q{i}.jpg"
                img_path = generate_image(q['image_prompt'], filename)
                q['image_path'] = img_path
                time.sleep(2)  # Rate limiting
    
    # Save to database (include topic_id from subtopic data)
    topic_id = data.get('topic_id')
    save_exercises_to_db(subtopic_id, questions, topic_id=topic_id, db_path=DB_PATH)
    
    return True


def main():
    """Build exercises for C1.01, C1.02, C1.03"""
    print("🏗️ Exercise Builder")
    print("=" * 50)
    
    # Target subtopics (Chemistry 0620)
    subtopics = [
        "chemistry_0620_C1.01",
        "chemistry_0620_C1.02", 
        "chemistry_0620_C1.03"
    ]
    
    for subtopic_id in subtopics:
        success = build_exercises_for_subtopic(subtopic_id, generate_images=True)
        if success:
            print(f"  ✅ Completed {subtopic_id}")
        else:
            print(f"  ❌ Failed {subtopic_id}")
        
        time.sleep(3)  # Rate limiting between subtopics
    
    # Show summary
    print("\n" + "=" * 50)
    print("📊 Summary")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Check if table exists
    table_exists = conn.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='exercises'
    """).fetchone()
    
    if table_exists:
        rows = conn.execute("""
            SELECT subtopic_id, COUNT(*) as cnt, 
                   SUM(CASE WHEN image_path IS NOT NULL THEN 1 ELSE 0 END) as with_images
            FROM exercises 
            GROUP BY subtopic_id
        """).fetchall()
        
        for r in rows:
            print(f"  {r[0]}: {r[1]} questions, {r[2]} with images")
    else:
        print("  No exercises generated yet")
    
    conn.close()


if __name__ == "__main__":
    main()
