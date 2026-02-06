#!/usr/bin/env python3
"""
LLM Enhancement Generator

Uses LLM to extract educational features from content ONLY.
Does NOT rewrite or summarize the main content.
"""

import sys
from pathlib import Path
from typing import Optional
import json
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import Config


def _parse_llm_json(response_text: str) -> dict:
    """
    Robustly parse JSON from LLM response.
    Handles common issues like markdown code blocks, trailing commas,
    unescaped newlines in strings, etc.
    """
    text = response_text.strip()
    
    # Remove markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
            # Remove language identifier if present
            if text.startswith(('json', 'JSON')):
                text = text[4:].strip()
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Fix common JSON issues
    
    # 1. Fix unescaped newlines in strings
    # This regex finds strings and escapes newlines within them
    def escape_newlines_in_strings(match):
        s = match.group(0)
        # Replace actual newlines with escaped version
        s = s.replace('\n', '\\n').replace('\r', '\\r')
        return s
    
    # Find JSON strings (simplified pattern)
    text = re.sub(r'"[^"]*(?:[^"\\]|\\.)*"', escape_newlines_in_strings, text, flags=re.DOTALL)
    
    # 2. Remove trailing commas before ] or }
    text = re.sub(r',\s*([}\]])', r'\1', text)
    
    # 3. Fix single quotes to double quotes (only for JSON keys/values)
    # This is risky but sometimes needed
    if "'" in text and '"' not in text:
        text = text.replace("'", '"')
    
    # 4. Try to extract just the JSON object
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        text = json_match.group(0)
    
    # Second attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 5. More aggressive fixes for truncated JSON
    # Try to complete truncated arrays
    open_brackets = text.count('[') - text.count(']')
    open_braces = text.count('{') - text.count('}')
    
    # Add missing closing brackets
    if open_brackets > 0 or open_braces > 0:
        # Find the last complete value (ends with " or number or ] or })
        last_valid = len(text)
        for i in range(len(text) - 1, 0, -1):
            if text[i] in '"]}0123456789':
                last_valid = i + 1
                break
        
        text = text[:last_valid]
        # Remove trailing comma
        text = text.rstrip().rstrip(',')
        # Close arrays and objects
        text += ']' * open_brackets + '}' * open_braces
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    
    # 6. Extract individual fields manually as last resort
    result = {
        'learning_objectives': [],
        'key_terms': [],
        'questions': [],
        'takeaways': []
    }
    
    # Try to extract arrays using regex
    for field in ['learning_objectives', 'key_terms', 'questions', 'takeaways']:
        pattern = rf'"{field}"\s*:\s*\[(.*?)\]'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            array_content = match.group(1)
            # Extract strings
            strings = re.findall(r'"([^"]*)"', array_content)
            if strings:
                if field == 'key_terms':
                    # key_terms has objects with term and definition
                    result[field] = [{"term": s, "definition": ""} for s in strings]
                else:
                    result[field] = strings
    
    return result


def generate_enhancements(
    content: str,
    title: str = "",
    model: str = "gemini-1.5-flash",
    max_tokens: int = 2000
) -> dict:
    """
    Extract ONLY educational features from content using LLM.
    
    Args:
        content: Raw markdown content (can use first 5K-10K chars for context)
        title: Content title
        model: Gemini model to use
        max_tokens: Maximum tokens for response
    
    Returns:
        Dictionary with extracted features:
        {
            'learning_objectives': [str],
            'key_terms': [{'term': str, 'definition': str}],
            'questions': [str],
            'takeaways': [str]
        }
    """
    # Use first 5000 characters for context (enough to extract features)
    context_content = content[:5000]
    
    prompt = f"""You are an educational content analyst. Your task is to extract ONLY educational features from this content. Do NOT rewrite, summarize, or return the main content.

Title: {title}

Content (first 5000 characters for context):
{context_content}

Extract and return ONLY the following in JSON format:

{{
    "learning_objectives": [
        "Objective 1 (what students will learn)",
        "Objective 2",
        ...
    ],
    "key_terms": [
        {{"term": "Term1", "definition": "Definition1"}},
        {{"term": "Term2", "definition": "Definition2"}},
        ...
    ],
    "questions": [
        "Question 1 (Think About It discussion question)",
        "Question 2",
        "Question 3"
    ],
    "takeaways": [
        "Takeaway 1 (key point)",
        "Takeaway 2",
        "Takeaway 3",
        "Takeaway 4",
        "Takeaway 5"
    ]
}}

Requirements:
- Extract 3-5 learning objectives
- Extract 5-8 important key terms with definitions
- Create 3 thoughtful discussion questions
- Provide 5-8 key takeaways
- Return ONLY valid JSON (no markdown code blocks, no extra text)
- Be concise and educational

Return the JSON response only."""

    try:
        import requests
        
        # Use OpenAI-compatible API
        api_url = Config.LLM_API_URL
        api_key = Config.LLM_API_KEY
        
        response = requests.post(
            f"{api_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens
            },
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"{response.status_code} {response.text[:200]}")
        
        result = response.json()
        response_text = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        
        # Parse and clean the JSON response
        enhancements = _parse_llm_json(response_text)
        
        # Validate structure
        required_keys = ['learning_objectives', 'key_terms', 'questions', 'takeaways']
        for key in required_keys:
            if key not in enhancements:
                enhancements[key] = []
        
        # Ensure lists
        enhancements['learning_objectives'] = list(enhancements.get('learning_objectives', []))
        enhancements['key_terms'] = list(enhancements.get('key_terms', []))
        enhancements['questions'] = list(enhancements.get('questions', []))
        enhancements['takeaways'] = list(enhancements.get('takeaways', []))
        
        return enhancements
        
    except Exception as e:
        print(f"⚠️  Error generating enhancements: {e}")
        # Return empty structure on error
        return {
            'learning_objectives': [],
            'key_terms': [],
            'questions': [],
            'takeaways': []
        }


