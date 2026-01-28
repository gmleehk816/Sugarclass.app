"""
LangGraph Workflow for AI Tutor

Implements a multi-agent tutoring workflow with:
- Supervisor: Routes to appropriate agent based on intent
- Planner: Creates learning plans and retrieves content
- Teacher: Delivers explanations and lessons
- Grader: Evaluates answers and provides feedback
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Literal, List
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    StateGraph = None
    END = None
    MemorySaver = None

try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.output_parsers import StrOutputParser
except ImportError:
    HumanMessage = None
    AIMessage = None
    SystemMessage = None
    ChatPromptTemplate = None

from .state import TutorState, Message, add_message, ContentContext, QuizState, StudentContext

logger = logging.getLogger(__name__)


class TutorWorkflow:
    """
    LangGraph-based multi-agent tutoring workflow.

    Agents:
    - Supervisor: Classifies intent and routes to appropriate agent
    - Planner: Retrieves content and creates learning plans
    - Teacher: Explains concepts and delivers lessons
    - Grader: Evaluates student answers and provides feedback
    """

    def __init__(
        self,
        llm: Any,
        tools: Dict[str, Any] = None,
        checkpointer: Any = None
    ):
        """
        Initialize the tutor workflow.

        Args:
            llm: The language model to use
            tools: Dictionary of tools (sql_retriever, rag_retriever, etc.)
            checkpointer: LangGraph checkpointer for persistence
        """
        self.llm = llm
        self.tools = tools or {}
        self.checkpointer = checkpointer or (MemorySaver() if MemorySaver else None)
        self.graph = None

        self._build_graph()

    def _build_graph(self) -> None:
        """Build the LangGraph state graph."""
        if StateGraph is None:
            logger.warning("LangGraph not installed, workflow disabled")
            return

        # Create the state graph
        workflow = StateGraph(TutorState)

        # Add nodes for each agent
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("teacher", self._teacher_node)
        workflow.add_node("grader", self._grader_node)

        # Set entry point
        workflow.set_entry_point("supervisor")

        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {
                "planner": "planner",
                "teacher": "teacher",
                "grader": "grader",
                "end": END
            }
        )

        # Add edges from other agents back to supervisor or end
        workflow.add_conditional_edges(
            "planner",
            self._route_after_planner,
            {
                "teacher": "teacher",
                "supervisor": "supervisor",
                "end": END
            }
        )

        workflow.add_edge("teacher", END)
        workflow.add_edge("grader", END)

        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        logger.info("Tutor workflow graph compiled successfully")

    def _route_from_supervisor(self, state: TutorState) -> str:
        """Route from supervisor based on classified intent."""
        if state.should_end_session:
            return "end"

        if state.error:
            return "end"

        intent = state.intent

        # If quiz is active and user provided answer to grader
        if state.quiz.is_active and state.user_input:
            return "grader"

        # Route based on intent
        if intent in ["learn", "review", "question"]:
            return "planner"
        elif intent == "practice":
            if state.content.syllabus_id:
                return "teacher"  # Already have content, generate quiz
            return "planner"  # Need to get content first
        elif intent == "off_topic":
            return "teacher"  # Teacher handles off-topic gracefully
        else:
            return "planner"  # Default to planner

    def _route_after_planner(self, state: TutorState) -> str:
        """Route after planner has retrieved content."""
        if state.error:
            return "end"

        # Always go to teacher, even if no content found
        # Teacher can handle "no content" case appropriately
        # This prevents infinite loop when RAG/SQLite return 0 results
        return "teacher"

    def _detect_response_complexity(self, user_input: str, conversation_history: str = "") -> dict:
        """
        Intelligently analyze question complexity and determine appropriate response depth.
        Considers question type, complexity, conversational context, and topic nature.
        
        Returns dict with 'complexity_level' and 'response_guidelines'
        """
        if not user_input:
            return {"complexity_level": "simple", "max_sentences": 2}
            
        lower_input = user_input.lower()
        word_count = len(lower_input.split())
        sentence_count = len(user_input.split('.'))
        
        # Initialize complexity factors
        complexity_score = 0  # Higher = needs more detailed response
        factors = []
        
        # Factor 1: Explicit explanation requests (HIGH IMPACT)
        explanation_phrases = [
            "explain", "explain in detail", "describe", "describe in detail",
            "tell me about", "tell me more about", "tell me everything about",
            "in detail", "more detail", "give me details", "elaborate", "elaborate on",
            "break it down", "break down", "step by step", "step-by-step",
            "teach me", "teach me about", "help me understand", "clarify"
        ]
        if any(phrase in lower_input for phrase in explanation_phrases):
            complexity_score += 3
            factors.append("explicit_explanation_request")
        
        # Factor 2: Question word types (HIGH IMPACT)
        # Why/how questions typically need explanation
        if lower_input.startswith("why ") or "why does" in lower_input or "why is" in lower_input:
            complexity_score += 2
            factors.append("why_question")
        elif lower_input.startswith("how ") or "how does" in lower_input or "how is" in lower_input:
            if "how to" not in lower_input:  # "how to" might be simple instructions
                complexity_score += 2
                factors.append("how_question")
        
        # Factor 3: Multi-part questions (HIGH IMPACT)
        # Contains "and" connecting multiple concepts
        if " and " in lower_input and word_count > 8:
            complexity_score += 2
            factors.append("multi_part_question")
        
        # Factor 4: Question length (MEDIUM IMPACT)
        if word_count > 10:
            complexity_score += 1
            factors.append("long_question")
        elif word_count > 6:
            complexity_score += 0.5
            factors.append("medium_length_question")
        
        # Factor 5: Conversational context (MEDIUM IMPACT)
        # Follow-up questions usually deserve more detail
        if conversation_history and len(conversation_history) > 0:
            follow_up_indicators = [
                "what about", "can you also", "what if", "what happens when",
                "does that mean", "so", "but", "then", "next"
            ]
            if any(indicator in lower_input for indicator in follow_up_indicators):
                complexity_score += 1.5
                factors.append("follow_up_question")
        
        # Factor 6: Simple definition questions (LOW IMPACT - reduces complexity)
        simple_patterns = [
            ("what is", 3), ("what are", 3), ("who is", 3), ("who are", 3),
            ("define", 4), ("meaning of", 4)
        ]
        for pattern, max_words in simple_patterns:
            if lower_input.startswith(pattern) and word_count <= max_words:
                complexity_score -= 1
                factors.append(f"simple_definition_{pattern.replace(' ', '_')}")
                break
        
        # Factor 7: Comparative/analytical questions (HIGH IMPACT)
        comparative_words = ["difference", "compare", "contrast", "vs", "versus", "between", "better", "worse"]
        if any(word in lower_input for word in comparative_words):
            complexity_score += 2
            factors.append("comparative_question")
        
        # Factor 8: Process/sequence questions (HIGH IMPACT)
        process_words = ["process", "sequence", "steps", "order", "procedure", "workflow", "algorithm"]
        if any(word in lower_input for word in process_words):
            complexity_score += 2
            factors.append("process_question")
        
        # Factor 9: Technical/complex topics (MEDIUM IMPACT)
        technical_indicators = [
            "function", "mechanism", "algorithm", "protocol", "structure",
            "architecture", "system", "theory", "principle", "concept"
        ]
        if any(indicator in lower_input for indicator in technical_indicators):
            complexity_score += 1
            factors.append("technical_topic")
        
        # Determine complexity level based on score
        if complexity_score >= 3:
            complexity_level = "detailed"
            max_sentences = None  # No limit - comprehensive explanations
            formatting = "detailed_with_structure"
        elif complexity_score >= 1.5:
            complexity_level = "moderate"
            max_sentences = None  # No limit - balanced explanations
            formatting = "moderate_with_bullets"
        else:
            complexity_level = "simple"
            max_sentences = None  # No limit - complete explanations
            formatting = "concise"
        
        return {
            "complexity_level": complexity_level,
            "max_sentences": max_sentences,
            "formatting": formatting,
            "complexity_score": complexity_score,
            "factors": factors
        }

    async def _supervisor_node(self, state: TutorState) -> Dict[str, Any]:
        """
        Supervisor agent: Classifies intent and prepares routing.
        """
        logger.info(f"Supervisor processing: {state.user_input[:50]}...")

        # Increment turn count
        state.turn_count += 1
        state.last_activity = datetime.now()

        # Add user message to history
        state = add_message(state, "user", state.user_input)

        # Check for session end signals
        end_phrases = ["bye", "goodbye", "exit", "quit", "end session"]
        if any(phrase in state.user_input.lower() for phrase in end_phrases):
            state.should_end_session = True
            state.response = "Goodbye! Great studying with you today. Keep up the good work!"
            return {"should_end_session": True, "response": state.response}

        # Classify intent using LLM
        intent_result = await self._classify_intent(state)

        return {
            "intent": intent_result["intent"],
            "confidence": intent_result["confidence"],
            "turn_count": state.turn_count,
            "messages": state.messages
        }

    async def _classify_intent(self, state: TutorState) -> Dict[str, Any]:
        """Classify user intent using LLM."""

        classification_prompt = f"""Classify the student's intent from their message.

