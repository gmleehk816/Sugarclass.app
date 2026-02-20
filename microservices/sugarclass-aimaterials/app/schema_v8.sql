-- ============================================================================
-- AI Materials V8 - New Database Schema
-- ============================================================================
-- This replaces the old aimaterials database with V8 architecture
-- ============================================================================

-- Drop existing tables (clean slate)
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS exercises;
DROP TABLE IF EXISTS content_processed;
DROP TABLE IF EXISTS content_raw;
DROP TABLE IF EXISTS subtopics;
DROP TABLE IF EXISTS topics;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS syllabuses;

-- ============================================================================
-- CORE HIERARCHY
-- ============================================================================

-- Syllabuses (Root level - IGCSE, A-Level, IB, HKDSE)
CREATE TABLE syllabuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,           -- e.g., 'IGCSE', 'A-Level', 'IB'
    display_name TEXT NOT NULL,          -- e.g., 'Cambridge IGCSE'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects (e.g., 'igcse_physics', 'igcse_biology')
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    syllabus_id INTEGER NOT NULL,
    subject_id TEXT NOT NULL UNIQUE,     -- e.g., 'igcse_physics_0625'
    name TEXT NOT NULL,                  -- e.g., 'Physics'
    code TEXT,                           -- e.g., '0625'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (syllabus_id) REFERENCES syllabuses(id) ON DELETE CASCADE
);

-- Topics/Chapters (e.g., 'P1', 'P2', 'Chapter 1')
CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    topic_id TEXT NOT NULL,              -- e.g., 'P1', 'C1', 'B1'
    name TEXT NOT NULL,                  -- e.g., 'Describing Motion'
    order_num INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE(subject_id, topic_id)
);

-- Subtopics (Smallest teachable unit)
CREATE TABLE subtopics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    subtopic_id TEXT NOT NULL,           -- e.g., 'P1.1', '2.4'
    slug TEXT NOT NULL,                  -- e.g., 'calculating-speed-and-acceleration'
    name TEXT NOT NULL,                  -- e.g., 'Calculating Speed and Acceleration'
    order_num INTEGER DEFAULT 0,
    markdown_file_path TEXT,             -- Path to source markdown file
    source_hash TEXT,                    -- MD5 hash for cache validation
    processed_at TIMESTAMP,              -- When V8 content was generated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
    UNIQUE(topic_id, subtopic_id)
);

-- ============================================================================
-- V8 CONTENT STORAGE
-- ============================================================================

-- V8 Concepts (6-8 per subtopic)
CREATE TABLE v8_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    concept_key TEXT NOT NULL,           -- e.g., 'speed_calculation'
    title TEXT NOT NULL,                 -- e.g., 'Calculating Average Speed'
    description TEXT,                    -- For SVG generation
    icon TEXT,                           -- Emoji icon
    order_num INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE,
    UNIQUE(subtopic_id, concept_key)
);

-- V8 Generated Content (Per concept)
CREATE TABLE v8_generated_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id INTEGER NOT NULL,
    content_type TEXT NOT NULL,          -- 'svg', 'bullets', 'image'
    content TEXT NOT NULL,               -- SVG code, HTML bullets, or image URL
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (concept_id) REFERENCES v8_concepts(id) ON DELETE CASCADE
);

-- V8 Quiz Questions (5 per subtopic)
CREATE TABLE v8_quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    question_num INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    options JSON NOT NULL,               -- {"A": "Option A", "B": "Option B", ...}
    correct_answer TEXT NOT NULL,        -- 'A', 'B', 'C', or 'D'
    explanation TEXT,
    difficulty TEXT DEFAULT 'medium',    -- 'easy', 'medium', 'hard'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE,
    UNIQUE(subtopic_id, question_num)
);

-- V8 Flashcards (8 per subtopic)
CREATE TABLE v8_flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    card_num INTEGER NOT NULL,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE,
    UNIQUE(subtopic_id, card_num)
);

-- V8 Real-Life Images (3 per subtopic)
CREATE TABLE v8_reallife_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    image_type TEXT NOT NULL,            -- 'everyday', 'sports', 'transport'
    image_url TEXT NOT NULL,             -- Base64 data URI or URL
    prompt TEXT,                         -- Original generation prompt
    title TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE,
    UNIQUE(subtopic_id, image_type)
);

-- V8 Past Papers
CREATE TABLE v8_past_papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    marks INTEGER NOT NULL DEFAULT 1,
    year TEXT,                           -- e.g., '2023'
    season TEXT,                         -- e.g., 'Summer', 'Winter', 'May/June'
    paper_reference TEXT,                -- e.g., 'Paper 1 Variant 2 (12)'
    mark_scheme TEXT,                    -- Multi-line answer/mark scheme
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);

-- V8 Learning Objectives (Extracted from source)
CREATE TABLE v8_learning_objectives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    objective_text TEXT NOT NULL,
    order_num INTEGER DEFAULT 0,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);

-- V8 Key Terms
CREATE TABLE v8_key_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    term TEXT NOT NULL,
    definition TEXT,
    order_num INTEGER DEFAULT 0,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);

-- V8 Formulas
CREATE TABLE v8_formulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    formula TEXT NOT NULL,
    description TEXT,
    order_num INTEGER DEFAULT 0,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);

