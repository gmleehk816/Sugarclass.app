#!/usr/bin/env python3
"""
Content Enhancer - Uses LLM to enhance educational content quality

This module takes raw markdown content and uses LLM to:
1. Improve explanations and clarity
2. Add examples and analogies
3. Enhance formatting and structure
4. Make content more engaging and educational

Unlike generate_llm_enhancements which only extracts metadata,
this module actually improves the main content itself.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List
import json
import re
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import Config


def _call_llm(prompt: str, model: str = "gemini-2.5-flash-cli", max_tokens: int = 8000) -> str:
    """Call the LLM API and return the response text."""
    import requests
    
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
            "max_tokens": max_tokens,
            "temperature": 0.7
        },
        timeout=300
    )
    
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text[:500]}")
    
    result = response.json()
    return result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()


def enhance_section_content(
    section_content: str,
    section_title: str = "",
    subject: str = "",
    context: str = "",
    model: str = "gemini-2.5-flash-cli"
) -> str:
    """
    Enhance a single section of content using LLM.
    
    Args:
        section_content: The markdown content of one section
        section_title: Title of the section
        subject: Subject area (e.g., Chemistry, Physics)
        context: Additional context about the topic
        model: LLM model to use
    
    Returns:
        Enhanced markdown content
    """
    
    prompt = f"""You are an expert educational content writer specializing in {subject or 'science education'}.

**Task**: Enhance the following educational content to make it clearer, more engaging, and more educational.

**Section Title**: {section_title}

**Original Content**:
```
{section_content[:6000]}
```

**Enhancement Guidelines**:
1. **Improve Clarity**: Rewrite confusing sentences to be clearer
2. **Add Examples**: Add real-world examples or analogies where helpful
3. **Better Explanations**: Expand on complex concepts with step-by-step explanations
4. **Engaging Language**: Use more engaging, student-friendly language
5. **Maintain Structure**: Keep the same general structure (headings, lists, tables)
6. **Preserve Key Information**: Don't remove any important facts or data
7. **Format Properly**: Use proper markdown formatting

**Important Rules**:
- Keep all original facts, figures, and data accurate
- Don't add incorrect information
- Maintain scientific accuracy
- Keep the content appropriate for IGCSE level students
- Output ONLY the enhanced markdown content, no explanations

**Enhanced Content**:"""

    try:
        enhanced = _call_llm(prompt, model=model, max_tokens=8000)
        
        # Clean up response
        if enhanced.startswith("```markdown"):
            enhanced = enhanced[11:]
        elif enhanced.startswith("```"):
            enhanced = enhanced[3:]
        if enhanced.endswith("```"):
            enhanced = enhanced[:-3]
        
        return enhanced.strip()
    except Exception as e:
        print(f"  ⚠️ Error enhancing section: {e}")
        return section_content  # Return original on error


def enhance_full_content(
    markdown_content: str,
    title: str = "",
    subject: str = "",
    model: str = "gemini-2.5-flash-cli",
    chunk_size: int = 3000,
    verbose: bool = True
) -> str:
    """
    Enhance full markdown content by processing it in chunks.
    
    Args:
        markdown_content: Full markdown content
        title: Content title
        subject: Subject area
        model: LLM model to use
        chunk_size: Size of chunks to process
        verbose: Print progress
    
    Returns:
        Enhanced markdown content
    """
    
    # Split content into sections by headings
    sections = split_into_sections(markdown_content)
    
    if verbose:
        print(f"  📝 Enhancing {len(sections)} sections...")
    
    enhanced_sections = []
    
    for i, (heading, content) in enumerate(sections):
        if verbose:
            print(f"    [{i+1}/{len(sections)}] Processing: {heading[:50]}...")
        
        # Skip very short sections or empty ones
        if len(content.strip()) < 100:
            enhanced_sections.append((heading, content))
            continue
        
        # Enhance the section
        enhanced_content = enhance_section_content(
            section_content=content,
            section_title=heading,
            subject=subject,
            context=title,
            model=model
        )
        
        enhanced_sections.append((heading, enhanced_content))
        
        # Rate limiting
        time.sleep(0.5)
    
    # Rebuild the document
    result_parts = []
    for heading, content in enhanced_sections:
        if heading:
            result_parts.append(heading)
        result_parts.append(content)
    
    return '\n\n'.join(result_parts)


def split_into_sections(markdown_content: str) -> List[tuple]:
    """
    Split markdown content into sections based on headings.
    
    Returns: List of (heading, content) tuples
    """
    lines = markdown_content.split('\n')
    sections = []
    current_heading = ""
    current_content = []
    
    for line in lines:
        # Check if this is a heading (# ## ### etc)
        if line.strip().startswith('#'):
            # Save previous section
            if current_content:
                sections.append((current_heading, '\n'.join(current_content)))
            current_heading = line.strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Don't forget the last section
    if current_content:
        sections.append((current_heading, '\n'.join(current_content)))
    
    return sections


def enhance_content_smart(
    markdown_content: str,
    title: str = "",
    subject: str = "",
    model: str = "gemini-2.5-flash-cli",
    verbose: bool = True
) -> Dict:
    """
    Smart content enhancement that:
    1. Enhances the main content
    2. Generates educational metadata (objectives, terms, questions, takeaways)
    
    This is the main function to use for full content enhancement.
    
    Args:
        markdown_content: Raw markdown content
        title: Content title
        subject: Subject area
        model: LLM model
        verbose: Print progress
    
    Returns:
        Dictionary with 'enhanced_content' and 'metadata'
    """
    
    if verbose:
        print(f"🚀 Starting smart content enhancement for: {title}")
        print(f"   Original content: {len(markdown_content):,} chars")
    
    # Step 1: Enhance the main content
    if verbose:
        print("📖 Step 1: Enhancing main content...")
    
    enhanced_content = enhance_full_content(
        markdown_content=markdown_content,
        title=title,
        subject=subject,
        model=model,
        verbose=verbose
    )
    
    if verbose:
        print(f"   Enhanced content: {len(enhanced_content):,} chars")
    
    # Step 2: Generate educational metadata
    if verbose:
        print("📚 Step 2: Generating educational metadata...")
    
    metadata = generate_educational_metadata(
        content=enhanced_content[:8000],  # Use first 8K of enhanced content
        title=title,
        subject=subject,
        model=model
    )
    
    if verbose:
        print(f"   Generated: {len(metadata.get('learning_objectives', []))} objectives, "
              f"{len(metadata.get('key_terms', []))} terms, "
              f"{len(metadata.get('questions', []))} questions, "
              f"{len(metadata.get('takeaways', []))} takeaways")
    
    return {
        'enhanced_content': enhanced_content,
        'metadata': metadata
    }


def generate_educational_metadata(
    content: str,
    title: str = "",
    subject: str = "",
    model: str = "gemini-2.5-flash-cli"
) -> Dict:
    """
    Generate educational metadata from content.
    
    Returns:
        Dictionary with learning_objectives, key_terms, questions, takeaways
    """
    
    prompt = f"""You are an educational content analyst for {subject or 'science'}.