Student context:
- Subject: {state.content.subject or 'Not specified'}
- Current topic: {state.content.subtopic or 'Not specified'}
- Quiz active: {state.quiz.is_active}

Student message: "{state.user_input}"

Classify as one of:
- "learn": Student wants to learn a new concept or topic OR wants to switch subjects
- "practice": Student wants to practice with exercises or quizzes
- "review": Student wants to review previously learned material
- "question": Student is asking a specific question about content
- "off_topic": Message is not related to studying at all (e.g., "what's the weather", "tell me a joke")

IMPORTANT SUBJECT SWITCHING RULE:
- If student mentions a different subject (e.g., "IB Music", "Engineering") while in ICT, classify as "learn" NOT "off_topic"
- Subject switching IS a learning request - they want to learn about the new subject
- Phrases like "lets talk about", "I want to study", "tell me about" = "learn" regardless of subject
- Only classify as "off_topic" if completely unrelated to education/learning

Respond with just the intent word."""

        try:
            if hasattr(self.llm, 'ainvoke'):
                response = await self.llm.ainvoke(classification_prompt)
                intent = response.content.strip().lower() if hasattr(response, 'content') else str(response).strip().lower()
            else:
                intent = "question"  # Default fallback

            # Validate intent
            valid_intents = ["learn", "practice", "review", "question", "off_topic"]
            if intent not in valid_intents:
                intent = "question"

            return {"intent": intent, "confidence": 0.8}
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {"intent": "question", "confidence": 0.5}

    async def _planner_node(self, state: TutorState) -> Dict[str, Any]:
        """
        Planner agent: Retrieves content and creates learning plan.
        """
        logger.info(f"Planner processing intent: {state.intent}")

        # Prepare updates dict with content nested under "content" key
        updates = {}
        content_updates = {}

        # CRITICAL: Check for chapter list request FIRST - before RAG retrieval
        # Chapter list requests should get ALL chapters, not RAG results
        is_chapter_list_request = any(phrase in state.user_input.lower() for phrase in [
            "what are the topics", "what topics", "list chapters", "list topics", 
            "what chapters", "chapter list", "topic list", "what's in this book", 
            "what is covered", "what does this book cover", "what are the subjects",
            "can you give me a list", "give me a list", "list all chapters",
            "all chapters", "all topics"
        ])
        
        # Only use RAG retriever if NOT a chapter list request
        # This prevents RAG from returning incomplete results when user wants all chapters
        if "rag_retriever" in self.tools and not is_chapter_list_request:
            try:
                rag_tool = self.tools["rag_retriever"]

                # Determine subject to pass to RAG
                current_subject = state.content.subject
                user_input_lower = state.user_input.strip().lower()

                # DEBUG: Log the current subject from state
                logger.info(f"Planner - current_subject from state.content.subject: '{current_subject}'")
                logger.info(f"Planner - state.content type: {type(state.content)}")

                # Detect confirmation phrases
                confirmation_phrases = ["yes", "no", "please", "ok", "okay", "sure", "thanks", "thank you", "go ahead", "continue"]
                is_confirmation = any(phrase in user_input_lower for phrase in confirmation_phrases)

                # Detect subject keywords in user query (to identify if they're asking about different subject)
                subject_keywords = [
                    "math", "mathematics", "maths", "algebra", "geometry", "calculus",
                    "physics", "chemistry", "biology", "science",
                    "english", "literature", "language",
                    "history", "geography", "economics", "business",
                    "computer", "computing", "ict", "programming",
                    "engineering",
                    "music", "ib music", "art", "drama", "theatre",
                    "french", "spanish", "german", "chinese", "mandarin",
                    "psychology", "sociology", "philosophy",
                    "accounting", "statistics"
                ]
                
                # Check if user mentions a different subject
                mentioned_subject = None
                for keyword in subject_keywords:
                    if keyword in user_input_lower:
                        mentioned_subject = keyword
                        break

                current_subject_lower = current_subject.lower() if current_subject else ""
                mentions_different_subject = (
                    mentioned_subject and
                    mentioned_subject not in current_subject_lower and
                    current_subject_lower not in mentioned_subject
                )

                # STRICT SUBJECT FILTERING: Always use current subject from sidebar selection
                # Never automatically switch - user must change from sidebar
                subject_to_search = current_subject
                
                if current_subject:
                    logger.info(f"STRICT FILTER: Only searching within {current_subject}")
                    logger.info(f"STRICT FILTER: Current subject from session: {current_subject}")
                else:
                    logger.info("No current subject - searching across all subjects")

                # Check for subject keywords BEFORE RAG search
                # Keywords that strongly suggest Engineering topics
                engineering_keywords = ["mechanical", "electrical", "electronic", "pneumatic", "structural", "materials", "forces", "stress", "strain", "circuits", "wiring", "components"]
                
                # Keywords that strongly suggest Music topics
                music_keywords = ["note", "rhythm", "melody", "harmony", "scale", "chord", "composition", "instrument", "pitch", "tempo", "dynamics"]
                
                # Keywords for Mathematics
                math_keywords = ["algebra", "geometry", "calculus", "equation", "formula", "function"]
                
                # Check if query mentions keywords from OTHER subjects
                has_other_subject_keywords = False
                if current_subject:
                    if "music" in current_subject.lower():
                        has_other_subject_keywords = any(kw in user_input_lower for kw in engineering_keywords + math_keywords)
                    elif "engineering" in current_subject.lower():
                        has_other_subject_keywords = any(kw in user_input_lower for kw in music_keywords + math_keywords)
                    elif "math" in current_subject.lower():
                        has_other_subject_keywords = any(kw in user_input_lower for kw in music_keywords + engineering_keywords)
                    elif "ict" in current_subject.lower():
                        has_other_subject_keywords = any(kw in user_input_lower for kw in music_keywords + engineering_keywords + math_keywords)

                rag_results = await self._invoke_tool(
                    rag_tool,
                    query=state.user_input,
                    syllabus=None,
                    subject=subject_to_search,  # STRICT: Always filter by current subject
                    limit=5
                )
                logger.info(f"RAG search for: {state.user_input[:50]}... (subject filter: {subject_to_search})")
                
                # Store content updates
                content_updates["rag_results"] = rag_results or []

                # Check for subject mismatch - user asking about different subject
                # If we have a current subject but no results, and user mentions different subject keywords
                subject_mismatch = False
                if current_subject and not rag_results and not is_confirmation:
                    
                    if has_other_subject_keywords or mentions_different_subject:
                        # Searched for current subject but found nothing
                        # User is clearly asking about a different subject
                        logger.warning(f"Subject mismatch: No results in {current_subject}, user asking about different subject")
                        subject_mismatch = True
                        # Set flags for teacher to respond with subject switch suggestion
                        content_updates["subject_mismatch"] = True
                        content_updates["requested_query"] = state.user_input
                        content_updates["current_subject"] = current_subject
                        # Skip SQLite - don't search for content from other subjects
                        content_updates["skip_sqlite"] = True
                    else:
                        logger.info(f"No RAG results - will let SQLite search within {current_subject}")
                elif rag_results:
                    # Check if query is clearly about a DIFFERENT subject using LLM
                    # This is more accurate than keyword matching - catches cases like "music notes" in ICT
                    if current_subject and (has_other_subject_keywords or mentions_different_subject):
                        # Use LLM to determine if this is truly about a different subject
                        llm_check_prompt = f"""Determine if the user's question is about a DIFFERENT subject than the current subject.

