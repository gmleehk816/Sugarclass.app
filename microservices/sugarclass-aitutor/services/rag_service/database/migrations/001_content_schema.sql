-- Content Database Schema (content_db)
-- This schema stores the syllabus hierarchy and content from markdown files

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Syllabus hierarchy table
-- Stores the structure: syllabus -> subject -> chapter -> subtopic -> content
CREATE TABLE IF NOT EXISTS syllabus_hierarchy (
    id SERIAL PRIMARY KEY,
    syllabus VARCHAR(100) NOT NULL,        -- e.g., 'CIE IGCSE', 'IB', 'AQA', 'Edexcel'
    subject VARCHAR(100) NOT NULL,          -- e.g., 'Mathematics', 'Physics', 'Combined Science'
    chapter VARCHAR(200) NOT NULL,          -- e.g., 'Differentiation', 'Forces and Motion'
    subtopic VARCHAR(200) NOT NULL,         -- e.g., 'Chain Rule', 'Newton Laws'
    content_type VARCHAR(50) NOT NULL,      -- 'textbook', 'exercise', 'exam_qa'
    file_path TEXT UNIQUE NOT NULL,         -- Original file path for tracking
    markdown_content TEXT,                  -- Full markdown content
    content_hash VARCHAR(64),               -- SHA256 hash for change detection
    word_count INTEGER DEFAULT 0,
    difficulty_level VARCHAR(20) DEFAULT 'core',  -- 'foundation', 'core', 'extended'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Composite unique constraint
    CONSTRAINT unique_content UNIQUE (syllabus, subject, chapter, subtopic, content_type)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_syllabus ON syllabus_hierarchy(syllabus);
CREATE INDEX IF NOT EXISTS idx_subject ON syllabus_hierarchy(subject);
CREATE INDEX IF NOT EXISTS idx_chapter ON syllabus_hierarchy(chapter);
CREATE INDEX IF NOT EXISTS idx_subtopic ON syllabus_hierarchy(subtopic);
CREATE INDEX IF NOT EXISTS idx_content_type ON syllabus_hierarchy(content_type);
CREATE INDEX IF NOT EXISTS idx_file_path ON syllabus_hierarchy(file_path);
CREATE INDEX IF NOT EXISTS idx_difficulty ON syllabus_hierarchy(difficulty_level);

-- Full text search indent
CREATE INDEX IF NOT EXISTS idx_content_fts ON syllabus_hierarchy
    USING gin(to_tsvector('english', COALESCE(markdown_content, '')));

-- Topic prerequisites table (for learning path)
-- Defines which topics should be learned before others
CREATE TABLE IF NOT EXISTS topic_prerequisites (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES syllabus_hierarchy(id) ON DELETE CASCADE,
    prerequisite_id INTEGER REFERENCES syllabus_hierarchy(id) ON DELETE CASCADE,
    strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),  -- How strongly required (0-1)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_prerequisite UNIQUE(topic_id, prerequisite_id),
    CONSTRAINT no_self_prerequisite CHECK (topic_id != prerequisite_id)
);

CREATE INDEX IF NOT EXISTS idx_prereq_topic ON topic_prerequisites(topic_id);
CREATE INDEX IF NOT EXISTS idx_prereq_prerequisite ON topic_prerequisites(prerequisite_id);

-- Content chunks table for RAG (linked to syllabus)
-- Stores chunked content with references to vector embeddings
CREATE TABLE IF NOT EXISTS content_chunks (
    id SERIAL PRIMARY KEY,
    syllabus_id INTEGER REFERENCES syllabus_hierarchy(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_content TEXT NOT NULL,
    chunk_type VARCHAR(50),  -- 'definition', 'example', 'formula', 'exercise', 'explanation'
    embedding_id VARCHAR(100),  -- Reference to Qdrant vector ID
    token_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_chunk UNIQUE(syllabus_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunk_syllabus ON content_chunks(syllabus_id);
CREATE INDEX IF NOT EXISTS idx_chunk_type ON content_chunks(chunk_type);
CREATE INDEX IF NOT EXISTS idx_chunk_embedding ON content_chunks(embedding_id);

-- Topic relationships table (for cross-referencing related topics)
CREATE TABLE IF NOT EXISTS topic_relationships (
    id SERIAL PRIMARY KEY,
    source_topic_id INTEGER REFERENCES syllabus_hierarchy(id) ON DELETE CASCADE,
    target_topic_id INTEGER REFERENCES syllabus_hierarchy(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,  -- 'related', 'extends', 'applies_to', 'contrasts'
    strength FLOAT DEFAULT 0.5 CHECK (strength >= 0 AND strength <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_relationship UNIQUE(source_topic_id, target_topic_id, relationship_type),
    CONSTRAINT no_self_relationship CHECK (source_topic_id != target_topic_id)
);

CREATE INDEX IF NOT EXISTS idx_rel_source ON topic_relationships(source_topic_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON topic_relationships(target_topic_id);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_syllabus_hierarchy_updated_at ON syllabus_hierarchy;
CREATE TRIGGER update_syllabus_hierarchy_updated_at
    BEFORE UPDATE ON syllabus_hierarchy
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for easy syllabus navigation
CREATE OR REPLACE VIEW syllabus_tree AS
SELECT
    sh.id,
    sh.syllabus,
    sh.subject,
    sh.chapter,
    sh.subtopic,
    sh.content_type,
    sh.difficulty_level,
    sh.word_count,
    sh.file_path,
    sh.created_at,
    sh.updated_at,
    COUNT(cc.id) as chunk_count,
    COUNT(DISTINCT tp.prerequisite_id) as prerequisite_count
FROM syllabus_hierarchy sh
LEFT JOIN content_chunks cc ON sh.id = cc.syllabus_id
LEFT JOIN topic_prerequisites tp ON sh.id = tp.topic_id
GROUP BY sh.id
ORDER BY sh.syllabus, sh.subject, sh.chapter, sh.subtopic;

-- View for content statistics
CREATE OR REPLACE VIEW content_statistics AS
SELECT
    syllabus,
    subject,
    COUNT(DISTINCT chapter) as chapter_count,
    COUNT(DISTINCT subtopic) as subtopic_count,
    COUNT(*) as total_content_items,
    SUM(word_count) as total_words,
    COUNT(CASE WHEN content_type = 'textbook' THEN 1 END) as textbook_count,
    COUNT(CASE WHEN content_type = 'exercise' THEN 1 END) as exercise_count,
    COUNT(CASE WHEN content_type = 'exam_qa' THEN 1 END) as exam_qa_count
FROM syllabus_hierarchy
GROUP BY syllabus, subject
ORDER BY syllabus, subject;