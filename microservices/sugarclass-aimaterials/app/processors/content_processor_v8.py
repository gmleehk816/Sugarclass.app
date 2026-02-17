"""
V8 Content Processor - Complete Pipeline Replacement
====================================================
Replaces the old content_splitter.py with V8 architecture.

Pipeline:
1. Read markdown files (from PDF extraction)
2. Split into chapters and subtopics
3. Generate V8 content (concepts, SVGs, quiz, flashcards, images)
4. Store in new V8 database schema

Usage:
    python content_processor_v8.py --subject igcse_physics --file <markdown_path>
    python content_processor_v8.py --process-all
"""

import os
import re
import sys
import json
import hashlib
import time
import argparse
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
except ImportError:
    print("Error: requests module not found. Run: pip install requests")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_DIR = Path(__file__).parent.parent
PROJECT_ROOT = APP_DIR.parent
DB_PATH = Path(os.getenv("DB_PATH", APP_DIR / "database" / "rag_content.db"))
MARKDOWN_DIR = PROJECT_ROOT / "output/markdown"
API_CONFIG_PATH = PROJECT_ROOT.parent.parent / "coding/api/api.txt"

# Load settings from config_fastapi if available
try:
    from config_fastapi import settings
    base_url = settings.LLM_API_URL or os.getenv("LLM_API_URL", "https://hb.dockerspeeds.asia/v1")
    # Ensure URL ends with /chat/completions for OpenAI-compatible API
    if not base_url.endswith('/chat/completions'):
        base_url = base_url.rstrip('/') + '/chat/completions'
    API_BASE_URL = base_url
    API_KEY = settings.LLM_API_KEY or os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
    MODEL = settings.LLM_MODEL or os.getenv("LLM_MODEL", "gemini-2.5-flash")
except ImportError:
    base_url = os.getenv("LLM_API_URL", "https://hb.dockerspeeds.asia/v1")
    if not base_url.endswith('/chat/completions'):
        base_url = base_url.rstrip('/') + '/chat/completions'
    API_BASE_URL = base_url
    API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
    MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

REQUEST_INTERVAL = 6.0  # 10 requests per minute
MAX_RETRIES = 3
REQUEST_TIMEOUT = 120
RETRY_DELAY = 5.0  # Seconds to wait before retry

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SubtopicData:
    """Represents a subtopic with all its content"""
    topic_id: str
    subtopic_id: str          # e.g., '2.4'
    slug: str                 # e.g., 'calculating-speed-and-acceleration'
    name: str                 # e.g., 'Calculating Speed and Acceleration'
    order_num: int
    markdown_content: str
    source_file: str
    source_hash: str


@dataclass
class ConceptData:
    """Represents a V8 concept"""
    concept_key: str          # e.g., 'speed_calculation'
    title: str                # e.g., 'Calculating Average Speed'
    description: str          # For SVG generation
    icon: str                 # Emoji
    order_num: int


# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Handle all database operations for V8 schema"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_subject_id(self, subject_code: str) -> Optional[int]:
        """Get subject ID by code"""
        cur = self.conn.execute(
            "SELECT id FROM subjects WHERE subject_id = ?",
            (subject_code,)
        )
        row = cur.fetchone()
        return row['id'] if row else None

    def get_topic_id(self, subject_id: int, topic_code: str) -> Optional[int]:
        """Get topic ID by subject and topic code"""
        cur = self.conn.execute(
            "SELECT id FROM topics WHERE subject_id = ? AND topic_id = ?",
            (subject_id, topic_code)
        )
        row = cur.fetchone()
        return row['id'] if row else None

    def create_subtopic(self, data: SubtopicData, topic_id: int) -> int:
        """Create a new subtopic and return its ID"""
        cur = self.conn.execute("""
            INSERT INTO subtopics (topic_id, subtopic_id, slug, name, order_num, markdown_file_path, source_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            topic_id,
            data.subtopic_id,
            data.slug,
            data.name,
            data.order_num,
            data.source_file,
            data.source_hash
        ))
        self.conn.commit()
        return cur.lastrowid

    def save_concepts(self, subtopic_id: int, concepts: List[ConceptData]):
        """Save concepts to database"""
        for concept in concepts:
            cur = self.conn.execute("""
                INSERT INTO v8_concepts (subtopic_id, concept_key, title, description, icon, order_num)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                subtopic_id,
                concept.concept_key,
                concept.title,
                concept.description,
                concept.icon,
                concept.order_num
            ))
            concept_id = cur.lastrowid

            # Create placeholder for generated content
            self.conn.execute("""
                INSERT INTO v8_generated_content (concept_id, content_type, content)
                VALUES (?, ?, ?)
            """, (concept_id, 'placeholder', 'Pending generation'))

        self.conn.commit()

    def save_quiz_question(self, subtopic_id: int, question_num: int, question: Dict):
        """Save a quiz question"""
        self.conn.execute("""
            INSERT INTO v8_quiz_questions
            (subtopic_id, question_num, question_text, options, correct_answer, explanation, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            subtopic_id,
            question_num,
            question.get('question'),
            json.dumps(question.get('options', {})),
            question.get('correct'),
            question.get('explanation'),
            question.get('difficulty', 'medium')
        ))
        self.conn.commit()

    def save_flashcard(self, subtopic_id: int, card_num: int, front: str, back: str):
        """Save a flashcard"""
        self.conn.execute("""
            INSERT INTO v8_flashcards (subtopic_id, card_num, front, back)
            VALUES (?, ?, ?, ?)
        """, (subtopic_id, card_num, front, back))
        self.conn.commit()

    def save_reallife_image(self, subtopic_id: int, image_type: str, image_url: str,
                           prompt: str, title: str, description: str):
        """Save a real-life image"""
        self.conn.execute("""
            INSERT INTO v8_reallife_images (subtopic_id, image_type, image_url, prompt, title, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (subtopic_id, image_type, image_url, prompt, title, description))
        self.conn.commit()

    def save_learning_objective(self, subtopic_id: int, objective: str, order_num: int):
        """Save a learning objective"""
        self.conn.execute("""
            INSERT INTO v8_learning_objectives (subtopic_id, objective_text, order_num)
            VALUES (?, ?, ?)
        """, (subtopic_id, objective, order_num))
        self.conn.commit()

    def save_key_term(self, subtopic_id: int, term: str, definition: str, order_num: int):
        """Save a key term"""
        self.conn.execute("""
            INSERT INTO v8_key_terms (subtopic_id, term, definition, order_num)
            VALUES (?, ?, ?, ?)
        """, (subtopic_id, term, definition, order_num))
        self.conn.commit()

    def save_formula(self, subtopic_id: int, formula: str, description: str, order_num: int):
        """Save a formula"""
        self.conn.execute("""
            INSERT INTO v8_formulas (subtopic_id, formula, description, order_num)
            VALUES (?, ?, ?, ?)
        """, (subtopic_id, formula, description, order_num))
        self.conn.commit()

    def mark_subtopic_processed(self, subtopic_id: int):
        """Mark subtopic as processed"""
        self.conn.execute("""
            UPDATE subtopics SET processed_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (subtopic_id,))
        self.conn.commit()

    def get_concepts(self, subtopic_id: int) -> List[Dict]:
        """Get all concepts for a subtopic"""
        cur = self.conn.execute("""
            SELECT id, concept_key, title, description, icon, order_num
            FROM v8_concepts WHERE subtopic_id = ? ORDER BY order_num
        """, (subtopic_id,))
        return [dict(row) for row in cur.fetchall()]

    def update_generated_content(self, concept_id: int, content_type: str, content: str):
        """Update or insert generated content for a concept"""
        # Try to update existing row
        cursor = self.conn.execute("""
            UPDATE v8_generated_content
            SET content = ?, generated_at = CURRENT_TIMESTAMP
            WHERE concept_id = ? AND content_type = ?
        """, (content, concept_id, content_type))

        # If no row was updated, insert a new one
        if cursor.rowcount == 0:
            self.conn.execute("""
                INSERT INTO v8_generated_content (concept_id, content_type, content)
                VALUES (?, ?, ?)
            """, (concept_id, content_type, content))

        self.conn.commit()


# ============================================================================
# MARKDOWN PARSER
# ============================================================================

class MarkdownParser:
    """Parse markdown files into structured content"""

    def __init__(self, markdown_path: Path):
        self.markdown_path = markdown_path
        self.content = ""
        self.source_hash = ""

    def read(self) -> str:
        """Read markdown file and calculate hash"""
        with open(self.markdown_path, 'r', encoding='utf-8', errors='ignore') as f:
            self.content = f.read()

        # Calculate MD5 hash
        with open(self.markdown_path, 'rb') as f:
            self.source_hash = hashlib.md5(f.read()).hexdigest()

        return self.content

    def extract_learning_objectives(self) -> List[str]:
        """Extract learning objectives from markdown"""
        objectives = []

        match = re.search(
            r'(?:learning objectives|objectives|aims)(?::|\n)(.+?)(?:\n#|\n\n\n|$)',
            self.content,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            obj_text = match.group(1)
            for line in obj_text.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line):
                    obj = re.sub(r'^[-*\d.\s]+', '', line).strip()
                    if obj and len(obj) > 10:
                        objectives.append(obj)

        return objectives if objectives else ["Understand key concepts"]

    def extract_key_terms(self) -> List[Tuple[str, str]]:
        """Extract key terms and definitions"""
        terms = []

        for match in re.finditer(r'\*\*(\w+(?:\s+\w+)*)\*\*[\s\-–—]+([^\n]+)', self.content):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if term and definition and len(definition) > 10:
                terms.append((term, definition))

        return terms[:15]

    def extract_formulas(self) -> List[Tuple[str, str]]:
        """Extract formulas"""
        formulas = []

        for match in re.finditer(r'([A-Za-z\s]+)\s*=\s*([^\n]+)', self.content):
            formula = match.group(0).strip()
            if any(char in formula for char in '+-*/=') and len(formula) > 5:
                # Try to extract description from formula
                lhs = match.group(1).strip()
                rhs = match.group(2).strip()
                formulas.append((formula, f"{lhs} equals {rhs}"))

        return formulas[:10]


# ============================================================================
# SPLITTER (Chapter/Subtopic Detection)
# ============================================================================

class ContentSplitter:
    """Split markdown into chapters and subtopics"""

    # Patterns for different textbook formats
    CHAPTER_PATTERNS = [
        r'^#\s+(Chapter\s*\d+[:\s].+)$',          # # Chapter 1: Title
        r'^#\s+([A-Z]\d+)\s+(.+)$',              # # P1 Describing Motion
        r'^#\s+(\d+)\.\s+(.+)$',                 # # 1. Title
        r'^\*\*(\d+)\.\s+([^*]+)\*\*$',          # **1. Title**
        r'^#\s+([^#\n]+)$',                      # # Any Header 1 (Generic Fallback)
    ]

    SUBTOPIC_PATTERNS = [
        r'^\*\*(\d+\.\d+)\*\*\s+(.+)$',          # **2.4** Calculating Speed
        r'^##\s+(\d+\.\d+)\s+(.+)$',             # ## 2.4 Calculating Speed
        r'^(\d+\.\d+)\s+(.+)$',                  # 2.4 Calculating Speed
        r'^([A-Z]\d+\.\d+)\s+(.+)$',             # P1.1 Describing Motion
        r'^##\s+([^#\n]+)$',                     # ## Any Header 2 (Generic Fallback)
    ]

    def __init__(self, markdown_content: str):
        self.content = markdown_content
        self.chapters = []
        self.subtopics = []

    def split(self) -> List[Dict]:
        """Split content into subtopics"""
        lines = self.content.split('\n')

        current_chapter = None
        current_subtopic = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line: continue
            # Check for chapter headers
            chapter_match = self._match_chapter(line)
            if chapter_match:
                # Save previous subtopic if exists
                if current_subtopic:
                    self._save_subtopic(current_subtopic, current_content)
                
                # Start new chapter tracking
                current_chapter = chapter_match
                current_subtopic = None
                current_content = []
                continue

            # Check for subtopic headers
            subtopic_match = self._match_subtopic(line)
            if subtopic_match:
                # Save previous subtopic
                if current_subtopic:
                    self._save_subtopic(current_subtopic, current_content)

                current_subtopic = subtopic_match
                current_content = []
                continue

            # Add content line
            if current_subtopic:
                current_content.append(line)
            elif current_chapter and not current_subtopic:
                # If we are in a chapter but haven't hit a subtopic header yet,
                # we don't save the content as a "subtopic" yet, but we allow
                # the loop to continue searching.
                pass

        # Save last subtopic
        if current_subtopic:
            self._save_subtopic(current_subtopic, current_content)

        return self.subtopics

    def _match_chapter(self, line: str) -> Optional[Dict]:
        """Check if line matches chapter pattern"""
        for pattern in self.CHAPTER_PATTERNS:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    num = groups[0]
                    title = groups[1]
                else:
                    num = "1" # Default
                    title = groups[0]
                
                return {
                    'num': num,
                    'title': title.strip(),
                    'type': 'chapter'
                }
        return None

    def _match_subtopic(self, line: str) -> Optional[Dict]:
        """Check if line matches subtopic pattern"""
        for pattern in self.SUBTOPIC_PATTERNS:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    num = groups[0]
                    title = groups[1]
                else:
                    # Generic H2 pattern
                    num = "" # No number
                    title = groups[0]
                
                # Create slug from title
                slug_base = title if title else (num if num else "subtopic")
                slug = re.sub(r'[^\w\s-]', '', slug_base).strip().lower()
                slug = re.sub(r'[-\s]+', '-', slug)
                return {
                    'num': num,
                    'title': title.strip(),
                    'slug': slug,
                    'type': 'subtopic'
                }
        return None

    def _save_subtopic(self, subtopic: Dict, content: List[str]):
        """Save subtopic with its content"""
        self.subtopics.append({
            **subtopic,
            'content': '\n'.join(content).strip()
        })


# ============================================================================
# GEMINI API CLIENT
# ============================================================================

class GeminiClient:
    """Gemini API client with rate limiting"""

    def __init__(self, api_key: str, model: str = MODEL):
        self.api_key = api_key
        self.model = model
        self.last_request_time = 0
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def _wait_for_rate_limit(self):
        """Wait to respect rate limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < REQUEST_INTERVAL:
            wait_time = REQUEST_INTERVAL - time_since_last
            print(f"    [RATE LIMIT] Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def generate(self, prompt: str, timeout: int = 120) -> Optional[str]:
        """Generate content from Gemini API"""
        request_data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._wait_for_rate_limit()

                response = requests.post(
                    API_BASE_URL,
                    headers=self.headers,
                    json=request_data,
                    timeout=timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]

                elif response.status_code == 429:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    print(f"    [ERROR] HTTP {response.status_code}")
                    return None

            except Exception as e:
                print(f"    [ERROR] {str(e)}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                return None

        return None

    def analyze_structure(self, content: str) -> Optional[List[Dict]]:
        """Analyze content and identify key concepts"""
        prompt = f"""You are an educational content analyzer. Analyze this content and identify 6-8 key concepts that would benefit from visual diagrams/SVGs.

Content:
{content[:12000]}

TASK: Identify 6-8 key concepts. For each concept, provide:
1. A short ID (lowercase, underscores, e.g., "speed_calculation")
2. A title (e.g., "Calculating Average Speed")
3. A brief description for SVG generation
4. An icon emoji

Return ONLY valid JSON in this exact format:
{{
  "concepts": [
    {{
      "id": "speed_calculation",
      "title": "Calculating Average Speed",
      "description": "Diagram showing distance-time graph with slope representing speed",
      "icon": "📈"
    }}
  ]
}}

Focus on concepts that are visually representable and core to understanding."""

        result = self.generate(prompt)
        if result:
            try:
                json_match = re.search(r'\{[\s\S]*\}', result)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return data.get('concepts', [])
            except json.JSONDecodeError:
                print("    Failed to parse structure JSON")
        return None

    def generate_svg(self, title: str, description: str) -> Optional[str]:
        """Generate SVG diagram"""
        prompt = f"""Create an ANIMATED SVG diagram for physics education.

**Topic: {title}**

**Description: {description}**

Requirements:
1. SVG viewBox="0 0 500 350"
2. Include CSS animations embedded in <style> tag
3. Use smooth, educational animations
4. Color scheme:
   - Primary: #be123c (rose)
   - Secondary: #0369a1 (physics blue)
   - Accent: #10B981 (green)
   - Background: #F9F9F9
5. Include proper labels
6. Add title at top
7. Use Inter, system-ui font family
8. Physics-specific: Show vectors, arrows, motion paths

Return ONLY the SVG code (no markdown)."""

        return self.generate(prompt)

    def generate_bullets(self, title: str, description: str, full_content: str) -> Optional[str]:
        """Generate PowerPoint-style bullets"""
        prompt = f"""Generate PowerPoint-style bullet points for this concept.

CONCEPT: {title}
DESCRIPTION: {description}

SOURCE CONTENT:
{full_content[:8000]}

REQUIREMENTS:
1. Create 5-8 clear bullet points
2. Each bullet should be ONE clear fact (1-2 lines max)
3. Use simple, direct language
4. Include key terminology
5. Start each bullet with an appropriate emoji
6. Use <strong> tags for important terms
7. Make it scannable

Example format:
- 📏 <strong>Speed formula:</strong> speed = distance ÷ time

Output ONLY the bullet points as HTML <li> tags (no <ul> wrapper)."""

        return self.generate(prompt)

    def generate_quiz(self, topic: str, content: str, num_questions: int = 5) -> Optional[Dict]:
        """Generate quiz questions"""
        prompt = f"""Create a multiple-choice quiz.

**Topic: {topic}**

**Content:**
{content[:3000]}

Requirements:
1. Generate {num_questions} questions
2. Each question has 4 options (A, B, C, D)
3. Include explanation for correct answer
4. Vary difficulty (2 easy, 2 medium, 1 hard)

Return ONLY valid JSON:
{{
  "quiz_title": "Quiz title",
  "questions": [
    {{
      "id": 1,
      "question": "Question text?",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct": "B",
      "explanation": "Explanation",
      "difficulty": "easy"
    }}
  ]
}}"""

        result = self.generate(prompt)
        if result:
            try:
                result = re.sub(r'```json\n?', '', result)
                result = re.sub(r'```\n?', '', result)
                return json.loads(result)
            except json.JSONDecodeError:
                print("    Warning: Failed to parse quiz JSON")
        return None

    def generate_flashcards(self, topic: str, content: str, num_cards: int = 8) -> Optional[Dict]:
        """Generate flashcards"""
        prompt = f"""Create educational flashcards.

**Topic: {topic}**

**Content:**
{content[:3000]}

Requirements:
1. Generate {num_cards} flashcards
2. Front: Term, concept, or question (concise)
3. Back: Definition, explanation, or answer (1-2 sentences)
4. Include formulas where relevant

Return ONLY valid JSON:
{{
  "deck_title": "Flashcards title",
  "cards": [
    {{
      "id": 1,
      "front": "What is speed?",
      "back": "Distance traveled per unit time. Formula: speed = distance/time"
    }}
  ]
}}"""

        result = self.generate(prompt)
        if result:
            try:
                result = re.sub(r'```json\n?', '', result)
                result = re.sub(r'```\n?', '', result)
                return json.loads(result)
            except json.JSONDecodeError:
                print("    Warning: Failed to parse flashcard JSON")
        return None


# ============================================================================
# V8 CONTENT GENERATOR
# ============================================================================

class V8ContentGenerator:
    """Generate all V8 content for a subtopic"""

    def __init__(self, gemini_client: GeminiClient, db: DatabaseManager):
        self.gemini = gemini_client
        self.db = db

    def generate_full_content(self, subtopic_id: int, markdown_content: str, topic_name: str):
        """Generate all V8 content for a subtopic"""

        print(f"\n[GENERATOR] Generating V8 content for subtopic {subtopic_id}...")

        # Step 1: Analyze structure
        print("\n  Step 1: Analyzing structure...")
        concepts = self.gemini.analyze_structure(markdown_content)

        if not concepts:
            # Use fallback
            concepts = self._get_fallback_concepts(topic_name)

        print(f"    Found {len(concepts)} concepts")

        # Save concepts to database
        for i, concept_data in enumerate(concepts):
            concept = ConceptData(
                concept_key=concept_data.get('id', f'concept_{i}'),
                title=concept_data.get('title', 'Concept'),
                description=concept_data.get('description', ''),
                icon=concept_data.get('icon', '📚'),
                order_num=i
            )
            self.db.save_concepts(subtopic_id, [concept])

        # Get saved concepts with IDs
        saved_concepts = self.db.get_concepts(subtopic_id)

        # Step 2: Generate SVGs and bullets for each concept
        print(f"\n  Step 2: Generating SVGs and content for {len(saved_concepts)} concepts...")
        for concept in saved_concepts:
            print(f"    Concept: {concept['title']}")

            # Generate SVG
            svg = self.gemini.generate_svg(concept['title'], concept['description'])
            if svg:
                self.db.update_generated_content(concept['id'], 'svg', svg)
                print(f"      ✓ SVG generated")
            else:
                print(f"      ✗ SVG failed")

            # Generate bullets
            bullets = self.gemini.generate_bullets(
                concept['title'],
                concept['description'],
                markdown_content
            )
            if bullets:
                self.db.update_generated_content(concept['id'], 'bullets', bullets)
                print(f"      ✓ Bullets generated")
            else:
                print(f"      ✗ Bullets failed")

            # Rate limiting between concepts
            time.sleep(REQUEST_INTERVAL)

        # Step 3: Generate quiz
        print(f"\n  Step 3: Generating quiz...")
        quiz = self.gemini.generate_quiz(topic_name, markdown_content, 5)
        if quiz and quiz.get('questions'):
            for i, q in enumerate(quiz['questions'], 1):
                self.db.save_quiz_question(subtopic_id, i, q)
            print(f"    ✓ Generated {len(quiz['questions'])} questions")
        else:
            print(f"    ✗ Quiz generation failed")

        # Step 4: Generate flashcards
        print(f"\n  Step 4: Generating flashcards...")
        flashcards = self.gemini.generate_flashcards(topic_name, markdown_content, 8)
        if flashcards and flashcards.get('cards'):
            for i, card in enumerate(flashcards['cards'], 1):
                self.db.save_flashcard(
                    subtopic_id,
                    i,
                    card.get('front', ''),
                    card.get('back', '')
                )
            print(f"    ✓ Generated {len(flashcards['cards'])} cards")
        else:
            print(f"    ✗ Flashcard generation failed")

        # Mark as processed
        self.db.mark_subtopic_processed(subtopic_id)
        print(f"\n  ✓ V8 content generation complete!")

    def _get_fallback_concepts(self, topic_name: str) -> List[Dict]:
        """Fallback concepts if AI analysis fails"""
        return [
            {
                "id": "concept_1",
                "title": f"Introduction to {topic_name}",
                "description": "Diagram showing basic concepts and setup",
                "icon": "📚"
            },
            {
                "id": "concept_2",
                "title": "Key Principles",
                "description": "Diagram illustrating main principles",
                "icon": "🎯"
            },
            {
                "id": "concept_3",
                "title": "Applications",
                "description": "Real-world application examples",
                "icon": "⚡"
            }
        ]


# ============================================================================
# MAIN PROCESSOR
# ============================================================================

class V8Processor:
    """Main V8 content processor"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db = DatabaseManager(db_path)
        self.db.connect()

        # Load API key
        self.api_key = self._load_api_key()
        self.gemini = GeminiClient(self.api_key) if self.api_key else None
        self.generator = V8ContentGenerator(self.gemini, self.db) if self.gemini else None

    def _load_api_key(self) -> Optional[str]:
        """Load API key from environment or config file"""
        # First check module-level API_KEY (loaded from settings/env)
        if API_KEY:
            return API_KEY

        # Then check environment directly
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")

        if not api_key and API_CONFIG_PATH.exists():
            with open(API_CONFIG_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('key:'):
                        return line.split(':', 1)[1].strip()

        return api_key

    def process_markdown_file(self, markdown_path: Path, subject_code: str, topic_code: str):
        """Process a single markdown file"""
        print(f"\n{'='*70}")
        print(f"PROCESSING: {markdown_path.name}")
        print(f"{'='*70}")

        # Get subject and topic IDs
        subject_id = self.db.get_subject_id(subject_code)
        if not subject_id:
            print(f"Error: Subject '{subject_code}' not found in database")
            return False

        topic_id = self.db.get_topic_id(subject_id, topic_code)
        if not topic_id:
            print(f"Error: Topic '{topic_code}' not found in database")
            return False

        # Read and parse markdown
        parser = MarkdownParser(markdown_path)
        markdown_content = parser.read()

        # Split into subtopics
        splitter = ContentSplitter(markdown_content)
        subtopic_data = splitter.split()

        print(f"\n[SPLITTER] Found {len(subtopic_data)} subtopics")

        # Process each subtopic
        for i, subtopic in enumerate(subtopic_data, 1):
            print(f"\n[{i}/{len(subtopic_data)}] Processing: {subtopic['title']}")

            # Create subtopic data
            data = SubtopicData(
                topic_id=topic_code,
                subtopic_id=subtopic['num'],
                slug=subtopic['slug'],
                name=subtopic['title'],
                order_num=i,
                markdown_content=subtopic['content'],
                source_file=str(markdown_path),
                source_hash=parser.source_hash
            )

            # Save subtopic to database
            subtopic_db_id = self.db.create_subtopic(data, topic_id)
            print(f"  → Created subtopic with ID: {subtopic_db_id}")

            # Extract and save learning objectives
            objectives = parser.extract_learning_objectives()
            for j, obj in enumerate(objectives, 1):
                self.db.save_learning_objective(subtopic_db_id, obj, j)
            print(f"  → Saved {len(objectives)} learning objectives")

            # Extract and save key terms
            terms = parser.extract_key_terms()
            for j, (term, definition) in enumerate(terms, 1):
                self.db.save_key_term(subtopic_db_id, term, definition, j)
            print(f"  → Saved {len(terms)} key terms")

            # Extract and save formulas
            formulas = parser.extract_formulas()
            for j, (formula, description) in enumerate(formulas, 1):
                self.db.save_formula(subtopic_db_id, formula, description, j)
            print(f"  → Saved {len(formulas)} formulas")

            # Generate V8 content if API is available
            if self.generator:
                self.generator.generate_full_content(
                    subtopic_db_id,
                    subtopic['content'],
                    subtopic['title']
                )
            else:
                print("  ⚠ Skipping V8 content generation (no API key)")

        return True

    def close(self):
        """Close database connection"""
        self.db.close()


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="V8 Content Processor - Complete Pipeline Replacement"
    )
    parser.add_argument("--subject", type=str, default="igcse_physics_0625",
                       help="Subject code (e.g., igcse_physics_0625)")
    parser.add_argument("--topic", type=str, required=True,
                       help="Topic code (e.g., P1, P2, 2)")
    parser.add_argument("--file", type=str, required=True,
                       help="Path to markdown file")
    parser.add_argument("--db", type=str,
                       help="Custom database path")

    args = parser.parse_args()

    db_path = Path(args.db) if args.db else DB_PATH
    markdown_path = Path(args.file)

    if not markdown_path.exists():
        print(f"Error: File not found: {markdown_path}")
        sys.exit(1)

    processor = V8Processor(db_path)

    try:
        success = processor.process_markdown_file(
            markdown_path,
            args.subject,
            args.topic
        )

        if success:
            print(f"\n{'='*70}")
            print("✓ PROCESSING COMPLETE!")
            print(f"{'='*70}")
        else:
            print("\n✗ Processing failed")
            sys.exit(1)

    finally:
        processor.close()


if __name__ == "__main__":
    main()