Current subject being studied: {current_subject}
User's question: "{state.user_input}"

Rules:
- If user asks "tell me about music notes" while in ICT → YES, different subject (tell to switch)
- If user asks "what is mechanical engineering" while in Music → YES, different subject (tell to switch)  
- If user asks "explain algebra" while in ICT → YES, different subject (tell to switch)
- Even if there are some tangential connections (MIDI in ICT, robotics in ICT), if the PRIMARY topic is clearly about a different subject, say YES
- If user asks about hardware in ICT → NO, same subject (answer normally)
- If user asks about notes in Music → NO, same subject (answer normally)

Respond with just YES or NO (uppercase)."""
                        
                        try:
                            llm_response = await self.llm.ainvoke(llm_check_prompt)
                            is_different_subject = "YES" in str(llm_response.content).upper() if hasattr(llm_response, 'content') else "YES" in str(llm_response).upper()
                            
                            if is_different_subject:
                                logger.warning(f"LLM confirms subject mismatch - query '{state.user_input[:30]}...' is about different subject, not {current_subject}")
                                subject_mismatch = True
                                # Set flags for teacher to respond with subject switch suggestion
                                content_updates["subject_mismatch"] = True
                                content_updates["requested_query"] = state.user_input
                                content_updates["current_subject"] = current_subject
                                # Skip SQLite - don't search for content from other subjects
                                content_updates["skip_sqlite"] = True
                            else:
                                logger.info(f"LLM confirms query is within {current_subject} subject - proceed with RAG results")
                        except Exception as e:
                            logger.error(f"LLM subject check error: {e}, using keyword-based detection")
                            # Fallback to keyword detection
                            subject_mismatch = True
                            content_updates["subject_mismatch"] = True
                            content_updates["requested_query"] = state.user_input
                            content_updates["current_subject"] = current_subject
                            content_updates["skip_sqlite"] = True
                    else:
                        # Normal case: query is within current subject
                        # Find the first result with a valid (non-empty) subject
                        top_result = rag_results[0]
                        detected_subject = None
                        for result in rag_results:
                            subj = result.get('subject')
                            if subj:  # Non-empty subject found
                                detected_subject = subj
                                top_result = result  # Use this result for metadata
                                logger.info(f"Found valid subject '{subj}' in RAG result (scanned {rag_results.index(result) + 1} results)")
                                break

                        # If no result has a subject, fall back to first result's subject (empty)
                        if not detected_subject:
                            detected_subject = rag_results[0].get('subject')
                            logger.warning(f"No RAG results have valid subject field, using first result")

                        # NEVER update subject - always keep the subject from sidebar selection/session
                        # Subject switching only happens when user selects from sidebar, not automatically
                        # CRITICAL: current_subject comes from session, detected_subject comes from RAG
                        # Always prefer session subject over RAG detection to maintain strict filtering
                        if current_subject:
                            content_updates["subject"] = current_subject
                            logger.info(f"Subject locked to session subject: {current_subject}")
                        else:
                            # Only use detected_subject if no session subject exists
                            content_updates["subject"] = detected_subject
                            logger.info(f"Using RAG-detected subject (no session subject): {detected_subject}")
                    
                    content_updates["syllabus_id"] = top_result.get("syllabus_id")
                    content_updates["syllabus"] = top_result.get("syllabus")
                    content_updates["chapter"] = top_result.get("chapter")
                    content_updates["subtopic"] = top_result.get("subtopic")
                    logger.info(f"RAG content - subject: {content_updates.get('subject')}, chapter: {top_result.get('chapter')}")
                else:
                    # No RAG results - keep current subject from sidebar
                    if current_subject:
                        content_updates["subject"] = current_subject
                        logger.info(f"No RAG results, maintaining sidebar subject: {current_subject}")

            except Exception as e:
                logger.error(f"RAG retrieval error: {e}")

        # Check if user is asking for chapter/topic list - use chapter_list_retriever
        is_chapter_list_request = any(phrase in state.user_input.lower() for phrase in [
            "what are the topics", "what topics", "what are the topics in", "topics in this book", "list all topics",
            "list chapters", "list topics", 
            "what chapters", "chapter list", "topic list", "what's in this book", 
            "what is covered", "what does this book cover", "what are the subjects",
            "all chapters", "all topics"
        ])
        
        if is_chapter_list_request and "chapter_list_retriever" in self.tools:
            # Use current subject if available, otherwise use session subject
            subject_for_list = state.content.subject if state.content.subject and state.content.subject != "General" else None
            
            if subject_for_list:
                try:
                    logger.info(f"Detected chapter list request, using chapter_list_retriever for {subject_for_list}")
                    chapter_tool = self.tools["chapter_list_retriever"]
                    
                    chapter_data = await self._invoke_tool(
                        chapter_tool,
                        subject=subject_for_list,
                        syllabus=state.student.curriculum
                    )
                    
                    if chapter_data and not chapter_data.get("error"):
                        # Format chapter list for teacher - include ALL chapters, not just first 20
                        chapters = chapter_data.get("chapters", [])
                        formatted_chapters = "\n".join([
                            f"• {ch['name']}" for ch in chapters  # Removed [:20] limit - show all chapters
                        ])
                        content_updates["chapter_list"] = formatted_chapters
                        content_updates["chapter_list_data"] = chapter_data
                        # CRITICAL: Preserve subject state
                        content_updates["subject"] = subject_for_list
                        logger.info(f"Chapter list retrieved: {len(chapters)} chapters found, subject preserved: {subject_for_list}")
                    else:
                        logger.warning(f"Chapter list retriever failed: {chapter_data.get('error')}")
                except Exception as e:
                    logger.error(f"Chapter list retrieval error: {e}")
            else:
                logger.warning("Chapter list request detected but no subject available")
        
        # Use SQLite retriever for structured content
        # ONLY if not a chapter list request OR if chapter list retrieval failed
        if "sqlite_retriever" in self.tools and not content_updates.get("skip_sqlite") and not content_updates.get("chapter_list"):
            try:
                # Get subject from RAG results (now in content_updates)
                detected_subject = content_updates.get("subject")
                detected_chapter = content_updates.get("chapter")
                
                # Check if RAG found good results
                rag_has_results = len(content_updates.get("rag_results", [])) > 0
                
                # CRITICAL: ALWAYS filter by current subject
                # SQLite should NEVER search broadly across all subjects
                # Use current subject from state if RAG didn't detect one
                use_subject_filter = True  # ALWAYS filter!
                subject_to_search = detected_subject if detected_subject else state.content.subject
                
                logger.info(f"SQLite filter strategy: subject_filter={use_subject_filter}, subject_to_search={subject_to_search}")
                
                sqlite_tool = self.tools["sqlite_retriever"]
                
                content_results = await self._invoke_tool(
                    sqlite_tool,
                    syllabus=state.student.curriculum,
                    subject=subject_to_search,  # ALWAYS filter by subject
                    topic=detected_chapter,
                    subtopic=content_updates.get("subtopic", state.content.subtopic),
                    limit=5
                )
                
                # NEVER search broadly - if no results, that's expected
                # The teacher will respond appropriately
                
                # Only use SQLite results to update content, NOT subject
                # Subject should only come from RAG or remain unchanged
                if content_results and len(content_results) > 0:
                    # Combine multiple content pieces
                    all_content = "\n\n".join([
                        f"## {r.get('title', r.get('subtopic', 'Content'))}\n{r.get('content', '')}"
                        for r in content_results[:3]
                    ])
                    content_updates["textbook_content"] = all_content
                    
                    # Update content context from first result, but NOT subject
                    # Subject should only come from RAG or remain unchanged
                    top_result = content_results[0]
                    content_updates["syllabus"] = top_result.get("syllabus")
                    # DO NOT update subject from SQLite - it overrides RAG's subject detection
                    # content_updates["subject"] = top_result.get("subject")  # <-- REMOVED
                    content_updates["chapter"] = top_result.get("chapter")
                    content_updates["subtopic"] = top_result.get("subtopic")
                    
                    logger.info(f"SQLite retriever found {len(content_results)} results (content only, no subject update)")

            except Exception as e:
                logger.error(f"SQLite retrieval error: {e}")

        # Return content updates under "content" key for LangGraph to merge
        if content_updates:
            updates["content"] = content_updates

        # Store tool results
        updates["tool_results"] = {
            "planner_completed": True,
            "content_found": bool(content_updates.get("rag_results", state.content.rag_results))
        }

        return updates

    async def _teacher_node(self, state: TutorState) -> Dict[str, Any]:
        """
        Teacher agent: Delivers explanations and generates content.
        """
        logger.info(f"Teacher processing for intent: {state.intent}")

        # CRITICAL: Check for subject mismatch
        if state.content.subject_mismatch:
            current_subject = state.content.current_subject or "this subject"
            requested_query = state.content.requested_query or "your question"
            response = f"❌ I couldn't find information about '{requested_query}' in {current_subject}.\n\nThis topic might be covered in a different subject. Please select the appropriate subject from the sidebar to learn about this topic."
            
            state = add_message(state, "assistant", response, "teacher")
            return {
                "response": response,
                "response_type": "subject_mismatch",
                "messages": state.messages,
                "current_agent": "teacher"
            }

        # Detect if user is explicitly asking for chapter list
        is_chapter_list_request = any(phrase in state.user_input.lower() for phrase in [
            "what are the topics", "what topics", "what are the topics in", "topics in this book",
            "list chapters", "list topics", "list all topics",
            "what chapters", "chapter list", "topic list", "what's in this book", 
            "what is covered", "what does this book cover", "what are the subjects",
            "can you give me a list", "give me a list", "list all chapters"
        ])

        # Build conversation history for context continuity
        conversation_history = ""
        if state.messages and len(state.messages) > 0:
            recent_messages = state.messages[-6:]  # Last 3 exchanges
            history_parts = []
            for msg in recent_messages:
                role = "Student" if msg.role == "user" else "Tutor"
                history_parts.append(f"{role}: {msg.content[:300]}")
            conversation_history = "\n".join(history_parts)

        # Smart complexity detection - determines response depth based on multiple factors
        complexity_analysis = self._detect_response_complexity(state.user_input, conversation_history)
        logger.info(f"Response complexity: {complexity_analysis['complexity_level']} (score: {complexity_analysis['complexity_score']}, factors: {complexity_analysis['factors']})")

        # Detect topic from conversation history (for confirmations like "yes please")
        conversation_topic = None
        if state.messages and len(state.messages) > 0:
            # Look at the last user message before current one to find the topic
            for msg in reversed(state.messages[:-1] if len(state.messages) > 1 else state.messages):
                if msg.role == "user":
                    # Extract potential topic from previous user message
                    conversation_topic = msg.content
                    break

        # Build context for teacher
        context_parts = []

        # Check if we have a chapter list (from chapter_list_retriever)
        if state.content.chapter_list:
            context_parts.append(f"Available chapters:\n{state.content.chapter_list}")
            logger.info(f"Using chapter list from Qdrant: {len(state.content.chapter_list_data.get('chapters', []))} chapters")
        else:
            # Check if RAG detected a different subject than the current subject
            rag_detected_subject = None
            rag_has_relevant_content = False
            if state.content.rag_results and len(state.content.rag_results) > 0:
                rag_detected_subject = state.content.rag_results[0].get('subject')
                rag_has_relevant_content = True
                logger.info(f"RAG detected subject in teacher: {rag_detected_subject}, current subject: {state.content.subject}")

            # Only use textbook content if it's relevant to the conversation
            # If RAG found nothing and this is a confirmation, don't use unrelated content
            is_confirmation = state.user_input.lower().strip() in ["yes", "yes please", "sure", "ok", "okay", "please", "go ahead", "continue"]

            if state.content.textbook_content and (rag_has_relevant_content or not is_confirmation):
                context_parts.append(f"Textbook content:\n{state.content.textbook_content[:2000]}")
            elif is_confirmation and not rag_has_relevant_content:
                # For confirmations without RAG results, rely on conversation history
                logger.info("Confirmation without RAG results - using conversation history only")

        if state.content.rag_results:
            rag_context = "\n".join([
                f"- {r.get('content_preview', '')}"
                for r in state.content.rag_results[:3]
            ])
            context_parts.append(f"Related content:\n{rag_context}")

        context = "\n\n".join(context_parts) if context_parts else "No specific content available."

        # SPECIAL HANDLING: Chapter list requests should show ALL chapters explicitly
        if is_chapter_list_request and state.content.chapter_list:
            # Directly return the chapter list - no summarization needed
            chapter_data = state.content.chapter_list_data
            chapters = chapter_data.get("chapters", [])
            
            # Format a comprehensive chapter list response
            if chapters:
                chapter_names = [ch['name'] for ch in chapters]
                teacher_response = f"""Here are all the chapters in this book ({len(chapters)} total):

