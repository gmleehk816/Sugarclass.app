"""
Comprehensive Math Processing for Content Building
Provides functions to extract, preserve, and restore mathematical expressions,
images, and tables during HTML content generation.
"""

import re
import random
import string
from typing import List, Tuple, Dict, Optional


def generate_placeholder(prefix: str = 'IMG') -> str:
    """Generate a unique placeholder string."""
    chars = string.ascii_lowercase + string.digits
    return f"__{prefix}_{''.join(random.choice(chars) for _ in range(16))}__"


def extract_math_expressions(markdown: str) -> Tuple[List[Dict[str, str]], str]:
    """
    Extract mathematical expressions from markdown content.
    
    Args:
        markdown: The markdown content to process
        
    Returns:
        Tuple of (list of expressions with placeholders, markdown with expressions replaced)
    """
    expressions = []
    result = markdown
    
    # Extract inline math ($...$)
    inline_pattern = r'\$(.*?)\$'
    for match in re.finditer(inline_pattern, result, re.DOTALL):
        expr = match.group(1).strip()
        if expr:
            placeholder = generate_placeholder('MATH_INLINE')
            expressions.append({
                'placeholder': placeholder,
                'expression': expr,
                'type': 'inline'
            })
            result = result[:match.start()] + placeholder + result[match.end():]
    
    # Extract block math ($$...$$)
    block_pattern = r'\$\$(.*?)\$\$'
    for match in re.finditer(block_pattern, result, re.DOTALL):
        expr = match.group(1).strip()
        if expr:
            placeholder = generate_placeholder('MATH_BLOCK')
            expressions.append({
                'placeholder': placeholder,
                'expression': expr,
                'type': 'block'
            })
            result = result[:match.start()] + placeholder + result[match.end():]
    
    return expressions, result


def extract_images(markdown: str) -> Tuple[List[Dict[str, str]], str]:
    """
    Extract image references from markdown content.
    
    Args:
        markdown: The markdown content to process
        
    Returns:
        Tuple of (list of images with placeholders, markdown with images replaced)
    """
    images = []
    result = markdown
    
    # Match markdown images: ![alt text](path)
    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    for match in re.finditer(image_pattern, result):
        alt_text = match.group(1)
        img_path = match.group(2)
        placeholder = generate_placeholder('IMG')
        images.append({
            'placeholder': placeholder,
            'path': img_path,
            'alt': alt_text
        })
        result = result[:match.start()] + placeholder + result[match.end():]
    
    return images, result


def extract_tables(markdown: str) -> Tuple[List[Dict[str, str]], str]:
    """
    Extract markdown tables from content.
    
    Args:
        markdown: The markdown content to process
        
    Returns:
        Tuple of (list of tables with placeholders, markdown with tables replaced)
    """
    tables = []
    result = markdown
    
    # Match markdown tables (simplified pattern)
    table_pattern = r'(\|[^\n]+\|[^\n]*\n)+'
    for match in re.finditer(table_pattern, result):
        table_content = match.group(0)
        # Verify it's actually a table (contains | separator)
        if '|' in table_content:
            placeholder = generate_placeholder('TABLE')
            tables.append({
                'placeholder': placeholder,
                'content': table_content
            })
            result = result[:match.start()] + placeholder + result[match.end():]
    
    return tables, result


def restore_math_expressions(html: str, expressions: List[Dict[str, str]]) -> str:
    """
    Restore mathematical expressions into HTML content.
    
    Args:
        html: The HTML content with placeholders
        expressions: List of expressions extracted earlier
        
    Returns:
        HTML with expressions restored as LaTeX
    """
    result = html
    
    for expr in expressions:
        placeholder = expr['placeholder']
        expression = expr['expression']
        expr_type = expr['type']
        
        if expr_type == 'inline':
            # Inline math: \(...\)
            replacement = f'\\({expression}\\)'
        else:
            # Block math: \[...\]
            replacement = f'\\[{expression}\\]'
        
        result = result.replace(placeholder, replacement)
    
    return result


def restore_images(html: str, images: List[Dict[str, str]]) -> str:
    """
    Restore image references into HTML content.
    
    Args:
        html: The HTML content with placeholders
        images: List of images extracted earlier
        
    Returns:
        HTML with image <img> tags restored
    """
    result = html
    
    for img in images:
        placeholder = img['placeholder']
        path = img['path']
        alt = img['alt']
        
        # Construct image tag
        img_tag = f'<img src="{path}" alt="{alt}" class="content-image">'
        result = result.replace(placeholder, img_tag)
    
    return result


