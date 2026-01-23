"""
SQLite Retriever Tool for AI Tutor

Retrieves content from SQLite database (rag_content.db).
Works with the existing database schema that has separate tables for syllabuses, subjects, topics, subtopics, and content.
"""

import logging
from typing import Dict, Any, Optional, List

try:
    from langchain_core.tools import tool, BaseTool
    from pydantic import BaseModel, Field
except ImportError:
    tool = None
    BaseTool = object
    BaseModel = object
    Field = lambda **kwargs: None

import sqlite3

logger = logging.getLogger(__name__)


class SQLiteRetrieverInput(BaseModel):
    """Input schema for SQLite retriever tool."""
    syllabus: Optional[str] = Field(
        default=None,
        description="Syllabus/curriculum name (e.g., 'Aqa gcse', 'cie_igcse')"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Subject name (e.g., 'Information and Communication Technology')"
    )
    topic: Optional[str] = Field(
        default=None,
        description="Topic/chapter name (e.g., 'Types and components of computer systems')"
    )
    subtopic: Optional[str] = Field(
        default=None,
        description="Subtopic name (e.g., 'Hardware and software')"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results to return"
    )


class SQLiteRetrieverTool(BaseTool):
    """
    Tool for retrieving educational content from SQLite database.
    
    The database has a normalized schema:
    - syllabuses: curriculum information
    - subjects: subjects under each syllabus
    - topics: topics within subjects
    - subtopics: detailed subtopics
    - content_raw: actual content markdown for each subtopic
    - content_processed: processed HTML content
    """

    name: str = "sqlite_retriever"
    description: str = """Retrieve educational content from the SQLite database.
    Use this to get textbook content for a specific syllabus, subject, topic, or subtopic.
    Returns structured content with markdown text."""

    args_schema: type = SQLiteRetrieverInput

    db_path: str = "/app/content/rag_content.db"

    def __init__(self, db_path: str = "/app/content/rag_content.db", **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path

    def _run(
        self,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        subtopic: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Synchronous retrieval of content from SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return dict-like rows
            cursor = conn.cursor()

            # Build query with joins to get content
            query = """
                SELECT 
                    s.name as syllabus_name,
                    sub.name as subject_name,
                    t.name as topic_name,
                    st.name as subtopic_name,
                    st.order_num as subtopic_order,
                    cr.title as content_title,
                    cr.markdown_content,
                    cr.char_count,
                    cr.source_file
                FROM content_raw cr
                LEFT JOIN subtopics st ON cr.subtopic_id = st.id
                LEFT JOIN topics t ON st.topic_id = t.id
                LEFT JOIN subjects sub ON t.subject_id = sub.id
                LEFT JOIN syllabuses s ON sub.syllabus_id = s.id
                WHERE 1=1
            """

            params = []

            if syllabus:
                query += " AND LOWER(s.name) LIKE LOWER(?)"
                params.append(f"%{syllabus}%")

            if subject:
                query += " AND LOWER(sub.name) LIKE LOWER(?)"
                params.append(f"%{subject}%")

            if topic:
                # Search in BOTH topic names AND subtopic names
                query += " AND (LOWER(t.name) LIKE LOWER(?) OR LOWER(st.name) LIKE LOWER(?))"
                params.append(f"%{topic}%")
                params.append(f"%{topic}%")

            if subtopic:
                query += " AND LOWER(st.name) LIKE LOWER(?)"
                params.append(f"%{subtopic}%")

            query += f" ORDER BY st.order_num LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append({
                    "syllabus": row["syllabus_name"],
                    "subject": row["subject_name"],
                    "chapter": row["topic_name"],
                    "subtopic": row["subtopic_name"],
                    "title": row["content_title"],
                    "content": row["markdown_content"],
                    "word_count": row["char_count"] if row["char_count"] else 0,
                    "source_file": row["source_file"]
                })

            logger.info(f"SQLite retriever found {len(results)} results")
            conn.close()
            return results

        except Exception as e:
            logger.error(f"SQLite retrieval error: {e}")
            return []


# Functional tool version using @tool decorator
_sqlite_retriever_instance: Optional[SQLiteRetrieverTool] = None


def init_sqlite_retriever(db_path: str = "/app/content/rag_content.db") -> None:
    """Initialize the SQLite retriever."""
    global _sqlite_retriever_instance
    _sqlite_retriever_instance = SQLiteRetrieverTool(db_path=db_path)


if tool is not None:
    @tool
    def sqlite_retriever_tool(
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        subtopic: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve educational content from the SQLite database.

        Use this to get textbook content for a specific syllabus, subject, topic, or subtopic.

        Args:
            syllabus: Curriculum name (e.g., 'Aqa gcse', 'cie_igcse')
            subject: Subject name (e.g., 'Information and Communication Technology')
            topic: Topic/chapter name
            subtopic: Subtopic name
            limit: Maximum results (default 5)

        Returns:
            List of content records with markdown content and metadata
        """
        if _sqlite_retriever_instance is None:
            logger.warning("SQLite retriever not initialized")
            return []

        return _sqlite_retriever_instance._run(
            syllabus=syllabus,
            subject=subject,
            topic=topic,
            subtopic=subtopic,
            limit=limit
        )
else:
    sqlite_retriever_tool = None