{chr(10).join([f"{i+1}. {name}" for i, name in enumerate(chapter_names)])}

Would you like to learn about any specific chapter?"""
            else:
                teacher_response = "I couldn't find any chapters in this book. Please try a different subject."
            
            state = add_message(state, "assistant", teacher_response, "teacher")
            return {
                "response": teacher_response,
                "response_type": "chapter_list",
                "messages": state.messages,
                "current_agent": "teacher"
            }

        # Check if no subject is selected
        has_no_subject = not state.content.subject or state.content.subject == "General"
        
        # Generate adaptive teacher prompt based on complexity analysis
        if has_no_subject:
            teacher_prompt = f"""You are a friendly and encouraging AI tutor helping a student learn.

Student info:
- Grade level: {state.student.grade_level or 'Not specified'}
- Learning style: {state.student.learning_style or 'Not specified'}
- Current subject: No subject selected
- Current topic: Not specified

Student's current message: "{state.user_input}"

CRITICAL: NO SUBJECT SELECTED
The student has NOT selected a subject yet. You must ask them to select a subject from the sidebar before you can help them.

STRICT RULES:
1. DO NOT suggest or mention ANY specific subject names (not ICT, not Engineering, not Music, etc.)
2. Simply ask the student to select a subject from the sidebar
3. Keep response to 1-2 sentences maximum
4. Be polite and helpful

