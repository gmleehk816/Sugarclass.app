"""
Agent Database Manager

Manages student profiles, sessions, mastery tracking, and learning logs
in the agent database.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger(__name__)


@dataclass
class StudentProfile:
    """Student profile data."""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    grade_level: Optional[str] = None
    curriculum: Optional[str] = None
    preferred_language: str = 'en'
    learning_style: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SessionData:
    """Tutoring session data."""
    session_id: str
    student_id: int
    subject: Optional[str] = None
    current_chapter: Optional[str] = None
    current_topic: Optional[str] = None
    difficulty_level: str = 'core'
    session_state: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.session_state is None:
            self.session_state = {}
        if self.metadata is None:
            self.metadata = {}


class AgentDBManager:
    """
    Manages the agent database for tutoring sessions.
    Handles students, sessions, mastery tracking, and logs.
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Establish database connection pool."""
        if asyncpg is None:
            raise ImportError("asyncpg is required. Install with: pip install asyncpg")

        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("Connected to agent database")

    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Agent database connection closed")

    # ==================== Student Management ====================

    async def create_student(self, profile: StudentProfile) -> int:
        """Create a new student profile."""
        async with self.pool.acquire() as conn:
            student_id = await conn.fetchval(
                """
                INSERT INTO students (
                    user_id, name, email, grade_level, curriculum,
                    preferred_language, learning_style, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = COALESCE(EXCLUDED.name, students.name),
                    email = COALESCE(EXCLUDED.email, students.email),
                    grade_level = COALESCE(EXCLUDED.grade_level, students.grade_level),
                    curriculum = COALESCE(EXCLUDED.curriculum, students.curriculum),
                    learning_style = COALESCE(EXCLUDED.learning_style, students.learning_style),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                profile.user_id,
                profile.name,
                profile.email,
                profile.grade_level,
                profile.curriculum,
                profile.preferred_language,
                profile.learning_style,
                json.dumps(profile.metadata)
            )
            return student_id

    async def get_student_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get student profile by external user ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM students WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None

    async def get_student_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Get student profile by internal ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM students WHERE id = $1",
                student_id
            )
            return dict(row) if row else None

    async def update_student(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update student profile fields."""
        allowed_fields = {
            'name', 'email', 'grade_level', 'curriculum',
            'preferred_language', 'learning_style', 'metadata'
        }

        # Filter to allowed fields
        updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if not updates:
            return False

        # Build update query
        set_clauses = []
        params = [user_id]
        for i, (field, value) in enumerate(updates.items(), start=2):
            if field == 'metadata':
                set_clauses.append(f"{field} = ${i}::jsonb")
                params.append(json.dumps(value))
            else:
                set_clauses.append(f"{field} = ${i}")
                params.append(value)

        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE students SET
                    {', '.join(set_clauses)},
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
                """,
                *params
            )
            return result == "UPDATE 1"

    # ==================== Session Management ====================

    async def create_session(self, session: SessionData) -> str:
        """Create a new tutoring session."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sessions (
                    session_id, student_id, subject, current_chapter,
                    current_topic, difficulty_level, session_state, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                session.session_id,
                session.student_id,
                session.subject,
                session.current_chapter,
                session.current_topic,
                session.difficulty_level,
                json.dumps(session.session_state),
                json.dumps(session.metadata)
            )
            return session.session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM sessions WHERE session_id = $1",
                session_id
            )
            return dict(row) if row else None

    async def get_active_sessions(self, student_id: int) -> List[Dict[str, Any]]:
        """Get all active sessions for a student."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM sessions
                WHERE student_id = $1 AND is_active = TRUE
                ORDER BY last_activity_at DESC
                """,
                student_id
            )
            return [dict(row) for row in rows]

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update session fields."""
        allowed_fields = {
            'subject', 'current_chapter', 'current_topic',
            'difficulty_level', 'session_state', 'is_active', 'metadata'
        }

        updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if not updates:
            return False

        set_clauses = []
        params = [session_id]
        for i, (field, value) in enumerate(updates.items(), start=2):
            if field in ('session_state', 'metadata'):
                set_clauses.append(f"{field} = ${i}::jsonb")
                params.append(json.dumps(value))
            else:
                set_clauses.append(f"{field} = ${i}")
                params.append(value)

        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE sessions SET
                    {', '.join(set_clauses)},
                    last_activity_at = CURRENT_TIMESTAMP
                WHERE session_id = $1
                """,
                *params
            )
            return "UPDATE 1" in result

    async def end_session(self, session_id: str) -> bool:
        """End a tutoring session."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE sessions SET
                    is_active = FALSE,
                    ended_at = CURRENT_TIMESTAMP
                WHERE session_id = $1
                """,
                session_id
            )
            return "UPDATE 1" in result

    async def increment_session_messages(self, session_id: str) -> None:
        """Increment the message count for a session."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sessions SET
                    total_messages = total_messages + 1,
                    last_activity_at = CURRENT_TIMESTAMP
                WHERE session_id = $1
                """,
                session_id
            )

    # ==================== Mastery Tracking ====================

    async def get_mastery_scores(
        self,
        student_id: int,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get mastery scores for a student."""
        async with self.pool.acquire() as conn:
            if subject:
                rows = await conn.fetch(
                    """
                    SELECT * FROM student_mastery
                    WHERE student_id = $1 AND subject = $2
                    ORDER BY chapter, subtopic
                    """,
                    student_id, subject
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM student_mastery
                    WHERE student_id = $1
                    ORDER BY subject, chapter, subtopic
                    """,
                    student_id
                )
            return [dict(row) for row in rows]

    async def update_mastery(
        self,
        student_id: int,
        syllabus_id: int,
        subject: str,
        chapter: str,
        subtopic: str,
        score_delta: float,
        is_correct: bool
    ) -> Dict[str, Any]:
        """Update mastery score for a topic."""
        async with self.pool.acquire() as conn:
            # Get current mastery
            current = await conn.fetchrow(
                """
                SELECT id, mastery_score, attempts_count, correct_count, streak_count
                FROM student_mastery
                WHERE student_id = $1 AND syllabus_id = $2
                """,
                student_id, syllabus_id
            )

            if current:
                # Update existing
                new_score = max(0.0, min(1.0, current['mastery_score'] + score_delta))
                new_attempts = current['attempts_count'] + 1
                new_correct = current['correct_count'] + (1 if is_correct else 0)
                new_streak = (current['streak_count'] + 1) if is_correct else 0

                # Calculate confidence based on attempts
                confidence = min(1.0, new_attempts / 10)

                # Calculate next review date (spaced repetition)
                if new_score >= 0.9:
                    next_review = datetime.now() + timedelta(days=14)
                elif new_score >= 0.8:
                    next_review = datetime.now() + timedelta(days=7)
                elif new_score >= 0.6:
                    next_review = datetime.now() + timedelta(days=3)
                else:
                    next_review = datetime.now() + timedelta(days=1)

                await conn.execute(
                    """
                    UPDATE student_mastery SET
                        mastery_score = $1,
                        confidence_level = $2,
                        attempts_count = $3,
                        correct_count = $4,
                        streak_count = $5,
                        last_practiced_at = CURRENT_TIMESTAMP,
                        next_review_at = $6,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $7
                    """,
                    new_score, confidence, new_attempts, new_correct,
                    new_streak, next_review, current['id']
                )

                return {
                    "previous_score": current['mastery_score'],
                    "new_score": new_score,
                    "attempts": new_attempts,
                    "streak": new_streak,
                    "next_review": next_review.isoformat()
                }
            else:
                # Create new mastery record
                initial_score = 0.1 if is_correct else 0.0
                next_review = datetime.now() + timedelta(days=1)

                await conn.execute(
                    """
                    INSERT INTO student_mastery (
                        student_id, syllabus_id, subject, chapter, subtopic,
                        mastery_score, confidence_level, attempts_count, correct_count,
                        streak_count, last_practiced_at, next_review_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, 0.1, 1, $7, $8, CURRENT_TIMESTAMP, $9)
                    """,
                    student_id, syllabus_id, subject, chapter, subtopic,
                    initial_score, 1 if is_correct else 0,
                    1 if is_correct else 0, next_review
                )

                return {
                    "previous_score": 0.0,
                    "new_score": initial_score,
                    "attempts": 1,
                    "streak": 1 if is_correct else 0,
                    "next_review": next_review.isoformat()
                }

    async def get_weak_topics(
        self,
        student_id: int,
        threshold: float = 0.5,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get topics where student needs improvement."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT subject, chapter, subtopic, mastery_score,
                       attempts_count, last_practiced_at, syllabus_id
                FROM student_mastery
                WHERE student_id = $1 AND mastery_score < $2
                ORDER BY mastery_score ASC, last_practiced_at ASC NULLS FIRST
                LIMIT $3
                """,
                student_id, threshold, limit
            )
            return [dict(row) for row in rows]

    async def get_topics_due_for_review(
        self,
        student_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get topics due for spaced repetition review."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT subject, chapter, subtopic, mastery_score,
                       next_review_at, last_practiced_at, syllabus_id
                FROM student_mastery
                WHERE student_id = $1 AND next_review_at <= CURRENT_TIMESTAMP
                ORDER BY next_review_at ASC
                LIMIT $2
                """,
                student_id, limit
            )
            return [dict(row) for row in rows]

    # ==================== Logging ====================

    async def log_interaction(
        self,
        session_id: int,
        student_id: int,
        message_type: str,
        content: str,
        agent_type: Optional[str] = None,
        syllabus_id: Optional[int] = None,
        is_correct: Optional[bool] = None,
        score: Optional[float] = None,
        latency_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Log an interaction in the lesson logs."""
        async with self.pool.acquire() as conn:
            log_id = await conn.fetchval(
                """
                INSERT INTO lesson_logs (
                    session_id, student_id, message_type, content,
                    agent_type, syllabus_id, is_correct, score,
                    latency_ms, tokens_used, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
                """,
                session_id, student_id, message_type, content,
                agent_type, syllabus_id, is_correct, score,
                latency_ms, tokens_used,
                json.dumps(metadata) if metadata else '{}'
            )
            return log_id

    async def get_session_logs(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get interaction logs for a session."""
        async with self.pool.acquire() as conn:
            # First get the internal session ID
            session = await conn.fetchrow(
                "SELECT id FROM sessions WHERE session_id = $1",
                session_id
            )
            if not session:
                return []

            rows = await conn.fetch(
                """
                SELECT * FROM lesson_logs
                WHERE session_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                session['id'], limit
            )
            return [dict(row) for row in rows]

    # ==================== Quiz Attempts ====================

    async def record_quiz_attempt(
        self,
        student_id: int,
        syllabus_id: int,
        question_content: str,
        student_answer: Optional[str] = None,
        correct_answer: Optional[str] = None,
        is_correct: Optional[bool] = None,
        score: Optional[float] = None,
        feedback: Optional[str] = None,
        session_id: Optional[int] = None,
        question_type: str = 'open_ended',
        hints_used: int = 0,
        time_taken_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Record a quiz attempt."""
        async with self.pool.acquire() as conn:
            attempt_id = await conn.fetchval(
                """
                INSERT INTO quiz_attempts (
                    student_id, session_id, syllabus_id, question_content,
                    question_type, student_answer, correct_answer, is_correct,
                    score, feedback, hints_used, time_taken_seconds, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id
                """,
                student_id, session_id, syllabus_id, question_content,
                question_type, student_answer, correct_answer, is_correct,
                score, feedback, hints_used, time_taken_seconds,
                json.dumps(metadata) if metadata else '{}'
            )
            return attempt_id

    async def get_quiz_history(
        self,
        student_id: int,
        syllabus_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get quiz attempt history for a student."""
        async with self.pool.acquire() as conn:
            if syllabus_id:
                rows = await conn.fetch(
                    """
                    SELECT * FROM quiz_attempts
                    WHERE student_id = $1 AND syllabus_id = $2
                    ORDER BY attempted_at DESC
                    LIMIT $3
                    """,
                    student_id, syllabus_id, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM quiz_attempts
                    WHERE student_id = $1
                    ORDER BY attempted_at DESC
                    LIMIT $2
                    """,
                    student_id, limit
                )
            return [dict(row) for row in rows]

    # ==================== Statistics ====================

    async def get_student_statistics(self, student_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a student."""
        async with self.pool.acquire() as conn:
            stats = {}

            # Overall mastery
            mastery_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as topics_studied,
                    AVG(mastery_score) as avg_mastery,
                    SUM(attempts_count) as total_attempts,
                    SUM(correct_count) as total_correct
                FROM student_mastery
                WHERE student_id = $1
                """,
                student_id
            )
            stats['mastery'] = dict(mastery_stats) if mastery_stats else {}

            # Session stats
            session_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_sessions,
                    SUM(total_messages) as total_messages,
                    SUM(total_questions_asked) as total_questions,
                    SUM(total_questions_correct) as total_correct
                FROM sessions
                WHERE student_id = $1
                """,
                student_id
            )
            stats['sessions'] = dict(session_stats) if session_stats else {}

            # Recent activity
            recent = await conn.fetch(
                """
                SELECT subject, mastery_score, last_practiced_at
                FROM student_mastery
                WHERE student_id = $1
                ORDER BY last_practiced_at DESC NULLS LAST
                LIMIT 5
                """,
                student_id
            )
            stats['recent_topics'] = [dict(row) for row in recent]

            return stats
