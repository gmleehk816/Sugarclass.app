#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import markdown
from typing import Optional
import re


def convert_markdown_to_html(markdown_text: str, add_toc: bool = True, theme: str = "default") -> str:
    if not markdown_text:
        return ""
    
    extensions = ['tables', 'fenced_code', 'codehilite', 'toc', 'attr_list', 'def_list', 'admonition', 'nl2br', 'sane_lists']
    extension_configs = {'codehilite': {'linenums': False, 'guess_lang': True}}
    
    html_content = markdown.markdown(markdown_text, extensions=extensions, extension_configs=extension_configs)
    
    if theme == "default":
        return wrap_default(html_content, add_toc)
    elif theme == "clean":
        return wrap_clean(html_content, add_toc)
    else:
        return wrap_modern(html_content, add_toc)


def wrap_default(html_content: str, add_toc: bool) -> str:
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Content</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .prose h2 {{ margin-top: 2rem; margin-bottom: 1rem; font-weight: 600; }}
        .prose h3 {{ margin-top: 1.5rem; margin-bottom: 0.75rem; font-weight: 600; }}
        .prose p {{ margin-bottom: 1rem; line-height: 1.7; }}
        .prose ul {{ margin-left: 1.5rem; margin-bottom: 1rem; }}
        .prose ol {{ margin-left: 1.5rem; margin-bottom: 1rem; }}
        .prose li {{ margin-bottom: 0.5rem; }}
        .prose table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        .prose th {{ background-color: #f3f4f6; padding: 0.75rem; text-align: left; font-weight: 600; }}
        .prose td {{ padding: 0.75rem; border: 1px solid #e5e7eb; }}
        .prose code {{ background-color: #f3f4f6; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-size: 0.875rem; }}
        .prose pre {{ background-color: #1f2937; color: #f9fafb; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; }}
        .prose pre code {{ background-color: transparent; padding: 0; color: inherit; }}
        .prose blockquote {{ border-left: 4px solid #6366f1; padding-left: 1rem; margin: 1rem 0; color: #4b5563; }}
        .toc {{ background-color: #f9fafb; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem; }}
    </style>
</head>
<body class="bg-gray-50">
    <div class="max-w-4xl mx-auto p-6 bg-white shadow-lg min-h-screen">
        <div class="prose">
            {html_content}
        </div>
    </div>
</body>
</html>'''


def wrap_clean(html_content: str, add_toc: bool) -> str:
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Content</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
    <article class="max-w-3xl mx-auto px-6 py-8 font-serif text-gray-800 leading-relaxed">
        {html_content}
    </article>
</body>
</html>'''


def wrap_modern(html_content: str, add_toc: bool) -> str:
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Content</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .gradient-bg {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .card-shadow {{ box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
        
        /* Professional Typography */
        .prose h1 {{ 
            font-family: 'Merriweather', serif;
            font-size: 2.5rem; 
            font-weight: 700; 
            color: #1a202c;
            margin-top: 0;
            margin-bottom: 1.5rem;
            line-height: 1.2;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.75rem;
        }}
        .prose h2 {{ 
            font-family: 'Merriweather', serif;
            font-size: 1.75rem; 
            font-weight: 600; 
            color: #2d3748;
            margin-top: 2.5rem; 
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
            padding-left: 1rem;
        }}
        .prose h3 {{ 
            font-size: 1.35rem; 
            font-weight: 600; 
            color: #4a5568;
            margin-top: 2rem; 
            margin-bottom: 0.75rem;
        }}
        .prose h4 {{ 
            font-size: 1.15rem; 
            font-weight: 600; 
            color: #718096;
            margin-top: 1.5rem; 
            margin-bottom: 0.5rem;
        }}
        .prose p {{ 
            font-size: 1.05rem;
            line-height: 1.8; 
            margin-bottom: 1.25rem;
            color: #4a5568;
        }}
        .prose ul, .prose ol {{ 
            margin-left: 1.5rem; 
            margin-bottom: 1.25rem;
        }}
        .prose li {{ 
            margin-bottom: 0.5rem;
            line-height: 1.7;
        }}
        .prose strong {{ 
            color: #2d3748;
            font-weight: 600;
        }}
        .prose em {{
            color: #553c9a;
        }}
        .prose code {{ 
            background-color: #edf2f7; 
            padding: 0.2rem 0.5rem; 
            border-radius: 0.375rem; 
            font-size: 0.9rem;
            color: #553c9a;
            font-family: 'Fira Code', monospace;
        }}
        .prose pre {{ 
            background-color: #1a202c; 
            color: #e2e8f0; 
            padding: 1.25rem; 
            border-radius: 0.75rem; 
            overflow-x: auto;
            margin: 1.5rem 0;
        }}
        .prose pre code {{ 
            background-color: transparent; 
            padding: 0; 
            color: inherit; 
        }}
        .prose blockquote {{ 
            border-left: 4px solid #667eea; 
            background: linear-gradient(90deg, #f7fafc, transparent);
            padding: 1rem 1.5rem; 
            margin: 1.5rem 0; 
            color: #4a5568;
            font-style: italic;
            border-radius: 0 0.5rem 0.5rem 0;
        }}
        .prose blockquote strong {{
            color: #553c9a;
            font-style: normal;
        }}
        .prose table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 1.5rem 0;
            border-radius: 0.5rem;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        .prose th {{ 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 1rem; 
            text-align: left; 
            font-weight: 600;
        }}
        .prose td {{ 
            padding: 0.875rem 1rem; 
            border-bottom: 1px solid #e2e8f0;
        }}
        .prose tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        .prose img {{
            border-radius: 0.75rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin: 1.5rem auto;
        }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-5xl mx-auto px-4">
        <div class="bg-white rounded-2xl card-shadow overflow-hidden">
            <div class="gradient-bg px-8 py-6">
                <h1 class="text-white text-3xl font-bold" style="border:none; margin:0; padding:0;">📚 Learning Content</h1>
            </div>
            <div class="p-8 lg:p-12 prose prose-lg max-w-none">
                {html_content}
            </div>
        </div>
    </div>
</body>
</html>'''


def add_enhancements_to_html(html_content: str, learning_objectives: Optional[list] = None, key_terms: Optional[list] = None, questions: Optional[list] = None, takeaways: Optional[list] = None) -> str:
    enhancements = []
    
    if learning_objectives:
        obj_html = '<div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded">'
        obj_html += '<h3 class="font-bold text-blue-800 mb-2">Learning Objectives</h3>'
        obj_html += '<ul class="space-y-1">'
        for obj in learning_objectives:
            obj_html += f'<li class="text-blue-700">- {obj}</li>'
        obj_html += '</ul></div>'
        enhancements.append(obj_html)
    
    if key_terms:
        terms_html = '<div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 mb-6 rounded">'
        terms_html += '<h3 class="font-bold text-yellow-800 mb-2">Key Terms</h3>'
        terms_html += '<ul class="space-y-2">'
        for term in key_terms:
            if isinstance(term, dict):
                term_text = term.get('term', '')
                definition = term.get('definition', '')
            else:
                term_text = str(term)
                definition = ''
            
            if definition:
                terms_html += f'<li><strong class="text-yellow-800">{term_text}:</strong> <span class="text-yellow-700">{definition}</span></li>'
            else:
                terms_html += f'<li class="text-yellow-700">- {term_text}</li>'
        terms_html += '</ul></div>'
        enhancements.append(terms_html)
    
    if questions:
        questions_html = '<div class="bg-purple-50 border-l-4 border-purple-500 p-4 mb-6 rounded">'
        questions_html += '<h3 class="font-bold text-purple-800 mb-2">Think About It</h3>'
        questions_html += '<ul class="space-y-2">'
        for i, question in enumerate(questions, 1):
            questions_html += f'<li class="text-purple-700">{i}. {question}</li>'
        questions_html += '</ul></div>'
        enhancements.append(questions_html)
    
    if takeaways:
        takeaways_html = '<div class="bg-green-50 border-l-4 border-green-500 p-4 mb-6 rounded">'
        takeaways_html += '<h3 class="font-bold text-green-800 mb-2">Key Takeaways</h3>'
        takeaways_html += '<ul class="space-y-1">'
        for takeaway in takeaways:
            takeaways_html += f'<li class="text-green-700">- {takeaway}</li>'
        takeaways_html += '</ul></div>'
        enhancements.append(takeaways_html)
    
    if enhancements:
        enhancements_block = ''.join(enhancements)
        html_content = html_content.replace(
            '<div class="max-w-4xl mx-auto p-6 bg-white shadow-lg min-h-screen">',
            f'<div class="max-w-4xl mx-auto p-6 bg-white shadow-lg min-h-screen">{enhancements_block}'
        )
    
    return html_content


def get_content_statistics(markdown_text: str) -> dict:
    stats = {
        'char_count': len(markdown_text),
        'word_count': len(markdown_text.split()),
        'line_count': len(markdown_text.split('\n')),
        'heading_count': len(re.findall(r'^#{1,6}\s', markdown_text, re.MULTILINE)),
        'table_count': len(re.findall(r'\|.*\|', markdown_text)),
        'code_block_count': len(re.findall(r'```[\s\S]*?```', markdown_text)),
        'list_count': len(re.findall(r'^[\-\*]\s', markdown_text, re.MULTILINE)) + len(re.findall(r'^\d+\.\s', markdown_text, re.MULTILINE))
    }
    return stats


if __name__ == "__main__":
    sample_md = "# Test\n\nThis is a test."
    html = convert_markdown_to_html(sample_md, theme="default")
    print(f"Input: {len(sample_md)} chars")
    print(f"Output: {len(html)} chars")
    print("OK")