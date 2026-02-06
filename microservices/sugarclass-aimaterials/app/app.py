import os
import sqlite3
import json
import re
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from debug_utils import setup_debug_routes, log_api_call

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for all routes

# Setup debug routes for Chrome DevTools
setup_debug_routes(app)

# Serve debug helper page
@app.route('/debug_helper.html')
def debug_helper_page():
    """Serve the Chrome DevTools helper page"""
    return send_from_directory(BASE_DIR, 'debug_helper.html')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'rag_content.db')  # Shared DB in project/database

# Note: Image handling removed - all content now served from RAG database
# No longer using materials_output or output folders

# SVG Content for B2.01 (copied from server.js logic)
B201_SVG = """
<div class="border border-slate-200 rounded-lg p-4 bg-white shadow-sm my-4">
    <svg viewBox="0 0 400 150" xmlns="http://www.w3.org/2000/svg" class="w-full rounded">
        <rect width="400" height="150" fill="#f8fafc" rx="8" />
        <g id="high-conc">
            <circle cx="50" cy="30" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="65" cy="45" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="40" cy="60" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="80" cy="35" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="55" cy="80" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="30" cy="95" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="70" cy="70" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="90" cy="50" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="45" cy="110" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="75" cy="100" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="60" cy="125" r="6" fill="#3b82f6" opacity="0.8" />
            <circle cx="95" cy="115" r="6" fill="#3b82f6" opacity="0.8" />
            <text x="65" y="140" font-family="sans-serif" font-size="12" fill="#1e3a8a" text-anchor="middle" font-weight="bold">High Conc.</text>
        </g>
        <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
            </marker>
        </defs>
        <line x1="130" y1="75" x2="250" y2="75" stroke="#64748b" stroke-width="3" marker-end="url(#arrowhead)" stroke-dasharray="5,5" />
        <text x="190" y="65" font-family="sans-serif" font-size="12" fill="#64748b" text-anchor="middle">Net Movement</text>
        <g id="low-conc">
            <circle cx="300" cy="40" r="6" fill="#3b82f6" opacity="0.6" />
            <circle cx="350" cy="90" r="6" fill="#3b82f6" opacity="0.6" />
            <circle cx="320" cy="120" r="6" fill="#3b82f6" opacity="0.6" />
            <circle cx="280" cy="80" r="6" fill="#3b82f6" opacity="0.6" />
            <text x="315" y="140" font-family="sans-serif" font-size="12" fill="#1e3a8a" text-anchor="middle" font-weight="bold">Low Conc.</text>
        </g>
    </svg>
    <p class="text-xs text-slate-500 mt-2 text-center">Figure B2.01 - Diffusion: Movement down a concentration gradient</p>
</div>
"""

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Note: Image serving routes removed - content is now served from RAG database
# Images are embedded or referenced in the database content directly

# AI-generated educational images directory
GENERATED_IMAGES_DIR = os.path.join(BASE_DIR, 'generated_images')
STATIC_GENERATED_IMAGES_DIR = os.path.join(BASE_DIR, 'static', 'generated_images')
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)
os.makedirs(STATIC_GENERATED_IMAGES_DIR, exist_ok=True)

@app.route('/generated_images/<path:filename>')
def serve_generated_images(filename):
    """Serve AI-generated educational images"""
    # Try static folder first
    static_path = os.path.join(STATIC_GENERATED_IMAGES_DIR, filename)
    if os.path.exists(static_path):
        return send_from_directory(STATIC_GENERATED_IMAGES_DIR, filename)
    return send_from_directory(GENERATED_IMAGES_DIR, filename)

@app.route('/static/generated_images/<path:filename>')
def serve_static_generated_images(filename):
    """Serve AI-generated educational images from static folder"""
    return send_from_directory(STATIC_GENERATED_IMAGES_DIR, filename)

