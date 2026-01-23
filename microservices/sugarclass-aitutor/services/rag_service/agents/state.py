"""
LangGraph State Definitions for AI Tutor

Defines the state schema for the multi-agent tutoring workflow.
"""

from typing import List, Dict, Any, Optional, Literal, Annotated
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import BaseModel, Field
import operator


class StudentContext(BaseModel):
    """Student context information for personalization."""
    student_id: int
    user_id: str
    name: Optional[str] = None
    grade_level: Optional[str] = None
    curriculum: Optional[str] = None
    preferred_language: str = "en"
    learning_style: Optional[str] = None

    # Current mastery data
    mastery_scores: Dict[str, float] = Field(default_factory=dict)
    weak_topics: List[Dict[str, Any]] = Field(default_factory=list)
    topics_due_review: List[Dict[str, Any]] = Field(default_factory=list)


class ContentContext(BaseModel):
    """Retrieved content context."""
    syllabus_id: Optional[int] = None
    syllabus: Optional[str] = None
    subject: Optional[str] = None
    chapter: Optional[str] = None
    subtopic: Optional[str] = None
    content_type: Optional[str] = None
    difficulty_level: str = "core"

    # Retrieved content
    textbook_content: Optional[str] = None
    exercises: List[Dict[str, Any]] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)

    # RAG results
    rag_results: List[Dict[str, Any]] = Field(default_factory=list)

    # Chapter list from Qdrant
    chapter_list: Optional[str] = None
    chapter_list_data: Dict[str, Any] = Field(default_factory=dict)

    # Subject mismatch handling
    subject_mismatch: bool = False
    requested_query: Optional[str] = None
    current_subject: Optional[str] = None
    skip_sqlite: bool = False


class QuizState(BaseModel):
    """State for quiz/assessment."""
    is_active: bool = False
    current_question: Optional[str] = None
    question_type: str = "open_ended"
    correct_answer: Optional[str] = None
    hints_given: int = 0
    max_hints: int = 3
    attempts: int = 0

    # For multi-question quizzes
    questions_asked: int = 0
    questions_correct: int = 0
    quiz_topic: Optional[str] = None


class Message(BaseModel):
    """A message in the conversation."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def merge_content(old: ContentContext, new: Any) -> ContentContext:
    """Reducer to merge content context updates."""
    if new is None:
        return old
    
    # If new is already a ContentContext, we still want to merge its non-None fields
    # or just trust it if it's a full replacement.
    # But usually LangGraph nodes return dicts for partial updates.
    if isinstance(new, dict):
        # Get existing data
        old_data = old.model_dump()
        # Update with new data
        old_data.update(new)
        return ContentContext(**old_data)
    
    return new


def merge_quiz(old: QuizState, new: Any) -> QuizState:
    """Reducer to merge quiz state updates."""
    if new is None:
        return old
    
    if isinstance(new, dict):
        old_data = old.model_dump()
        old_data.update(new)
        return QuizState(**old_data)
    
    return new


def merge_messages(old: List[Message], new: Any) -> List[Message]:
    """Reducer to merge message history."""
    if not new:
        return old
    
    if isinstance(new, list):
        # If the new list contains messages already in the old list, 
        # we need to be careful not to duplicate.
        # But for simplicity, if it's a full list replacement (like our nodes do),
        # we check if it's longer than the old one.
        if len(new) > len(old):
            return new
        # If it's just new messages to append
        return old + new
        
    return old


class TutorState(BaseModel):
    """
    Main state for the AI Tutor LangGraph workflow.

    This state is passed between agents and maintains the full
    context of the tutoring session.
    """

    # Session identification
    session_id: str
    student: StudentContext

    # Conversation history (using Annotated for reducer)
    messages: Annotated[List[Message], merge_messages] = Field(default_factory=list)

    # Current user input
    user_input: str = ""

    # Agent routing
    current_agent: Literal["supervisor", "planner", "teacher", "grader"] = "supervisor"
    next_agent: Optional[str] = None

    # Intent classification
    intent: Optional[str] = None  # "learn", "practice", "review", "question", "off_topic"
    confidence: float = 0.0

    # Content context
    content: Annotated[ContentContext, merge_content] = Field(default_factory=ContentContext)

    # Quiz state
    quiz: Annotated[QuizState, merge_quiz] = Field(default_factory=QuizState)

    # Response generation
    response: str = ""
    response_type: str = "text"  # "text", "quiz", "explanation", "feedback"

    # Tool results
    tool_results: Dict[str, Any] = Field(default_factory=dict)

    # Session metadata
    turn_count: int = 0
    session_start: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)

    # Flags
    needs_clarification: bool = False
    should_end_session: bool = False
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


def create_initial_state(
    session_id: str,
    student_id: int,
    user_id: str,
    **student_kwargs
) -> TutorState:
    """Create initial state for a new tutoring session."""
    student = StudentContext(
        student_id=student_id,
        user_id=user_id,
        **student_kwargs
    )

    return TutorState(
        session_id=session_id,
        student=student
    )


# State update helpers
def add_message(state: TutorState, role: str, content: str, agent_type: str = None) -> TutorState:
    """Add a message to the conversation history."""
    message = Message(
        role=role,
        content=content,
        agent_type=agent_type
    )
    state.messages.append(message)
    state.last_activity = datetime.now()
    return state


def update_content_context(state: TutorState, **kwargs) -> TutorState:
    """Update the content context."""
    for key, value in kwargs.items():
        if hasattr(state.content, key):
            setattr(state.content, key, value)
    return state


def start_quiz(
    state: TutorState,
    question: str,
    correct_answer: str,
    question_type: str = "open_ended",
    topic: str = None
) -> TutorState:
    """Start a quiz question."""
    state.quiz.is_active = True
    state.quiz.current_question = question
    state.quiz.correct_answer = correct_answer
    state.quiz.question_type = question_type
    state.quiz.hints_given = 0
    state.quiz.attempts = 0
    if topic:
        state.quiz.quiz_topic = topic
    return state


def end_quiz_question(state: TutorState, is_correct: bool) -> TutorState:
    """End the current quiz question."""
    state.quiz.is_active = False
    state.quiz.questions_asked += 1
    if is_correct:
        state.quiz.questions_correct += 1
    state.quiz.current_question = None
    state.quiz.correct_answer = None
    return state
