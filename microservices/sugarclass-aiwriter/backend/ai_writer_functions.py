#!/usr/bin/env python3
"""
AI Writer Functions - Shared module for AI writing assistance
This module provides LLM-based writing assistance functions that can be used
by both the Flask aiwriter app and the Streamlit newscollect app.
"""

import os
import requests
from dotenv import load_dotenv
import time
import logging
from typing import Optional, Tuple, List, Dict
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global session for connection pooling (reused across calls)
_llm_session: Optional[requests.Session] = None

# Simple in-memory cache for LLM responses (cache_key -> (content, timestamp))
_llm_cache: Dict[str, Tuple[str, float]] = {}
_CACHE_TTL = 300  # Cache for 5 minutes


def _clean_expired_cache():
    """Remove expired entries from the LLM cache."""
    import time as _time
    current_time = _time.time()
    expired_keys = [
        key for key, (_, timestamp) in _llm_cache.items()
        if current_time - timestamp > _CACHE_TTL
    ]
    for key in expired_keys:
        del _llm_cache[key]
    if expired_keys:
        logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")


def _get_cache_key(system_prompt: str, user_prompt: str, model: str, temperature: float, max_tokens: int, is_selection: bool = False) -> str:
    """Generate a cache key from request parameters."""
    import hashlib
    # Include is_selection flag to explicitly distinguish between selection and full text improvements
    # Use full MD5 hash of user_prompt (not just first 16 chars) to avoid collisions
    # Include content length for additional distinction
    key_string = f"{model}:{temperature}:{max_tokens}:{is_selection}:{len(user_prompt)}:{hashlib.md5(user_prompt.encode()).hexdigest()}"
    return hashlib.md5(key_string.encode()).hexdigest()


def _get_session() -> requests.Session:
    """Get or create a reusable requests session for connection pooling."""
    global _llm_session
    if _llm_session is None:
        _llm_session = requests.Session()
        # Configure session for better performance
        _llm_session.headers.update({
            "Content-Type": "application/json",
        })
        logger.info("Created new LLM session with connection pooling")
    return _llm_session

# Path to aiwriter's .env
_AIWRITER_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DOTENV_PATH = os.path.join(_AIWRITER_PATH, ".env")


def _reload_config():
    """Reload config from api.txt each time to get fresh values"""
    if os.path.exists(_DOTENV_PATH):
        load_dotenv(dotenv_path=_DOTENV_PATH, override=True)
    else:
        load_dotenv(override=True)


def get_llm_config(use_case: str = None):
    """Get LLM configuration from environment"""
    # Reload config to ensure fresh values
    _reload_config()
    
    base_url = (os.getenv("LLM_BASE_URL") or "").strip().rstrip("/")
    api_key = (os.getenv("LLM_API_KEY") or "").strip()
    
    # Use gemini-3-flash-preview as default - more reliable
    default_model = "gemini-3-flash-preview"
    
    if use_case == "summary":
        model = (os.getenv("LLM_MODEL_SUMMARY") or os.getenv("LLM_MODEL") or default_model).strip()
    elif use_case == "draft":
        model = (os.getenv("LLM_MODEL_DRAFT") or os.getenv("LLM_MODEL") or default_model).strip()
    else:
        model = (os.getenv("LLM_MODEL") or default_model).strip()
    
    return base_url, api_key, model


def _is_response_complete(content: str, min_length: int = 50) -> bool:
    """
    Check if the LLM response appears complete.

    Args:
        content: The response content to validate
        min_length: Minimum expected character length

    Returns:
        True if response appears complete, False otherwise
    """
    if not content or len(content.strip()) < min_length:
        return False

    content = content.strip()

    # Check for truncation indicators
    truncation_signals = ["...", "\n\n\n", "�", "https://", "http://"]
    if any(signal in content[-50:] for signal in truncation_signals):
        return False

    # Check if ends with proper punctuation (sentence completion)
    last_char = content[-1] if content else ""
    if last_char not in {".", "!", "?", '"', "'", ":", ";", "*", ")", "]", "}"}:
        # Might be truncated - but allow if it ends with a complete word structure
        # Check if it's mid-word (common truncation pattern)
        if len(content.split()[-1]) < 3:  # Very short last word might be truncated
            return False

    return True