Example responses:
- "Please select a subject from the sidebar to get started."
- "I can help with any subject! Please choose one from the sidebar first."
- "Select a subject from the sidebar so I can assist you."

DO NOT say: "I can help with ICT or Engineering"
DO NOT say: "Tell me if you want ICT or another subject"

Your response should be neutral and NOT suggest any specific subject."""
        
        elif complexity_analysis['complexity_level'] == 'detailed':
            # Detailed response (comprehensive) - for complex questions, explanations, comparative requests
            teacher_prompt = f"""You are a friendly and encouraging AI tutor helping a student learn.

Student info:
- Grade level: {state.student.grade_level or 'Not specified'}
- Learning style: {state.student.learning_style or 'Not specified'}
- Current subject: {state.content.subject}
- Current topic: {state.content.subtopic or 'Not specified'}

Recent conversation history:
{conversation_history if conversation_history else "No previous conversation."}

Available context:
{context}

Student's current message: "{state.user_input}"

Intent: {state.intent}

RESPONSE COMPLEXITY: DETAILED (Comprehensive explanation needed)
This question requires a thorough, well-structured response. Provide as comprehensive an explanation as needed.

CRITICAL CONVERSATION CONTINUITY RULE:
- If the student says "yes", "yes please", "continue", etc., they are responding to YOUR previous message
- Look at the conversation history to understand what topic you were discussing
- Continue discussing that SAME topic - do NOT switch to a different subject
- If you were discussing IB Music, continue with IB Music
- If you were discussing ICT, continue with ICT
- IGNORE any unrelated textbook content if it doesn't match the conversation topic

