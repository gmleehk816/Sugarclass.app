#!/usr/bin/env python3
"""
Enhanced Educational HTML Template

Creates beautiful, well-formatted educational content with:
- Clean, modern design
- Proper typography
- Enhanced learning components
- Responsive layout
"""

import re
import markdown


def create_educational_html(
    markdown_content: str,
    title: str = "Learning Content",
    chapter_number: int = 1,
    subtopic_number: int = 1,
    learning_objectives: list = None,
    key_terms: list = None,
    questions: list = None,
    takeaways: list = None
) -> str:
    """
    Create beautifully formatted educational HTML from markdown content.
    """
    
    # Convert markdown to HTML
    extensions = ['tables', 'fenced_code', 'codehilite', 'toc', 'attr_list', 'admonition', 'nl2br', 'sane_lists']
    html_body = markdown.markdown(markdown_content, extensions=extensions)
    
    # Process and enhance the HTML
    html_body = enhance_html_content(html_body)
    
    # Build the full HTML document
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                        serif: ['Merriweather', 'Georgia', 'serif']
                    }},
                    colors: {{
                        primary: {{
                            50: '#eff6ff',
                            100: '#dbeafe',
                            500: '#3b82f6',
                            600: '#2563eb',
                            700: '#1d4ed8',
                            800: '#1e40af',
                        }},
                        accent: {{
                            500: '#8b5cf6',
                            600: '#7c3aed',
                        }}
                    }}
                }}
            }}
        }}
    </script>
    <style>
        /* Base Typography */
        body {{
            font-family: 'Inter', system-ui, sans-serif;
            line-height: 1.7;
            color: #1f2937;
        }}
        
        /* Content Styles */
        .content-body {{
            font-family: 'Merriweather', Georgia, serif;
        }}
        
        .content-body h1 {{
            font-family: 'Inter', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #1e40af;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #dbeafe;
        }}
        
        .content-body h2 {{
            font-family: 'Inter', sans-serif;
            font-size: 1.5rem;
            font-weight: 600;
            color: #1d4ed8;
            margin-top: 2rem;
            margin-bottom: 0.75rem;
        }}
        
        .content-body h3 {{
            font-family: 'Inter', sans-serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: #374151;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .content-body p {{
            margin-bottom: 1.25rem;
            text-align: justify;
        }}
        
        .content-body ul, .content-body ol {{
            margin-left: 1.5rem;
            margin-bottom: 1.25rem;
        }}
        
        .content-body li {{
            margin-bottom: 0.5rem;
        }}
        
        .content-body li::marker {{
            color: #3b82f6;
        }}
        
        /* Tables */
        .content-body table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
        }}
        
        .content-body th {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 0.875rem 1rem;
            text-align: left;
            font-weight: 600;
        }}
        
        .content-body td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .content-body tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        
        .content-body tr:hover {{
            background-color: #eff6ff;
        }}
        
        /* Images */
        .content-body img {{
            max-width: 100%;
            height: auto;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin: 1.5rem auto;
            display: block;
        }}
        
        /* Code */
        .content-body code {{
            background-color: #f1f5f9;
            padding: 0.2rem 0.5rem;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            color: #7c3aed;
        }}
        
        .content-body pre {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #e2e8f0;
            padding: 1.25rem;
            border-radius: 0.75rem;
            overflow-x: auto;
            margin: 1.5rem 0;
        }}
        
        .content-body pre code {{
            background: transparent;
            padding: 0;
            color: inherit;
        }}
        
        /* Blockquotes */
        .content-body blockquote {{
            border-left: 4px solid #8b5cf6;
            background: linear-gradient(90deg, #f5f3ff 0%, transparent 100%);
            padding: 1rem 1.5rem;
            margin: 1.5rem 0;
            border-radius: 0 0.5rem 0.5rem 0;
            font-style: italic;
            color: #4b5563;
        }}
        
        /* Custom Components */
        .learning-card {{
            border-radius: 1rem;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }}
        
        .chapter-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 1rem;
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            border-radius: 2rem;
            font-weight: 600;
            font-size: 0.875rem;
        }}
        
        /* Figure Captions */
        .figure-caption {{
            text-align: center;
            font-style: italic;
            color: #6b7280;
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }}
        
        /* Key Definition */
        .key-definition {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 1rem 1.5rem;
            margin: 1.5rem 0;
            border-radius: 0 0.5rem 0.5rem 0;
        }}
        
        /* Important Note */
        .important-note {{
            background: #fce7f3;
            border-left: 4px solid #ec4899;
            padding: 1rem 1.5rem;
            margin: 1.5rem 0;
            border-radius: 0 0.5rem 0.5rem 0;
        }}
        
        /* Print Styles */
        @media print {{
            body {{ font-size: 11pt; }}
            .no-print {{ display: none; }}
            .content-body h1 {{ page-break-before: always; }}
        }}
    </style>
