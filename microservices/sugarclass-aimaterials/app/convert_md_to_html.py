"""Convert creative markdown to styled HTML"""

import markdown

# Read the creative rewrite
with open('chemistry_creative_rewrite.md', 'r', encoding='utf-8') as f:
    content = f.read()

print(f'Total content: {len(content):,} chars')

# Convert markdown to HTML
extensions = ['tables', 'fenced_code', 'toc', 'nl2br', 'sane_lists']
html_body = markdown.markdown(content, extensions=extensions)

# Wrap with Tailwind template
html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>States of Matter - Creative Rewrite</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; }
        .prose h1 { font-size: 2.5rem; font-weight: 700; color: #1e3a5f; margin-bottom: 1rem; }
        .prose h2 { font-size: 1.75rem; font-weight: 600; color: #2563eb; margin-top: 2.5rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }
        .prose h3 { font-size: 1.25rem; font-weight: 600; color: #4b5563; margin-top: 1.5rem; }
        .prose h4 { font-size: 1.1rem; font-weight: 600; color: #6b7280; margin-top: 1rem; }
        .prose p { margin-bottom: 1rem; line-height: 1.8; color: #374151; }
        .prose ul, .prose ol { margin-left: 1.5rem; margin-bottom: 1rem; }
        .prose li { margin-bottom: 0.5rem; line-height: 1.7; }
        .prose strong { color: #1f2937; }
        .prose table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .prose th { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 0.75rem; text-align: left; }
        .prose td { padding: 0.75rem; border: 1px solid #e5e7eb; }
        .prose tr:nth-child(even) { background-color: #f9fafb; }
        .prose blockquote { border-left: 4px solid #3b82f6; padding-left: 1rem; margin: 1rem 0; color: #4b5563; background: #eff6ff; padding: 1rem; border-radius: 0.5rem; }
        .prose hr { margin: 2rem 0; border-color: #e5e7eb; }
        .prose code { background: #f3f4f6; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-size: 0.9rem; }
    </style>
</head>
<body class="bg-gray-50">
    <div class="max-w-4xl mx-auto p-8 bg-white shadow-lg min-h-screen">
        <div class="prose max-w-none">
''' + html_body + '''
        </div>
    </div>
</body>
</html>'''

# Save
with open('sample_creative_chemistry.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'HTML saved: {len(html):,} chars')