CREATIVE TEACHING LAYER - BE A REAL TEACHER, NOT A COPY-PASTE MACHINE:
- NEVER directly copy-paste textbook content - always SYTHESIZE and REPHRASE in your own words
- Use YOUR OWN teaching voice, personality, and style to explain concepts
- Create original analogies and examples that make concepts easier to understand
- Connect concepts to real-world situations, student interests, or daily life
- Ask thought-provoking questions to engage the student's thinking
- Use storytelling elements when appropriate (short scenarios, "Imagine if...", "Think of it like...")
- Add personal teaching touches: enthusiasm, encouragement, humor, relatable references
- Anticipate common misconceptions and address them proactively
- Use metaphors from music, sports, nature, technology, or other relatable areas
- Teach like you're talking one-on-one with a student who's genuinely interested

TEACHING TECHNIQUES TO USE:
- Socratic questioning: "Have you ever thought about why...?" "What do you think happens when...?"
- Progressive disclosure: Start simple, build complexity gradually
- Visual descriptions: Describe mental images, diagrams, or scenarios
- Interactive elements: "Try to imagine...", "Picture yourself...", "Think of a time when..."
- Multiple perspectives: Show different ways to understand the same concept
- Relevance connections: "This matters because...", "You'll use this when...", "This is similar to..."