# Serve Q&A images from past papers
# Make path configurable via environment variable
QA_IMAGES_DIR = os.environ.get('QA_IMAGES_PATH') or \
    os.path.join(BASE_DIR, '..', 'output', 'materials_output', 'cie igcse', 
                 'Combined Science (0653)', 'Past_Papers_by_topics',
                 'Cambridge_IGCSE_Science Coordinate(0654)_COORDINATED SCIENCES P2_2017-2023_Password_Removed',
                 'vlm', 'images')

@app.route('/qa_images/<path:filename>')
def serve_qa_images(filename):
    """Serve Q&A images from past papers"""
    if os.path.exists(QA_IMAGES_DIR):
        return send_from_directory(QA_IMAGES_DIR, filename)
    return "Q&A images path not found", 404

# Engineering textbook images - sourced from output folder (BMAD compliant)
ENGINEERING_IMAGES_DIR = os.path.join(BASE_DIR, 'static', 'engineering_images')

@app.route('/static/engineering_images/<path:filename>')
def serve_engineering_images(filename):
    """Serve engineering textbook images from static folder"""
    if os.path.exists(ENGINEERING_IMAGES_DIR):
        return send_from_directory(ENGINEERING_IMAGES_DIR, filename)
    return "Engineering images not found", 404

# Business Studies textbook images - sourced from output folder
# Make path configurable via environment variable or use relative path
BUSINESS_IMAGES_DIR = os.environ.get('BUSINESS_IMAGES_PATH') or \
    os.path.join(BASE_DIR, '..', '..', 'SynologyDrive', 'coding', 'tutorsystem', 'output', 'materials_output', 'cie igcse', 'Business Studies (0450)', 'Textbook', 'Cambridge IGCSE and O Level Business Sixth Edition', 'Cambridge IGCSE and O Level Business Sixth Edition_e1ddbad202818f467f247ede31905df6', 'vlm', 'images')

@app.route('/static/business_images/<path:filename>')
def serve_business_images(filename):
    """Serve Business Studies textbook images from output folder"""
    # Handle nested paths like 'images/filename.jpg'
    if filename.startswith('images/'):
        filename = filename.replace('images/', '')
        
    if os.path.exists(BUSINESS_IMAGES_DIR):
        return send_from_directory(BUSINESS_IMAGES_DIR, filename)
    return "Business Studies images not found", 404

@app.route('/images/<path:filename>')
def serve_images_alt(filename):
    """Alternate route for images (for markdown compatibility)"""
    # Try Business Studies images first
    if os.path.exists(os.path.join(BUSINESS_IMAGES_DIR, filename)):
        return send_from_directory(BUSINESS_IMAGES_DIR, filename)
        
    # Then try Engineering images
    if os.path.exists(ENGINEERING_IMAGES_DIR):
        return send_from_directory(ENGINEERING_IMAGES_DIR, filename)
    return "Images not found", 404

# AI-generated exercise images directory
EXERCISE_IMAGES_DIR = os.path.join(BASE_DIR, 'exercise_images')
os.makedirs(EXERCISE_IMAGES_DIR, exist_ok=True)

@app.route('/exercise_images/<path:filename>')
def serve_exercise_images(filename):
    """Serve AI-generated exercise images"""
    return send_from_directory(EXERCISE_IMAGES_DIR, filename)

