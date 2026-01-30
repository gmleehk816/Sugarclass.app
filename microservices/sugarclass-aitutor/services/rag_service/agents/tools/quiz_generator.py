"""
Quiz Generator Tool for AI Tutor

LangChain tool for generating quiz questions based on content
and student mastery levels.
"""

import logging
import random
from typing import Dict, Any, Optional, List, Literal

try:
    from langchain_core.tools import tool, BaseTool
    from pydantic import BaseModel, Field
except ImportError:
    tool = None
    BaseTool = object
    BaseModel = object
    Field = lambda **kwargs: None

logger = logging.getLogger(__name__)


class QuizGeneratorInput(BaseModel):
    """Input schema for quiz generator tool."""
    action: Literal[
        "generate_question",
        "generate_quiz",
        "get_hint",
        "check_answer"
    ] = Field(
        description="Action to perform"
    )
    syllabus_id: Optional[int] = Field(
        default=None,
        description="Content ID to generate questions from"
    )
    content: Optional[str] = Field(
        default=None,
        description="Content text to generate questions from"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Subject area"
    )
    topic: Optional[str] = Field(
        default=None,
        description="Specific topic"
    )
    difficulty: Optional[str] = Field(
        default="core",
        description="Difficulty level: 'foundation', 'core', or 'extended'"
    )
    question_type: Optional[str] = Field(
        default="open_ended",
        description="Question type: 'multiple_choice', 'open_ended', 'fill_blank', 'true_false'"
    )
    num_questions: int = Field(
        default=1,
        description="Number of questions to generate"
    )
    question: Optional[str] = Field(
        default=None,
        description="Current question (for hints)"
    )
    correct_answer: Optional[str] = Field(
        default=None,
        description="Correct answer (for checking)"
    )
    student_answer: Optional[str] = Field(
        default=None,
        description="Student's answer to check"
    )
    hints_given: int = Field(
        default=0,
        description="Number of hints already given"
    )