</head>
<body class="bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
    <!-- Header -->
    <header class="bg-white shadow-sm sticky top-0 z-50">
        <div class="max-w-5xl mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <div class="chapter-badge">
                        <span>📚 Chapter {chapter_number}.{subtopic_number}</span>
                    </div>
                    <h1 class="text-xl font-bold text-gray-800 hidden sm:block">{title}</h1>
                </div>
                <div class="flex items-center space-x-2 text-sm text-gray-500">
                    <span>🧪</span>
                    <span>Chemistry</span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-5xl mx-auto px-6 py-8">
        <!-- Learning Objectives Card -->
        {_render_learning_objectives(learning_objectives) if learning_objectives else ''}
        
        <!-- Content Area -->
        <article class="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div class="bg-gradient-to-r from-blue-600 to-blue-800 px-8 py-6">
                <h1 class="text-3xl font-bold text-white">{title}</h1>
                <p class="text-blue-100 mt-2">Cambridge IGCSE Chemistry</p>
            </div>
            
            <div class="p-8 content-body">
                {html_body}
            </div>
        </article>
        
        <!-- Key Terms Card -->
        {_render_key_terms(key_terms) if key_terms else ''}
        
        <!-- Review Questions -->
        {_render_questions(questions) if questions else ''}
        
        <!-- Key Takeaways -->
        {_render_takeaways(takeaways) if takeaways else ''}
    </main>

    <!-- Footer -->
    <footer class="bg-gray-800 text-white py-8 mt-12">
        <div class="max-w-5xl mx-auto px-6 text-center">
            <p class="text-gray-400 text-sm">
                📖 Educational Content | Cambridge IGCSE Chemistry
            </p>
        </div>
    </footer>