# API: Get exercises for a subtopic
@app.route('/api/exercises/<subtopic_id>')
def get_exercises(subtopic_id):
    """Get generated exercises for a subtopic"""
    conn = get_db()
    
    # Check if exercises table exists
    table_exists = conn.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='exercises'
    """).fetchone()
    
    if not table_exists:
        conn.close()
        return jsonify([])
    
    rows = conn.execute("""
        SELECT * FROM exercises 
        WHERE subtopic_id LIKE ? 
        ORDER BY question_num
    """, (f'%{subtopic_id}%',)).fetchall()
    conn.close()
    
    exercises = []
    for row in rows:
        ex = dict(row)
        if ex.get('options'):
            try:
                ex['options'] = json.loads(ex['options'])
            except:
                pass
        exercises.append(ex)
    
    return jsonify(exercises)

# API: Get all exercises for a topic
@app.route('/api/topics/<topic_id>/exercises')
def get_topic_exercises(topic_id):
    """Get all exercises for subtopics under a topic"""
    conn = get_db()
    
    # Check if exercises table exists
    table_exists = conn.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='exercises'
    """).fetchone()
    
    if not table_exists:
        conn.close()
        return jsonify([])
    
    rows = conn.execute("""
        SELECT e.*, s.name as subtopic_name
        FROM exercises e
        JOIN subtopics s ON s.id = e.subtopic_id
        WHERE e.subtopic_id LIKE ?
        ORDER BY e.subtopic_id, e.question_num
    """, (f'%{topic_id}%',)).fetchall()
    conn.close()
    
    exercises = []
    for row in rows:
        ex = dict(row)
        if ex.get('options'):
            try:
                ex['options'] = json.loads(ex['options'])
            except:
                pass
        exercises.append(ex)
    
    return jsonify(exercises)

# API: Get all topics
@app.route('/api/topics')
def get_topics():
    log_api_call('/api/topics')
    conn = get_db_connection()
    topics = conn.execute('SELECT * FROM topics ORDER BY order_num').fetchall()
    conn.close()
    return jsonify([dict(row) for row in topics])

# API: Get subtopics for a topic
@app.route('/api/topics/<topic_id>/subtopics')
def get_subtopics(topic_id):
    conn = get_db_connection()
    subtopics = conn.execute('SELECT * FROM subtopics WHERE topic_id = ? ORDER BY order_num', (topic_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in subtopics])

# API: Get content for a subtopic (OLD ROUTE - Delegates to DB route)
@app.route('/api/content/<subtopic_id>')
def get_content(subtopic_id):
    """Legacy route - redirects to DB content endpoint"""
    return get_db_content(subtopic_id)

# API: Get questions
@app.route('/api/topics/<topic_id>/questions')
def get_questions(topic_id):
    conn = get_db_connection()
    # Support both short (B1) and full (combined_science_0653_B1) topic IDs
    rows = conn.execute('SELECT * FROM questions WHERE topic_id LIKE ? ORDER BY id', (f'%{topic_id}',)).fetchall()
    conn.close()
    
    questions = []
    for row in rows:
        q = dict(row)
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options'])
            except:
                pass
        if q.get('meta'):
            try:
                q['meta'] = json.loads(q['meta'])
            except:
                pass
        questions.append(q)
        
    return jsonify(questions)

