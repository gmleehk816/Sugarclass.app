"""
Chapter List Retriever Tool for AI Tutor

Specialized tool for retrieving ALL chapters for a subject.
Unlike the standard RAG retriever which returns top-k similar documents,
this tool retrieves enough documents to get ALL unique chapters.
"""

import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict

try:
    from langchain_core.tools import tool, BaseTool
    from pydantic import BaseModel, Field
except ImportError:
    tool = None
    BaseTool = object
    BaseModel = object
    Field = lambda **kwargs: None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
except ImportError:
    QdrantClient = None
    Filter = None

logger = logging.getLogger(__name__)


class ChapterListRetrieverInput(BaseModel):
    """Input schema for chapter list retriever tool."""
    subject: str = Field(
        description="The subject to get chapters for (e.g., 'IB Music', 'ICT', 'Engineering')"
    )
    syllabus: Optional[str] = Field(
        default=None,
        description="Filter by syllabus/curriculum (e.g., 'CIE_IGCSE')"
    )


class ChapterListRetrieverTool(BaseTool):
    """
    Tool for retrieving ALL chapters for a subject.
    
    Unlike the standard RAG retriever which returns top-k similar documents,
    this tool retrieves enough documents to get ALL unique chapters for a subject.
    """

    name: str = "chapter_list_retriever"
    description: str = """Get ALL chapters for a specific subject.
    Use this when a student asks to list all chapters or topics in their textbook.
    Returns a comprehensive list of all available chapters."""

    args_schema: type = ChapterListRetrieverInput

    qdrant_client: Any = None
    embedding_model: Any = None
    collection_name: str = "aitutor_documents"

    def __init__(
        self,
        qdrant_client: Any = None,
        embedding_model: Any = None,
        collection_name: str = "aitutor_documents",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.qdrant_client = qdrant_client
        self.embedding_model = embedding_model
        self.collection_name = collection_name

    def _run(self, **kwargs) -> Dict[str, Any]:
        """Synchronous run."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._arun(**kwargs))

    def _extract_core_subject(self, subject: str) -> str:
        """Extract core subject name from full subject string.
        
        Examples:
        - "AQA GCSE Engineering" -> "Engineering"
        - "CIE IGCSE ICT" -> "ICT"
        - "IB Music" -> "Music"
        - "Engineering" -> "Engineering"
        """
        import re
        
        # Try to find known subjects
        known_subjects = [
            "Engineering", "ICT", "Computer Science", "Mathematics", "Maths",
            "Physics", "Chemistry", "Biology", "Science",
            "English", "Literature", "Language",
            "History", "Geography", "Economics", "Business",
            "Music", "Art", "Drama", "Theatre",
            "French", "Spanish", "German", "Chinese", "Mandarin",
            "Psychology", "Sociology", "Philosophy",
            "Accounting", "Statistics", "Combined Science"
        ]
        
        # Check if any known subject is in the string
        for known in sorted(known_subjects, key=len, reverse=True):  # Check longer subjects first
            if known.lower() in subject.lower():
                return known
        
        # Fallback: use last word as core subject
        words = subject.split()
        if len(words) > 1:
            return words[-1]
        
        return subject
    
    async def _arun(
        self,
        subject: str,
        syllabus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve all chapters for a subject."""
        if self.qdrant_client is None:
            logger.error("Qdrant client not initialized")
            return {"error": "Qdrant client not initialized"}

        try:
            # Extract core subject name to match Qdrant data
            core_subject = self._extract_core_subject(subject)
            logger.info(f"Extracted core subject: '{core_subject}' from '{subject}'")
            
            # Build filter conditions - use core subject for better matching
            filter_conditions = [
                FieldCondition(
                    key="subject",
                    match=MatchValue(value=core_subject)
                )
            ]

            if syllabus:
                filter_conditions.append(
                    FieldCondition(
                        key="syllabus",
                        match=MatchValue(value=syllabus)
                    )
                )
            
            # Create filter
            search_filter = Filter(must=filter_conditions) if Filter else None

            # Start with a reasonable limit and increase if needed
            # We want to get enough documents to cover all chapters
            limit = 500  # Large enough to get all chapters
            
            logger.info(f"Retrieving up to {limit} documents for subject: {subject}")

            # Perform search - use a generic query vector to get diverse results
            # Generate a simple embedding
            query_vector = self._generate_embedding(subject) or [0.1] * 384

            # Get documents using scroll to get ALL matching documents
            all_points = []
            offset = None
            batch_size = 100
            
            while len(all_points) < limit:
                results, offset = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                    scroll_filter=search_filter
                )
                
                if not results:
                    break
                
                all_points.extend(results)
                
                # Stop if we've got all documents (offset is None when done)
                if offset is None:
                    break
            
            logger.info(f"Retrieved {len(all_points)} documents for subject: {subject}")

            # Extract unique chapters
            chapters = set()
            chapter_documents = defaultdict(list)
            
            for point in all_points:
                payload = point.payload
                chapter = payload.get('chapter', 'Unknown')
                subtopic = payload.get('subtopic', '')
                content = payload.get('content', '')
                filename = payload.get('filename', '')
                
                if chapter and chapter != 'Unknown':
                    chapters.add(chapter)
                    # Store some context for each chapter
                    chapter_documents[chapter].append({
                        'subtopic': subtopic,
                        'content_preview': content[:200] if content else '',
                        'filename': filename
                    })
            
            # Sort chapters alphabetically
            sorted_chapters = sorted(list(chapters))
            
            # Build response
            result = {
                "subject": subject,
                "total_documents": len(all_points),
                "total_chapters": len(sorted_chapters),
                "chapters": [
                    {
                        "name": chapter,
                        "subtopics": len(set(doc['subtopic'] for doc in chapter_documents[chapter] if doc['subtopic'])),
                        "documents": len(chapter_documents[chapter])
                    }
                    for chapter in sorted_chapters
                ]
            }
            
            logger.info(f"Found {len(sorted_chapters)} unique chapters for {subject}")
            return result

        except Exception as e:
            logger.error(f"Chapter list retrieval error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        if self.embedding_model is None:
            return None

        try:
            # Handle different embedding model interfaces
            if hasattr(self.embedding_model, 'embed_query'):
                return self.embedding_model.embed_query(text)
            elif hasattr(self.embedding_model, 'encode'):
                result = self.embedding_model.encode(text)
                return result.tolist() if hasattr(result, 'tolist') else list(result)
            elif callable(self.embedding_model):
                return self.embedding_model(text)
            else:
                logger.warning("Unknown embedding model interface")
                return None
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None


# Global instance for functional tool
_chapter_list_retriever_instance: Optional[ChapterListRetrieverTool] = None


def init_chapter_list_retriever(
    qdrant_client: Any,
    embedding_model: Any,
    collection_name: str = "aitutor_documents"
) -> None:
    """Initialize the chapter list retriever."""
    global _chapter_list_retriever_instance
    _chapter_list_retriever_instance = ChapterListRetrieverTool(
        qdrant_client=qdrant_client,
        embedding_model=embedding_model,
        collection_name=collection_name
    )


if tool is not None:
    @tool
    async def chapter_list_tool(
        subject: str,
        syllabus: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ALL chapters for a specific subject.

        Use this when a student asks to list all chapters, topics, or sections
        in their textbook or curriculum material.

        Args:
            subject: The subject name (e.g., 'IB Music', 'ICT', 'Engineering')
            syllabus: Optional curriculum filter (e.g., 'CIE_IGCSE', 'IB')

        Returns:
            Dictionary with all chapters for the subject, including counts
            of subtopics and documents per chapter.
        """
        if _chapter_list_retriever_instance is None:
            logger.warning("Chapter list retriever not initialized")
            return {"error": "Chapter list retriever not initialized"}

        return await _chapter_list_retriever_instance._arun(
            subject=subject,
            syllabus=syllabus
        )
else:
    chapter_list_tool = None