def restore_tables(html: str, tables: List[Dict[str, str]]) -> str:
    """
    Restore markdown tables into HTML content (converts to HTML tables).
    
    Args:
        html: The HTML content with placeholders
        tables: List of tables extracted earlier
        
    Returns:
        HTML with tables restored as HTML table elements
    """
    result = html
    
    for table in tables:
        placeholder = table['placeholder']
        markdown_table = table['content']
        
        # Convert markdown table to HTML table
        html_table = markdown_to_html_table(markdown_table)
        result = result.replace(placeholder, html_table)
    
    return result


def markdown_to_html_table(markdown_table: str) -> str:
    """
    Convert a markdown table to HTML table format.
    
    Args:
        markdown_table: The markdown table string
        
    Returns:
        HTML table string
    """
    lines = markdown_table.strip().split('\n')
    
    if len(lines) < 2:
        return '<div class="table-placeholder">' + markdown_table + '</div>'
    
    rows = [line for line in lines if line.strip()]
    
    # Check if second row is a separator (contains only |, -, :)
    if len(rows) > 1 and re.match(r'^[\|:\-\s]+$', rows[1]):
        # Remove separator row
        separator_row = rows.pop(1)
        is_header = True
    else:
        is_header = False
    
    html_parts = ['<table class="content-table">']
    
    for i, row in enumerate(rows):
        # Split by | and remove empty first/last elements
        cells = [cell.strip() for cell in row.split('|')]
        cells = [c for c in cells if c or (c == '' and 0 < cells.index(c) < len(cells) - 1)]
        
        if not cells:
            continue
        
        if is_header and i == 0:
            html_parts.append('<thead>')
            html_parts.append('<tr>')
            for cell in cells:
                html_parts.append(f'<th>{cell}</th>')
            html_parts.append('</tr>')
            html_parts.append('</thead>')
            html_parts.append('<tbody>')
        else:
            html_parts.append('<tr>')
            for cell in cells:
                html_parts.append(f'<td>{cell}</td>')
            html_parts.append('</tr>')
    
    if is_header:
        html_parts.append('</tbody>')
    
    html_parts.append('</table>')
    
    return ''.join(html_parts)


def clean_markdown_for_ai(markdown: str) -> str:
    """
    Clean markdown content before sending to AI.
    Removes problematic elements that might confuse the AI.
    
    Args:
        markdown: The markdown content to clean
        
    Returns:
        Cleaned markdown content
    """
    # Remove code blocks from other languages (keep inline)
    result = re.sub(r'```[a-zA-Z]+\n.*?```', '[CODE BLOCK REMOVED]', markdown, flags=re.DOTALL)
    
    # Remove HTML comments
    result = re.sub(r'<!--.*?-->', '', result, flags=re.DOTALL)
    
    # Remove excessive whitespace
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


def create_fallback_html(title: str, markdown: str, 
                        math_expressions: List[Dict[str, str]] = None,
                        images: List[Dict[str, str]] = None,
                        tables: List[Dict[str, str]] = None) -> str:
    """
    Create fallback HTML content when AI generation fails.
    
    Args:
        title: The content title
        markdown: The markdown content
        math_expressions: List of math expressions (if any)
        images: List of images (if any)
        tables: List of tables (if any)
        
    Returns:
        Basic HTML content
    """
    # Use python-markdown if available, otherwise basic conversion
    try:
        import markdown as md_lib
        html_content = md_lib.markdown(
            markdown, 
            extensions=['tables', 'fenced_code', 'extra']
        )
    except ImportError:
        # Very basic markdown conversion
        html_content = markdown.replace('\n', '<br>\n')
        # Convert headers
        html_content = re.sub(r'^### (.*)$', '<h3>\\1</h3>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.*)$', '<h2>\\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^# (.*)$', '<h1>\\1</h1>', html_content, flags=re.MULTILINE)
        # Convert bold
        html_content = re.sub(r'\*\*(.*?)\*\*', '<strong>\\1</strong>', html_content)
        html_content = re.sub(r'__(.*?)__', '<strong>\\1</strong>', html_content)
        # Convert italic
        html_content = re.sub(r'\*(.*?)\*', '<em>\\1</em>', html_content)
        html_content = re.sub(r'_(.*?)_', '<em>\\1</em>', html_content)
    
    # Restore math expressions if provided
    if math_expressions:
        html_content = restore_math_expressions(html_content, math_expressions)
    else:
        # Add MathJax script for any remaining LaTeX
        if not re.search(r'mathjax', html_content, re.IGNORECASE):
            html_content += '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>'
    
    # Wrap in HTML structure
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }}
            .content-table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            .content-table th, .content-table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            .content-table th {{
                background-color: #f5f5f5;
            }}
            .content-image {{
                max-width: 100%;
                height: auto;
                margin: 20px 0;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            code {{
                background-color: #f5f5f5;
                padding: 2px 5px;
                border-radius: 3px;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="content">
            {html_content}
        </div>
    </body>
    </html>
    """
    
    return full_html