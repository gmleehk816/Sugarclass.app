"""
Extraction Rules for Content Builder
Provides regex patterns and functions to extract structured content from raw markdown files.
"""

import re
from typing import List, Dict, Optional, Tuple


# ============================================
# Header and Section Patterns
# ============================================

TOPIC_HEADER_PATTERN = r'^#{1,3}\s+(.+)$'
SUBTOPIC_HEADER_PATTERN = r'^#{4,6}\s+(.+)$'
SECTION_PATTERN = r'^##+\s+(.+)$'


# ============================================
# Content Block Patterns
# ============================================

KEY_DEFINITION_PATTERN = r'\*\*([A-Za-z\s]+?)\*\*:\s*(.+?)\n'
KEY_TERM_PATTERN = r'\*([A-Za-z\s]+?)\*:\s*(.+?)\n'
KEY_POINT_PATTERN = r'\d+\.?\s+([A-Z][^.\n]+)'
BULLET_POINT_PATTERN = r'^[\s]*[•\-\*]\s+(.+)$'


# ============================================
# Mathematical Expression Patterns
# ============================================

INLINE_MATH_PATTERN = r'\$([^$]+)\$'
BLOCK_MATH_PATTERN = r'\$\$([^$]+)\$\$'


# ============================================
# Image and Table Patterns
# ============================================

IMAGE_PATTERN = r'!\[([^\]]*)\]\(([^\)]+)\)'
TABLE_PATTERN = r'(\|[^\n]+\|[^\n]*\n)+'


# ============================================
# Extraction Functions
# ============================================

def extract_headers(content: str) -> List[Dict[str, str]]:
    """
    Extract all headers from markdown content.
    
    Args:
        content: The markdown content
        
    Returns:
        List of headers with level and text
    """
    headers = []
    
    # Match headers (### Header text)
    pattern = r'^(#{1,6})\s+(.+)$'
    matches = re.finditer(pattern, content, re.MULTILINE)
    
    for match in matches:
        level = len(match.group(1))
        text = match.group(2).strip()
        headers.append({
            'level': level,
            'text': text,
            'position': match.start()
        })
    
    return headers


def extract_key_definitions(content: str) -> List[Dict[str, str]]:
    """
    Extract key definitions from content.
    
    Args:
        content: The markdown content
        
    Returns:
        List of definitions with term and explanation
    """
    definitions = []
    
    # Pattern: **Term**: Explanation
    pattern = r'\*\*([A-Za-z\s]+?)\*\*:\s*(.+?)(?=\n|$|\*\*)'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        term = match.group(1).strip()
        explanation = match.group(2).strip()
        definitions.append({
            'term': term,
            'explanation': explanation
        })
    
    return definitions


def extract_key_points(content: str) -> List[str]:
    """
    Extract key points from numbered lists or bullet points.
    
    Args:
        content: The markdown content
        
    Returns:
        List of key points
    """
    points = []
    
    # Numbered points: 1. Point text
    numbered_pattern = r'^\s*\d+\.?\s+(.+)$'
    matches = re.finditer(numbered_pattern, content, re.MULTILINE)
    
    for match in matches:
        point = match.group(1).strip()
        if len(point) > 10:  # Filter out very short points
            points.append(point)
    
    # Bullet points: - Point text or * Point text
    bullet_pattern = r'^\s*[\-\*]\s+(.+)$'
    matches = re.finditer(bullet_pattern, content, re.MULTILINE)
    
    for match in matches:
        point = match.group(1).strip()
        if len(point) > 10:
            points.append(point)
    
    return points


def extract_math_expressions(content: str) -> List[Dict[str, str]]:
    """
    Extract mathematical expressions from content.
    
    Args:
        content: The markdown content
        
    Returns:
        List of expressions with type and content
    """
    expressions = []
    
    # Inline math: $expression$
    inline_pattern = r'\$([^$]+)\$'
    matches = re.finditer(inline_pattern, content)
    
    for match in matches:
        expr = match.group(1).strip()
        if expr:
            expressions.append({
                'type': 'inline',
                'content': expr
            })
    
    # Block math: $$expression$$
    block_pattern = r'\$\$([^$]+)\$\$'
    matches = re.finditer(block_pattern, content, re.DOTALL)
    
    for match in matches:
        expr = match.group(1).strip()
        if expr:
            expressions.append({
                'type': 'block',
                'content': expr
            })
    
    return expressions