</body>
</html>'''


def _render_learning_objectives(objectives: list) -> str:
    if not objectives:
        return ''
    
    items = '\n'.join([f'<li class="flex items-start"><span class="text-green-500 mr-2 mt-1">✓</span><span>{obj}</span></li>' for obj in objectives])
    
    return f'''
        <div class="learning-card mb-8">
            <div class="bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-4">
                <h2 class="text-xl font-bold text-white flex items-center">
                    <span class="mr-2">🎯</span> Learning Objectives
                </h2>
            </div>
            <div class="bg-white p-6">
                <p class="text-gray-600 mb-4">By the end of this section, you will be able to:</p>
                <ul class="space-y-3">
                    {items}
                </ul>
            </div>
        </div>
    '''


def _render_key_terms(terms: list) -> str:
    if not terms:
        return ''
    
    items = []
    for term in terms:
        if isinstance(term, dict):
            t = term.get('term', '')
            d = term.get('definition', '')
        else:
            t = str(term)
            d = ''
        items.append(f'''
            <div class="bg-gray-50 rounded-lg p-4 border-l-4 border-purple-500">
                <dt class="font-semibold text-purple-700">{t}</dt>
                <dd class="text-gray-600 mt-1">{d}</dd>
            </div>
        ''')
    
    terms_html = '\n'.join(items)
    
    return f'''
        <div class="learning-card mt-8">
            <div class="bg-gradient-to-r from-purple-500 to-violet-600 px-6 py-4">
                <h2 class="text-xl font-bold text-white flex items-center">
                    <span class="mr-2">📖</span> Key Terms & Definitions
                </h2>
            </div>
            <div class="bg-white p-6">
                <dl class="space-y-4">
                    {terms_html}
                </dl>
            </div>
        </div>
    '''


def _render_questions(questions: list) -> str:
    if not questions:
        return ''
    
    items = '\n'.join([f'''
        <li class="bg-amber-50 rounded-lg p-4 border-l-4 border-amber-500">
            <span class="font-semibold text-amber-800">Q{i+1}:</span>
            <span class="text-gray-700 ml-2">{q}</span>
        </li>
    ''' for i, q in enumerate(questions)])
    
    return f'''
        <div class="learning-card mt-8">
            <div class="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-4">
                <h2 class="text-xl font-bold text-white flex items-center">
                    <span class="mr-2">❓</span> Review Questions
                </h2>
            </div>
            <div class="bg-white p-6">
                <p class="text-gray-600 mb-4">Test your understanding with these questions:</p>
                <ul class="space-y-4">
                    {items}
                </ul>
            </div>
        </div>
    '''


def _render_takeaways(takeaways: list) -> str:
    if not takeaways:
        return ''
    
    items = '\n'.join([f'<li class="flex items-start"><span class="text-blue-500 mr-2">💡</span><span>{t}</span></li>' for t in takeaways])
    
    return f'''
        <div class="learning-card mt-8">
            <div class="bg-gradient-to-r from-blue-500 to-cyan-500 px-6 py-4">
                <h2 class="text-xl font-bold text-white flex items-center">
                    <span class="mr-2">✨</span> Key Takeaways
                </h2>
            </div>
            <div class="bg-white p-6">
                <ul class="space-y-3">
                    {items}
                </ul>
            </div>
        </div>
    '''


def enhance_html_content(html: str) -> str:
    """
    Enhance HTML content with better formatting.
    """
    # Enhance figure captions
    html = re.sub(
        r'<p>(Figure \d+[^<]*)</p>',
        r'<p class="figure-caption">\1</p>',
        html
    )
    
    # Convert KEY INFO blocks to special styling
    html = re.sub(
        r'<p><strong>KEY INFO[^<]*</strong>([^<]+)</p>',
        r'<div class="key-definition"><strong>🔑 Key Information</strong><br>\1</div>',
        html,
        flags=re.IGNORECASE
    )
    
    # Convert IMPORTANT blocks
    html = re.sub(
        r'<p><strong>IMPORTANT[^<]*</strong>([^<]+)</p>',
        r'<div class="important-note"><strong>⚠️ Important</strong><br>\1</div>',
        html,
        flags=re.IGNORECASE
    )
    
    return html


if __name__ == "__main__":
    # Test
    sample_md = """
# States of Matter

## Introduction

Matter can exist in three states: solid, liquid, and gas.

## Key Concepts

- Solids have a fixed shape
- Liquids take the shape of their container
- Gases fill all available space
"""
    
    html = create_educational_html(
        markdown_content=sample_md,
        title="States of Matter",
        chapter_number=1,
        subtopic_number=1,
        learning_objectives=[
            "Understand the three states of matter",
            "Explain the properties of solids, liquids, and gases"
        ],
        key_terms=[
            {"term": "Solid", "definition": "A state of matter with fixed shape and volume"},
            {"term": "Liquid", "definition": "A state of matter with fixed volume but variable shape"}
        ],
        questions=[
            "What are the three states of matter?",
            "How does temperature affect state changes?"
        ],
        takeaways=[
            "Matter exists in three main states",
            "State changes depend on temperature and pressure"
        ]
    )
    
    print("HTML generated successfully!")
    print(f"Length: {len(html)} chars")
