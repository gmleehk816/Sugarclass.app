"""
PostgreSQL Retriever Tool for AI Tutor

Retrieves content from PostgreSQL tutor_content database.
Works with the migrated syllabus_hierarchy table structure.
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

try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger(name=__name__)


class PostgresRetrieverInput(BaseModel):
    """Input schema for PostgreSQL retriever tool."""
    syllabus: Optional[str] = Field(
        default=None,
        description="Syllabus/curriculum name (e.g., 'Aqa gcse', 'cie_igcse')"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Subject name (e.g., 'Information and Communication Technology')"
    )
    chapter: Optional[str] = Field(
        default=None,
        description="Chapter name (e.g., 'Types and components of computer systems')"
    )
    subtopic: Optional[str] = Field(
        default=None,
        description="Subtopic name (e.g., 'Hardware and software')"
    )
    content_type: Optional[str] = Field(
        default=None,
        description="Filter by content type: 'textbook', 'exercise'"
    )
    difficulty_level: Optional[str] = Field(
        default=None,
        description="Filter by difficulty: 'foundation', 'core', 'extended'"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results to return"
    )


class PostgresRetrieverTool(BaseTool):
    """
    Tool for retrieving educational content from PostgreSQL database.
    
    Uses the syllabus_hierarchy table that was migrated from SQLite.
    Content is organized by: syllabus > subject > chapter > subtopic > chunk.
    """

    name: str = "postgres_retriever"
    description: str = """Retrieve educational content from PostgreSQL database.
    Use this to get textbook content for a specific syllabus, subject, chapter, or subtopic.
    Returns structured content with markdown text and metadata."""

    args_schema: type = PostgresRetrieverInput

    def __init__(self, pool: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.pool = pool

    def _run(
        self,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        chapter: Optional[str] = None,
        subtopic: Optional[str] = None,
        content_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Synchronous retrieval from PostgreSQL database."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._arun(
            syllabus=syllabus,
            subject=subject,
            chapter=chapter,
            subtopic=subtopic,
            content_type=content_type,
            difficulty_level=difficulty_level,
            limit=limit
        ))

    async def _arun(
        self,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        chapter: Optional[str] = None,
        subtopic: Optional[str] = None,
        content_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Async retrieval from PostgreSQL database."""
        if self.pool is None:
            logger.error("PostgreSQL pool not initialized")
            return []

        try:
            async with self.pool.acquire() as conn:
                # Build query with filters
                query = """
                    SELECT 
                        sh.id,
                        sh.syllabus,
                        sh.subject,
                        sh.chapter,
                        sh.subtopic,
                        sh.content_type,
                        sh.markdown_content,
                        sh.difficulty_level,
                        sh.word_count,
                        sh.file_path
                    FROM syllabus_hierarchy sh
                    WHERE 1=1
                """
                params = []

                if syllabus:
                    query += " AND LOWER(sh.syllabus) LIKE LOWER($1)"
                    params.append(f"%{syllabus}%")

                if subject:
                    query += " AND LOWER(sh.subject) LIKE LOWER($2)"
                    params.append(f"%{subject}%")

                if chapter:
                    query += " AND LOWER(sh.chapter) LIKE LOWER($3)"
                    params.append(f"%{chapter}%")

                if subtopic:
                    query += " AND LOWER(sh.subtopic) LIKE LOWER($4)"
                    params.append(f"%{subtopic}%")

                if content_type:
                    query += " AND sh.content_type = $5"
                    params.append(content_type)

                if difficulty_level:
                    query += " AND sh.difficulty_level = $6"
                    params.append(difficulty_level)

                query += f" ORDER BY sh.id LIMIT $7"
                params.append(limit)

                # Execute query
                rows = await conn.fetch(query, *params)

                results = []
                for row in rows:
                    results.append({
                        "id": row['id'],
                        "syllabus": row['syllabus'],
                        "subject": row['subject'],
                        "chapter": row['chapter'],
                        "subtopic": row['subtopic'],
                        "content_type": row['content_type'],
                        "content": row['markdown_content'],
                        "difficulty_level": row['difficulty_level'],
                        "word_count": row['word_count'],
                        "file_path": row['file_path']
                    })

                logger.info(f"PostgreSQL retriever found {len(results)} results")
                return results

        except Exception as e:
            logger.error(f"PostgreSQL retrieval error: {e}")
            return []


# Functional tool version using @tool decorator
_postgres_retriever_instance: Optional[PostgresRetrieverTool] = None


def init_postgres_retriever(pool: Any = None) -> None:
    """Initialize the PostgreSQL retriever."""
    global _postgres_retriever_instance
    _postgres_retriever_instance = PostgresRetrieverTool(pool=pool)


if tool is not None:
    @tool
    async def postgres_retriever_tool(
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
               chapter: Optional[str] = None,
        subtopic: Optional[str] = None,
        content_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve educational content from PostgreSQL database.

        Use this to get textbook content for a specific syllabus, subject, chapter, or subtopic.

        Args:
            syllabus: Curriculum name (e.g., 'Aqa gcse', 'cie_igcse')
            subject: Subject name (e.g., 'Information and Communication Technology')
            chapter: Topic/chapter name
            subtopic: Subtopic name
            content_type: Filter by type ('textbook', 'exercise')
            difficulty_level: Filter by difficulty ('foundation', 'core', 'extended')
            limit: Maximum results (default 5)

        Returns:
            List of content records with markdown content and metadata
        """
        if _postgres_retriever_instance is None:
            logger.warning("PostgreSQL retriever not initialized")
            return []

        return await _postgres_retriever_instance._arun(
            syllabus=syllabus,
            subject=subject,
            chapter=chapter,
            subtopic=subtopic,
            content_type=content_type,
            difficulty_level=difficulty_level,
            limit=limit
        )
else:
    postgres_retriever_tool = None