def extract_images(content: str) -> List[Dict[str, str]]:
    """
    Extract image references from content.
    
    Args:
        content: The markdown content
        
    Returns:
        List of images with alt text and path
    """
    images = []
    
    # Pattern: ![alt text](path)
    pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        alt_text = match.group(1)
        path = match.group(2)
        images.append({
            'alt': alt_text,
            'path': path
        })
    
    return images


def extract_tables(content: str) -> List[str]:
    """
    Extract markdown tables from content.
    
    Args:
        content: The markdown content
        
    Returns:
        List of table markdown strings
    """
    tables = []
    
    # Pattern: Multiple rows with pipe separators
    lines = content.split('\n')
    current_table = []
    
    for line in lines:
        if '|' in line and line.strip():
            current_table.append(line)
        elif current_table:
            # Table ended
            if len(current_table) >= 2:  # At least header and separator
                tables.append('\n'.join(current_table))
            current_table = []
    
    # Check for table at end of content
    if len(current_table) >= 2:
        tables.append('\n'.join(current_table))
    
    return tables


def extract_code_blocks(content: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from content.
    
    Args:
        content: The markdown content
        
    Returns:
        List of code blocks with language and content
    """
    code_blocks = []
    
    # Pattern: ```language
    # code
    # ```
    pattern = r'```(\w*)\n(.*?)```'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        language = match.group(1) or 'text'
        code = match.group(2)
        code_blocks.append({
            'language': language,
            'content': code
        })
    
    return code_blocks


# ============================================
# Content Analysis Functions
# ============================================

def analyze_content_structure(content: str) -> Dict[str, any]:
    """
    Analyze the overall structure of content.
    
    Args:
        content: The markdown content
        
    Returns:
        Dictionary with structure analysis
    """
    headers = extract_headers(content)
    definitions = extract_key_definitions(content)
    points = extract_key_points(content)
    math_exprs = extract_math_expressions(content)
    images = extract_images(content)
    tables = extract_tables(content)
    code_blocks = extract_code_blocks(content)
    
    return {
        'header_count': len(headers),
        'header_levels': [h['level'] for h in headers],
        'definition_count': len(definitions),
        'key_points_count': len(points),
        'math_expressions_count': len(math_exprs),
        'image_count': len(images),
        'table_count': len(tables),
        'code_block_count': len(code_blocks),
        'has_examples': 'example' in content.lower(),
        'has_summary': 'summary' in content.lower() or 'conclusion' in content.lower()
    }


def extract_subtopic_structure(content: str, subtopic_id: str = None) -> Dict[str, any]:
    """
    Extract structured information for a subtopic.
    
    Args:
        content: The markdown content
        subtopic_id: Optional subtopic identifier
        
    Returns:
        Dictionary with extracted structured data
    """
    headers = extract_headers(content)
    
    # Find main title (first h1 or h2)
    title = subtopic_id or "Untitled"
    for header in headers:
        if header['level'] <= 2:
            title = header['text']
            break
    
    structure = analyze_content_structure(content)
    
    return {
        'subtopic_id': subtopic_id,
        'title': title,
        'structure': structure,
        'headers': headers,
        'definitions': extract_key_definitions(content),
        'key_points': extract_key_points(content),
        'images': extract_images(content),
        'math_expressions': extract_math_expressions(content),
        'tables': extract_tables(content)
    }


def clean_content_for_ai(content: str, max_length: int = 8000) -> str:
    """
    Clean and prepare content for AI processing.
    
    Args:
        content: The markdown content
        max_length: Maximum length to keep
        
    Returns:
        Cleaned content
    """
    # Remove excessive whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', content)
    
    # Remove HTML comments
    cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
    
    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + '... [truncated]'
    
    return cleaned.strip()