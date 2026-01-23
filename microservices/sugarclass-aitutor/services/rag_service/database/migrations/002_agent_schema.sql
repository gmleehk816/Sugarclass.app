-- Agent Database Schema (agent_db)
-- This schema stores runtime state for tutoring sessions, student profiles, and learning progress

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Students table
-- Stores student profiles and preferences
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,   -- External user ID (from auth system)
    name VARCHAR(200),
    email VARCHAR(200),
    grade_level VARCHAR(50),                 -- e.g., 'Year 10', 'Grade 11', 'Form 5'
    curriculum VARCHAR(100),                 -- e.g., 'CIE IGCSE', 'IB', 'AQA'
    preferred_language VARCHAR(10) DEFAULT 'en',
    learning_style VARCHAR(50),              -- 'visual', 'auditory', 'kinesthetic', 'reading'
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_student_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_student_curriculum ON students(curriculum);
CREATE INDEX IF NOT EXISTS idx_student_active ON students(is_active);

-- Topic mastery tracking
-- Tracks student progress on each topic with spaced repetition support
CREATE TABLE IF NOT EXISTS student_mastery (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    syllabus_id INTEGER NOT NULL,            -- References content_db.syllabus_hierarchy.id
    subject VARCHAR(100) NOT NULL,
    chapter VARCHAR(200) NOT NULL,
    subtopic VARCHAR(200) NOT NULL,
    mastery_score FLOAT DEFAULT 0.0 CHECK (mastery_score >= 0 AND mastery_score <= 1),
    confidence_level FLOAT DEFAULT 0.0 CHECK (confidence_level >= 0 AND confidence_level <= 1),
    attempts_count INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    streak_count INTEGER DEFAULT 0,          -- Consecutive correct answers
    last_practiced_at TIMESTAMP WITH TIME ZONE,
    next_review_at TIMESTAMP WITH TIME ZONE, -- Spaced repetition scheduling
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_student_topic UNIQUE(student_id, syllabus_id)
);

CREATE INDEX IF NOT EXISTS idx_mastery_student ON student_mastery(student_id);
CREATE INDEX IF NOT EXISTS idx_mastery_subject ON student_mastery(subject);
CREATE INDEX IF NOT EXISTS idx_mastery_syllabus ON student_mastery(syllabus_id);
CREATE INDEX IF NOT EXISTS idx_mastery_next_review ON student_mastery(next_review_at);
CREATE INDEX IF NOT EXISTS idx_mastery_score ON student_mastery(mastery_score);

-- Tutoring sessions
-- Tracks active and historical tutoring sessions
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,  -- UUID for external reference
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    subject VARCHAR(100),
    current_chapter VARCHAR(200),
    current_topic VARCHAR(200),
    difficulty_level VARCHAR(20) DEFAULT 'core',
    session_state JSONB DEFAULT '{}',         -- LangGraph checkpoint state
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    total_messages INTEGER DEFAULT 0,
    total_questions_asked INTEGER DEFAULT 0,
    total_questions_correct INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_session_student ON sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_session_active ON sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_session_subject ON sessions(subject);
CREATE INDEX IF NOT EXISTS idx_session_last_activity ON sessions(last_activity_at);

