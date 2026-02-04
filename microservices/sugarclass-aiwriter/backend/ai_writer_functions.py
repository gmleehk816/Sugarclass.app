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

# Try to import textstat, make it optional if not available
try:
    from textstat import flesch_kincaid_grade, gunning_fog
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    # Will log later when logger is initialized

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log textstat availability after logger is configured
if not TEXTSTAT_AVAILABLE:
    logger.warning("textstat not available - readability checks will be skipped")

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


def _get_cache_key(system_prompt: str, user_prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    """Generate a cache key from request parameters."""
    import hashlib
    # Create a hash of the key parameters for the cache key
    key_string = f"{model}:{temperature}:{max_tokens}:{system_prompt[:100]}:{user_prompt[:200]}"
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
             validate_completeness: bool = True) -> Tuple[Optional[str], Optional[str]]:
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

    Returns:
        (content, error) - content is None on error
    """
    base_url, api_key, model = get_llm_config(use_case)

    if not base_url or not api_key:
        return None, "LLM not configured. Set LLM_BASE_URL and LLM_API_KEY in environment."

    session = _get_session()

    # Clean expired cache entries periodically
    _clean_expired_cache()

    # Check cache for existing response
    cache_key = _get_cache_key(system_prompt, user_prompt, model, temperature, max_tokens)
    if cache_key in _llm_cache:
        cached_content, timestamp = _llm_cache[cache_key]
        import time as _time
        if _time.time() - timestamp < _CACHE_TTL:
            logger.info(f"Cache hit for key {cache_key[:8]}...")
            return cached_content, None
        else:
            # Expired, remove from cache
            del _llm_cache[cache_key]

    # Calculate minimum expected length based on prompts
    expected_min_length = max(50, len(user_prompt) // 10)

    # Track total time spent on retries (max 30 seconds)
    _start_time = time.time()
    _MAX_RETRY_TIME = 30  # Maximum total time for all retries

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
                timeout=30,  # 30 seconds for faster failure and retry
            )
            elapsed = time.time() - start_time
            logger.info(f"LLM response: status={resp.status_code}, time={elapsed:.2f}s")

            # Handle rate limiting with exponential backoff
            if resp.status_code == 429:
                if retry_count < max_retries:
                    elapsed_total = time.time() - _start_time
                    if elapsed_total >= _MAX_RETRY_TIME:
                        return None, f"Request timeout (exceeded {_MAX_RETRY_TIME}s total retry time)"
                    wait_time = (2 ** retry_count) * 1  # 1s, 2s, 4s
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
            logger.error(f"Request timeout after 30s (attempt {retry_count + 1})")
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

        # Cache successful response
        import time as _time
        _llm_cache[cache_key] = (str(content), _time.time())
        logger.debug(f"Cached response for key {cache_key[:8]}...")

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


def check_spelling_basic(user_text: str) -> dict:
    """
    Spell checking using pyspellchecker library (optimized with batch operations).

    Args:
        user_text: The student's written text

    Returns:
        Dictionary with spelling errors found with original word positions
    """
    try:
        from spellchecker import SpellChecker
        spell = SpellChecker()
    except ImportError:
        logger.warning("pyspellchecker not available - spelling check disabled")
        return {'has_errors': False, 'errors': [], 'count': 0}

    errors = []
    words = user_text.split()

    # Pre-process words to check - collect clean words with their indices
    words_to_check = []
    indices_to_check = []

    for i, word in enumerate(words):
        # Strip punctuation from both ends for checking
        clean_word = re.sub(r'^[^\w\'-]|[^\w\'-]$', '', word)

        # Skip very short words
        if len(clean_word) < 3:
            continue

        # Skip numbers
        if clean_word.isdigit():
            continue

        # Skip if word starts with capital (likely a proper noun)
        if clean_word[0].isupper():
            continue

        # Skip if word contains digits (like "asrc", "cuny2", etc.)
        if any(c.isdigit() for c in clean_word.lower()):
            continue

        # Skip common acronyms and technical terms (all lowercase versions)
        skip_words = {
            'asrc', 'cuny', 'nyc', 'ai', 'ml', 'api', 'url', 'http', 'https',
            'html', 'css', 'js', 'json', 'xml', 'sql', 'ios', 'android',
            'gpu', 'cpu', 'ram', 'usb', 'wifi', 'bluetooth', 'app', 'apps'
        }
        if clean_word.lower() in skip_words:
            continue

        words_to_check.append(clean_word)
        indices_to_check.append((i, word))

    if not words_to_check:
        return {'has_errors': False, 'errors': [], 'count': 0}

    # Batch check all unknown words at once (much faster)
    misspelled = spell.unknown(words_to_check)

    # Build errors list with positions
    for clean_word, (i, original_word) in zip(words_to_check, indices_to_check):
        if clean_word.lower() in misspelled:
            # Get the most likely correction
            correction = spell.correction(clean_word)

            # Only add if we found a valid correction AND it's different
            if correction and correction.lower() != clean_word.lower():
                # Sanity check: correction should be reasonable length
                if abs(len(correction) - len(clean_word)) <= 3:
                    errors.append({
                        'word': clean_word,  # The cleaned word without punctuation
                        'original': original_word,     # Original word with punctuation for display
                        'correction': correction,
                        'position': i
                    })

    return {
        'has_errors': len(errors) > 0,
        'errors': errors[:10],  # Limit to 10 errors
        'count': len(errors)
    }


def check_grammar_code_based(user_text: str) -> dict:
    """
    Code-based grammar checking using pattern matching.
    Detects common grammatical errors without AI.

    Args:
        user_text: The student's written text

    Returns:
        Dictionary with grammar errors found
    """
    errors = []

    # Subject-verb agreement patterns
    sv_agreement_errors = [
        (r'\b(he|she|it)\s+(have)\b', r'\1 \2', '"he have" → "he has" (subject-verb agreement)'),
        (r'\b(they|we|you)\s+(has)\b', r'\1 \2', '"they has" → "they have" (subject-verb agreement)'),
        (r'\b(there)\s+(is)\s+(?:a|an|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+\w+', r'\1 are', '"there is multiple" → "there are" (subject-verb agreement)'),
    ]

    # Article/determiner errors
    article_errors = [
        (r'\b(a)\s+([aeiou][a-z]+)\b', r'an \2', '"a [vowel]" → "an [vowel]"'),
        (r'\b(an)\s+([bcdfghjklmnpqrstvwxyz][a-z]+)\b', r'a \2', '"an [consonant]" → "a [consonant]"'),
    ]

    # Missing auxiliary verbs (will/can/shall/may/must + verb without be/have)
    missing_auxiliary = [
        (r'\b(will|can|shall|may|must)\s+([a-z]+ed)\b(?!\s+be)', r'\1 be \2', '"will constructed" → "will be constructed" (missing auxiliary verb)'),
        (r'\b(will|can|shall|may|must)\s+([a-z]+ing)\b(?!\s+be)', r'\1 be \2', '"will creating" → "will be creating" (missing auxiliary verb)'),
        (r'\b(will|can|shall|may|must)\s+([a-z]+s)\b(?!\s+be)', r'\1 be \2', '"will creates" → "will be creates" (missing auxiliary verb)'),
    ]

    # Missing "to" after certain verbs
    missing_to = [
        (r'\b(want|need|try|going|have)\s+(?!to\b)([a-z]+ing)\b', r'\1 to \2', '"want doing" → "want to do" (missing "to")'),
        (r'\b(want|need)\s+(?!to\b)([a-z]+)\b', r'\1 to \2', '"want go" → "want to go" (missing "to")'),
    ]

    # Wrong tense forms
    wrong_tense = [
        (r'\b(I|we|they|you)\s+(has)\b', r'\1 have', '"they has" → "they have" (wrong tense)'),
        (r'\b(he|she|it)\s+(have)\b', r'\1 has', '"he have" → "he has" (wrong tense)'),
    ]

    # Common word confusions
    word_confusion = [
        (r'\b(its)\s+(a|an)\b', r'it is', '"its a" → "it\'s a" (its vs it\'s)'),
        (r'\b(your)\s+(welcome)\b', r'you\'re welcome', '"your welcome" → "you\'re welcome" (your vs you\'re)'),
        (r'\b(their)\s+(is|are)\b', r'they\'re \2', '"their is" → "they\'re are" (their vs they\'re)'),
    ]

    # Missing auxiliary verbs (do/does/don't/doesn't)
    missing_do = [
        (r'\b(it|he|she)\s+(dont)\b', r"\1 doesn't", '"it dont" → "it doesn\'t" (missing auxiliary)'),
        (r'\b(they|we|you)\s+(dont)\b', r"\1 don't", '"they dont" → "they don\'t" (missing auxiliary)'),
        (r'\b(it|he|she)\s+(doesnt)\b', r"\1 doesn't", '"it doesnt" → "it doesn\'t" (missing apostrophe)'),
        (r'\b(they|we|you)\s+(doesnt)\b', r"\1 don't", '"they doesnt" → "they don\'t" (wrong auxiliary)'),
    ]

    # Common irregular verbs
    irregular_verbs = [
        (r'\b(maked)\b', 'made', '"maked" → "made" (irregular verb)'),
        (r'\b(taked)\b', 'took', '"taked" → "took" (irregular verb)'),
        (r'\b(gived)\b', 'gave', '"gived" → "gave" (irregular verb)'),
        (r'\b(writed)\b', 'wrote', '"writed" → "wrote" (irregular verb)'),
        (r'\b(keepped)\b', 'kept', '"keepped" → "kept" (irregular verb)'),
    ]

    # Missing past tense -ed
    missing_ed = [
        (r'\b(name)\s+(a|an|the)\b', 'named', '"name a" → "named a" (missing -ed)'),
        (r'\b(use)\s+(a|an|the)\b', 'used', '"use a" → "used a" (missing -ed)'),
        (r'\b(call)\s+(a|an|the)\b', 'called', '"call a" → "called a" (missing -ed)'),
    ]

    # Pluralization errors
    plural_errors = [
        (r'\bmany\s+way\b', 'many ways', '"many way" → "many ways" (missing plural)'),
        (r'\b(all\s+the)\s+([a-z]+)\s+(is|was)\b', r'all the \2s are', '"all the [word] is" → "all the [word]s are" (plural)'),
        (r'\btwo\s+([a-z]+)\s+(is|was)\b', r'two \2s are', '"two [word] is" → "two [word]s are" (plural)'),
    ]

    # Double negatives
    double_negative = r'\b(not|never|nothing|nowhere|neither|nobody)\s+(not|never|nothing|nowhere|nobody)\b'

    # Run all checks
    for pattern, correction_template, explanation in sv_agreement_errors + article_errors + missing_auxiliary + word_confusion + missing_to + wrong_tense + missing_do + irregular_verbs + missing_ed + plural_errors:
        for match in re.finditer(pattern, user_text, re.IGNORECASE):
            # Expand backreferences in correction template to get actual replacement text
            actual_correction = correction_template
            for i in range(1, len(match.groups()) + 1):
                if match.group(i):
                    # Replace \1, \2, etc. with actual captured groups
                    actual_correction = actual_correction.replace('\\' + str(i), match.group(i))

            errors.append({
                'type': 'Grammar',
                'found': match.group(0),
                'correction': actual_correction,
                'explanation': explanation,
                'position': match.start()
            })

    # Double negative check
    for match in re.finditer(double_negative, user_text, re.IGNORECASE):
        errors.append({
            'type': 'Grammar',
            'found': match.group(0),
            'correction': 'remove one negative',
            'explanation': 'Double negative - remove one negative word',
            'position': match.start()
        })

    logger.info(f"Grammar check found {len(errors)} errors")
    for error in errors[:3]:  # Log first 3 errors for debugging
        logger.info(f"  - '{error['found']}' → '{error['correction']}' ({error['explanation']})")

    return {
        'has_errors': len(errors) > 0,
        'errors': errors,
        'count': len(errors)
    }


def check_punctuation_code_based(user_text: str) -> dict:
    """
    Code-based punctuation checking.

    Args:
        user_text: The student's written text

    Returns:
        Dictionary with punctuation errors found
    """
    errors = []

    # Check for missing capitalization after sentence endings
    for match in re.finditer(r'[.!?]\s+([a-z])', user_text):
        errors.append({
            'type': 'Punctuation',
            'found': match.group(0),
            'correction': match.group(0)[0] + ' ' + match.group(1).upper(),
            'explanation': 'Capitalize the first letter after a period',
            'position': match.start()
        })

    # Check for missing periods at end
    lines = user_text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if line and not line.endswith(('.', '!', '?', '"', "'")):
            if len(line) > 20:  # Only if it looks like a sentence
                errors.append({
                    'type': 'Punctuation',
                    'found': line[-20:] if len(line) > 20 else line,
                    'correction': line + '.',
                    'explanation': 'Add a period at the end of the sentence',
                    'position': i
                })

    # Check for multiple spaces
    for match in re.finditer(r'  +', user_text):
        errors.append({
            'type': 'Punctuation',
            'found': match.group(0),
            'correction': ' ',
            'explanation': 'Use single space between words',
            'position': match.start()
        })

    # Check for space before punctuation
    for match in re.finditer(r'\s+([,.!?;:])', user_text):
        errors.append({
            'type': 'Punctuation',
            'found': match.group(0),
            'correction': match.group(1),
            'explanation': 'Remove space before punctuation',
            'position': match.start()
        })

    return {
        'has_errors': len(errors) > 0,
        'errors': errors[:10],  # Limit to first 10
        'count': len(errors)
    }


def check_style_code_based(user_text: str, year_level: int = 10) -> dict:
    """
    Code-based style checking using readability metrics and patterns.

    Args:
        user_text: The student's written text
        year_level: Student year level for appropriate complexity

    Returns:
        Dictionary with style feedback
    """
    suggestions = []
    sentences = re.split(r'[.!?]+', user_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return {'has_suggestions': False, 'suggestions': [], 'count': 0}

    # Check sentence length variation
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0

    if avg_length > 25:
        suggestions.append({
            'type': 'Style',
            'issue': f'Sentences are too long (average {avg_length:.1f} words)',
            'suggestion': 'Try breaking long sentences into shorter ones for clarity',
        })

    # Check for repetitive sentence starts
    first_words = [s.split()[0].lower() for s in sentences if s.split()]
    from collections import Counter
    first_word_counts = Counter(first_words)
    for word, count in first_word_counts.items():
        if count >= 3 and len(sentences) >= 4:
            suggestions.append({
                'type': 'Style',
                'issue': f'Starting {count} sentences with "{word}"',
                'suggestion': f'Vary sentence openings - try using transition words like "However", "Additionally", "Moreover"',
            })

    # Check for readability
    if TEXTSTAT_AVAILABLE:
        try:
            grade_level = flesch_kincaid_grade(user_text)
            if grade_level > year_level + 3:
                suggestions.append({
                    'type': 'Style',
                    'issue': f'Readability grade {grade_level:.1f} is above your level (Year {year_level})',
                    'suggestion': 'Consider using simpler vocabulary and shorter sentences',
                })
        except Exception as e:
            logger.debug(f"Readability check failed: {e}")
            pass  # Readability check failed, skip
    else:
        pass  # textstat not available, skip readability check

    # Check for weak words/phrases
    weak_phrases = [
        (r'\b(very|really|quite|rather)\s+', 'Avoid overusing intensifiers like "very" and "really"'),
        (r'\b(got|get)\s+', 'Replace "got/get" with more specific verbs like "received", "obtained", "became"'),
        (r'\b(stuff|things)\b', 'Use specific nouns instead of vague words like "stuff" and "things"'),
        (r'\b(basically|actually|literally)\s+', 'Remove unnecessary filler words'),
    ]

    for pattern, suggestion in weak_phrases:
        matches = list(re.finditer(pattern, user_text, re.IGNORECASE))
        if len(matches) >= 2:  # Only suggest if used multiple times
            suggestions.append({
                'type': 'Style',
                'issue': f'Overused phrase: {matches[0].group(0).strip()}',
                'suggestion': suggestion,
            })

    return {
        'has_suggestions': len(suggestions) > 0,
        'suggestions': suggestions[:5],
        'count': len(suggestions)
    }


def generate_improved_text_ai_only(text_to_improve: str, article_context: str, year_level: int) -> tuple:
    """
    Use AI ONLY for rewriting the text, not for formatting feedback.
    All analysis is done by code.

    Args:
        text_to_improve: The text to improve
        article_context: Source article for reference
        year_level: Student year level

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

    # System prompt with explicit instructions to avoid truncation
    system_prompt = f"""You are a writing assistant. Fix ALL spelling, grammar, punctuation, and clarity errors in the text.

Your task:
1. Correct spelling mistakes (e.g., "teh" → "the", "dont" → "don't")
2. Fix grammar errors (subject-verb agreement, tense, etc.)
3. Fix punctuation (missing periods, commas, capitalization)
4. Improve clarity while keeping the same meaning

IMPORTANT:
- Keep the same general length and meaning - do NOT summarize or expand significantly
- Keep the same number of sentences - fix errors within each sentence
- Output ONLY the corrected text, no explanations or labels
- {language_note}

Text to correct ({word_count} words):"""

    user_prompt = text_to_improve

    # Dynamic max_tokens based on input size to prevent truncation
    # Use word_count * 3 for output (rewritten text could be same length or longer)
    # Minimum 2000 tokens, no upper cap for safety
    estimated_tokens = max(2000, word_count * 3)

    content, error = llm_chat(system_prompt, user_prompt, temperature=0.2, max_tokens=estimated_tokens, use_case="draft")

    if error:
        return None, error

    # Clean up the response - remove any labels AI might have added
    if content:
        content = content.strip()

        # Remove common prefixes AI might add
        for prefix in ["Improved:", "IMPROVED:", "Here's the improved version:", "Rewritten:",
                        "Rewritten text:", "Here is the rewritten text:", "The improved version is:",
                        "Improved version:", "Here's your rewritten text:", "Below is the improved text:"]:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()

        # Remove any suffixes like explanations
        for suffix in ["I hope this helps!", "Let me know if you need any changes.",
                        "This version maintains the same meaning while fixing errors.",
                        "The improved version above fixes all the errors."]:
            if content.endswith(suffix):
                content = content[:-len(suffix)].strip()

        # If content contains section markers, extract only the first part
        for marker in ["PLAGIARISM CHECK:", "FEEDBACK:", "LEARNING TIP:", "GRAMMAR:",
                       "PUNCTUATION:", "STYLE:", "SPELLING:", "CLARITY:"]:
            if marker in content:
                content = content.split(marker)[0].strip()

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
    text_to_improve = selected_text if selected_text else paragraph

    # Early return for invalid input
    if not text_to_improve or len(text_to_improve.strip()) < 10:
        return "Please provide some text to improve."

    # Early return for very short text - skip AI entirely
    if len(text_to_improve.strip()) < 30:
        # Just do basic checks and return
        year_level = normalize_year_level(year_level)
        spell_result = check_spelling_basic(text_to_improve)
        grammar_result = check_grammar_code_based(text_to_improve)
        punctuation_result = check_punctuation_code_based(text_to_improve)

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

    is_selection = bool(selected_text)
    text_length = len(text_to_improve)
    logger.info(f"Improving {'selected text' if is_selection else 'full text'}, length: {text_length}")

    year_level = normalize_year_level(year_level)

    # ===== OPTIMIZED CODE-BASED CHECKS =====
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

    # Always check spelling - it's fast
    spell_result = check_spelling_basic(text_to_improve)

    # Always check grammar - it's fast with regex
    grammar_result = check_grammar_code_based(text_to_improve)

    # Always check punctuation - it's fast with regex
    punctuation_result = check_punctuation_code_based(text_to_improve)

    # Skip style check for very short texts (< 100 chars)
    if text_length < 100:
        style_result = {'has_suggestions': False, 'suggestions': [], 'count': 0}
    else:
        style_result = check_style_code_based(text_to_improve, year_level)

    # ===== USE LLM TO REWRITE THE TEXT =====
    improved_text, llm_error = generate_improved_text_ai_only(text_to_improve, article_context, year_level)

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
    response_parts.append("\nSTYLE:")
    if style_result['has_suggestions']:
        for suggestion in style_result['suggestions'][:3]:
            response_parts.append(f"• {suggestion['issue']}: {suggestion['suggestion']}")
    else:
        response_parts.append("• No style suggestions - good job!")

    # 4. MISSPELLED_WORDS section for frontend highlighting (simple format)
    # Format: word1,word2,word3 (comma-separated list)
    if spell_result['has_errors']:
        misspelled_words = ','.join([error['word'] for error in spell_result['errors']])
        response_parts.append(f"\n\nMISSPELLED_WORDS:\n{misspelled_words}")

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
