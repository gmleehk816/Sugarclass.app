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

# Path to aiwriter's api.txt
_AIWRITER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aiwriter")
_DOTENV_PATH = os.path.join(_AIWRITER_PATH, "api.txt")


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


def llm_chat(system_prompt: str, user_prompt: str, temperature: float = 0.3, 
             max_tokens: int = 1000, use_case: str = None, retry_model: str = None) -> tuple[str, str]:
    """
    Call LLM API and return (content, error).
    Returns (None, error_message) on failure.
    If content is empty, retries with retry_model (default: gemini-3-flash-preview).
    """
    base_url, api_key, model = get_llm_config(use_case)
    
    if not base_url or not api_key:
        return None, "LLM not configured. Set LLM_BASE_URL and LLM_API_KEY in environment."
    
    def _try_request(use_model, retry_count=0, max_retries=3):
        payload = {
            "model": use_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            resp = requests.post(
                f"{base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
            
            # Handle rate limiting with exponential backoff
            if resp.status_code == 429:
                if retry_count < max_retries:
                    wait_time = (2 ** retry_count) * 1  # 1s, 2s, 4s
                    time.sleep(wait_time)
                    return _try_request(use_model, retry_count + 1, max_retries)
                return None, f"API rate limit exceeded (HTTP 429). Please try again in a few moments."
            
            if resp.status_code >= 400:
                return None, f"API error: HTTP {resp.status_code}"
            
            data = resp.json()
            content = (data.get("choices") or [])[0].get("message", {}).get("content")
            return content, None
            
        except requests.Timeout:
            if retry_count < max_retries:
                time.sleep(1)
                return _try_request(use_model, retry_count + 1, max_retries)
            return None, "Request timeout"
        except requests.RequestException as e:
            return None, f"Request error: {e}"
    
    try:
        # First attempt with configured model
        content, error = _try_request(model)
        
        if error:
            return None, error
        
        # If empty response, try fallback model
        if not content and model != "gemini-3-flash-preview":
            fallback = retry_model or "gemini-3-flash-preview"
            content, error = _try_request(fallback)
            if error:
                return None, error
        
        if not content:
            return None, "Empty response from LLM (tried fallback)"
        
        return str(content), None
        
    except requests.Timeout:
        return None, "Request timeout"
    except requests.RequestException as e:
        return None, f"Request error: {e}"
    except (ValueError, KeyError, IndexError) as e:
        return None, f"Parse error: {e}"


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
    
    # Truncate for prompt
    if len(article_text) > 4000:
        article_text = article_text[:4000]
    
    # Adjust complexity based on year level
    if year_level <= 8:
        complexity = "Use simple language suitable for ages 11-13. Keep sentences short and clear."
    elif year_level <= 10:
        complexity = "Use age-appropriate language for ages 14-15. Include some more advanced vocabulary."
    else:
        complexity = "Use sophisticated language appropriate for senior students aged 16-18."
    
    system_prompt = f"""Generate a COMPACT prewrite summary with bullet points:
• Main topic: 1 sentence
• Key facts: 3 bullets (max 10 words each)
• Structure: Intro/Body/Conclusion (1 line each)
{complexity}
Aim for 100-150 words MAX. Use plain text with asterisks (*) for bullets. Be extremely concise."""

    user_prompt = f"Article title: {article_title}\n\nArticle text:\n{article_text}"
    
    content, error = llm_chat(system_prompt, user_prompt, temperature=0.3, max_tokens=300, use_case="summary")
    
    if error:
        return f"Error generating summary: {error}"
    
    return content or "No summary generated."


def generate_ai_suggestion(user_text: str, article_title: str = "", article_text: str = "",
                          year_level = 10) -> str:
    """
    Generate AI suggestion for the next paragraph based on user's writing.
    
    Args:
        user_text: What the user has written so far
        article_title: Title of the source article
        article_text: Text of the source article
        year_level: Student year level (7-13, can be int or string like 'Year 7')
    
    Returns:
        AI suggested next paragraph or error message
    """
    if not user_text or len(user_text.strip()) < 10:
        return "Please write at least a sentence before asking for suggestions."
    
    # Normalize year level to integer
    year_level = normalize_year_level(year_level)
    
    # Analyze current writing
    word_count = len(user_text.split())
    paragraphs_written = len([p for p in user_text.split('\n') if p.strip()])
    
    # Determine what to suggest next
    if word_count < 40:
        next_focus = "Explain the main event in more detail: who is involved, what happened, when and where."
    elif word_count < 100:
        next_focus = "Add important context: why this happened, background information, or key facts from the article."
    elif word_count < 200:
        next_focus = "Discuss consequences or reactions: what are the effects, how people responded, or what happens next."
    else:
        next_focus = "Add deeper analysis: broader implications, connections to other events, or expert opinions from the article."
    
    # Truncate article text
    if len(article_text) > 2500:
        article_text = article_text[:2500]
    
    # Adjust language for year level
    if year_level <= 8:
        language_note = "Write in simple, clear language for younger students (ages 11-13)."
    elif year_level <= 10:
        language_note = "Write in age-appropriate language for middle secondary students (ages 14-15)."
    else:
        language_note = "Write in sophisticated language appropriate for senior students (ages 16-18)."
    
    system_prompt = f"""You are a writing coach helping a student write about a news article.
They have written {word_count} words so far. Suggest what their NEXT paragraph should cover.
{next_focus}
{language_note}
Return ONLY one complete, well-developed paragraph (4-6 sentences, 100-150 words) using facts from the source article below.
Do NOT repeat information they've already written. Plain text only, no markdown, no quotes."""

    topic_context = ""
    if article_title or article_text:
        topic_context += "\n\nSource News Article:\n"
        if article_title:
            topic_context += f"Title: {article_title}\n\n"
        if article_text:
            topic_context += f"Article Content:\n{article_text[:1200]}"
    
    user_prompt = f"What the student has written so far:\n{user_text}{topic_context}"
    
    content, error = llm_chat(system_prompt, user_prompt, temperature=0.4, max_tokens=300, use_case="draft")
    
    if error:
        return f"Error generating suggestion: {error}"
    
    return content or "No suggestion generated."


def improve_paragraph(paragraph: str, article_context: str = "", year_level = 10) -> str:
    """
    Improve a single paragraph with better structure and language.
    
    Args:
        paragraph: The paragraph to improve
        article_context: Context from the source article
        year_level: Student year level (7-13, can be int or string like 'Year 7')
    
    Returns:
        Improved version of the paragraph
    """
    if not paragraph or len(paragraph.strip()) < 20:
        return "Please provide some text to improve."
    
    # Normalize year level to integer
    year_level = normalize_year_level(year_level)
    
    if year_level <= 8:
        language_note = "Keep language simple and clear for ages 11-13."
    elif year_level <= 10:
        language_note = "Use moderate complexity for ages 14-15."
    else:
        language_note = "Use sophisticated language for ages 16-18."
    
    system_prompt = f"""Improve this student's paragraph:
1. Fix any grammar or spelling errors
2. Improve sentence structure and flow
3. Make it more engaging while keeping the core meaning
{language_note}
Return ONLY the improved paragraph. No explanations, no markdown."""

    content, error = llm_chat(system_prompt, paragraph, temperature=0.3, max_tokens=200, use_case="draft")
    
    if error:
        return paragraph  # Return original on error
    
    return content or paragraph


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