def generate_enhancements_batch(
    contents: list,
    titles: list = None,
    model: str = "gemini-1.5-flash",
    max_tokens: int = 2000
) -> list:
    """
    Generate enhancements for multiple contents.
    
    Args:
        contents: List of markdown content strings
        titles: List of titles (optional)
        model: Gemini model to use
        max_tokens: Maximum tokens per response
    
    Returns:
        List of enhancement dictionaries
    """
    if titles is None:
        titles = [""] * len(contents)
    
    results = []
    total = len(contents)
    
    for i, (content, title) in enumerate(zip(contents, titles), 1):
        print(f"Processing enhancement {i}/{total}: {title or 'Untitled'}")
        
        enhancements = generate_enhancements(
            content=content,
            title=title,
            model=model,
            max_tokens=max_tokens
        )
        
        results.append(enhancements)
        
        # Small delay to avoid rate limiting
        if i < total:
            import time
            time.sleep(0.5)
    
    return results


def validate_enhancements(enhancements: dict) -> dict:
    """
    Validate and score enhancement quality.
    
    Args:
        enhancements: Enhancement dictionary
    
    Returns:
        Dictionary with validation results and score
    """
    score = 0
    issues = []
    
    # Check learning objectives
    obj_count = len(enhancements.get('learning_objectives', []))
    if 3 <= obj_count <= 5:
        score += 25
    elif obj_count >= 1:
        score += 15
        issues.append(f"Learning objectives: {obj_count} (recommended 3-5)")
    else:
        issues.append("No learning objectives found")
    
    # Check key terms
    terms = enhancements.get('key_terms', [])
    if isinstance(terms[0], dict) if terms else False:
        term_count = len(terms)
        if 5 <= term_count <= 8:
            score += 25
        elif term_count >= 3:
            score += 15
            issues.append(f"Key terms: {term_count} (recommended 5-8)")
        else:
            issues.append(f"Insufficient key terms: {term_count}")
    else:
        issues.append("Key terms not in correct format")
    
    # Check questions
    q_count = len(enhancements.get('questions', []))
    if q_count == 3:
        score += 25
    elif q_count >= 1:
        score += 15
        issues.append(f"Questions: {q_count} (recommended 3)")
    else:
        issues.append("No questions found")
    
    # Check takeaways
    t_count = len(enhancements.get('takeaways', []))
    if 5 <= t_count <= 8:
        score += 25
    elif t_count >= 3:
        score += 15
        issues.append(f"Takeaways: {t_count} (recommended 5-8)")
    else:
        issues.append(f"Insufficient takeaways: {t_count}")
    
    return {
        'score': score,
        'max_score': 100,
        'passed': score >= 60,
        'issues': issues
    }


if __name__ == "__main__":
    # Test with sample content
    sample_content = """# Introduction to Materials Science

## Overview
Materials science is the study of materials and their properties. It encompasses various types of materials including metals, ceramics, polymers, and composites.

## Key Concepts

### Material Properties
Materials have various properties including mechanical, electrical, thermal, and optical properties. These properties determine how materials can be used in different applications.

### Material Selection
When selecting materials for engineering applications, engineers must consider factors such as strength, durability, cost, and environmental impact.

## Applications

1. Construction: Steel and concrete
2. Electronics: Silicon and copper
3. Aerospace: Aluminum and titanium
4. Medical: Biocompatible materials

The atomic structure of materials determines their macroscopic properties. Crystalline materials have ordered atomic arrangements, while amorphous materials have disordered structures.
"""
    
    print("=" * 80)
    print("Testing LLM Enhancement Generator")
    print("=" * 80)
    print()
    
    print("Generating enhancements for sample content...")
    enhancements = generate_enhancements(
        content=sample_content,
        title="Introduction to Materials Science"
    )
    
    print("\n" + "=" * 80)
    print("Generated Enhancements")
    print("=" * 80)
    print()
    
    print(f"Learning Objectives ({len(enhancements['learning_objectives'])}):")
    for i, obj in enumerate(enhancements['learning_objectives'], 1):
        print(f"  {i}. {obj}")
    
    print(f"\nKey Terms ({len(enhancements['key_terms'])}):")
    for term in enhancements['key_terms']:
        if isinstance(term, dict):
            print(f"  • {term.get('term', 'N/A')}: {term.get('definition', 'N/A')}")
        else:
            print(f"  • {term}")
    
    print(f"\nQuestions ({len(enhancements['questions'])}):")
    for i, question in enumerate(enhancements['questions'], 1):
        print(f"  {i}. {question}")
    
    print(f"\nKey Takeaways ({len(enhancements['takeaways'])}):")
    for i, takeaway in enumerate(enhancements['takeaways'], 1):
        print(f"  {i}. {takeaway}")
    
    # Validate
    print("\n" + "=" * 80)
    print("Validation Results")
    print("=" * 80)
    
    validation = validate_enhancements(enhancements)
    print(f"Score: {validation['score']}/{validation['max_score']}")
    print(f"Passed: {'✅' if validation['passed'] else '❌'}")
    
    if validation['issues']:
        print("\nIssues:")
        for issue in validation['issues']:
            print(f"  ⚠️  {issue}")
    
    print("\n✓ Test complete!")