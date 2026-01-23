"""
Profile Manager Tool for AI Tutor

LangChain tool for managing student profiles, mastery tracking,
and learning progress.
"""

import logging
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime

try:
    from langchain_core.tools import tool, BaseTool
    from pydantic import BaseModel, Field
except ImportError:
    tool = None
    BaseTool = object
    BaseModel = object
    Field = lambda **kwargs: None

logger = logging.getLogger(__name__)


class ProfileManagerInput(BaseModel):
    """Input schema for profile manager tool."""
    action: Literal[
        "get_profile",
        "update_profile",
        "get_mastery",
        "update_mastery",
        "get_weak_topics",
        "get_review_topics",
        "get_statistics"
    ] = Field(
        description="Action to perform on the student profile"
    )
    student_id: int = Field(
        description="Internal student ID"
    )
    syllabus_id: Optional[int] = Field(
        default=None,
        description="Syllabus hierarchy ID for mastery updates"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Subject for filtering mastery data"
    )
    chapter: Optional[str] = Field(
        default=None,
        description="Chapter name for mastery updates"
    )
    subtopic: Optional[str] = Field(
        default=None,
        description="Subtopic name for mastery updates"
    )
    is_correct: Optional[bool] = Field(
        default=None,
        description="Whether the student's answer was correct"
    )
    score: Optional[float] = Field(
        default=None,
        description="Score for the interaction (0.0 to 1.0)"
    )
    updates: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Profile fields to update"
    )