-- ============================================================================
-- PROCESSING QUEUE (For background generation)
-- ============================================================================

-- Background tasks for V8 generation
CREATE TABLE v8_processing_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL UNIQUE,
    subtopic_id INTEGER,
    task_type TEXT NOT NULL,             -- 'full_generation', 'svg_only', 'quiz_only', etc.
    status TEXT DEFAULT 'pending',       -- 'pending', 'running', 'cancelling', 'completed', 'failed', 'cancelled'
    progress INTEGER DEFAULT 0,          -- 0-100
    message TEXT,
    error TEXT,
    cancel_requested INTEGER DEFAULT 0,  -- 0/1 cooperative cancellation flag
    started_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE SET NULL
);

-- Task logs (detailed progress tracking)
CREATE TABLE v8_task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    log_level TEXT DEFAULT 'info',       -- 'info', 'warning', 'error'
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES v8_processing_tasks(task_id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_subtopics_topic ON subtopics(topic_id);
CREATE INDEX idx_subtopics_slug ON subtopics(slug);
CREATE INDEX idx_v8_concepts_subtopic ON v8_concepts(subtopic_id);
CREATE INDEX idx_v8_generated_content_concept ON v8_generated_content(concept_id);
CREATE INDEX idx_v8_generated_content_type ON v8_generated_content(content_type);
CREATE INDEX idx_v8_quiz_subtopic ON v8_quiz_questions(subtopic_id);
CREATE INDEX idx_v8_flashcards_subtopic ON v8_flashcards(subtopic_id);
CREATE INDEX idx_v8_reallife_subtopic ON v8_reallife_images(subtopic_id);
CREATE INDEX idx_v8_past_papers_subtopic ON v8_past_papers(subtopic_id);
CREATE INDEX idx_v8_tasks_status ON v8_processing_tasks(status);
CREATE INDEX idx_v8_tasks_subtopic ON v8_processing_tasks(subtopic_id);

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert default syllabuses
INSERT INTO syllabuses (name, display_name, description) VALUES
    ('IGCSE', 'Cambridge IGCSE', 'Cambridge International General Certificate of Secondary Education'),
    ('A-LEVEL', 'Cambridge International A-Level', 'Cambridge International Advanced Level'),
    ('IB', 'IB Diploma Programme', 'International Baccalaureate Diploma Programme'),
    ('HKDSE', 'HKDSE', 'Hong Kong Diploma of Secondary Education');

-- Insert Physics subject
INSERT INTO subjects (syllabus_id, subject_id, name, code, description) VALUES
    (1, 'igcse_physics_0625', 'Physics', '0625', 'Cambridge IGCSE Physics (0625)');

-- ============================================================================
-- VIEWS FOR CONVENIENT QUERIES
-- ============================================================================

-- View: Subtopics with full hierarchy info
CREATE VIEW v_subtopics_full AS
SELECT
    s.id,
    s.subtopic_id,
    s.slug,
    s.name,
    s.order_num,
    s.processed_at,
    t.topic_id,
    t.name AS topic_name,
    sub.subject_id,
    sub.name AS subject_name,
    sy.display_name AS syllabus_name
FROM subtopics s
JOIN topics t ON s.topic_id = t.id
JOIN subjects sub ON t.subject_id = sub.id
JOIN syllabuses sy ON sub.syllabus_id = sy.id;

-- View: V8 content completeness status
CREATE VIEW v_v8_content_status AS
SELECT
    s.id AS subtopic_id,
    s.subtopic_id,
    s.name AS subtopic_name,
    COUNT(DISTINCT c.id) AS concept_count,
    COUNT(DISTINCT CASE WHEN gc.content_type = 'svg' THEN gc.id END) AS svg_count,
    COUNT(DISTINCT CASE WHEN gc.content_type = 'bullets' THEN gc.id END) AS bullet_count,
    COUNT(DISTINCT q.id) AS quiz_count,
    COUNT(DISTINCT f.id) AS flashcard_count,
    COUNT(DISTINCT r.id) AS reallife_image_count,
    COUNT(DISTINCT pp.id) AS past_paper_count,
    s.processed_at
FROM subtopics s
LEFT JOIN v8_concepts c ON s.id = c.subtopic_id
LEFT JOIN v8_generated_content gc ON c.id = gc.concept_id
LEFT JOIN v8_quiz_questions q ON s.id = q.subtopic_id
LEFT JOIN v8_flashcards f ON s.id = f.subtopic_id
LEFT JOIN v8_reallife_images r ON s.id = r.subtopic_id
LEFT JOIN v8_past_papers pp ON s.id = pp.subtopic_id
GROUP BY s.id;

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE TRIGGER update_syllabuses_timestamp
AFTER UPDATE ON syllabuses
FOR EACH ROW
BEGIN
    UPDATE syllabuses SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER update_subjects_timestamp
AFTER UPDATE ON subjects
FOR EACH ROW
BEGIN
    UPDATE subjects SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER update_topics_timestamp
AFTER UPDATE ON topics
FOR EACH ROW
BEGIN
    UPDATE topics SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER update_subtopics_timestamp
AFTER UPDATE ON subtopics
FOR EACH ROW
BEGIN
    UPDATE subtopics SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