CRITICAL FORMATTING RULES (MUST FOLLOW):
❌ NEVER use markdown headers (no #, ##, ###)
❌ NEVER use numbered section headers like "### 1. Title" or "## Section Name"  
❌ NEVER start lines with asterisks for bullet points (* item)
❌ NEVER use excessive bold (**text**) - maximum 2-3 per response
✅ Use clean paragraph breaks to organize content
✅ Use simple numbered lists only when listing 3+ items (1. First, 2. Second)
✅ Use simple dashes for short lists (- item)
✅ Keep formatting minimal and professional

STRUCTURE YOUR RESPONSES - PROFESSIONAL & CLEAN:
1. Start with a warm, engaging opening sentence
2. Explain in clear, flowing paragraphs - NOT formatted sections
3. Integrate examples naturally within paragraphs, not as separate labeled sections
4. Use line breaks between main ideas for readability
5. End with an encouraging close or invitation for follow-up questions

LENGTH MANAGEMENT:
- Provide thorough coverage of complex topics
- Use concise but complete paragraphs (2-4 sentences each)
- Don't ramble or provide unnecessary details
- Aim for comprehensive but not overwhelming - quality over quantity

Instructions:
- If intent is "learn": Teach creatively with original examples and analogies
- If intent is "question": Provide comprehensive answer with clear explanations
- If intent is "review": Give detailed summary with insights and connections
- If intent is "practice": Offer guidance with problem-solving approaches

BE A CREATIVE, ENGAGING TEACHER - not a textbook reader!"""
        
        elif complexity_analysis['complexity_level'] == 'moderate':
            # Moderate response (5 sentences max) - for balanced explanations, follow-up questions
            teacher_prompt = f"""You are a friendly and encouraging AI tutor helping a student learn.

Student info:
- Grade level: {state.student.grade_level or 'Not specified'}
- Learning style: {state.student.learning_style or 'Not specified'}
- Current subject: {state.content.subject}
- Current topic: {state.content.subtopic or 'Not specified'}

Recent conversation history:
{conversation_history if conversation_history else "No previous conversation."}

Available context:
{context}

Student's current message: "{state.user_input}"

Intent: {state.intent}

RESPONSE COMPLEXITY: MODERATE (Balanced explanation needed)
This question needs a balanced response with some detail. Provide a complete answer.

CRITICAL CONVERSATION CONTINUITY RULE:
- If the student says "yes", "yes please", "continue", etc., they are responding to YOUR previous message
- Look at the conversation history to understand what topic you were discussing
- Continue discussing that SAME topic - do NOT switch to a different subject
- If you were discussing IB Music, continue with IB Music
- If you were discussing ICT, continue with ICT
- IGNORE any unrelated textbook content if it doesn't match the conversation topic

CREATIVE TEACHING LAYER - BE A REAL TEACHER, NOT A COPY-PASTE MACHINE:
- NEVER directly copy-paste content - always EXPLAIN in your own words with your personal teaching style
- Use YOUR voice and personality - sound like a helpful human teacher
- Create simple, original analogies that make sense to the student
- Connect to everyday life, student experiences, or relatable situations
- Ask engaging questions: "Have you ever noticed...?" "Can you think of a time when...?"
- Use casual, conversational language while remaining educational
- Add enthusiasm and encouragement to your explanations
- Make concepts feel relevant and interesting

TEACHING TECHNIQUES TO USE:
- Simple analogies: "Think of it like..." "It's similar to when you..."
- Personal connections: "This is just like..." "You've probably seen this when..."
- Thoughtful questions: "Why do you think that happens?" "What would happen if...?"
- Clear, everyday language - avoid jargon unless necessary, then explain it

CRITICAL FORMATTING RULES (MUST FOLLOW):
❌ NEVER use markdown headers (no #, ##, ###)
❌ NEVER use numbered section headers like "### 1. Title"
❌ NEVER use asterisks for bullet points (* item)
❌ NEVER use excessive bold (**text**) - maximum 1-2 per response
✅ Use clean paragraph breaks to organize content
✅ Use simple dashes for short lists if needed (- item)
✅ Keep formatting minimal and conversational

LENGTH MANAGEMENT:
- Provide complete, clear explanations
- Use conversational paragraphs
- Don't over-explain, but ensure understanding

BE A FRIENDLY, HELPFUL TEACHER who makes learning enjoyable!"""
        
        else:
            # Simple response (3 sentences max) - for quick questions, simple definitions
            teacher_prompt = f"""You are a friendly and encouraging AI tutor helping a student learn.

Student info:
- Grade level: {state.student.grade_level or 'Not specified'}
- Learning style: {state.student.learning_style or 'Not specified'}
- Current subject: {state.content.subject}
- Current topic: {state.content.subtopic or 'Not specified'}

Recent conversation history:
{conversation_history if conversation_history else "No previous conversation."}

Available context:
{context}

Student's current message: "{state.user_input}"

Intent: {state.intent}

RESPONSE COMPLEXITY: SIMPLE (Direct explanation needed)
This is a straightforward question. Provide a complete, clear answer.

CRITICAL CONVERSATION CONTINUITY RULE:
- If the student says "yes", "yes please", "continue", etc., they are responding to YOUR previous message
- Look at the conversation history to understand what topic you were discussing
- Continue discussing that SAME topic - do NOT switch to a different subject
- If you were discussing IB Music, continue with IB Music
- If you were discussing ICT, continue with ICT
- IGNORE any unrelated textbook content if it doesn't match the conversation topic

CREATIVE TEACHING LAYER - BE A REAL TEACHER, NOT A COPY-PASTE MACHINE:
- NEVER just copy-paste - always EXPLAIN in YOUR OWN words with YOUR personal style
- Sound like a helpful, friendly human teacher, not a robot
- Use simple, natural language as if you're talking to a friend
- Add warmth and personality to your explanation
- Make it feel personal and relatable
- Even simple explanations can have a personal touch: "Here's how I would explain it..." "Think of it this way..."

TEACHING TECHNIQUES TO USE:
- Simple, conversational explanations
- Warm, encouraging tone
- Personal touches: "I like to think of it as..." "The way I remember it..."
- Make the student feel supported and understood

CRITICAL FORMATTING RULES (MUST FOLLOW):
❌ NEVER use markdown headers (no #, ##, ###)
❌ NEVER use numbered section headers like "### 1. Title"
❌ NEVER use asterisks for bullet points (* item)
❌ Keep bold to minimum - only if truly needed
✅ Use clean, simple paragraph text
✅ Keep formatting minimal and natural

LENGTH: Keep responses direct but complete. Simple doesn't mean cold - keep it warm and human.

BE A WARM, FRIENDLY TEACHER who makes students feel comfortable asking questions!"""

        try:
            # Check if LLM supports streaming
            if hasattr(self.llm, 'astream'):
                # Stream the response
                full_response = ""
                async for chunk in self.llm.astream(teacher_prompt):
                    if hasattr(chunk, 'content'):
                        full_response += chunk.content
                    else:
                        full_response += str(chunk)
                teacher_response = full_response
            elif hasattr(self.llm, 'ainvoke'):
                response = await self.llm.ainvoke(teacher_prompt)
                teacher_response = response.content if hasattr(response, 'content') else str(response)
            else:
                teacher_response = "I'm here to help you learn! What topic would you like to explore?"

            # Add message
            state = add_message(state, "assistant", teacher_response, "teacher")

            return {
                "response": teacher_response,
                "response_type": "explanation" if state.intent == "learn" else "text",
                "messages": state.messages,
                "current_agent": "teacher"
            }

        except Exception as e:
            logger.error(f"Teacher response error: {e}")
            return {
                "response": "I apologize, I'm having trouble right now. Could you try asking again?",
                "error": str(e)
            }

    async def _grader_node(self, state: TutorState) -> Dict[str, Any]:
        """
        Grader agent: Evaluates student answers and provides feedback.
        """
        logger.info("Grader evaluating student answer")

        if not state.quiz.is_active:
            return {
                "response": "There's no active question to grade. Would you like to practice?",
                "current_agent": "grader"
            }

        student_answer = state.user_input
        correct_answer = state.quiz.correct_answer
        question = state.quiz.current_question

        # Use LLM to evaluate the answer
        grading_prompt = f"""You are grading a student's answer.

Question: {question}
Correct answer: {correct_answer}
Student's answer: {student_answer}

Evaluate if the student's answer is correct, partially correct, or incorrect.
Consider:
- The core concept being tested
- Allow for different phrasings that convey the same meaning
- Partial credit for partially correct answers

Respond in this format:
VERDICT: [correct/partial/incorrect]
SCORE: [0.0 to 1.0]
FEEDBACK: [Encouraging feedback explaining what was right/wrong and the correct concept]"""

        try:
            if hasattr(self.llm, 'ainvoke'):
                response = await self.llm.ainvoke(grading_prompt)
                grading_result = response.content if hasattr(response, 'content') else str(response)
            else:
                grading_result = "VERDICT: partial\nSCORE: 0.5\nFEEDBACK: Let me check your answer."

            # Parse grading result
            is_correct = "correct" in grading_result.lower() and "incorrect" not in grading_result.lower()

            # Extract score
            score = 0.5
            if "SCORE:" in grading_result:
                try:
                    score_line = [l for l in grading_result.split('\n') if 'SCORE:' in l][0]
                    score = float(score_line.split(':')[1].strip())
                except:
                    pass

            # Extract feedback
            feedback = grading_result
            if "FEEDBACK:" in grading_result:
                feedback = grading_result.split("FEEDBACK:")[-1].strip()

            # Update mastery if profile manager tool available
            if "profile_manager" in self.tools and state.content.syllabus_id:
                try:
                    await self._invoke_tool(
                        self.tools["profile_manager"],
                        action="update_mastery",
                        student_id=state.student.student_id,
                        syllabus_id=state.content.syllabus_id,
                        is_correct=is_correct,
                        score=score
                    )
                except Exception as e:
                    logger.error(f"Mastery update error: {e}")

            # Update quiz state
            quiz_updates = state.quiz.model_copy()
            quiz_updates.is_active = False
            quiz_updates.questions_asked += 1
            if is_correct:
                quiz_updates.questions_correct += 1

            state = add_message(state, "assistant", feedback, "grader")

            return {
                "response": feedback,
                "response_type": "feedback",
                "quiz": quiz_updates,
                "messages": state.messages,
                "current_agent": "grader",
                "tool_results": {
                    "grading": {
                        "is_correct": is_correct,
                        "score": score
                    }
                }
            }

        except Exception as e:
            logger.error(f"Grading error: {e}")
            return {
                "response": "I had trouble grading your answer. Let's try another question.",
                "error": str(e)
            }

    async def _invoke_tool(self, tool: Any, **kwargs) -> Any:
        """Invoke a tool with the given arguments."""
        try:
            if hasattr(tool, 'ainvoke'):
                return await tool.ainvoke(kwargs)
            elif hasattr(tool, 'invoke'):
                return tool.invoke(kwargs)
            elif callable(tool):
                result = tool(**kwargs)
                if hasattr(result, '__await__'):
                    return await result
                return result
        except Exception as e:
            logger.error(f"Tool invocation error: {e}")
            return None

    async def run(
        self,
        state: TutorState | Dict[str, Any],
        config: Dict[str, Any] = None
    ) -> TutorState:
        """
        Run workflow with given state.

        Args:
        state: The current tutor state (TutorState object or dict)
            config: Optional configuration (thread_id for checkpointing)

        Returns:
            Updated state after workflow execution
        """
        if self.graph is None:
            logger.error("Workflow graph not initialized")
            state.error = "Workflow not available"
            state.response = "I'm sorry, tutoring system is not fully initialized."
            return state

        config = config or {}
        
        # CRITICAL: Preserve input subject before workflow runs
        # This ensures we can restore it if checkpointer overwrites it
        input_subject = None
        if isinstance(state, dict):
            content_obj = state.get("content", {})
            if isinstance(content_obj, dict):
                input_subject = content_obj.get("subject")
            elif hasattr(content_obj, 'subject'):
                input_subject = getattr(content_obj, 'subject', None)
        elif hasattr(state, 'content'):
            if isinstance(state.content, dict):
                input_subject = state.content.get("subject")
            elif hasattr(state.content, 'subject'):
                input_subject = getattr(state.content, 'subject', None)
        
        if input_subject:
            logger.info(f"WORKFLOW RUN: Preserving input subject '{input_subject}' before checkpointer load")
        
        # Handle different input types
        if isinstance(state, dict):
            # Extract session_id from dict for config
            if "configurable" not in config and "session_id" in state:
                config["configurable"] = {"thread_id": state["session_id"]}
            elif "configurable" not in config and "session_id" in state.get("student", {}):
                # session_id might be nested in student
                pass
            input_dict = state
        else:
            # TutorState object
            if "configurable" not in config:
                config["configurable"] = {"thread_id": state.session_id}
            input_dict = state.model_dump()

        try:
            # Run the graph - checkpointer will merge saved state with input_dict
            result = await self.graph.ainvoke(input_dict, config)

            # Convert result back to TutorState and merge updates
            if isinstance(result, dict):
                logger.info(f"Workflow result keys: {list(result.keys())}")
                
                # If input was a dict, we need to create a TutorState object
                if isinstance(state, dict):
                    from .state import create_initial_state
                    state = create_initial_state(
                        session_id=result.get("session_id", "unknown"),
                        student_id=result.get("student", {}).get("student_id", 0) if isinstance(result.get("student"), dict) else 0,
                        user_id=result.get("student", {}).get("user_id", "unknown") if isinstance(result.get("student"), dict) else "unknown"
                    )
                
                # Handle content updates - merge into existing content
                if "content" in result and result["content"]:
                    if isinstance(result["content"], dict):
                        # Merge dict updates into existing content
                        for key, value in result["content"].items():
                            if hasattr(state.content, key):
                                setattr(state.content, key, value)
                        logger.info(f"Merged content updates. New subject: {state.content.subject}")
                    elif isinstance(result["content"], ContentContext):
                        state.content = result["content"]
                        logger.info(f"Replaced content. New subject: {state.content.subject}")
                    
                    # CRITICAL: Ensure state.content is a ContentContext object, not a dict
                    # The checkpointer might have loaded it as a dict
                    if isinstance(state.content, dict):
                        logger.warning(f"Converting content from dict to ContentContext")
                        state.content = ContentContext(**state.content)
                
                # Helper function to safely get subject from content object
                def get_subject_from_content(content):
                    if isinstance(content, dict):
                        return content.get("subject")
                    elif hasattr(content, 'subject'):
                        return content.subject
                    return None
                
                # Handle quiz updates
                if "quiz" in result and result["quiz"]:
                    if isinstance(result["quiz"], dict):
                        result["quiz"] = QuizState(**result["quiz"])
                    state.quiz = result["quiz"]
                
                # Handle student updates
                if "student" in result and result["student"]:
                    if isinstance(result["student"], dict):
                        result["student"] = StudentContext(**result["student"])
                    state.student = result["student"]
                
                # Update state with other results
                for key, value in result.items():
                    if hasattr(state, key) and key not in ["content", "quiz", "student"]:
                        if value is not None:  # Only update if not None
                            setattr(state, key, value)
                            logger.info(f"Updated state.{key} = {value}")

            # CRITICAL: Force restore input subject if it was lost
            # The checkpointer might load old state without subject
            if input_subject and state.content.subject != input_subject:
                logger.warning(f"CHECKPINTER OVERRIDE: Restoring input subject '{input_subject}' (was '{state.content.subject}')")
                state.content.subject = input_subject
            
            return state

        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            error_msg = str(e)
            # Handle both TutorState and dict inputs
            if isinstance(state, dict):
                # If state is a dict, we can't set attributes
                # Return a TutorState with error set
                from .state import create_initial_state
                error_state = create_initial_state(
                    session_id=state.get("session_id", "unknown"),
                    student_id=state.get("student", {}).get("student_id", 0) if isinstance(state.get("student"), dict) else 0,
                    user_id=state.get("student", {}).get("user_id", "unknown") if isinstance(state.get("student"), dict) else "unknown"
                )
                # Preserve subject from input - safely handle both dict and ContentContext
                content_data = state.get("content", {})
                if isinstance(content_data, dict):
                    input_subject = content_data.get("subject")
                elif hasattr(content_data, 'subject'):
                    input_subject = getattr(content_data, 'subject', None)
                else:
                    input_subject = None
                
                if input_subject:
                    error_state.content.subject = input_subject
                error_state.error = error_msg
                error_state.response = "I encountered an error. Please try again."
                return error_state
            else:
                # State is a TutorState object
                state.response = "I encountered an error. Please try again."
                return state

    async def chat(
        self,
        session_id: str,
        user_input: str,
        state: TutorState = None
    ) -> str:
        """
        Simple chat interface for the tutor.

        Args:
            session_id: The session identifier
            user_input: The user's message
            state: Optional existing state

        Returns:
            The tutor's response
        """
        if state is None:
            # This shouldn't happen in production - state should be loaded
            logger.warning("No state provided, creating minimal state")
            from .state import create_initial_state
            state = create_initial_state(
                session_id=session_id,
                student_id=0,
                user_id="anonymous"
            )

        state.user_input = user_input

        result_state = await self.run(state)

        return result_state.response