class ProfileManagerTool(BaseTool):
    """
    Tool for managing student profiles and mastery tracking.

    Handles:
    - Profile retrieval and updates
    - Mastery score tracking with spaced repetition
    - Identifying weak topics for review
    - Learning statistics
    """

    name: str = "profile_manager"
    description: str = """Manage student profiles and track learning progress.
    Use this to get/update student info, track mastery scores,
    find weak topics that need review, and get learning statistics."""

    args_schema: type = ProfileManagerInput

    db_manager: Any = None

    def __init__(self, db_manager: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager

    def _run(self, **kwargs) -> Dict[str, Any]:
        """Synchronous run."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._arun(**kwargs))

    async def _arun(
        self,
        action: str,
        student_id: int,
        syllabus_id: Optional[int] = None,
        subject: Optional[str] = None,
        chapter: Optional[str] = None,
        subtopic: Optional[str] = None,
        is_correct: Optional[bool] = None,
        score: Optional[float] = None,
        updates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async execution of profile management actions."""
        if self.db_manager is None:
            logger.error("Datr not initialized")
            return {"error": "Database manager not available"}

        try:
            if action == "get_profile":
                return await self._get_profile(student_id)

            elif action == "update_profile":
                return await self._update_profile(student_id, updates or {})

            elif action == "get_mastery":
                return await self._get_mastery(student_id, subject)

            elif action == "update_mastery":
                return await self._update_mastery(
                    student_id, syllabus_id, subject,
                    chapter, subtopic, is_correct, score
                )

            elif action == "get_weak_topics":
                return await self._get_weak_topics(student_id)

            elif action == "get_review_topics":
                return await self._get_review_topics(student_id)

            elif action == "get_statistics":
                return await self._get_statistics(student_id)

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Profile manager error: {e}")
            return {"error": str(e)}

    async def _get_profile(self, student_id: int) -> Dict[str, Any]:
        """Get student profile by ID."""
        profile = await self.db_manager.get_student_by_id(student_id)
        if profile:
            return {"success": True, "profile": profile}
        return {"success": False, "error": "Student not found"}

    async def _update_profile(
        self,
        student_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update student profile fields."""
        # Get user_id first
        profile = await self.db_manager.get_student_by_id(student_id)
        if not profile:
            return {"success": False, "error": "Student not found"}

        success = await self.db_manager.update_student(
            profile["user_id"],
            updates
        )
        return {"success": success}

    async def _get_mastery(
        self,
        student_id: int,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get mastery scores for a student."""
        scores = await self.db_manager.get_mastery_scores(student_id, subject)
        return {
            "success": True,
            "mastery_scores": scores,
            "count": len(scores)
        }

    async def _update_mastery(
        self,
        student_id: int,
        syllabus_id: Optional[int],
        subject: Optional[str],
        chapter: Optional[str],
        subtopic: Optional[str],
        is_correct: Optional[bool],
        score: Optional[float]
    ) -> Dict[str, Any]:
        """Update mastery score for a topic."""
        if syllabus_id is None:
            return {"success": False, "error": "syllabus_id required"}

        if is_correct is None:
            return {"success": False, "error": "is_correct required"}

        # Calculate score delta based on correctness
        if score is not None:
            score_delta = (score - 0.5) * 0.2  # Scale to reasonable delta
        else:
            score_delta = 0.1 if is_correct else -0.05

        result = await self.db_manager.update_mastery(
            student_id=student_id,
            syllabus_id=syllabus_id,
            subject=subject or "Unknown",
            chapter=chapter or "Unknown",
            subtopic=subtopic or "Unknown",
            score_delta=score_delta,
            is_correct=is_correct
        )

        return {"success": True, "mastery_update": result}

    async def _get_weak_topics(self, student_id: int) -> Dict[str, Any]:
        """Get topics where student needs improvement."""
        weak_topics = await self.db_manager.get_weak_topics(
            student_id,
            threshold=0.5,
            limit=5
        )
        return {
            "success": True,
            "weak_topics": weak_topics,
            "count": len(weak_topics)
        }

    async def _get_review_topics(self, student_id: int) -> Dict[str, Any]:
        """Get topics due for spaced repetition review."""
        review_topics = await self.db_manager.get_topics_due_for_review(
            student_id,
            limit=5
        )
        return {
            "success": True,
            "review_topics": review_topics,
            "count": len(review_topics)
        }

    async def _get_statistics(self, student_id: int) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        stats = await self.db_manager.get_student_statistics(student_id)
        return {"success": True, "statistics": stats}


# Global instance
_profile_manager_instance: Optional[ProfileManagerTool] = None


def init_profile_manager(db_manager: Any) -> None:
    """Initialize the profile manager with a database manager."""
    global _profile_manager_instance
    _profile_manager_instance = ProfileManagerTool(db_manager=db_manager)


if tool is not None:
    @tool
    async def profile_manager_tool(
        action: str,
        student_id: int,
        syllabus_id: Optional[int] = None,
        subject: Optional[str] = None,
        chapter: Optional[str] = None,
        subtopic: Optional[str] = None,
        is_correct: Optional[bool] = None,
        score: Optional[float] = None,
        updates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Manage student profiles and track learning progress.

        Actions:
        - get_profile: Get student profile information
        - update_profile: Update profile fields
        - get_mastery: Get mastery scores (optionally filtered by subject)
        - update_mastery: Update mastery after answering a question
        - get_weak_topics: Find topics needing improvement
        - get_review_topics: Get topics due for spaced repetition review
        - get_statistics: Get comprehensive learning statistics

        Args:
            action: The action to perform
            student_id: Internal student ID
            syllabus_id: Content ID for mastery updates
            subject: Subject filter
            chapter: Chapter name
            subtopic: Subtopic name
            is_correct: Whether answer was correct (for mastery updates)
            score: Score value 0.0-1.0 (for mastery updates)
            updates: Dict of profile fields to update

        Returns:
            Result of the action with success status
        """
        if _profile_manager_instance is None:
            logger.warning("Profile manager not initialized")
            return {"error": "Profile manager not available"}

        return await _profile_manager_instance._arun(
            action=action,
            student_id=student_id,
            syllabus_id=syllabus_id,
            subject=subject,
            chapter=chapter,
            subtopic=subtopic,
            is_correct=is_correct,
            score=score,
            updates=updates
        )
else:
    profile_manager_tool = None