Analyze this content and extract educational metadata.

**Title**: {title}

**Content**:
```
{content[:8000]}
```

Return a JSON object with:
1. **learning_objectives**: 4-6 clear, measurable learning objectives starting with action verbs (Understand, Explain, Describe, Compare, Analyze, Apply)
2. **key_terms**: 6-10 important terms with clear definitions. Format: [{{"term": "...", "definition": "..."}}]
3. **questions**: 4-6 thought-provoking discussion or review questions
4. **takeaways**: 5-8 key points students should remember

**Output only valid JSON, no markdown code blocks or extra text**:"""

    try:
        response = _call_llm(prompt, model=model, max_tokens=3000)
        
        # Parse JSON
        return _parse_json_response(response)
    except Exception as e:
        print(f"  ⚠️ Error generating metadata: {e}")
        return {
            'learning_objectives': [],
            'key_terms': [],
            'questions': [],
            'takeaways': []
        }


def _parse_json_response(response: str) -> Dict:
    """Parse JSON from LLM response with error handling."""
    text = response.strip()
    
    # Remove markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Remove trailing commas
    text = re.sub(r',\s*([}\]])', r'\1', text)
    
    # Extract JSON object
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        text = json_match.group(0)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Return empty structure
        return {
            'learning_objectives': [],
            'key_terms': [],
            'questions': [],
            'takeaways': []
        }


# Test function
if __name__ == "__main__":
    # Quick test
    test_content = """
# States of Matter

Matter exists in three main states: solid, liquid, and gas.

## Solids
In solids, particles are closely packed together in a regular arrangement. They vibrate but don't move from their positions. Solids have:
- Fixed shape
- Fixed volume
- High density

## Liquids  
In liquids, particles are close together but can move past each other. Liquids have:
- No fixed shape (takes container shape)
- Fixed volume
- Medium density

## Gases
In gases, particles are far apart and move randomly at high speeds. Gases have:
- No fixed shape
- No fixed volume (fills container)
- Low density

The state of matter depends on temperature and pressure.
"""
    
    result = enhance_content_smart(
        markdown_content=test_content,
        title="States of Matter",
        subject="Chemistry",
        verbose=True
    )
    
    print("\n" + "="*50)
    print("ENHANCED CONTENT:")
    print("="*50)
    print(result['enhanced_content'][:2000])
    print("\n" + "="*50)
    print("METADATA:")
    print("="*50)
    print(json.dumps(result['metadata'], indent=2))