# API: Get all subtopics with status
@app.route('/api/subtopics')
def get_all_subtopics():
    conn = get_db_connection()
    query = """
        SELECT s.*, t.name as topic_name, t.type as topic_type,
               CASE WHEN c.id IS NOT NULL THEN 1 ELSE 0 END as has_content
        FROM subtopics s
        LEFT JOIN topics t ON s.topic_id = t.id
        LEFT JOIN content c ON s.id = c.subtopic_id
        ORDER BY t.order_num, s.order_num
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

# ============================================================
# NEW: Syllabus & Subject APIs (from materials folder structure)
# ============================================================

MATERIALS_DIR = os.path.join(BASE_DIR, '..', 'materials')
MATERIALS_OUTPUT_DIR = os.path.join(BASE_DIR, '..', 'output', 'materials_output')

@app.route('/api/syllabuses')
def get_syllabuses():
    """Get all syllabuses from materials folder"""
    syllabuses = []
    
    if os.path.exists(MATERIALS_DIR):
        for item in sorted(os.listdir(MATERIALS_DIR)):
            item_path = os.path.join(MATERIALS_DIR, item)
            if os.path.isdir(item_path) and not item.endswith('.json'):
                # Count subjects in this syllabus
                subjects = [s for s in os.listdir(item_path) if os.path.isdir(os.path.join(item_path, s))]
                
                # Check if any content exists in output
                output_path = os.path.join(MATERIALS_OUTPUT_DIR, item)
                has_content = os.path.exists(output_path) and len(os.listdir(output_path)) > 0 if os.path.exists(output_path) else False
                
                syllabuses.append({
                    'id': item,
                    'name': item.replace('-', ' ').replace('_', ' ').title(),
                    'subject_count': len(subjects),
                    'has_content': has_content
                })
    
    # Sort: syllabuses with content first
    syllabuses.sort(key=lambda x: (not x['has_content'], x['name']))
    
    return jsonify(syllabuses)

@app.route('/api/syllabuses/<syllabus_id>/subjects')
def get_subjects(syllabus_id):
    """Get all subjects for a syllabus"""
    subjects = []
    syllabus_path = os.path.join(MATERIALS_DIR, syllabus_id)
    output_syllabus_path = os.path.join(MATERIALS_OUTPUT_DIR, syllabus_id)
    
    if os.path.exists(syllabus_path):
        for item in sorted(os.listdir(syllabus_path)):
            item_path = os.path.join(syllabus_path, item)
            if os.path.isdir(item_path):
                # Count PDFs/content in this subject
                pdf_count = len([f for f in os.listdir(item_path) if f.endswith('.pdf')]) if os.path.exists(item_path) else 0
                
                # Check subfolders for more PDFs
                for sub in os.listdir(item_path):
                    sub_path = os.path.join(item_path, sub)
                    if os.path.isdir(sub_path):
                        pdf_count += len([f for f in os.listdir(sub_path) if f.endswith('.pdf')]) if os.path.exists(sub_path) else 0
                
                # Check if processed content exists (real content, not placeholders)
                output_subject_path = os.path.join(output_syllabus_path, item)
                has_content = False
                content_files = 0
                
                if os.path.exists(output_subject_path):
                    for root, dirs, files in os.walk(output_subject_path):
                        for f in files:
                            if f.endswith('.md') and 'content' in f:
                                # Check if it's real content (>1KB) or just a placeholder
                                file_path = os.path.join(root, f)
                                file_size = os.path.getsize(file_path)
                                if file_size > 1024:  # More than 1KB = real content
                                    content_files += 1
                    has_content = content_files > 0
                
                subjects.append({
                    'id': item,
                    'name': item,
                    'syllabus_id': syllabus_id,
                    'pdf_count': pdf_count,
                    'has_content': has_content,
                    'content_files': content_files
                })
    
    # Sort: subjects with content first, then by name
    subjects.sort(key=lambda x: (not x['has_content'], x['name']))
    
    return jsonify(subjects)

@app.route('/api/syllabuses/<syllabus_id>/subjects/<subject_id>/topics')
def get_subject_topics(syllabus_id, subject_id):
    """Get topics/chapters for a subject"""
    topics = []
    subject_path = os.path.join(MATERIALS_DIR, syllabus_id, subject_id)
    output_subject_path = os.path.join(MATERIALS_OUTPUT_DIR, syllabus_id, subject_id)
    
    if os.path.exists(subject_path):
        for item in sorted(os.listdir(subject_path)):
            item_path = os.path.join(subject_path, item)
            if os.path.isdir(item_path):
                # Check for content
                output_topic_path = os.path.join(output_subject_path, item)
                has_content = os.path.exists(os.path.join(output_topic_path, 'content.md')) or \
                              os.path.exists(os.path.join(output_topic_path, 'content_enhanced.md'))
                
                topics.append({
                    'id': item,
                    'name': item.replace('_', ' ').replace('-', ' '),
                    'syllabus_id': syllabus_id,
                    'subject_id': subject_id,
                    'has_content': has_content
                })
    
    return jsonify(topics)

@app.route('/api/materials/content/<path:content_path>')
def get_materials_content(content_path):
    """Get content from materials_output folder"""
    # Try enhanced first, then regular content
    enhanced_path = os.path.join(MATERIALS_OUTPUT_DIR, content_path, 'content_enhanced.md')
    regular_path = os.path.join(MATERIALS_OUTPUT_DIR, content_path, 'content.md')
    
    content_file = enhanced_path if os.path.exists(enhanced_path) else regular_path
    
    if os.path.exists(content_file):
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert markdown to HTML (basic)
        import markdown
        html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
        
        return jsonify({
            'path': content_path,
            'markdown': content,
            'html_content': html_content,
            'is_enhanced': os.path.exists(enhanced_path)
        })
    
    return jsonify({'error': 'Content not found'}), 404

# ============== SQLite Database API ==============
# DB_PATH already defined at top of file

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/db/subjects')
def get_db_subjects():
    """Get all subjects from SQLite with topic counts"""
    log_api_call('/api/db/subjects')
    conn = get_db()
    rows = conn.execute("""
        SELECT s.id, s.name, 'N/A' as code,
               COUNT(DISTINCT t.id) as topic_count,
               COUNT(DISTINCT st.id) as subtopic_count,
               COUNT(DISTINCT cr.id) as processed_count
        FROM subjects s
        LEFT JOIN topics t ON t.subject_id = s.id
        LEFT JOIN subtopics st ON st.topic_id = t.id
        LEFT JOIN content_raw cr ON cr.subtopic_id = st.id
        GROUP BY s.id
        ORDER BY s.name
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/db/subjects/<subject_id>/chapters')
def get_db_chapters(subject_id):
    """Get main chapters for a subject (not all 858 topics)"""
    conn = get_db()
    # Get topics that look like main chapters (start with "1 ", "2 ", etc.)
    rows = conn.execute("""
        SELECT t.id, t.name, 
               SUBSTR(t.name, 1, 1) as chapter_num,  # Extract chapter number
               COUNT(DISTINCT s.id) as subtopic_count,
               COUNT(DISTINCT cr.id) as content_count
        FROM topics t
        LEFT JOIN subtopics s ON s.topic_id = t.id
        LEFT JOIN content_raw cr ON cr.subtopic_id = s.id
        WHERE t.subject_id = ?
          AND t.name GLOB '[0-9] *'  -- Starts with number and space (main chapters)
          AND t.name NOT LIKE '%.%'  -- Not subsections like "1.1"
        GROUP BY t.id
        ORDER BY CAST(SUBSTR(t.name, 1, 1) AS INTEGER)
    """, (subject_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/db/subjects/<subject_id>/topics')
def get_db_subject_topics(subject_id):
    """Get all topics for a specific subject - filters out duplicates/loose topics"""
    conn = get_db()
    # Only return topics that have proper order_num OR are Chapter type
    # This filters out duplicate loose topics like "The nature of business activity"
    rows = conn.execute("""
        SELECT t.id, t.name, 'topic' as type, t.subject_id, 
               COALESCE(t.order_num, 9999) as order_num,
               COUNT(DISTINCT s.id) as subtopic_count,
               COUNT(DISTINCT cr.id) as processed_count
        FROM topics t
        LEFT JOIN subtopics s ON s.topic_id = t.id
        LEFT JOIN content_raw cr ON cr.subtopic_id = s.id
        WHERE t.subject_id = ?
          AND (t.type = 'Chapter' OR t.order_num IS NOT NULL OR t.name LIKE '%SECTION%')
        GROUP BY t.id
        ORDER BY COALESCE(t.order_num, 9999)
    """, (subject_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/db/topics')
def get_db_topics():
    """Get all topics from SQLite"""
    conn = get_db()
    rows = conn.execute("""
        SELECT t.id, t.name, 'topic' as type, t.subject_id, COALESCE(t.order_num, 999) as order_num,
               COUNT(DISTINCT s.id) as subtopic_count,
               COUNT(DISTINCT cr.id) as processed_count
        FROM topics t
        LEFT JOIN subtopics s ON s.topic_id = t.id
        LEFT JOIN content_raw cr ON cr.subtopic_id = s.id
        GROUP BY t.id
        ORDER BY t.order_num
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/db/topics/<topic_id>/subtopics')
def get_db_subtopics(topic_id):
    """Get subtopics for a topic from SQLite - uses content_processed table"""
    conn = get_db()
    # Use exact match for topic_id (which is a string like 'engineering_gcse_8852_ch1')
    rows = conn.execute("""
        SELECT s.id, s.name, s.topic_id, s.order_num,
               (SELECT id FROM content_raw WHERE subtopic_id = s.id LIMIT 1) as raw_id,
               (SELECT LENGTH(markdown_content) FROM content_raw WHERE subtopic_id = s.id LIMIT 1) as raw_chars,
               (SELECT id FROM content_processed WHERE subtopic_id = s.id LIMIT 1) as processed_id,
               (SELECT LENGTH(html_content) FROM content_processed WHERE subtopic_id = s.id LIMIT 1) as processed_chars
        FROM subtopics s
        WHERE s.topic_id = ?
        ORDER BY s.order_num
    """, (topic_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/db/content/<subtopic_id>')
def get_db_content(subtopic_id):
    """Get content for a subtopic from SQLite - uses content_raw + content_processed"""
    log_api_call('/api/db/content', {'subtopic_id': subtopic_id})
    conn = get_db()
    
    # Get mode parameter (default to 'processed' for best viewing experience)
    mode = request.args.get('mode', 'processed')
    
    # Get raw content from content_raw table
    row = conn.execute("""
        SELECT cr.id, cr.subtopic_id, cr.markdown_content, cr.title,
               s.name as subtopic_name, t.name as topic_name
        FROM content_raw cr
        LEFT JOIN subtopics s ON s.id = cr.subtopic_id
        LEFT JOIN topics t ON s.topic_id = t.id
        WHERE cr.subtopic_id LIKE ?
    """, (f"%{subtopic_id}%",)).fetchone()
    
    if not row:
        conn.close()
        return jsonify({'error': 'Content not found'}), 404
    
    row_dict = dict(row)
    actual_subtopic_id = row_dict['subtopic_id']
    
    # Get processed content from content_processed table
    processed_row = conn.execute("""
        SELECT html_content, summary, processor_version
        FROM content_processed
        WHERE subtopic_id = ?
        LIMIT 1
    """, (actual_subtopic_id,)).fetchone()
    
    conn.close()
    
    # Use the actual subtopic name from subtopics table
    subtopic_name = row_dict.get('subtopic_name') or row_dict.get('title') or 'Content'
    subtopic_desc = ''
    
    # If mode is raw, return markdown
    if mode == 'raw':
        return jsonify({
            'id': row_dict['id'],
            'subtopic_id': actual_subtopic_id,
            'subtopic_name': subtopic_name,
            'topic_name': row_dict.get('topic_name'),
            'markdown_content': row_dict['markdown_content'],
            'html_content': None,
            'summary': subtopic_name,
            'is_processed': False
        })
    else:
        # Return HTML content (prefer processed, fallback to converted markdown)
        html = None
        if processed_row:
            html = processed_row['html_content']
        
        if not html and row_dict.get('markdown_content'):
            import markdown
            html = markdown.markdown(row_dict['markdown_content'], extensions=['tables', 'fenced_code'])
        
        return jsonify({
            'id': row_dict['id'],
            'subtopic_id': actual_subtopic_id,
            'subtopic_name': subtopic_name,
            'topic_name': row_dict.get('topic_name'),
            'description': subtopic_desc,
            'html_content': html,
            'markdown_content': row_dict['markdown_content'],
            'summary': processed_row['summary'] if processed_row else subtopic_name,
            'is_processed': processed_row is not None,
            'processor_version': processed_row['processor_version'] if processed_row else None
        })

@app.route('/api/db/stats')
def get_db_stats():
    """Get database statistics - uses content_processed table"""
    conn = get_db()
    stats = {}
    for table in ['syllabuses', 'subjects', 'topics', 'subtopics', 'content_raw', 'content_processed']:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            stats[table] = count
        except:
            stats[table] = 0
    conn.close()
    return jsonify(stats)

# ============================================================
# CREATIVE REWRITE API ENDPOINTS
# ============================================================

@app.route('/api/content/<subtopic_id>/with-rewrite')
def get_content_with_rewrite(subtopic_id):
    """Get both raw and processed content for a subtopic"""
    import markdown
    
    conn = get_db()
    
    # Get raw content from content_raw
    row = conn.execute("""
        SELECT cr.id, cr.subtopic_id, cr.markdown_content, cr.title,
               s.name as subtopic_name,
               t.name as topic_name, t.id as topic_id
        FROM content_raw cr
        LEFT JOIN subtopics s ON s.id = cr.subtopic_id
        LEFT JOIN topics t ON s.topic_id = t.id
        WHERE cr.subtopic_id LIKE ?
    """, (f"%{subtopic_id}%",)).fetchone()
    
    if not row:
        conn.close()
        return jsonify({'error': 'Content not found'}), 404
    
    content_data = dict(row)
    actual_subtopic_id = content_data['subtopic_id']
    
    # Get processed content from content_processed - prioritize creative/latest versions
    # Order by: creative-ai > hybrid-gemini-2.5 > gemini-3-flash > others
    processed_row = conn.execute("""
        SELECT * FROM content_processed
        WHERE subtopic_id = ?
        ORDER BY 
            CASE 
                WHEN processor_version LIKE '%creative%' THEN 1
                WHEN processor_version LIKE '%hybrid-gemini-2.5%' THEN 2
                WHEN processor_version LIKE '%gemini-3-flash%' THEN 3
                WHEN processor_version LIKE '%hybrid%' THEN 4
                ELSE 5
            END,
            id DESC
        LIMIT 1
    """, (actual_subtopic_id,)).fetchone()
    
    processed_data = dict(processed_row) if processed_row else None
    conn.close()
    
    # Convert markdown to HTML for raw content
    raw_html = None
    
    # ALWAYS convert raw markdown to HTML for the raw content tab
    # The processed content will be shown in the rewrite tab
    if content_data.get('markdown_content') and len(content_data.get('markdown_content', '')) > 0:
        # Convert raw markdown to HTML for display in raw tab
        raw_md_html = markdown.markdown(
            content_data['markdown_content'],
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
                'markdown.extensions.toc',
                'markdown.extensions.codehilite',
                'markdown.extensions.footnotes',
                'markdown.extensions.smarty'
            ]
        )
        
        # Wrap in styled template
        css_path = os.path.join(BASE_DIR, 'static', 'markdown_style.css')
        css_style = ""
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                css_style = f.read()
        
        raw_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{content_data.get('subtopic_name') or content_data.get('title')}</title>
            <style>
            {css_style}
            .raw-markdown-content {{
                font-family: Georgia, 'Times New Roman', Times, serif;
                line-height: 1.8;
                color: #1a1a1a;
                padding: 40px 60px;
                max-width: 900px;
                margin: 0 auto;
            }}
            </style>
        </head>
        <body>
            <div class="raw-markdown-content">
            {raw_md_html}
            </div>
        </body>
        </html>
        """
    
    return jsonify({
        'subtopic_id': actual_subtopic_id,
        'subtopic_name': content_data.get('subtopic_name') or content_data.get('title'),
        'topic_id': content_data.get('topic_id'),
        'topic_name': content_data.get('topic_name'),
        'raw_content': {
            'markdown': content_data.get('markdown_content'),
            'html': raw_html
        },
        'rewrite': {
            'has_rewrite': processed_data is not None,
            'html': processed_data.get('html_content') if processed_data else None,
            'created_at': processed_data.get('processed_at') if processed_data else None,
            'processor_version': processed_data.get('processor_version') if processed_data else None
        }
    })

@app.route('/api/rewrite/<subtopic_id>', methods=['POST'])
def trigger_rewrite(subtopic_id):
    """Trigger LLM rewrite for a subtopic"""
    from creative_rewriter_service import rewrite_subtopic, get_existing_rewrite
    
    try:
        # Check if OpenAI API key is set
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({'error': 'OPENAI_API_KEY not configured'}), 500
        
        # Trigger rewrite
        result = rewrite_subtopic(subtopic_id)
        
        return jsonify({
            'success': True,
            'subtopic_id': subtopic_id,
            'message': 'Rewrite generated successfully',
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rewrite/status/<subtopic_id>')
def get_rewrite_status(subtopic_id):
    """Check if a subtopic has been processed"""
    conn = get_db()
    row = conn.execute("""
        SELECT id, processor_version, processed_at
        FROM content_processed
        WHERE subtopic_id = ?
        LIMIT 1
    """, (subtopic_id,)).fetchone()
    conn.close()
    
    if row:
        return jsonify({
            'has_rewrite': True,
            'version': row['processor_version'],
            'created_at': row['processed_at']
        })
    else:
        return jsonify({
            'has_rewrite': False
        })

# ============================================================
# CHAPTER-BASED NAVIGATION API ENDPOINTS
# NOTE: Disabled - database doesn't have proper chapter structure
# Frontend now uses topic-based navigation instead
# ============================================================

# @app.route('/api/db/subjects/<subject_id>/chapters')
# @app.route('/api/db/chapters/<chapter_id>/subtopics') 

# @app.route('/api/db/chapters/<chapter_id>/overview')
# @app.route('/api/db/content/chapter/<chapter_id>')
# All chapter endpoints commented out - database schema doesn't support them (except the one we need)

@app.route('/api/db/subjects/<subject_id>/all-subtopics')
def api_all_subtopics(subject_id):
    return get_all_subtopics_for_subject(subject_id)

def get_all_subtopics_for_subject(subject_id):
    """Get all subtopics for a subject, with chapter info - uses content_processed"""
    conn = get_db()
    rows = conn.execute("""
        SELECT
            s.id,
            s.name,
            s.topic_id,
            s.order_num,
            t.id as chapter_id,
            t.order_num as chapter_num,
            t.name as chapter_title,
            (SELECT COUNT(*) FROM content_raw WHERE subtopic_id = s.id) > 0 as has_content,
            (SELECT COUNT(*) FROM content_processed WHERE subtopic_id = s.id) > 0 as has_rewrite
        FROM subtopics s
        JOIN topics t ON s.topic_id = t.id
        WHERE t.subject_id = ?
        ORDER BY t.order_num, s.order_num
    """, (subject_id,)).fetchall()
    conn.close()
    return jsonify({'subtopics': [dict(r) for r in rows]})


# Serve React Frontend
@app.route('/')
@app.route('/<path:path>')
def serve_frontend(path=''):
    """Serve React frontend or fallback to index.html for client-side routing"""
    frontend_dir = os.path.join(BASE_DIR, 'static', 'frontend')
    
    # If path is empty or doesn't exist, serve index.html
    if path and os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    else:
        # Fallback to index.html for React Router
        index_path = os.path.join(frontend_dir, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(frontend_dir, 'index.html')
        else:
            return jsonify({"error": "Frontend not built. Run setup_production.bat first."}), 404

if __name__ == '__main__':
    print("AI Tutor Flask Server starting on port 5000...")
    app.run(port=5000, debug=True)