class QuizGeneratorTool(BaseTool):
    """
    Tool for generating educational quiz questions.

    Generates questions based on content, checks answers,
    and provides progressive hints.
    """

    name: str = "quiz_generator"
    description: str = """Generate quiz questions and check answers.
    Use this to create practice questions from content,
    provide hints, and evaluate student responses."""

    args_schema: type = QuizGeneratorInput

    llm: Any = None
    db_pool: Any = None

    def __init__(self, llm: Any = None, db_pool: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm
        self.db_pool = db_pool

    def _run(self, **kwargs) -> Dict[str, Any]:
        """Synchronous run."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._arun(**kwargs))

    async def _arun(
        self,
        action: str,
        syllabus_id: Optional[int] = None,
        content: Optional[str] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: str = "core",
        question_type: str = "open_ended",
        num_questions: int = 1,
        question: Optional[str] = None,
        correct_answer: Optional[str] = None,
        student_answer: Optional[str] = None,
        hints_given: int = 0
    ) -> Dict[str, Any]:
        """Async execution of quiz generation actions."""
        try:
            if action == "generate_question":
                return await self._generate_question(
                    syllabus_id, content, subject, topic,
                    difficulty, question_type
                )

            elif action == "generate_quiz":
                return await self._generate_quiz(
                    syllabus_id, content, subject, topic,
                    difficulty, question_type, num_questions
                )

            elif action == "get_hint":
                return await self._get_hint(
                    question, correct_answer, hints_given
                )

            elif action == "check_answer":
                return await self._check_answer(
                    question, correct_answer, student_answer
                )

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Quiz generator error: {e}")
            return {"error": str(e)}

    async def _get_content(self, syllabus_id: int) -> Optional[str]:
        """Retrieve content from database by ID."""
        if self.db_pool is None:
            return None

        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT markdown_content FROM syllabus_hierarchy WHERE id = $1",
                    syllabus_id
                )
                return row["markdown_content"] if row else None
        except Exception as e:
            logger.error(f"Content retrieval error: {e}")
            return None

    async def _generate_question(
        self,
        syllabus_id: Optional[int],
        content: Optional[str],
        subject: Optional[str],
        topic: Optional[str],
        difficulty: str,
        question_type: str
    ) -> Dict[str, Any]:
        """Generate a single quiz question."""
        # Get content if syllabus_id provided
        if syllabus_id and not content:
            content = await self._get_content(syllabus_id)

        if not content:
            return {"error": "No content provided for question generation"}

        # Truncate content if too long
        content_preview = content[:3000] if len(content) > 3000 else content

        # Build prompt for question generation
        prompt = f"""Generate a {difficulty} difficulty {question_type} question based on this content.

Subject: {subject or 'General'}
Topic: {topic or 'Not specified'}
Content:
{content_preview}

Requirements:
- Difficulty: {difficulty} (foundation=easy, core=medium, extended=challenging)
- Question type: {question_type}
- The question should test understanding, not just memorization
- Provide a clear, unambiguous correct answer

"""

        if question_type == "multiple_choice":
            prompt += """Format your response as:
QUESTION: ### [Your question]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
CORRECT: [Letter of correct answer]
EXPLANATION: **[Brief explanation of why this is correct]**"""
        elif question_type == "true_false":
            prompt += """Format your response as:
QUESTION: ### [Your statement]
CORRECT: **[True or False]**
EXPLANATION: [Brief explanation]"""
        elif question_type == "fill_blank":
            prompt += """Format your response as:
QUESTION: ### [Sentence with _____ for the blank]
CORRECT: **[Word or phrase that fills the blank]**
EXPLANATION: [Brief explanation]"""
        else:  # open_ended
            prompt += """Format your response as:
QUESTION: ### [Your question]
CORRECT: **[Expected answer or key points]**
EXPLANATION: [What a good answer should include]"""

        try:
            if self.llm and hasattr(self.llm, 'ainvoke'):
                response = await self.llm.ainvoke(prompt)
                result_text = response.content if hasattr(response, 'content') else str(response)
            else:
                # Fallback: generate simple question
                return self._generate_fallback_question(content, question_type)

            # Parse the response
            return self._parse_question_response(result_text, question_type)

        except Exception as e:
            logger.error(f"Question generation error: {e}")
            return self._generate_fallback_question(content, question_type)

    def _parse_question_response(
        self,
        response: str,
        question_type: str
    ) -> Dict[str, Any]:
        """Parse LLM response into structured question data."""
        result = {
            "success": True,
            "question_type": question_type,
            "question": "",
            "correct_answer": "",
            "explanation": "",
            "options": None
        }

        lines = response.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith("QUESTION:"):
                result["question"] = line[9:].strip()
            elif line.startswith("CORRECT:"):
                result["correct_answer"] = line[8:].strip()
            elif line.startswith("EXPLANATION:"):
                result["explanation"] = line[12:].strip()
            elif question_type == "multiple_choice":
                if line.startswith(("A)", "B)", "C)", "D)")):
                    if result["options"] is None:
                        result["options"] = []
                    result["options"].append(line)

        # Validate we got the essential parts
        if not result["question"]:
            result["question"] = response.split('\n')[0]
        if not result["correct_answer"]:
            result["correct_answer"] = "See explanation"

        return result

    def _generate_fallback_question(
        self,
        content: str,
        question_type: str
    ) -> Dict[str, Any]:
        """Generate a simple fallback question without LLM."""
        # Extract key terms from content
        words = content.split()
        key_terms = [w for w in words if len(w) > 5 and w[0].isupper()][:5]

        if question_type == "true_false":
            return {
                "success": True,
                "question_type": "true_false",
                "question": f"This content discusses {key_terms[0] if key_terms else 'the topic'}.",
                "correct_answer": "True",
                "explanation": "Based on the provided content."
            }
        else:
            return {
                "success": True,
                "question_type": "open_ended",
                "question": f"Explain the main concept discussed in this section about {key_terms[0] if key_terms else 'the topic'}.",
                "correct_answer": "A complete answer should cover the key points from the content.",
                "explanation": "This is an open-ended question to test understanding."
            }

    async def _generate_quiz(
        self,
        syllabus_id: Optional[int],
        content: Optional[str],
        subject: Optional[str],
        topic: Optional[str],
        difficulty: str,
        question_type: str,
        num_questions: int
    ) -> Dict[str, Any]:
        """Generate multiple quiz questions."""
        questions = []

        for i in range(num_questions):
            q = await self._generate_question(
                syllabus_id, content, subject, topic,
                difficulty, question_type
            )
            if q.get("success"):
                q["question_number"] = i + 1
                questions.append(q)

        return {
            "success": True,
            "quiz": questions,
            "total_questions": len(questions),
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty
        }

    async def _get_hint(
        self,
        question: Optional[str],
        correct_answer: Optional[str],
        hints_given: int
    ) -> Dict[str, Any]:
        """Generate a progressive hint for the question."""
        if not question:
            return {"error": "No question provided"}

        if hints_given >= 3:
            return {
                "success": True,
                "hint": f"The answer is: {correct_answer}",
                "hint_level": "answer",
                "hints_remaining": 0
            }

        # Generate hint based on level
        hint_prompts = [
            f"Give a subtle hint for this question without revealing the answer:\nQuestion: {question}\nAnswer: {correct_answer}\nProvide a hint that points in the right direction.",
            f"Give a more direct hint for this question:\nQuestion: {question}\nAnswer: {correct_answer}\nProvide a hint that narrows down the possibilities.",
            f"Give a strong hint that almost reveals the answer:\nQuestion: {question}\nAnswer: {correct_answer}\nProvide a hint that makes the answer nearly obvious."
        ]

        try:
            if self.llm and hasattr(self.llm, 'ainvoke'):
                response = await self.llm.ainvoke(hint_prompts[hints_given])
                hint = response.content if hasattr(response, 'content') else str(response)
            else:
                # Fallback hints
                fallback_hints = [
                    "Think about the key concepts mentioned in the lesson.",
                    f"The answer relates to: {correct_answer[:20]}..." if correct_answer else "Review the main topic.",
                    f"The answer starts with: {correct_answer[0]}..." if correct_answer else "You're close!"
                ]
                hint = fallback_hints[hints_given]

            return {
                "success": True,
                "hint": hint,
                "hint_level": hints_given + 1,
                "hints_remaining": 2 - hints_given
            }

        except Exception as e:
            logger.error(f"Hint generation error: {e}")
            return {"error": str(e)}

    async def _check_answer(
        self,
        question: Optional[str],
        correct_answer: Optional[str],
        student_answer: Optional[str]
    ) -> Dict[str, Any]:
        """Check if student's answer is correct."""
        if not student_answer:
            return {"error": "No student answer provided"}

        if not correct_answer:
            return {"error": "No correct answer to compare against"}

        # Simple exact match check
        is_exact_match = student_answer.strip().lower() == correct_answer.strip().lower()

        if is_exact_match:
            return {
                "success": True,
                "is_correct": True,
                "score": 1.0,
                "feedback": "Correct! Well done!"
            }

        # Use LLM for semantic comparison
        if self.llm and hasattr(self.llm, 'ainvoke'):
            check_prompt = f"""Compare the student's answer to the correct answer.

Question: {question}
Correct Answer: {correct_answer}
Student's Answer: {student_answer}

Evaluate:
1. Is the student's answer correct, partially correct, or incorrect?
2. What score (0.0 to 1.0) would you give?
3. What feedback would help the student?

Respond in format:
VERDICT: [correct/partial/incorrect]
SCORE: [0.0-1.0]
FEEDBACK: [Your feedback. Use markdown signs like **bold** and *italics* for clarity.]"""

            try:
                response = await self.llm.ainvoke(check_prompt)
                result_text = response.content if hasattr(response, 'content') else str(response)

                # Parse response
                is_correct = "correct" in result_text.lower() and "incorrect" not in result_text.lower()
                score = 0.5  # Default

                for line in result_text.split('\n'):
                    if "SCORE:" in line:
                        try:
                            score = float(line.split(':')[1].strip())
                        except:
                            pass

                feedback = result_text
                if "FEEDBACK:" in result_text:
                    feedback = result_text.split("FEEDBACK:")[-1].strip()

                return {
                    "success": True,
                    "is_correct": is_correct or score >= 0.8,
                    "score": score,
                    "feedback": feedback,
                    "correct_answer": correct_answer
                }

            except Exception as e:
                logger.error(f"Answer checking error: {e}")

        # Fallback: simple comparison
        return {
            "success": True,
            "is_correct": False,
            "score": 0.0,
            "feedback": f"Not quite. The correct answer is: {correct_answer}",
            "correct_answer": correct_answer
        }


# Global instance for functional tool
_quiz_generator_instance: Optional[QuizGeneratorTool] = None


def init_quiz_generator(llm: Any = None, db_pool: Any = None) -> None:
    """Initialize the quiz generator with LLM and database pool."""
    global _quiz_generator_instance
    _quiz_generator_instance = QuizGeneratorTool(llm=llm, db_pool=db_pool)


if tool is not None:
    @tool
    async def quiz_generator_tool(
        action: str,
        syllabus_id: Optional[int] = None,
        content: Optional[str] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: str = "core",
        question_type: str = "open_ended",
        num_questions: int = 1,
        question: Optional[str] = None,
        correct_answer: Optional[str] = None,
        student_answer: Optional[str] = None,
        hints_given: int = 0
    ) -> Dict[str, Any]:
        """
        Generate quiz questions and check answers.

        Actions:
        - generate_question: Create a single question from content
        - generate_quiz: Create multiple questions
        - get_hint: Get a progressive hint for current question
        - check_answer: Evaluate student's answer

        Args:
            action: Action to perform
            syllabus_id: Content ID to generate from
            content: Direct content text
            subject: Subject area
            topic: Specific topic
            difficulty: 'foundation', 'core', or 'extended'
            question_type: 'multiple_choice', 'open_ended', 'fill_blank', 'true_false'
            num_questions: Number of questions for quiz
            question: Current question (for hints)
            correct_answer: Correct answer (for checking)
            student_answer: Student's answer to check
            hints_given: Hints already provided

        Returns:
            Generated question(s), hint, or answer evaluation
        """
        if _quiz_generator_instance is None:
            logger.warning("Quiz generator not initialized")
            return {"error": "Quiz generator not available"}

        return await _quiz_generator_instance._arun(
            action=action,
            syllabus_id=syllabus_id,
            content=content,
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            question_type=question_type,
            num_questions=num_questions,
            question=question,
            correct_answer=correct_answer,
            student_answer=student_answer,
            hints_given=hints_given
        )
else:
    quiz_generator_tool = None
