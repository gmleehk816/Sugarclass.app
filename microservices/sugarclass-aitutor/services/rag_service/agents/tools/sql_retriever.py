"""
SQL Retriever Tool for AI Tutor

LangChain tool for retrieving content from the SQL database.
Provides structured access to syllabus hierarchy and content.
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

logger = logging.getLogger(__name__)


class SQLRetrieverInput(BaseModel):
    """Input schema for SQL retriever tool."""
    syllabus_id: Optional[int] = Field(
        default=None,
        description="Specific syllabus hierarchy ID to retrieve"
    )
    syllabus: Optional[str] = Field(
        default=None,
        description="Syllabus/curriculum name (e.g., 'CIE_IGCSE', 'IB')"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Subject name (e.g., 'Mathematics', 'Physics')"
    )
    chapter: Optional[str] = Field(
        default=None,
        description="Chapter name"
    )
    subtopic: Optional[str] = Field(
        default=None,
        description="Subtopic name"
    )
    content_type: Optional[str] = Field(
        default=None,
        description="Content type: 'textbook', 'exercise', or 'exam_qa'"
    )
    difficulty_level: Optional[str] = Field(
        default=None,
        description="Difficulty level: 'core', 'extended', or 'foundation'"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results to return"
    )


class SQLRetrieverTool(BaseTool):
    """
    Tool for retrieving educational content from the SQL database.

    Retrieves syllabus hierarchy, textbook content, exercises,
    and exam questions based on various filters.
    """

    name: str = "sql_retriever"
    description: str = """Retrieve educational content from the database.
    Use this to get textbook content, exercises, or exam questions
    for a specific syllabus, subject, chapter, or topic.
    Returns structured content with metadata."""

    args_schema: type = SQLRetrieverInput

    db_pool: Any = None

    def __init__(self, db_pool: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.db_pool = db_pool

    def _run(
        self,
        syllabus_id: Optional[int] = None,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        chapter: Optional[str] = None,
        subtopic: Optional[str] = None,
        content_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Synchronous run - not recommended for async applications."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._arun(
                syllabus_id=syllabus_id,
                syllabus=syllabus,
                subject=subject,
                chapter=chapter,
                subtopic=subtopic,
                content_type=content_type,
                difficulty_level=difficulty_level,
                limit=limit
            )
        )

    async def _arun(
        self,
        syllabus_id: Optional[int] = None,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        chapter: Optional[str] = None,
        subtopic: Optional[str] = None,
        content_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Async retrieval of content from database."""
        if self.db_pool is None:
            logger.error("Database pool not initialized")
            return []

        try:
            async with self.db_pool.acquire() as conn:
                # Build query dynamically
                conditions = []
                params = []
                param_idx = 1

                if syllabus_id is not None:
                    conditions.append(f"id = ${param_idx}")
                    params.append(syllabus_id)
                    param_idx += 1

                if syllabus:
                    conditions.append(f"LOWER(syllabus) = LOWER(${param_idx})")
                    params.append(syllabus)
                    param_idx += 1

                if subject:
                    conditions.append(f"LOWER(subject) LIKE LOWER(${param_idx})")
                    params.append(f"%{subject}%")
                    param_idx += 1

                if chapter:
                    conditions.append(f"LOWER(chapter) LIKE LOWER(${param_idx})")
                    params.append(f"%{chapter}%")
                    param_idx += 1

                if subtopic:
                    conditions.append(f"LOWER(subtopic) LIKE LOWER(${param_idx})")
                    params.append(f"%{subtopic}%")
                    param_idx += 1

                if content_type:
                    conditions.append(f"content_type = ${param_idx}")
                    params.append(content_type)
                    param_idx += 1

                if difficulty_level:
                    conditions.append(f"difficulty_level = ${param_idx}")
                    params.append(difficulty_level)
                    param_idx += 1
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"

                query = f"""
                    SELECT id, syllabus, subject, chapter, subtopic,
                           content_type, markdown_content, difficulty_level,
                           word_count, metadata
                    FROM syllabus_hierarchy
                    WHERE {where_clause}
                    ORDER BY syllabus, subject, chapter, subtopic
                    LIMIT {limit}
                """

                rows = await conn.fetch(query, *params)

                results = []
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "syllabus": row["syllabus"],
                        "subject": row["subject"],
                        "chapter": row["chapter"],
                        "subtopic": row["subtopic"],
                        "content_type": row["content_type"],
                        "markdown_content": row["markdown_content"],
                        "difficulty_level": row["difficulty_level"],
                        "word_count": row["word_count"],
                        "metadata": row["metadata"]
                    })

                logger.info(f"SQL retriever found {len(results)} results")
                return results

        except Exception as e:
            logger.error(f"SQL retrieval error: {e}")
            return []


# Functional tool version using @tool decorator
_sql_retriever_instance: Optional[SQLRetrieverTool] = None


def init_sql_retriever(db_pool: Any) -> None:
    """Initialize the SQL retriever with a database pool."""
    global _sql_retriever_instance
    _sql_retriever_instance = SQLRetrieverTool(db_pool=db_pool)


if tool is not None:
    @tool
    async def sql_retriever_tool(
        syllabus_id: Optional[int] = None,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        chapter: Optional[str] = None,
        subtopic: Optional[str] = None,
        content_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve educational content from the SQL database.

        Use this to get textbook contxercises, or exam questions
        for a specific syllabus, subject, chapter, or topic.

        Args:
            syllabus_id: Specific content ID to retrieve
            syllabus: Curriculum name (e.g., 'CIE_IGCSE')
            subject: Subject name (e.g., 'Mathematics')
            chapter: Chapter name
            subtopic: Subtopic name
            content_type: 'textbook', 'exercise', or 'exam_qa'
            difficulty_level: 'core', 'extended', or 'foundation'
            limit: Maximum results (default 5)

        Returns:
            List of content records with markdown content and metadata
        """
        if _sql_retriever_instance is None:
            logger.warning("SQL retriever not initialized")
            return []

        return await _sql_retriever_instance._arun(
            syllabus_id=syllabus_id,
            syllabus=syllabus,
            subject=subject,
            chapter=chapter,
            subtopic=subtopic,
            content_type=content_type,
            difficulty_level=difficulty_level,
            limit=limit
        )
else:
    sql_retriever_tool = None