def llm_chat(system_prompt: str, user_prompt: str, temperature: float = 0.3,
             max_tokens: int = 1000, use_case: str = None, retry_model: str = None,
             validate_completeness: bool = True, is_selection: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Call LLM API and return (content, error).

    Args:
        system_prompt: System prompt for the LLM
        user_prompt: User prompt for the LLM
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        use_case: Use case for model selection ('summary', 'draft', etc.)
        retry_model: Fallback model if primary fails
        validate_completeness: Whether to validate response completeness
        is_selection: Whether this is for a selected text (vs full text) - affects caching

    Returns:
        (content, error) - content is None on error
    """
    base_url, api_key, model = get_llm_config(use_case)

    if not base_url or not api_key:
        return None, "LLM not configured. Set LLM_BASE_URL and LLM_API_KEY in environment."

    session = _get_session()

    # CACHE DISABLED - causing issues with selection vs full text distinction
    # # Clean expired cache entries periodically
    # _clean_expired_cache()
    #
    # # Check cache for existing response
    # cache_key = _get_cache_key(system_prompt, user_prompt, model, temperature, max_tokens, is_selection)
    # if cache_key in _llm_cache:
    #     cached_content, timestamp = _llm_cache[cache_key]
    #     import time as _time
    #     if _time.time() - timestamp < _CACHE_TTL:
    #         logger.info(f"Cache hit for key {cache_key[:8]}...")
    #         return cached_content, None
    #     else:
    #         # Expired, remove from cache
    #         del _llm_cache[cache_key]

    # Calculate minimum expected length based on what we're asking the AI to produce
    # Extract the actual text to improve from the user prompt for better length estimation
    import re
    text_match = re.search(r'STUDENT\'S TEXT TO IMPROVE:\s*(.+)', user_prompt, re.DOTALL)
    if text_match:
        input_text_length = len(text_match.group(1))
        # Expected output should be similar to input length (we're fixing, not rewriting entirely)
        expected_min_length = max(50, int(input_text_length * 0.7))  # Allow some reduction but not drastic
    else:
        # Fallback for other use cases
        expected_min_length = max(50, len(user_prompt) // 10)

    # Track total time spent on retries (max 90 seconds for better reliability)
    _start_time = time.time()
    _MAX_RETRY_TIME = 90  # Maximum total time for all retries

    def _try_request(use_model: str, retry_count: int = 0, max_retries: int = 5) -> Tuple[Optional[str], Optional[str]]:
        """Make a single API request attempt."""
        payload = {
            "model": use_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.info(f"LLM request: model={use_model}, max_tokens={max_tokens}, attempt={retry_count + 1}")

        try:
            start_time = time.time()
            resp = session.post(
                f"{base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload,
                timeout=60,  # 60 seconds for longer texts
            )
            elapsed = time.time() - start_time
            logger.info(f"LLM response: status={resp.status_code}, time={elapsed:.2f}s")

            # Handle rate limiting with exponential backoff
            if resp.status_code == 429:
                if retry_count < max_retries:
                    elapsed_total = time.time() - _start_time
                    if elapsed_total >= _MAX_RETRY_TIME:
                        return None, f"Request timeout (exceeded {_MAX_RETRY_TIME}s total retry time)"
                    wait_time = (2 ** retry_count) * 0.5  # 0.5s, 1s, 2s, 4s, 8s (faster retries)
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry (total elapsed: {elapsed_total:.1f}s)")
                    time.sleep(wait_time)
                    return _try_request(use_model, retry_count + 1, max_retries)
                return None, f"API rate limit exceeded (HTTP 429). Please try again in a few moments."

            if resp.status_code >= 400:
                logger.error(f"API error: HTTP {resp.status_code}, response={resp.text[:200]}")
                return None, f"API error: HTTP {resp.status_code}"

            data = resp.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

            # Log response details
            logger.info(f"Response length: {len(content) if content else 0} chars")

            if not content:
                logger.warning("Empty response received")
                return None, None  # Signal to retry with fallback

            # Validate response completeness if requested
            if validate_completeness and not _is_response_complete(content, expected_min_length):
                logger.warning(f"Response appears incomplete (length={len(content)}, ends with: '{content[-50:]}'")
                # Return content but also flag as potentially incomplete
                # Will trigger retry if this is the first attempt
                return content, "INCOMPLETE"

            return content, None

        except requests.Timeout:
            logger.error(f"Request timeout after 60s (attempt {retry_count + 1})")
            if retry_count < max_retries:
                elapsed_total = time.time() - _start_time
                if elapsed_total >= _MAX_RETRY_TIME:
                    return None, f"Request timeout (exceeded {_MAX_RETRY_TIME}s total retry time)"
                time.sleep(0.5)
                return _try_request(use_model, retry_count + 1, max_retries)
            return None, "Request timeout"
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            return None, f"Request error: {e}"
        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"Parse error: {e}")
            return None, f"Parse error: {e}"

    try:
        # First attempt with configured model
        content, error = _try_request(model)

        # If we got an incomplete response on first try, retry once more
        if error == "INCOMPLETE" and content:
            logger.info("Retrying due to incomplete response...")
            time.sleep(0.5)  # Brief pause before retry
            content, error = _try_request(model)
            if error == "INCOMPLETE":
                # Second attempt also incomplete, use the content but strip any artifacts
                content = content.strip().rstrip(".")
                logger.warning("Using potentially incomplete response after retry")
                error = None

        if error and error != "INCOMPLETE":
            return None, error

        # If still empty or failed, try fallback model
        if not content and model != "gemini-3-flash-preview":
            fallback = retry_model or "gemini-3-flash-preview"
            logger.info(f"Retrying with fallback model: {fallback}")
            content, error = _try_request(fallback)
            if error and error != "INCOMPLETE":
                return None, error
            if error == "INCOMPLETE" and content:
                # Use incomplete fallback response
                content = content.strip().rstrip(".")
                error = None

        if not content:
            return None, "Empty response from LLM (tried fallback)"

        # CACHE DISABLED - causing issues with selection vs full text distinction
        # # Cache successful response
        # import time as _time
        # _llm_cache[cache_key] = (str(content), _time.time())
        # logger.debug(f"Cached response for key {cache_key[:8]}...")

        return str(content), None

    except Exception as e:
        logger.exception(f"Unexpected error in llm_chat: {e}")
        return None, f"Unexpected error: {e}"


def normalize_year_level(year_level) -> int:
    """Convert year_level to integer from various formats.

    Args:
        year_level: Can be int, str like '7' or 'Year 7', etc.

    Returns:
        Integer year level (7-13), defaults to 10 if invalid
    """
    try:
        if isinstance(year_level, int):
            return max(7, min(13, year_level))

        # Handle string formats like "Year 7" or "7"
        year_str = str(year_level).strip()

        # Extract number from "Year X" format
        if year_str.lower().startswith('year'):
            year_str = year_str.lower().replace('year', '').strip()

        # Convert to int
        year_int = int(year_str)
        return max(7, min(13, year_int))
    except (ValueError, AttributeError):
        # Default to year 10 if parsing fails
        return 10


def detect_plagiarism_code_based(user_text: str, article_text: str) -> dict:
    """
    Optimized code-based plagiarism detection using similarity matching.

    Checks for:
    1. Exact phrase matches (5+ consecutive words)
    2. High similarity sentences
    3. Overall similarity percentage

    Args:
        user_text: The student's written text
        article_text: The source article text

    Returns:
        Dictionary with plagiarism findings:
        {
            'has_plagiarism': bool,
            'similarity_percent': float,
            'copied_phrases': List[str],
            'details': str
        }
    """
    # Early exit for short texts or missing article
    if not article_text or not user_text or len(user_text.strip()) < 20:
        return {
            'has_plagiarism': False,
            'similarity_percent': 0.0,
            'copied_phrases': [],
            'details': 'Text too short for plagiarism check.'
        }

    # Clean texts for comparison
    user_clean = re.sub(r'\s+', ' ', user_text.lower().strip())
    article_clean = re.sub(r'\s+', ' ', article_text.lower().strip())

    # Quick similarity check first using word sets (much faster)
    user_words_set = set(user_clean.split())
    article_words_set = set(article_clean.split())

    if len(user_words_set) == 0:
        return {
            'has_plagiarism': False,
            'similarity_percent': 0.0,
            'copied_phrases': [],
            'details': 'No text to check.'
        }

    # Calculate similarity percentage using word overlap
    overlap = len(user_words_set & article_words_set)
    similarity_percent = round((overlap / len(user_words_set)) * 100, 1)

    # Only do detailed phrase checking if similarity is high enough
    if similarity_percent < 30:
        # Low similarity, skip detailed checking
        return {
            'has_plagiarism': False,
            'similarity_percent': similarity_percent,
            'copied_phrases': [],
            'details': f"Good job! Your writing appears original (similarity: {similarity_percent}%)."
        }

    # For higher similarity, find specific copied phrases
    user_words = user_clean.split()
    article_words = article_clean.split()

    # Use a set for faster duplicate detection
    seen_phrases = set()
    copied_phrases = []
    min_phrase_length = 5

    # Build article phrase lookup for O(1) lookups
    article_phrases = set()
    for i in range(len(article_words) - min_phrase_length + 1):
        article_phrases.add(' '.join(article_words[i:i + min_phrase_length]))

    # Find matching sequences
    i = 0
    while i <= len(user_words) - min_phrase_length:
        phrase = ' '.join(user_words[i:i + min_phrase_length])

        if phrase in article_phrases and phrase not in seen_phrases:
            # Found a match, extend to find full sequence
            extended_phrase = phrase
            j = i + min_phrase_length
            while j < len(user_words):
                test_phrase = extended_phrase + ' ' + user_words[j]
                if test_phrase in article_clean:
                    extended_phrase = test_phrase
                    j += 1
                else:
                    break

            if extended_phrase not in seen_phrases:
                copied_phrases.append(extended_phrase)
                seen_phrases.add(extended_phrase)

            # Skip ahead to avoid overlapping matches
            i = j
        else:
            i += 1

    # Limit results to avoid overwhelming output
    copied_phrases = copied_phrases[:3]

    has_plagiarism = len(copied_phrases) > 0 or similarity_percent > 60

    # Build details message
    if has_plagiarism:
        if copied_phrases:
            details = f"Found {len(copied_phrases)} potentially copied phrase(s). "
            details += "You should rewrite these in your own words. "
        else:
            details = "High similarity detected with source article. "

        if similarity_percent > 60:
            details += f"Your text is {similarity_percent}% similar to the source - try using more original wording."
        else:
            details += f"Similarity: {similarity_percent}%"
    else:
        details = f"Good job! Your writing appears original (similarity: {similarity_percent}%)."

    return {
        'has_plagiarism': has_plagiarism,
        'similarity_percent': similarity_percent,
        'copied_phrases': copied_phrases,
        'details': details
    }


def _aggressive_informal_language_check(text: str, article_context: str = "", is_selection: bool = False) -> list:
    """
    Second-pass aggressive check for informal/slang language using LLM.
    This catches patterns the first check might have missed.

    Args:
        text: The student's written text
        article_context: Source article for context awareness (optional)
        is_selection: Whether this is for a selected text portion (affects caching)

    Returns:
        List of style suggestions with informal words found
    """
    # Use shorter text for this check (first 1000 chars)
    text_to_check = text[:1000] if len(text) > 1000 else text
    # Also limit article context to keep prompt manageable
    article_context_truncated = article_context[:1500] if article_context else ""

    context_note = ""
    if article_context_truncated:
        context_note = f"""

SOURCE ARTICLE (for reference - don't flag words that appear in this article):
{article_context_truncated}"""

    system_prompt = """You are an informal language detector for news writing. Find ALL informal/slang words.

Look for these PATTERNS:
- Text abbreviations: missing letters (tho, cuz, pls, w/, ur, u)
- Numbers replacing letters: gr8, b4, l8r, 2morow
- Shortened contractions: gonna, wanna, gotta, kinda, sorta, shoulda
- Conversational filler: wow, yeah, so, just, like, really, very
- Text-speak: lol, lmao, omg, tf, btw
- Casual phrases: "so yeah", "or something", "I mean"

IMPORTANT:
- SKIP words inside quotation marks (these are quotes, not student's writing)
- SKIP technical terms that appear in the source article
- Focus on the student's casual/conversational language

Return JSON with informal words found:
[{"issue": "Informal word 'obvs'", "suggestion": "Use 'obviously'"}]

JSON ONLY, no markdown."""

    user_prompt = f"""Find ALL informal words in this text:

{text_to_check}{context_note}

Return JSON array of informal words found. JSON ONLY."""

    try:
        response, error = llm_chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=800,
            use_case='aggressive_style_check',
            is_selection=is_selection
        )

        if error or not response:
            logger.warning(f"Aggressive style check failed: {error}")
            return []

        import json
        import re

        # Try to extract JSON array from response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            response = json_match.group()

        result = json.loads(response)
        return result if isinstance(result, list) else []

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Failed to parse aggressive style check: {e}")
        return []


def check_with_llm(user_text: str, year_level: int = 10, article_context: str = "", is_selection: bool = False) -> dict:
    """
    Unified grammar, spelling, and punctuation check using LLM.
    This replaces all hardcoded regex-based checks with AI-powered analysis.

    Args:
        user_text: The student's written text
        year_level: Student's year level for context-appropriate feedback
        article_context: Source article for context-aware checking (optional)
        is_selection: Whether this is for a selected text portion (affects caching)

    Returns:
        Dictionary with categorized errors found
    """
    # Truncate very long text for LLM analysis (keep first 2000 chars)
    text_to_analyze = user_text[:2000] if len(user_text) > 2000 else user_text
    text_ellipsis = "..." if len(user_text) > 2000 else ""
    # Truncate article context to keep prompt manageable
    article_context_truncated = article_context[:1500] if article_context else ""

    context_note = ""
    if article_context_truncated:
        context_note = f"""

SOURCE ARTICLE (for context):
{article_context_truncated}

Use this to:
- Skip technical terms that appear in the article
- Skip words inside quotation marks (direct quotes)
- Give smarter suggestions using article vocabulary"""

    # System prompt focused on PATTERNS of informal language, not specific words
    system_prompt = """You are a STRICT English teacher analyzing news writing. Identify ALL errors and informal language.

DETECT THESE PATTERNS:

**SPELLING/INFORMAL WORDS** - Look for:
- Text-speak patterns: missing vowels (tho, cuz, pls), numbers for words (gr8, b4, l8r)
- Abbreviations: w/, w/o, bc, ur, u, pls, thx
- Contractions of going to/want to: gonna, wanna, gotta
- Shortened words: kinda, sorta, shoulda, coulda, woulda, tryna, outta
- Any word that looks like it was typed quickly without proper spelling

**GRAMMAR** - Look for:
- Subject-verb agreement: "they was", "she don't", "he don't"
- Wrong verb tense: "I seen", "I done", "could of"
- Double negatives: "don't know nothing", "won't never"
- Sentence fragments or incomplete thoughts

**PUNCTUATION** - Look for:
- Missing period at end of sentences
- Comma splices (joining sentences with only comma)
- Missing capitalization (start of sentences, proper nouns)
- Run-on sentences

**STYLE/TONE** - Look for:
- Conversational filler: wow, yeah, so, just, like, um, uh
- Vague qualifiers: kind of, sort of, really, very, super, pretty, a lot
- Text-speak abbreviations: lol, lmao, omg, btw, tf
- Casual phrases: "so yeah", "I mean", "you know", "or something"
- Any tone that sounds like texting/social media, not journalism

CRITICAL: This is NEWS WRITING. Formal tone required. Flag anything casual.
SKIP: Words inside quotes, technical terms from source article."""

    user_prompt = f"""Analyze this text for errors. Return JSON ONLY.

STUDENT'S TEXT:
{text_to_analyze}{text_ellipsis}

Year Level: {year_level}{context_note}

JSON format:
{{
    "spelling": [{{"word": "incorrect", "correction": "correct", "position": 0}}],
    "grammar": [{{"found": "incorrect", "correction": "correct", "explanation": "why", "position": 0}}],
    "punctuation": [{{"found": "issue", "correction": "fix", "explanation": "why", "position": 0}}],
    "style": [{{"issue": "informal word 'obvs'", "suggestion": "use 'obviously'"}}]
}}

Rules:
- position = character index in original text
- SKIP words inside quotation marks
- SKIP technical terms from source article
- Flag informal language in student's own writing
- Flag filler words: wow, yeah, so, just, like, really, very
- Flag vague phrases: "kind of", "sort of", "a lot"
- If perfect text, return empty arrays
- JSON ONLY, no markdown"""

    try:
        # Dynamic max_tokens based on text length for grammar check
        # Longer texts need more tokens for detailed feedback
        grammar_tokens = max(1500, len(user_text) // 2)

        response, error = llm_chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=grammar_tokens,
            use_case='grammar_check',
            is_selection=is_selection
        )

        if error or not response:
            logger.warning(f"LLM grammar check failed: {error}")
            return _get_empty_check_result()

        # Parse JSON response
        import json
        import re

        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            response = json_match.group()

        result = json.loads(response)

        # Validate and structure the response
        spelling_errors = result.get('spelling', [])[:10]
        grammar_errors = result.get('grammar', [])[:5]
        punctuation_errors = result.get('punctuation', [])[:5]
        style_suggestions = result.get('style', [])[:3]

        # Log what was found for debugging
        total_errors = len(spelling_errors) + len(grammar_errors) + len(punctuation_errors) + len(style_suggestions)
        logger.info(f"LLM grammar check found {total_errors} total issues (spelling: {len(spelling_errors)}, grammar: {len(grammar_errors)}, punctuation: {len(punctuation_errors)}, style: {len(style_suggestions)})")

        # If LLM found few errors, run a second-pass aggressive check for informal language
        # This catches slang/informal words the first check might have missed
        if total_errors < 5 and len(user_text) > 30:
            logger.info("Running second-pass aggressive informal language check")
            style_from_fallback = _aggressive_informal_language_check(user_text, article_context, is_selection)
            if style_from_fallback:
                # Merge with existing style suggestions, avoiding duplicates
                existing_informal = {s.get('issue', '') for s in style_suggestions}
                for suggestion in style_from_fallback:
                    if suggestion.get('issue', '') not in existing_informal:
                        style_suggestions.append(suggestion)
                logger.warning(f"Added {len(style_from_fallback)} informal words via aggressive check")

        return {
            'spelling': {
                'has_errors': len(spelling_errors) > 0,
                'errors': spelling_errors,
                'count': len(spelling_errors)
            },
            'grammar': {
                'has_errors': len(grammar_errors) > 0,
                'errors': grammar_errors,
                'count': len(grammar_errors)
            },
            'punctuation': {
                'has_errors': len(punctuation_errors) > 0,
                'errors': punctuation_errors,
                'count': len(punctuation_errors)
            },
            'style': {
                'has_suggestions': len(style_suggestions) > 0,
                'suggestions': style_suggestions,
                'count': len(style_suggestions)
            },
            '_using_fallback': False
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM grammar check response: {e}")
        return _get_empty_check_result()
    except Exception as e:
        logger.error(f"LLM grammar check error: {e}")
        return _get_empty_check_result()


def _get_empty_check_result() -> dict:
    """Return empty check result when LLM fails."""
    return {
        'spelling': {'has_errors': False, 'errors': [], 'count': 0},
        'grammar': {'has_errors': False, 'errors': [], 'count': 0},
        'punctuation': {'has_errors': False, 'errors': [], 'count': 0},
        'style': {'has_suggestions': False, 'suggestions': [], 'count': 0},
        '_using_fallback': True
    }


def _clean_ai_response(content: str) -> str:
    """
    Clean AI response by removing common prefixes, suffixes, and filler phrases.
    Applied to all AI-generated content to ensure clean output.
    """
    if not content:
        return content

    content = content.strip()

    # Remove common prefixes AI might add
    unwanted_prefixes = [
        "Improved:", "IMPROVED:", "Here's the improved version:", "Rewritten:",
        "Rewritten text:", "Here is the rewritten text:", "The improved version is:",
        "Improved version:", "Here's your rewritten text:", "Below is the improved text:",
        "The improved text is:", "Corrected text:", "CORRECTED:",
        "Here's a suggestion:", "Suggested paragraph:", "Suggestion:",
        "Here's your writing plan:", "Writing plan:", "Summary:",
        "Here is the summary:", "Plan:", "Outline:"
    ]

    for prefix in unwanted_prefixes:
        if content.startswith(prefix):
            content = content[len(prefix):].strip()

    # Remove unwanted suffixes and AI filler
    unwanted_suffixes = [
        "I hope this helps!", "Let me know if you need any changes.",
        "This version maintains the same meaning while fixing errors.",
        "The improved version above fixes all the errors.",
        "Hope this helps with your writing!",
        "Would you like me to", "Let me know if you'd like",
        "I can also help you", "I'd be happy to",
        "Feel free to ask", "Let me know if you need",
        "Let me know if you want me to", "I can provide more",
        "Would you like any", "I'd be happy to provide"
    ]

    for suffix in unwanted_suffixes:
        if content.endswith(suffix):
            content = content[:-len(suffix)].strip()

    # Remove lines starting with AI filler phrases (conversational content)
    import re
    filler_patterns = [
        r'\n\n(Would you like|Let me know|I can help|I can also|Feel free|Hope this|I\'d be happy|I can provide|Let me know if).*?(?=\n\n|$)',
        r'\n\n(Here\'s another?|(I hope|Feel free|Would you|Let me|I can|I\'d)).*?(?=\n\n|$)'
    ]

    for pattern in filler_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE).strip()

    return content


def _format_improved_text(text: str) -> str:
    """
    Clean up formatting of improved text output from AI.

    Handles:
    - Excessive whitespace
    - Paragraph structure
    - Punctuation spacing
    - Sentence endings and capitalization
    - Quote and parentheses spacing
    - Double periods

    Args:
        text: The text to format

    Returns:
        Formatted text
    """
    if not text:
        return text

    import re

    # Remove excessive whitespace (more than 2 consecutive spaces)
    text = re.sub(r' {3,}', '  ', text)

    # Fix paragraph structure - ensure double newlines between paragraphs
    # but collapse more than 2 consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Fix spacing after punctuation
    text = re.sub(r'([.!?])\s{2,}', r'\1 ', text)  # Multiple spaces after sentence endings
    text = re.sub(r'([,;:])\s{2,}', r'\1 ', text)  # Multiple spaces after commas, semicolons, colons

    # Ensure space after sentence endings if missing
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)

    # Fix space before punctuation
    text = re.sub(r'\s+([.,!?;:)])', r'\1', text)

    # Fix missing space after opening quotes/parentheses
    text = re.sub(r'([\(])"', r'\1 "', text)  # (Quote -> ( "Quote"
    text = re.sub(r'([\(]"?)([A-Z])', r'\1 \2', text)  # (Word -> ( Word

    # Remove double periods
    text = re.sub(r'\.{2,}', '.', text)

    # Ensure sentences end with proper punctuation
    # If a line ends without punctuation and next line starts with capital, add period
    lines = text.split('\n')
    for i in range(len(lines) - 1):
        current = lines[i].strip()
        next_line = lines[i + 1].strip()
        if current and not current[-1] in '.!?' and next_line and next_line[0].isupper():
            lines[i] = current + '.'
    text = '\n'.join(lines)

    # Fix spacing around quotes
    text = re.sub(r'"\s+', '"', text)  # Remove space after opening quote
    text = re.sub(r'\s+"', '"', text)  # Remove space before closing quote

    # Collapse multiple spaces into single (except after periods)
    text = re.sub(r'(?<!\.)\s{2,}', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def generate_improved_text_ai_only(text_to_improve: str, article_context: str, year_level: int, is_selection: bool = False) -> tuple:
    """
    Use AI ONLY for rewriting the text, not for formatting feedback.
    All analysis is done by code.

    Args:
        text_to_improve: The text to improve
        article_context: Source article for reference (used to maintain factual accuracy)
        year_level: Student year level
        is_selection: Whether this is for a selected text portion (affects caching)

    Returns:
        Tuple of (improved_text, error)
    """
    word_count = len(text_to_improve.split())
    char_count = len(text_to_improve)

    if year_level <= 8:
        language_note = "Simple language for ages 11-13."
    elif year_level <= 10:
        language_note = "Moderate complexity for ages 14-15."
    else:
        language_note = "Sophisticated language for ages 16-18."

    # Truncate article context if too long (keep it reasonable for the prompt)
    article_context_truncated = article_context[:4000] if article_context else ""

    # System prompt focused on aggressive professional rewriting
    system_prompt = f"""You are a professional news editor. REWRITE the student's informal writing into a polished news article.

Your task - TRANSFORM the writing style:
1. Remove ALL informal language (slang, conversational filler: "kinda", "obvs", "wow", "like 99% or something")
2. Fix ALL grammar and punctuation errors
3. Convert to professional journalistic tone: objective, factual, concise
4. Use proper news structure: clear topic sentences, logical flow, active voice
5. Remove conversational phrases: "which is kinda wild", "so yeah", "or maybe some fuel, not sure"
6. Fix run-on sentences - break into proper sentences
7. Use specific numbers instead of vague approximations when possible

TRANSFORMATION RULES:
- "kinda wild" → "remarkable" or "notable"
- "obvs big" → "significantly" or "notably"
- "wow" → remove (just state facts)
- "like 99%" → "approximately 99%" when exact, otherwise vague descriptions
- "which is funny cuz" → remove (not relevant for news)
- "so yeah" → remove
- "or maybe, not sure" → remove uncertainty
- "Go Brrr" → proper headline style
- Keep facts, remove opinion/conversational tone

CRITICAL:
- This MUST sound like a PROFESSIONAL news article from BBC, Reuters, or AP
- NO conversational tone, NO slang, NO uncertainty
- DO NOT add new facts, but DO rewrite EVERYTHING professionally
- Make it sound like a journalist wrote it, not a student

OUTPUT ONLY:
- The professionally rewritten text, nothing else
- No explanations, no labels"""

    user_prompt = f"""SOURCE ARTICLE (for factual reference):
{article_context_truncated}

STUDENT'S TEXT TO IMPROVE:
{text_to_improve}"""

    # Dynamic max_tokens based on input size to prevent truncation
    # Use word_count * 4 for output (rewritten text could be same length or longer)
    # Higher minimum and multiplier to prevent truncation
    estimated_tokens = max(3000, word_count * 4)

    content, error = llm_chat(system_prompt, user_prompt, temperature=0.2, max_tokens=estimated_tokens, use_case="draft", is_selection=is_selection)

    if error:
        return None, error

    # Clean up AI response (remove prefixes, suffixes, filler)
    if content:
        content = _clean_ai_response(content)
        # Format the improved text (fix spacing, punctuation, structure)
        content = _format_improved_text(content)

        # Also split on section markers if they appear after the improved text
        import re
        section_pattern = r'\n\n(?:PLAGIARISM CHECK|FEEDBACK|LEARNING TIP|GRAMMAR|PUNCTUATION|STYLE|SPELLING|CLARITY)\s*:'
        if re.search(section_pattern, content):
            content = re.split(section_pattern, content)[0].strip()

    return content if content else None, None


def generate_prewrite_summary(article_title: str, article_text: str, year_level = 10) -> str:
    """
    Generate a prewrite summary for the given article.

    Args:
        article_title: Title of the article
        article_text: Full text of the article
        year_level: Student year level (7-13)

    Returns:
        Prewrite summary text or error message
    """
    if not article_text or len(article_text.strip()) < 100:
        return "Article text is too short or not available."

    # Normalize year level to integer
    year_level = normalize_year_level(year_level)

    # Truncate article text
    if len(article_text) > 3000:
        article_text = article_text[:3000]

    # Age-specific writing plan structure
    if year_level <= 8:
        system_prompt = """Create a writing plan for Year 7-8. CRITICAL RULES:
- Each bullet MAXIMUM 10 WORDS
- ONE line only per bullet
- Use ALL CAPS for headers
- Simple language only

OUTPUT FORMAT (follow exactly):

=== MAIN TOPIC ===
[10 words max]

=== KEY FACTS ===
- [10 words max]
- [10 words max]
- [10 words max]

=== PARAGRAPHS ===
1. [10 words max]
2. [10 words max]
3. [10 words max]

Example:
=== MAIN TOPIC ===
Tiny chip converts infrared to visible light

=== KEY FACTS ===
- CUNY scientists created metasurface chip
- Converts 1530nm infrared to 510nm green
- 100x more efficient, no moving parts

=== PARAGRAPHS ===
1. Introduce microscopic light conversion breakthrough
2. Explain metasurface technology and efficiency
3. Discuss applications in tech and medicine"""

    elif year_level <= 10:
        system_prompt = """Create a writing plan for Year 9-10. CRITICAL RULES:
- Each bullet MAXIMUM 10 WORDS
- ONE line only per bullet
- Use ALL CAPS for headers

OUTPUT FORMAT (follow exactly):

=== MAIN TOPIC ===
[10 words max]

=== KEY POINTS ===
- Context: [10 words max]
- Events: [10 words max]
- People: [10 words max]
- Results: [10 words max]

=== PARAGRAPHS ===
1. [10 words max]
2. [10 words max]
3. [10 words max]
4. [10 words max]
5. [10 words max]

Example:
=== MAIN TOPIC ===
Ultra-thin metasurface chip revolutionizes light control

=== KEY POINTS ===
- Context: Engineers needed better light control
- Events: Team built ultra-thin metasurface chip
- People: Professor Andrea Alù led CUNY research
- Results: 100x efficiency, beam steering achieved

=== PARAGRAPHS ===
1. Introduce breakthrough in light control technology
2. Describe metasurface chip design and function
3. Explain light conversion and steering mechanism
4. Analyze efficiency improvements over previous devices
5. Discuss implications for future optical technologies"""

    else:
        system_prompt = """Create a writing plan for Year 11-13. CRITICAL RULES:
- Each bullet MAXIMUM 10 WORDS
- ONE line only per bullet
- Use ALL CAPS for headers

OUTPUT FORMAT (follow exactly):

=== THESIS ===
[10 words max]

=== KEY ELEMENTS ===
- Background: [10 words max]
- Evidence: [10 words max]
- Analysis: [10 words max]
- Perspectives: [10 words max]
- Implications: [10 words max]

=== PARAGRAPHS ===
1. [10 words max]
2. [10 words max]
3. [10 words max]
4. [10 words max]
5. [10 words max]
6. [10 words max]

Example:
=== THESIS ===
Metasurface breakthrough solves photonics efficiency-control tradeoff

=== KEY ELEMENTS ===
- Background: Photonics needed compact light control
- Evidence: Metasurface achieves 100x efficiency boost
- Analysis: Breakthrough solves efficiency-control tradeoff
- Perspectives: Enables new miniaturized optical devices
- Implications: Advances LIDAR, medical tech, communications

=== PARAGRAPHS ===
1. Introduce metasurface chip breakthrough in photonics
2. Explain background of light control challenges
3. Present evidence of efficiency improvements
4. Analyze significance of tradeoff solution
5. Evaluate implications for optical technologies
6. Conclude with future applications and impact"""

    user_prompt = f"Year Level: {year_level}\n\nArticle: {article_title}\n\n{article_text}"

    logger.info(f"Generating prewrite for Year {year_level}")

    content, error = llm_chat(system_prompt, user_prompt, temperature=0.3, max_tokens=600, use_case="summary")

    if error:
        logger.error(f"Failed to generate prewrite: {error}")
        return f"Error generating summary: {error}"

    # Clean up AI response
    if content:
        content = _clean_ai_response(content)

    logger.info(f"Generated prewrite summary: {len(content) if content else 0} characters")

    return content or "No summary generated."


def generate_ai_suggestion(user_text: str, article_title: str = "", article_text: str = "",
                          year_level = 10, prewrite_summary: str = "") -> str:
    """
    Generate AI suggestion for the next paragraph based on user's writing.

    Args:
        user_text: What the user has written so far
        article_title: Title of the source article
        article_text: Text of the source article
        year_level: Student year level (7-13, can be int or string like 'Year 7')
        prewrite_summary: Optional writing plan/outline from the Plan tab

    Returns:
        AI suggested next paragraph or error message
    """
    if not user_text or len(user_text.strip()) < 10:
        return "Please write at least a sentence before asking for suggestions."

    # Normalize year level to integer
    year_level = normalize_year_level(year_level)

    # Analyze current writing
    word_count = len(user_text.split())
    paragraphs_written = len([p for p in user_text.split('\n\n') if p.strip()])

    # Age-appropriate paragraph length and complexity
    if year_level <= 8:
        # Years 7-8: 3-4 sentences, 60-100 words
        target_sentences = "3-4"
        target_words = "60-100"
        complexity_note = "Use simple, clear sentences. Start with a topic sentence, add 2-3 supporting details, end with a simple conclusion."
    elif year_level <= 10:
        # Years 9-10: 4-5 sentences, 80-120 words
        target_sentences = "4-5"
        target_words = "80-120"
        complexity_note = "Use varied sentence structures. Include a topic sentence, supporting evidence, and analytical commentary."
    else:
        # Years 11-13: 5-6 sentences, 120-180 words
        target_sentences = "5-6"
        target_words = "120-180"
        complexity_note = "Use sophisticated language with varied sentence structures. Include strong topic sentences, evidence, analysis, and thoughtful transitions."

    # Determine what to suggest next based on age group and writing plan
    if prewrite_summary:
        # Follow the writing plan structure based on age
        if year_level <= 8:
            # Years 7-8: 3 paragraphs
            if paragraphs_written == 0:
                next_focus = "Paragraph 1: Introduce the topic. Write about what/who this is about."
            elif paragraphs_written == 1:
                next_focus = "Paragraph 2: What happened. Add details about the main event."
            else:
                next_focus = "Paragraph 3: Why it matters. Explain the significance."
        elif year_level <= 10:
            # Years 9-10: 5 paragraphs
            if paragraphs_written == 0:
                next_focus = "Paragraph 1: Introduction with hook. Grab attention."
            elif paragraphs_written == 1:
                next_focus = "Paragraph 2: Background. Add context."
            elif paragraphs_written == 2:
                next_focus = "Paragraph 3: Evidence. Provide details and facts."
            elif paragraphs_written == 3:
                next_focus = "Paragraph 4: Implications. Discuss what this means."
            else:
                next_focus = "Paragraph 5: Conclusion. Summarize and end strongly."
        else:
            # Years 11-13: 6 paragraphs
            if paragraphs_written == 0:
                next_focus = "Paragraph 1: Introduction with compelling hook."
            elif paragraphs_written == 1:
                next_focus = "Paragraph 2: Background and context."
            elif paragraphs_written == 2:
                next_focus = "Paragraph 3: Detailed evidence and examples."
            elif paragraphs_written == 3:
                next_focus = "Paragraph 4: Analysis and interpretation."
            elif paragraphs_written == 4:
                next_focus = "Paragraph 5: Critical evaluation or implications."
            else:
                next_focus = "Paragraph 6: Conclusion with broader significance."
    else:
        # No writing plan - use word count-based progression
        if word_count < 40:
            next_focus = "Explain the main event in more detail: who is involved, what happened, when and where."
        elif word_count < 100:
            next_focus = "Add important context: why this happened, background information, or key facts from the article."
        elif word_count < 200:
            next_focus = "Discuss consequences or reactions: what are the effects, how people responded, or what happens next."
        else:
            next_focus = "Add deeper analysis: broader implications, connections to other events, or expert opinions from the article."

    # Truncate article text - increased to provide more context
    if len(article_text) > 5000:
        article_text = article_text[:5000]

    # Adjust language for year level
    if year_level <= 8:
        language_note = "Write in SIMPLE, CLEAR language for ages 11-13. Use short sentences. Avoid complex vocabulary."
    elif year_level <= 10:
        language_note = "Write in age-appropriate language for ages 14-15. Use varied sentences with some advanced vocabulary."
    else:
        language_note = "Write in SOPHISTICATED language for ages 16-18. Use complex sentence structures, advanced vocabulary, and analytical depth."

    # Build system prompt - ALWAYS emphasize age-appropriateness
    if prewrite_summary:
        system_prompt = f"""You are an expert writing coach helping a Year {year_level} student (age {year_level + 4}-{year_level + 5}).

THEY HAVE WRITTEN {paragraphs_written + 1} PARAGRAPH(S) SO FAR ({word_count} words).

YOUR TASK: Suggest ONLY the content for their NEXT paragraph.

CRITICAL REQUIREMENTS:
1. {target_sentences} sentences, {target_words} words
2. {complexity_note}
3. {language_note}
4. {next_focus}

WRITING PLAN TO FOLLOW:
{prewrite_summary}

STRICTLY FOLLOW the structure outlined in their writing plan. Your suggestion should align with the next logical section of their plan.

DO NOT repeat information already written. Use NEW information from the source article.
Return ONLY the paragraph text - no introductions, no explanations, no markdown formatting."""

    else:
        system_prompt = f"""You are an expert writing coach helping a Year {year_level} student (age {year_level + 4}-{year_level + 5}).

THEY HAVE WRITTEN {paragraphs_written + 1} PARAGRAPH(S) SO FAR ({word_count} words).

YOUR TASK: Suggest ONLY the content for their NEXT paragraph.

CRITICAL REQUIREMENTS:
1. {target_sentences} sentences, {target_words} words
2. {complexity_note}
3. {language_note}
4. {next_focus}

DO NOT repeat information already written. Use NEW information from the source article.
Return ONLY the paragraph text - no introductions, no explanations, no markdown formatting."""

    # Build user prompt with writing plan if available
    user_prompt = f"Student's current writing:\n{user_text}"

    if prewrite_summary:
        user_prompt += f"\n\nTheir Writing Plan (FOLLOW THIS CLOSELY):\n{prewrite_summary}"

    if article_title or article_text:
        user_prompt += "\n\nSource News Article:\n"
        if article_title:
            user_prompt += f"Title: {article_title}\n\n"
        if article_text:
            user_prompt += f"Article Content:\n{article_text[:1500]}"

    # Increase max_tokens for longer paragraphs
    estimated_tokens = max(1500, word_count * 2)

    logger.info(f"Generating suggestion for Year {year_level}: {paragraphs_written + 1} paragraph(s) written, {word_count} words")
    logger.info(f"Using writing plan: {bool(prewrite_summary)}")
    logger.info(f"Target: {target_sentences} sentences, {target_words} words")

    content, error = llm_chat(system_prompt, user_prompt, temperature=0.4, max_tokens=estimated_tokens, use_case="draft")

    if error:
        logger.error(f"Failed to generate suggestion: {error}")
        return f"Error generating suggestion: {error}"

    # Clean up AI response
    if content:
        content = _clean_ai_response(content)

    logger.info(f"Generated suggestion: {len(content) if content else 0} characters")

    return content or "No suggestion generated."


def improve_paragraph(paragraph: str, article_context: str = "", year_level = 10, selected_text: str = "") -> str:
    """
    Improve a student's writing with CODE-BASED analysis.

    Uses CODE-BASED checks for:
    - Plagiarism detection (similarity matching)
    - Spelling checking (dictionary)
    - Grammar checking (pattern matching)
    - Punctuation checking (rules)
    - Style checking (readability metrics)

    Uses AI ONLY for:
    - Rewriting the text (keeping same length)

    Args:
        paragraph: The full text or paragraph to improve
        article_context: Context from the source article (for plagiarism checking)
        year_level: Student year level (7-13, can be int or string like 'Year 7')
        selected_text: Optional specific text selection to focus on

    Returns:
        Improved version with detailed mentor feedback
    """
    # Determine if this is a selection improvement (must be defined early)
    is_selection = bool(selected_text)
    text_to_improve = selected_text if selected_text else paragraph

    # Early return for invalid input
    if not text_to_improve or len(text_to_improve.strip()) < 10:
        return "Please provide some text to improve."

    # Early return for very short text - skip AI entirely
    if len(text_to_improve.strip()) < 30:
        # Just do basic checks and return
        year_level = normalize_year_level(year_level)
        check_results = check_with_llm(text_to_improve, year_level, article_context, is_selection)

        spell_result = check_results['spelling']
        grammar_result = check_results['grammar']
        punctuation_result = check_results['punctuation']

        response_parts = [f"IMPROVED:\n{text_to_improve}"]
        response_parts.append("\n\nPLAGIARISM CHECK:\n✅ Text too short for plagiarism check.")
        response_parts.append("\n\nFEEDBACK:")

        # Spelling - ALWAYS show
        response_parts.append("\nSPELLING:")
        if spell_result['has_errors']:
            for error in spell_result['errors'][:3]:
                response_parts.append(f"• \"{error['word']}\" → \"{error['correction']}\"")
        else:
            response_parts.append("• No spelling errors found!")

        # Grammar - ALWAYS show
        response_parts.append("\nGRAMMAR:")
        if grammar_result['has_errors']:
            for error in grammar_result['errors'][:2]:
                response_parts.append(f"• \"{error['found']}\" → \"{error['correction']}\"")
        else:
            response_parts.append("• No grammar errors found!")

        # Punctuation - ALWAYS show
        response_parts.append("\nPUNCTUATION:")
        if punctuation_result['has_errors']:
            for error in punctuation_result['errors'][:2]:
                response_parts.append(f"• {error['explanation']}")
        else:
            response_parts.append("• No punctuation errors found!")

        # Style - ALWAYS show
        response_parts.append("\nSTYLE:")
        response_parts.append("• Write more text for style suggestions!")

        if spell_result['has_errors']:
            misspelled = ','.join([error['word'] for error in spell_result['errors']])
            response_parts.append(f"\n\nMISSPELLED_WORDS:\n{misspelled}")

        response_parts.append("\n\nLEARNING TIP:\nWrite more text to get detailed AI-powered improvements and feedback.")

        return "".join(response_parts)

    text_length = len(text_to_improve)
    logger.info(f"Improving {'selected text' if is_selection else 'full text'}, length: {text_length}")

    year_level = normalize_year_level(year_level)

    # ===== LLM-BASED CHECKS =====
    # Use LLM for grammar, spelling, and punctuation checking
    check_results = check_with_llm(text_to_improve, year_level, article_context, is_selection)

    spell_result = check_results['spelling']
    grammar_result = check_results['grammar']
    punctuation_result = check_results['punctuation']

    # Style check - use LLM results (always included in check_with_llm response)
    style_result = check_results.get('style', {'has_suggestions': False, 'suggestions': [], 'count': 0})

    # Skip plagiarism check for very short texts (< 80 chars) - not meaningful
    if text_length < 80:
        plagiarism_result = {
            'has_plagiarism': False,
            'similarity_percent': 0.0,
            'copied_phrases': [],
            'details': 'Text too short for plagiarism check.'
        }
    else:
        plagiarism_result = detect_plagiarism_code_based(text_to_improve, article_context)

    # ===== USE LLM TO REWRITE THE TEXT =====
    improved_text, llm_error = generate_improved_text_ai_only(text_to_improve, article_context, year_level, is_selection)

    # If LLM fails, fall back to original text
    if llm_error or not improved_text:
        logger.warning(f"LLM improvement failed: {llm_error}, using original text")
        improved_text = text_to_improve
    else:
        logger.info(f"Successfully generated improved text using LLM")

    # ===== BUILD RESPONSE IN CODE (NOT AI!) =====
    response_parts = []

    # 1. IMPROVED section
    response_parts.append(f"IMPROVED:\n{improved_text}")

    # 2. PLAGIARISM CHECK section
    if plagiarism_result['has_plagiarism']:
        plagiarism_text = f"⚠️ Found {plagiarism_result['similarity_percent']}% similarity to source. "
        if plagiarism_result['copied_phrases']:
            plagiarism_text += f"{len(plagiarism_result['copied_phrases'])} potentially copied phrase(s):\n"
            for phrase in plagiarism_result['copied_phrases'][:3]:
                plagiarism_text += f"  • \"{phrase[:80]}{'...' if len(phrase) > 80 else ''}\"\n"
        plagiarism_text += "Please rewrite these in your own words."
    else:
        plagiarism_text = f"✅ Good job! Your writing appears original ({plagiarism_result['similarity_percent']}% similarity)."

    response_parts.append(f"\n\nPLAGIARISM CHECK:\n{plagiarism_text}")

    # 3. FEEDBACK section - build from code results
    response_parts.append("\n\nFEEDBACK:")

    # Spelling - ALWAYS show this category
    response_parts.append("\nSPELLING:")
    if spell_result['has_errors']:
        for error in spell_result['errors'][:5]:
            response_parts.append(f"• \"{error['word']}\" → \"{error['correction']}\"")
    else:
        response_parts.append("• No spelling errors found!")

    # Grammar - ALWAYS show this category
    response_parts.append("\nGRAMMAR:")
    if grammar_result['has_errors']:
        logger.info(f"Adding {len(grammar_result['errors'])} grammar errors to response")
        for error in grammar_result['errors'][:5]:
            response_parts.append(f"• \"{error['found']}\" → \"{error['correction']}\" ({error['explanation']})")
    else:
        logger.info("No grammar errors found to add to response")
        response_parts.append("• No grammar errors found!")

    # Punctuation - ALWAYS show this category
    response_parts.append("\nPUNCTUATION:")
    if punctuation_result['has_errors']:
        for error in punctuation_result['errors'][:5]:
            response_parts.append(f"• {error['explanation']}")
    else:
        response_parts.append("• No punctuation errors found!")

    # Style - ALWAYS show this category
    # Format: "informal phrase" → "formal replacement" (explanation)
    response_parts.append("\nSTYLE:")
    if style_result['has_suggestions']:
        for suggestion in style_result['suggestions'][:3]:
            # Parse suggestion to extract informal word and formal replacement
            # Expected format from LLM/fallback: issue='Informal word "obvs"', suggestion='Use "obviously" instead'
            issue = suggestion.get('issue', '')
            suggest = suggestion.get('suggestion', '')

            # Extract the informal word from issue (look for quoted text)
            import re
            informal_match = re.search(r'"([^"]+)"', issue)
            formal_match = re.search(r'"([^"]+)"', suggest)

            if informal_match and formal_match:
                informal = informal_match.group(1)
                formal = formal_match.group(1)
                # Build explanation from remaining text
                explanation = suggest.replace(f'"{formal}"', '').replace('Use ', '').replace(' instead', '').strip()
                response_parts.append(f'• "{informal}" → "{formal}" ({explanation})')
            else:
                # Fallback to original format if parsing fails
                response_parts.append(f"• {issue}: {suggest}")
    else:
        response_parts.append("• No style suggestions - good job!")

    # 4. MISSPELLED_WORDS section for frontend highlighting (simple format)
    # Format: word1,word2,word3 (comma-separated list)
    if spell_result['has_errors']:
        misspelled_words = ','.join([error['word'] for error in spell_result['errors']])
        response_parts.append(f"\n\nMISSPELLED_WORDS:\n{misspelled_words}")

    # 4.5. INFORMAL_WORDS section for frontend highlighting (slang/informal words)
    # Format: word1,word2,word3 (comma-separated list)
    if style_result['has_suggestions']:
        informal_words = []
        for suggestion in style_result['suggestions'][:3]:
            issue = suggestion.get('issue', '')
            # Extract the informal word from issue (look for quoted text)
            import re
            informal_match = re.search(r'"([^"]+)"', issue)
            if informal_match:
                informal_words.append(informal_match.group(1))
        if informal_words:
            response_parts.append(f"\n\nINFORMAL_WORDS:\n{','.join(informal_words)}")

    # 5. LEARNING TIP - code-based
    learning_tips = [
        "Read your writing aloud to catch awkward phrasing.",
        "Use transition words like 'however', 'therefore', 'meanwhile' to connect ideas.",
        "Vary your sentence length to keep readers engaged.",
        "Replace weak words like 'very' or 'really' with stronger alternatives.",
        "Always proofread for missing punctuation and capitalization."
    ]

    # Select a relevant tip based on what errors were found
    if grammar_result['has_errors']:
        tip = learning_tips[0]
    elif punctuation_result['has_errors']:
        tip = learning_tips[4]
    elif style_result['has_suggestions']:
        tip = learning_tips[3]
    else:
        tip = learning_tips[2]

    response_parts.append(f"\n\nLEARNING TIP:\n{tip}")

    result = "".join(response_parts)
    logger.info(f"Improvement complete, returned {len(result)} characters")
    return result


# Test function
if __name__ == "__main__":
    print("Testing AI Writer functions...")
    
    # Test config
    base_url, api_key, model = get_llm_config()
    print(f"LLM Config: base_url={base_url[:30] if base_url else 'NOT SET'}..., model={model}")
    
    if base_url and api_key:
        # Test prewrite
        print("\nTesting prewrite summary...")
        summary = generate_prewrite_summary(
            "Test Article", 
            "This is a test article about climate change and its effects on coastal cities. Scientists warn that sea levels could rise by several meters by the end of the century.",
            year_level=10
        )
        print(f"Summary: {summary[:200]}...")
    else:
        print("LLM not configured - skipping API tests")