-- Lesson interaction logs
-- Detailed log of all interactions during tutoring sessions
CREATE TABLE IF NOT EXISTS lesson_logs (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message_type VARCHAR(50) NOT NULL,        -- 'user_query', 'agent_response', 'quiz', 'feedback', 'hint'
    agent_type VARCHAR(50),                   -- 'supervisor', 'planner', 'teacher', 'grader'
    content TEXT NOT NULL,
    syllabus_id INTEGER,                      -- Topic being discussed (references content_db)
    is_correct BOOLEAN,                       -- For quiz answers
    score FLOAT,                              -- For graded responses (0-1)
    latency_ms INTEGER,                       -- Response time in milliseconds
    tokens_used INTEGER,                      -- LLM tokens consumed
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_log_session ON lesson_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_log_student ON lesson_logs(student_id);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON lesson_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_type ON lesson_logs(message_type);
CREATE INDEX IF NOT EXISTS idx_log_agent ON lesson_logs(agent_type);

-- Quiz attempts
-- Detailed tracking of quiz/exercise attempts
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    syllabus_id INTEGER NOT NULL,             -- References content_db.syllabus_hierarchy.id
    question_id VARCHAR(100),                 -- Optional: specific question identifier
    question_content TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'open_ended',  -- 'multiple_choice', 'open_ended', 'fill_blank'
    student_answer TEXT,
    correct_answer TEXT,
    is_correct BOOLEAN,
    score FLOAT CHECK (score >= 0 AND score <= 1),  -- Partial credit support
    feedback TEXT,
    hints_used INTEGER DEFAULT 0,
    time_taken_seconds INTEGER,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_quiz_student ON quiz_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_quiz_session ON quiz_attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_quiz_syllabus ON quiz_attempts(syllabus_id);
CREATE INDEX IF NOT EXISTS idx_quiz_correct ON quiz_attempts(is_correct);
CREATE INDEX IF NOT EXISTS idx_quiz_attempted ON quiz_attempts(attempted_at);

-- Learning goals
-- Student-defined or system-suggested learning goals
CREATE TABLE IF NOT EXISTS learning_goals (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    syllabus_id INTEGER,                      -- Target topic (references content_db)
    subject VARCHAR(100) NOT NULL,
    goal_type VARCHAR(50) NOT NULL,           -- 'mastery', 'review', 'exam_prep', 'custom'
    target_score FLOAT DEFAULT 0.8,
    current_score FLOAT DEFAULT 0.0,
    target_date DATE,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_goal_student ON learning_goals(student_id);
CREATE INDEX IF NOT EXISTS idx_goal_completed ON learning_goals(is_completed);
CREATE INDEX IF NOT EXISTS idx_goal_target_date ON learning_goals(target_date);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
DROP TRIGGER IF EXISTS update_students_updated_at ON students;
CREATE TRIGGER update_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_student_mastery_updated_at ON student_mastery;
CREATE TRIGGER update_student_mastery_updated_at
    BEFORE UPDATE ON student_mastery
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for student progress summary
CREATE OR REPLACE VIEW student_progress_summary AS
SELECT
    s.id as student_id,
    s.user_id,
    s.name,
    s.curriculum,
    sm.subject,
    COUNT(DISTINCT sm.syllabus_id) as topics_studied,
    AVG(sm.mastery_score) as avg_mastery,
    SUM(sm.attempts_count) as total_attempts,
    SUM(sm.correct_count) as total_correct,
    CASE
        WHEN SUM(sm.attempts_count) > 0
        THEN ROUND(SUM(sm.correct_count)::numeric / SUM(sm.attempts_count) * 100, 2)
        ELSE 0
    END as accuracy_percent,
    MAX(sm.last_practiced_at) as last_activity
FROM students s
LEFT JOIN student_mastery sm ON s.id = sm.student_id
GROUP BY s.id, s.user_id, s.name, s.curriculum, sm.subject
ORDER BY s.id, sm.subject;

-- View for topics due for review (spaced repetition)
CREATE OR REPLACE VIEW topics_due_for_review AS
SELECT
    sm.id,
    sm.student_id,
    s.user_id,
    s.name as student_name,
    sm.subject,
    sm.chapter,
    sm.subtopic,
    sm.mastery_score,
    sm.next_review_at,
    sm.last_practiced_at,
    sm.streak_count,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - sm.next_review_at)) / 3600 as hours_overdue
FROM student_mastery sm
JOIN students s ON sm.student_id = s.id
WHERE sm.next_review_at <= CURRENT_TIMESTAMP
ORDER BY sm.next_review_at ASC;

-- View for session statistics
CREATE OR REPLACE VIEW session_statistics AS
SELECT
    s.student_id,
    st.user_id,
    st.name as student_name,
    COUNT(s.id) as total_sessions,
    SUM(s.total_messages) as total_messages,
    SUM(s.total_questions_asked) as total_questions,
    SUM(s.total_questions_correct) as total_correct,
    AVG(EXTRACT(EPOCH FROM (COALESCE(s.ended_at, CURRENT_TIMESTAMP) - s.started_at)) / 60) as avg_session_minutes,
    MAX(s.started_at) as last_session
FROM sessions s
JOIN students st ON s.student_id = st.id
GROUP BY s.student_id, st.user_id, st.name
ORDER BY last_session DESC;
