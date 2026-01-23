"""
Quality checker module for news articles.
Validates article quality using multiple criteria:
- Word count validation (minimum/maximum limits)
- Readability scoring (Flesch-Kincaid)
- Age group classification
- AI quality review (Gemini API)
"""
import os
import re
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import readability libraries
try:
    from textstat import flesch_reading_ease, flesch_kincaid_grade, syllable_count
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False
    print("[Warning] textstat not installed, readability scoring disabled")

# Import Gemini API
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("[Warning] google-generativeai not installed, AI quality review disabled")


# Age group word count requirements
AGE_GROUP_WORD_COUNTS = {
    "7-10": {"min": 150, "max": 600},
    "11-13": {"min": 250, "max": 900},
    "14-16": {"min": 400, "max": 1500},
}

# Readability score thresholds (Flesch Reading Ease)
# Higher score = easier to read
READABILITY_THRESHOLDS = {
    "7-10": (80, 100),   # Very easy
    "11-13": (60, 80),   # Standard
    "14-16": (0, 60),    # Fairly difficult to difficult
}


def count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    # Remove extra whitespace and split
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def calculate_readability(text: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate readability scores for text.
    
    Returns:
        (flesch_score, grade_level) tuple
        flesch_score: 0-100 (higher = easier)
        grade_level: US grade level
    """
    if not HAS_TEXTSTAT or not text:
        return None, None
    
    try:
        # Flesch Reading Ease: 0-100 (higher = easier)
        flesch_score = flesch_reading_ease(text)
        
        # Flesch-Kincaid Grade Level: US school grade
        grade = flesch_kincaid_grade(text)
        
        return flesch_score, grade
    except Exception as e:
        print(f"[ReadabilityError] {e}")
        return None, None


def classify_age_group(
    readability_score: Optional[float],
    word_count: int
) -> Optional[str]:
    """
    Classify article into age group based on readability.
    
    Args:
        readability_score: Flesch Reading Ease score (0-100)
        word_count: Number of words in article
    
    Returns:
        Age group string: "7-10", "11-13", "14-16", or None
    """
    if readability_score is None:
        return None
    
    # Classify by readability score
    if readability_score >= 80:
        age_group = "7-10"
    elif readability_score >= 60:
        age_group = "11-13"
    else:
        age_group = "14-16"
    
    # Validate word count for this age group
    limits = AGE_GROUP_WORD_COUNTS[age_group]
    if word_count < limits["min"] or word_count > limits["max"]:
        # Try next age group
        if age_group == "7-10" and word_count >= AGE_GROUP_WORD_COUNTS["11-13"]["min"]:
            age_group = "11-13"
        elif age_group == "11-13" and word_count >= AGE_GROUP_WORD_COUNTS["14-16"]["min"]:
            age_group = "14-16"
        elif age_group == "14-16" and word_count <= AGE_GROUP_WORD_COUNTS["11-13"]["max"]:
            age_group = "11-13"
    
    return age_group


def validate_article_length(text: str, age_group: Optional[str] = None) -> bool:
    """
    Validate article meets length requirements.
    
    Args:
        text: Article text
        age_group: Optional target age group
    
    Returns:
        True if valid, False if too short/long
    """
    word_count = count_words(text)
    
    if age_group:
        limits = AGE_GROUP_WORD_COUNTS.get(age_group)
        if limits:
            return limits["min"] <= word_count <= limits["max"]
    
    # General minimum (too short for any group)
    if word_count < 150:
        return False
    
    # General maximum (too long for kids)
    if word_count > 1500:
        return False
    
    return True


def check_quality_with_gemini(
    title: str,
    text: str,
    age_group: Optional[str] = None
) -> Tuple[Optional[float], Optional[str]]:
    """
    Use Gemini API to evaluate article quality.
    
    Args:
        title: Article title
        text: Article text
        age_group: Target age group
    
    Returns:
        (quality_score, feedback) tuple
        quality_score: 1-10 (reject < 5)
        feedback: Detailed quality assessment
    """
    if not HAS_GEMINI:
        return None, "Gemini API not available"
    
    # Configure Gemini
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        return None, "No Gemini API key configured"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        
        # Build prompt
        age_context = f" for age group {age_group}" if age_group else ""
        prompt = f"""Evaluate this news article{age_context} on a scale of 1-10.

Title: {title}

Text: {text[:2000]}

Criteria:
1. Educational Value: Does it teach something useful?
2. Factual Accuracy: Is information presented objectively?
3. Age Appropriateness: Is content suitable for kids{age_context}?
4. Engagement: Is it interesting and well-written?
5. Safety: Is content appropriate (no violence/inappropriate themes)?

Respond in this format:
SCORE: [1-10]
FEEDBACK: [One sentence summary]
"""
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Parse response
        score_match = re.search(r'SCORE:\s*(\d+)', result_text)
        feedback_match = re.search(r'FEEDBACK:\s*(.+)', result_text, re.DOTALL)
        
        if score_match:
            score = float(score_match.group(1))
            feedback = feedback_match.group(1).strip() if feedback_match else result_text
            return score, feedback
        
        return None, "Failed to parse Gemini response"
    
    except Exception as e:
        return None, f"Gemini API error: {str(e)}"


def evaluate_article(
    title: str,
    text: str,
    use_gemini: bool = False
) -> Dict:
    """
    Comprehensive article quality evaluation.
    
    Args:
        title: Article title
        text: Article full text
        use_gemini: Whether to use Gemini API for quality review
    
    Returns:
        Dictionary with quality metrics:
        {
            "word_count": int,
            "readability_score": float,
            "grade_level": float,
            "age_group": str,
            "is_valid_length": bool,
            "quality_score": float (if Gemini used),
            "quality_feedback": str (if Gemini used),
            "quality_check_status": str
        }
    """
    # Calculate basic metrics
    word_count = count_words(text)
    readability_score, grade_level = calculate_readability(text)
    
    # Classify age group
    age_group = classify_age_group(readability_score, word_count)
    
    # Validate length
    is_valid_length = validate_article_length(text, age_group)
    
    # Build result
    result = {
        "word_count": word_count,
        "readability_score": readability_score,
        "grade_level": grade_level,
        "age_group": age_group,
        "is_valid_length": is_valid_length,
        "quality_check_status": "checked",
    }
    
    # Optional Gemini quality check
    if use_gemini and age_group:
        quality_score, feedback = check_quality_with_gemini(title, text, age_group)
        result["quality_score"] = quality_score
        result["quality_feedback"] = feedback
        
        # Overall status
        if quality_score is not None:
            if quality_score >= 7:
                result["quality_check_status"] = "excellent"
            elif quality_score >= 5:
                result["quality_check_status"] = "good"
            else:
                result["quality_check_status"] = "rejected"
    
    return result


def should_keep_article(evaluation: Dict) -> bool:
    """
    Determine if article should be kept based on quality evaluation.
    
    Args:
        evaluation: Result from evaluate_article()
    
    Returns:
        True if article should be kept, False if rejected
    """
    # Must have valid length
    if not evaluation.get("is_valid_length"):
        return False
    
    # Must be classifiable into an age group
    if not evaluation.get("age_group"):
        return False
    
    # If Gemini scored it, must be >= 5
    quality_score = evaluation.get("quality_score")
    if quality_score is not None and quality_score < 5:
        return False
    
    return True


# Test function
if __name__ == "__main__":
    # Test article
    test_text = """
    Climate change is affecting our planet in many ways. Scientists have 
    discovered that polar ice caps are melting faster than expected. This 
    causes sea levels to rise, which can flood coastal cities. Animals like 
    polar bears are losing their homes. We can help by reducing our carbon 
    footprint, using less electricity, and recycling more. Every small action 
    counts in protecting our environment for future generations.
    """
    
    test_title = "How Climate Change Affects Our Planet"
    
    print("Testing quality checker...")
    print(f"\nTitle: {test_title}")
    print(f"Text length: {len(test_text)} chars")
    
    evaluation = evaluate_article(test_title, test_text, use_gemini=False)
    
    print("\n=== Evaluation Results ===")
    print(f"Word Count: {evaluation['word_count']}")
    print(f"Readability Score: {evaluation['readability_score']:.1f}")
    print(f"Grade Level: {evaluation['grade_level']:.1f}")
    print(f"Age Group: {evaluation['age_group']}")
    print(f"Valid Length: {evaluation['is_valid_length']}")
    print(f"Should Keep: {should_keep_article(evaluation)}")
