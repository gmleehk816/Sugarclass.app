"""
Math Content Rewriter - Final Version
======================================
Uses AI to transform math content like other subjects, while preserving all math expressions.
"""

import os
import re
import sqlite3
import json
import requests
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Paths
APP_DIR = Path(__file__).parent.parent
PROJECT_ROOT = APP_DIR.parent
DB_PATH = APP_DIR / "rag_content.db"
GENERATED_IMAGES_DIR = APP_DIR / "generated_images"
GENERATED_IMAGES_DIR.mkdir(exist_ok=True)

# API Configuration
API_KEY = os.getenv("NANO_BANANA_API_KEY", "")
API_URL = os.getenv("NANO_BANANA_API_URL", "https://newapi.aisonnet.org/v1/chat/completions")
MODEL = os.getenv("NANO_BANANA_MODEL", "nano-banana")

PROCESSOR_VERSION = "math-final-4.0"


class MathContentRewriterFinal:
    """Final math processor - AI-enhanced like other subjects"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
    
    def protect_math_expressions(self, text: str) -> Tuple[str, Dict]:
        """Protect all LaTeX math expressions"""
        math_map = {}
        counter = 0
        
        # Protect display math ($$...$$)
        def replace_display(match):
            nonlocal counter
            counter += 1
            key = f"__MATH_DISPLAY_{counter}__"
            math_map[key] = ('display', match.group(1).strip())
            return key
        
        text = re.sub(r'\$\$(.*?)\$\$', replace_display, text, flags=re.DOTALL)
        
        # Protect inline math ($...$)
        def replace_inline(match):
            nonlocal counter
            counter += 1
            key = f"__MATH_INLINE_{counter}__"
            math_map[key] = ('inline', match.group(1).strip())
            return key
        
        text = re.sub(r'\$([^$\n]+?)\$', replace_inline, text)
        
        return text, math_map
    
    def restore_math_expressions(self, html: str, math_map: Dict) -> str:
        """Restore math expressions with proper MathJax formatting"""
        for key, (math_type, math_content) in math_map.items():
            # Clean the math expression
            cleaned = self._clean_math_expression(math_content)
            
            if math_type == 'display':
                replacement = f'<div class="math-display">\\[{cleaned}\\]</div>'
            else:
                replacement = f'<span class="math-inline">\\({cleaned}\\)</span>'
            
            html = html.replace(key, replacement)
        
        return html
    
    def _clean_math_expression(self, math: str) -> str:
        """Clean and format math expression"""
        # Fix spacing in arrays for better readability
        math = re.sub(r'\\begin\{array\}\{l\}(.*?)\\end\{array\}', 
                     lambda m: self._format_array(m.group(1)), math, flags=re.DOTALL)
        
        # Fix spacing issues
        math = re.sub(r'\s+', ' ', math)  # Multiple spaces to single
        math = re.sub(r'\s*([+\-=])\s*', r' \1 ', math)  # Space around operators
        
        return math.strip()
    
    def _format_array(self, content: str) -> str:
        """Format array content"""
        lines = [line.strip() for line in content.split('\\\\') if line.strip()]
        formatted = ' \\\\ '.join(lines)
        return f'\\begin{{array}}{{l}} {formatted} \\end{{array}}'
    
    def get_content_by_subtopic(self, subtopic_id: str) -> Optional[Dict]:
        """Get content by subtopic ID"""
        query = """
            SELECT cr.id, cr.subtopic_id, cr.title, cr.char_count, cr.markdown_content,
                   s.name as subtopic_name, t.name as topic_name, t.type as subject_type
            FROM content_raw cr
            LEFT JOIN subtopics s ON cr.subtopic_id = s.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE cr.subtopic_id LIKE ?
        """
        row = self.conn.execute(query, (f"%{subtopic_id}%",)).fetchone()
        return dict(row) if row else None
    
    def rewrite_math_content(self, content: Dict) -> Dict:
        """Rewrite math content with AI - similar to other subjects"""
        markdown = self._structure_exercises(content['markdown_content'])
        title = content.get('title', 'Unknown')
        subject_type = content.get('subject_type', 'Mathematics')
        
        print(f"   📐 Processing: {title}")
        print(f"      Full content: {len(markdown)} chars")
        
        # Protect math expressions FIRST
        protected_markdown, math_map = self.protect_math_expressions(markdown)
        print(f"      Protected {len(math_map)} math expressions")
        
        # Use FULL content (not truncated like other subjects)
        system_prompt = """You are an expert educational content designer for IGCSE Mathematics students (ages 14-16).
Transform raw textbook markdown into engaging, visually-structured HTML content while PRESERVING ALL mathematical expressions.

CRITICAL REQUIREMENTS:
1. **PRESERVE ALL MATH PLACEHOLDERS**: Keep __MATH_INLINE_X__ and __MATH_DISPLAY_X__ EXACTLY as shown - DO NOT MODIFY THEM
2. **PRESERVE ALL CONTENT**: Include every word, example, exercise, and problem from the original
3. **PRESERVE STRUCTURE**: Keep exercise numbering, letter labels (a, b, c), and problem structure
4. **PRESERVE IMAGES**: Keep all ![](images/...) references exactly

Design Principles (same as other subjects):
1. Visual Learning: Clear sections, proper spacing
2. Chunked Information: Break into digestible sections but keep ALL content
3. Clear Hierarchy: Use proper headings (h1, h2, h3)
4. Key Terms: Highlight definitions with colored boxes
5. Examples: Style examples with distinct containers
6. Exercises: Format exercises clearly with proper structure
7. Text Alignment: All text should be left-aligned (text-left), except math displays which are centered
8. Line Height: Use proper line-height (1.7) for readability
9. Spacing: Consistent margins and padding throughout

Output Format:
- Return clean HTML (no markdown, no code blocks)
- Use Tailwind CSS classes like: text-2xl, font-bold, mt-6, mb-4, my-2, text-left, etc.
- Use semantic HTML5 elements
- Create distinct sections with proper spacing
- Style with Tailwind-like utility classes
- Use colors: blue for headings, green for key terms, gray for examples
- Ensure all paragraphs and text are left-aligned (text-left class)
- Use proper line-height for readability

MATH HANDLING:
- Replace __MATH_INLINE_X__ with: <span class="math-inline">__MATH_INLINE_X__</span>
- Replace __MATH_DISPLAY_X__ with: <div class="math-display">__MATH_DISPLAY_X__</div>
- Keep ALL placeholders - they will be replaced with actual LaTeX later

EXERCISE FORMATTING:
- Format exercises as: <div class="exercise-item"><span class="exercise-label">a</span> <span class="math-inline">__MATH_INLINE_X__</span></div>
- Keep exercise structure: numbered problems, lettered sub-items
- Preserve all exercise content"""

        user_prompt = f"""Transform this IGCSE Mathematics content about "{title}" into beautiful HTML using Tailwind CSS classes.

ORIGINAL CONTENT (FULL TEXT - PRESERVE EVERYTHING):
{protected_markdown}

Requirements:
1. **PRESERVE ALL CONTENT**: Include every paragraph, example, exercise, problem, and solution
2. **PRESERVE ALL MATH PLACEHOLDERS**: Keep __MATH_INLINE_X__ and __MATH_DISPLAY_X__ exactly as shown
3. **PRESERVE ALL IMAGES**: Keep ![](images/...) references
4. Use Tailwind CSS classes like other subjects:
   - Headings: text-2xl font-bold mt-6 mb-4 text-left
   - Paragraphs: my-2 text-left (left-align all text)
   - Sections: proper spacing with mt-4, mb-4, text-left
   - Line height: Use leading-relaxed or line-height: 1.7 for readability
5. Format exercises clearly:
   - Exercise headings: text-xl font-semibold mt-4 mb-2 text-left
   - Exercise items: flex layout with labels, text-left alignment
   - Keep all exercise letters and numbers
   - Ensure exercise items are properly aligned
6. Style examples and key terms with colored boxes
7. Make it visually appealing with proper spacing and typography
8. Keep ALL original text - don't summarize or skip anything
9. TEXT ALIGNMENT: All text content must be left-aligned (text-left class). Only math displays should be centered.
10. Images: Ensure images are properly centered and responsive

Return ONLY the HTML content, no explanations or code blocks."""

        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.5,  # Balanced for structure and creativity
                    "max_tokens": 20000  # Large token limit for full content
                },
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                html_content = result['choices'][0]['message']['content']
                
                # Clean up HTML
                html_content = self._clean_html(html_content)
                html_content = self._strip_speaker_icons(html_content)
                html_content = self._strip_math_delimiters(html_content)
                
                # Fix image paths
                html_content = self._fix_image_paths(html_content)
                
                # Restore math expressions with MathJax
                html_content = self.restore_math_expressions(html_content, math_map)
                
                # Fix double-wrapped spans and clean up
                html_content = self._fix_math_wrapping(html_content)
                
                # Normalize exercise layout for clear numbering/labels
                html_content = self._format_exercises_html(html_content)
                
                # Ensure proper text alignment
                html_content = self._fix_text_alignment(html_content)
                
                # Add MathJax script
                html_content = self._add_mathjax(html_content)
                
                # If images got lost or corrupted, fallback to deterministic pipeline
                if "<img" not in html_content:
                    print("    ⚠️ AI output missing images - using fallback renderer")
                    return self._fallback_processing(markdown, title, math_map)
                
                # Extract summary and key terms
                summary = self._extract_summary(markdown, title)
                key_terms = self._extract_math_terms(markdown)
                
                return {
                    "html_content": html_content,
                    "summary": summary,
                    "key_terms": key_terms
                }
            else:
                print(f"    ⚠️ API error: {response.status_code}")
                print(f"    Response: {response.text[:300]}")
                
        except Exception as e:
            print(f"    ⚠️ Rewrite error: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback: basic conversion
        return self._fallback_processing(markdown, title, math_map)
    
    def _fix_math_wrapping(self, html: str) -> str:
        """Fix double-wrapped math spans and ensure proper formatting"""
        # Remove double-wrapped spans
        html = re.sub(r'<span class="math-inline"><span class="math-inline">(.*?)</span></span>', 
                     r'<span class="math-inline">\1</span>', html)
        html = re.sub(r'<div class="math-display"><div class="math-display">(.*?)</div></div>', 
                     r'<div class="math-display">\1</div>', html)
        
        # Ensure all math expressions are properly wrapped
        # Find any raw \(...\) that aren't wrapped
        html = re.sub(r'(?<!<span class="math-inline">)\\\(([^)]+)\\\)(?!</span>)', 
                     r'<span class="math-inline">\\(\1\\)</span>', html)
        
        # Find any raw \[...\] that aren't wrapped
        html = re.sub(r'(?<!<div class="math-display">)\\\[([^\]]+)\\\](?!</div>)', 
                     r'<div class="math-display">\\[\1\\]</div>', html, flags=re.DOTALL)
        
        return html
    
    def _fix_text_alignment(self, html: str) -> str:
        """Ensure all text elements have proper left alignment"""
        # Add text-left to paragraphs without alignment
        html = re.sub(r'<p\s+([^>]*?)(?<!text-left)(?<!text-center)(?<!text-right)([^>]*?)>', 
                     lambda m: f'<p {m.group(1)}{m.group(2)} style="text-align: left; line-height: 1.7;">' if 'style=' not in m.group(0) else m.group(0), html)
        
        # Add text-left to headings without alignment (except math displays)
        html = re.sub(r'<h([1-6])\s+([^>]*?)(?<!text-left)(?<!text-center)(?<!text-right)([^>]*?)>', 
                     lambda m: f'<h{m.group(1)} {m.group(2)}{m.group(3)} style="text-align: left;">' if 'style=' not in m.group(0) and 'math-display' not in m.group(0) else m.group(0), html)
        
        # Add text-left to lists
        html = re.sub(r'<ul\s+([^>]*?)(?<!text-left)([^>]*?)>', 
                     lambda m: f'<ul {m.group(1)}{m.group(2)} style="text-align: left;">' if 'style=' not in m.group(0) else m.group(0), html)
        html = re.sub(r'<ol\s+([^>]*?)(?<!text-left)([^>]*?)>', 
                     lambda m: f'<ol {m.group(1)}{m.group(2)} style="text-align: left;">' if 'style=' not in m.group(0) else m.group(0), html)
        
        # Add text-left to divs (except math-display which should be centered)
        html = re.sub(r'<div\s+([^>]*?)(?<!text-left)(?<!text-center)(?<!text-right)([^>]*?)(?<!math-display)([^>]*?)>', 
                     lambda m: f'<div {m.group(1)}{m.group(2)}{m.group(3)} style="text-align: left;">' if 'style=' not in m.group(0) and 'math-display' not in m.group(0) else m.group(0), html)
        
        return html
    
    def _structure_exercises(self, markdown: str) -> str:
        """Normalize exercise lines so labels and expressions stay together"""
        lines = [ln.rstrip() for ln in markdown.split('\n')]
        normalized = []
        i = 0
        label_re = re.compile(r'^[a-z]$|^[a-z]\\b', re.IGNORECASE)
        number_re = re.compile(r'^\\d+\\b')
        
        while i < len(lines):
            line = lines[i].strip()
            # Combine label-only line with next expression line
            if (label_re.match(line) or number_re.match(line)) and (i + 1 < len(lines)):
                next_line = lines[i + 1].strip()
                # If next line is not another label/number heading, merge
                if next_line and not label_re.match(next_line) and not number_re.match(next_line):
                    combined = f"{line} {next_line}".strip()
                    normalized.append(combined)
                    i += 2
                    continue
            normalized.append(line)
            i += 1
        
        return "\n".join(normalized)
    
    def _format_exercises_html(self, html: str) -> str:
        """Turn leading label lines (a, b, c, 1, 2, 3) into aligned exercise items"""
        # Convert paragraphs starting with label into exercise items
        def make_item(label: str, body: str) -> str:
            return (
                f'<div class="exercise-item">'
                f'<span class="exercise-label">{label.strip()}</span>'
                f'<span class="exercise-body">{body.strip()}</span>'
                f'</div>'
            )
        
        para_pattern = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL)
        
        def convert_paragraph(match):
            inner = match.group(1).strip()
            m = re.match(r'([a-zA-Z0-9]+)\s+(.*)', inner, re.DOTALL)
            if m:
                label = m.group(1)
                body = m.group(2)
                # Only treat as exercise label if it's a single letter or a pure number (e.g., a, b, c, 1, 2)
                if re.fullmatch(r'[a-zA-Z]', label) or re.fullmatch(r'\d+', label):
                    return make_item(label, body)
            return match.group(0)
        
        return para_pattern.sub(convert_paragraph, html)
    
    def _fix_image_paths(self, html: str) -> str:
        """Fix image paths to use /images/ route with proper styling"""
        def fix_img(match):
            full_tag = match.group(0)
            path = match.group(1)
            
            # Extract filename
            if path.startswith('/images/'):
                filename = path.replace('/images/', '')
            elif path.startswith('images/'):
                filename = path.replace('images/', '')
            else:
                filename = path
            
            # Ensure proper image tag with styling
            if 'class=' in full_tag:
                # Update existing class
                return re.sub(r'class=["\'][^"\']*["\']', 
                            r'class="my-6 mx-auto block max-w-full h-auto rounded-lg shadow-md"', 
                            full_tag.replace(path, f'/images/{filename}'))
            else:
                # Add class attribute
                return full_tag.replace(path, f'/images/{filename}').replace('<img', '<img class="my-6 mx-auto block max-w-full h-auto rounded-lg shadow-md"')
        
        # Fix img tags
        html = re.sub(r'<img\s+([^>]*?)src=["\']([^"\']+)["\']([^>]*?)>', fix_img, html)
        
        # Fix markdown image syntax
        def fix_markdown_img(m):
            alt = m.group(1)
            path = m.group(2)
            filename = path.replace('images/', '') if 'images/' in path else path
            return f'<img src="/images/{filename}" alt="{alt}" class="my-6 mx-auto block max-w-full h-auto rounded-lg shadow-md">'
        
        html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_markdown_img, html)
        return html
    
    def _clean_html(self, html: str) -> str:
        """Clean up HTML response"""
        if html.startswith("```html"):
            html = html[7:]
        if html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        return html.strip()
    
    def _add_mathjax(self, html: str) -> str:
        """Add MathJax script for rendering - ensure it actually renders"""
        mathjax = """
<script>
  // Configure MathJax BEFORE loading
  window.MathJax = {
    tex: {
      inlineMath: [['\\(', '\\)']],
      displayMath: [['\\[', '\\]']],
      processEscapes: true,
      processEnvironments: true
    },
    options: {
      skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
      ignoreHtmlClass: 'tex2jax_ignore',
      processHtmlClass: 'tex2jax_process'
    },
    startup: {
      ready: function() {
        MathJax.startup.defaultReady();
        // Process immediately
        if (MathJax.typesetPromise) {
          MathJax.typesetPromise().then(function() {
            console.log('MathJax rendered successfully');
          }).catch(function(err) {
            console.error('MathJax rendering error:', err);
          });
        }
      }
    }
  };
</script>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<script>
  // Force rendering after MathJax loads
  (function() {
    var attempts = 0;
    function renderMath() {
      attempts++;
      if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise().then(function() {
          console.log('MathJax typeset complete');
        }).catch(function(err) {
          console.error('MathJax error:', err);
          if (attempts < 10) {
            setTimeout(renderMath, 500);
          }
        });
      } else if (attempts < 20) {
        setTimeout(renderMath, 200);
      }
    }
    
    // Try immediately
    renderMath();
    
    // Also try on DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', renderMath);
    }
    
    // And after a delay
    setTimeout(renderMath, 2000);
  })();
</script>
<style>
/* Math Display */
.math-display { 
  margin: 1.5rem auto; 
  text-align: center; 
  overflow-x: auto; 
  padding: 1rem; 
  background: #f8fafc; 
  border-radius: 8px;
  display: block;
  max-width: 100%;
}
.math-inline { 
  display: inline; 
  padding: 0 3px; 
  vertical-align: baseline;
}
.MathJax { 
  font-size: 1.1em !important; 
}

/* Text Alignment and Spacing */
.prose, .prose p {
  text-align: left;
  line-height: 1.7;
  margin-bottom: 1rem;
}
.prose h1, .prose h2, .prose h3 {
  text-align: left;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}
.prose ul, .prose ol {
  text-align: left;
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}
.prose li {
  margin-bottom: 0.5rem;
  line-height: 1.7;
}

/* Exercise formatting */
.prose .exercise-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  text-align: left;
}
.prose .exercise-label {
  font-weight: 600;
  margin-right: 0.5rem;
  min-width: 1.5rem;
  text-align: left;
}

/* Images */
.prose img {
  display: block;
  margin: 1.5rem auto;
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Hide LaTeX code while MathJax processes */
.math-inline:not(:has(.MathJax)),
.math-display:not(:has(.MathJax)) {
  opacity: 0;
  transition: opacity 0.3s;
}
.math-inline .MathJax,
.math-display .MathJax {
  opacity: 1;
}
</style>
"""
        return html + mathjax

    def _strip_speaker_icons(self, html: str) -> str:
        """Remove any stray speaker/audio icons from AI output"""
        return re.sub(r'[🔊🔉🔈🔇]', '', html)

    def _strip_math_delimiters(self, html: str) -> str:
        """Remove LaTeX delimiters and dollars so math renders as plain text"""
        html = re.sub(r'<span class="math-inline">\\\((.*?)\\\)</span>', 
                      lambda m: f'<span class="math-inline math-plain">{m.group(1)}</span>', 
                      html, flags=re.DOTALL)
        html = re.sub(r'<div class="math-display">\\\[(.*?)\\\]</div>', 
                      lambda m: f'<div class="math-display math-plain">{m.group(1)}</div>', 
                      html, flags=re.DOTALL)
        html = re.sub(r'\$\$(.*?)\$\$', r'\1', html, flags=re.DOTALL)
        html = re.sub(r'\$([^\$]+)\$', r'\1', html)
        replacements = {
            r'\\times': 'x',
            r'\\div': '/',
            r'\\cdot': '·',
            r'\\pm': '±',
            r'\\mp': '∓',
            r'\\leq': '≤',
            r'\\geq': '≥',
            r'\\neq': '≠'
        }
        for k, v in replacements.items():
            html = html.replace(k, v)
        html = html.replace('\\', '')
        return html
    
    def _extract_summary(self, markdown: str, title: str) -> str:
        """Extract summary"""
        lines = markdown.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('!') and not line.startswith('$'):
                clean = re.sub(r'\$[^$]+\$', '', line)
                clean = re.sub(r'\$\$.*?\$\$', '', clean, flags=re.DOTALL)
                if clean and len(clean) > 20:
                    return clean[:200] + "..." if len(clean) > 200 else clean
        return f"Mathematics: {title}"
    
    def _extract_math_terms(self, markdown: str) -> str:
        """Extract mathematical terms"""
        terms = set()
        headings = re.findall(r'^#+\s+(.+)$', markdown, re.MULTILINE)
        for heading in headings[:5]:
            if len(heading) < 50:
                terms.add(heading.strip())
        return ", ".join(list(terms)[:10])
    
    def _fallback_processing(self, markdown: str, title: str, math_map: Dict) -> Dict:
        """Fallback: basic conversion with Tailwind classes"""
        protected, _ = self.protect_math_expressions(markdown)
        
        # Convert to HTML with Tailwind classes
        html = protected
        html = re.sub(r'^# (.+)$', r'<h1 class="text-2xl font-bold mt-6 mb-4" style="text-align: left;">\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2 class="text-xl font-semibold mt-4 mb-2" style="text-align: left;">\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3 class="text-lg font-semibold mt-3 mb-2" style="text-align: left;">\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong class="font-semibold">\1</strong>', html)
        html = self._fix_image_paths(html)
        
        # Paragraphs
        lines = html.split('\n')
        result = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('<'):
                result.append(line)
            else:
                result.append(f'<p class="my-2" style="text-align: left; line-height: 1.7;">{line}</p>')
        html = '\n'.join(result)
        
        # Restore math
        html = self.restore_math_expressions(html, math_map)
        html = self._strip_speaker_icons(html)
        html = self._strip_math_delimiters(html)
        
        # Normalize exercise layout for clear numbering/labels
        html = self._format_exercises_html(html)
        
        # Ensure proper text alignment
        html = self._fix_text_alignment(html)
        
        html = self._add_mathjax(html)
        
        return {
            "html_content": html,
            "summary": f"Mathematics: {title}",
            "key_terms": ""
        }
    
    def save_processed(self, raw_id: int, subtopic_id: str, result: Dict) -> int:
        """Save processed content"""
        self.conn.execute("DELETE FROM content_processed WHERE subtopic_id = ?", (subtopic_id,))
        cursor = self.conn.execute("""
            INSERT INTO content_processed 
            (raw_id, subtopic_id, html_content, summary, key_terms, processor_version)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (raw_id, subtopic_id, result["html_content"], result["summary"], 
              result["key_terms"], PROCESSOR_VERSION))
        self.conn.commit()
        return cursor.lastrowid
    
    def process(self, content: Dict) -> Dict:
        """Full pipeline"""
        subtopic_id = content['subtopic_id']
        title = content.get('title', 'Unknown')
        
        print(f"\n📐 Processing: {subtopic_id}")
        print(f"   Title: {title}")
        
        result = self.rewrite_math_content(content)
        processed_id = self.save_processed(content['id'], subtopic_id, result)
        
        print(f"   ✅ Processed: {len(result['html_content'])} chars HTML")
        
        return {
            "raw_id": content['id'],
            "processed_id": processed_id,
            "subtopic_id": subtopic_id,
            "html_length": len(result["html_content"]),
            "summary": result["summary"][:100]
        }
    
    def close(self):
        self.conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subtopic", type=str, help="Process by subtopic ID")
    args = parser.parse_args()
    
    rewriter = MathContentRewriterFinal()
    try:
        if args.subtopic:
            content = rewriter.get_content_by_subtopic(args.subtopic)
            if content:
                result = rewriter.process(content)
                print(f"\n✅ Done: {result}")
            else:
                print("❌ Content not found")
        else:
            parser.print_help()
    finally:
        rewriter.close()



======================================
Uses AI to transform math content like other subjects, while preserving all math expressions.
"""

import os
import re
import sqlite3
import json
import requests
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Paths
APP_DIR = Path(__file__).parent.parent
PROJECT_ROOT = APP_DIR.parent
DB_PATH = APP_DIR / "rag_content.db"
GENERATED_IMAGES_DIR = APP_DIR / "generated_images"
GENERATED_IMAGES_DIR.mkdir(exist_ok=True)

# API Configuration
API_KEY = os.getenv("NANO_BANANA_API_KEY", "sk-G1dul1YrH5Z7aWubh8rgiv7dodjM3DcpvOuPw6aKNomKt95M")
API_URL = os.getenv("NANO_BANANA_API_URL", "https://newapi.aisonnet.org/v1/chat/completions")
MODEL = os.getenv("NANO_BANANA_MODEL", "nano-banana")

PROCESSOR_VERSION = "math-final-4.0"


class MathContentRewriterFinal:
    """Final math processor - AI-enhanced like other subjects"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
    
    def protect_math_expressions(self, text: str) -> Tuple[str, Dict]:
        """Protect all LaTeX math expressions"""
        math_map = {}
        counter = 0
        
        # Protect display math ($$...$$)
        def replace_display(match):
            nonlocal counter
            counter += 1
            key = f"__MATH_DISPLAY_{counter}__"
            math_map[key] = ('display', match.group(1).strip())
            return key
        
        text = re.sub(r'\$\$(.*?)\$\$', replace_display, text, flags=re.DOTALL)
        
        # Protect inline math ($...$)
        def replace_inline(match):
            nonlocal counter
            counter += 1
            key = f"__MATH_INLINE_{counter}__"
            math_map[key] = ('inline', match.group(1).strip())
            return key
        
        text = re.sub(r'\$([^$\n]+?)\$', replace_inline, text)
        
        return text, math_map
    
    def restore_math_expressions(self, html: str, math_map: Dict) -> str:
        """Restore math expressions with proper MathJax formatting"""
        for key, (math_type, math_content) in math_map.items():
            # Clean the math expression
            cleaned = self._clean_math_expression(math_content)
            
            if math_type == 'display':
                replacement = f'<div class="math-display">\\[{cleaned}\\]</div>'
            else:
                replacement = f'<span class="math-inline">\\({cleaned}\\)</span>'
            
            html = html.replace(key, replacement)
        
        return html
    
    def _clean_math_expression(self, math: str) -> str:
        """Clean and format math expression"""
        # Fix spacing in arrays for better readability
        math = re.sub(r'\\begin\{array\}\{l\}(.*?)\\end\{array\}', 
                     lambda m: self._format_array(m.group(1)), math, flags=re.DOTALL)
        
        # Fix spacing issues
        math = re.sub(r'\s+', ' ', math)  # Multiple spaces to single
        math = re.sub(r'\s*([+\-=])\s*', r' \1 ', math)  # Space around operators
        
        return math.strip()
    
    def _format_array(self, content: str) -> str:
        """Format array content"""
        lines = [line.strip() for line in content.split('\\\\') if line.strip()]
        formatted = ' \\\\ '.join(lines)
        return f'\\begin{{array}}{{l}} {formatted} \\end{{array}}'
    
    def get_content_by_subtopic(self, subtopic_id: str) -> Optional[Dict]:
        """Get content by subtopic ID"""
        query = """
            SELECT cr.id, cr.subtopic_id, cr.title, cr.char_count, cr.markdown_content,
                   s.name as subtopic_name, t.name as topic_name, t.type as subject_type
            FROM content_raw cr
            LEFT JOIN subtopics s ON cr.subtopic_id = s.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE cr.subtopic_id LIKE ?
        """
        row = self.conn.execute(query, (f"%{subtopic_id}%",)).fetchone()
        return dict(row) if row else None
    
    def rewrite_math_content(self, content: Dict) -> Dict:
        """Rewrite math content with AI - similar to other subjects"""
        markdown = self._structure_exercises(content['markdown_content'])
        title = content.get('title', 'Unknown')
        subject_type = content.get('subject_type', 'Mathematics')
        
        print(f"   📐 Processing: {title}")
        print(f"      Full content: {len(markdown)} chars")
        
        # Protect math expressions FIRST
        protected_markdown, math_map = self.protect_math_expressions(markdown)
        print(f"      Protected {len(math_map)} math expressions")
        
        # Use FULL content (not truncated like other subjects)
        system_prompt = """You are an expert educational content designer for IGCSE Mathematics students (ages 14-16).
Transform raw textbook markdown into engaging, visually-structured HTML content while PRESERVING ALL mathematical expressions.

CRITICAL REQUIREMENTS:
1. **PRESERVE ALL MATH PLACEHOLDERS**: Keep __MATH_INLINE_X__ and __MATH_DISPLAY_X__ EXACTLY as shown - DO NOT MODIFY THEM
2. **PRESERVE ALL CONTENT**: Include every word, example, exercise, and problem from the original
3. **PRESERVE STRUCTURE**: Keep exercise numbering, letter labels (a, b, c), and problem structure
4. **PRESERVE IMAGES**: Keep all ![](images/...) references exactly

Design Principles (same as other subjects):
1. Visual Learning: Clear sections, proper spacing
2. Chunked Information: Break into digestible sections but keep ALL content
3. Clear Hierarchy: Use proper headings (h1, h2, h3)
4. Key Terms: Highlight definitions with colored boxes
5. Examples: Style examples with distinct containers
6. Exercises: Format exercises clearly with proper structure
7. Text Alignment: All text should be left-aligned (text-left), except math displays which are centered
8. Line Height: Use proper line-height (1.7) for readability
9. Spacing: Consistent margins and padding throughout

Output Format:
- Return clean HTML (no markdown, no code blocks)
- Use Tailwind CSS classes like: text-2xl, font-bold, mt-6, mb-4, my-2, text-left, etc.
- Use semantic HTML5 elements
- Create distinct sections with proper spacing
- Style with Tailwind-like utility classes
- Use colors: blue for headings, green for key terms, gray for examples
- Ensure all paragraphs and text are left-aligned (text-left class)
- Use proper line-height for readability

MATH HANDLING:
- Replace __MATH_INLINE_X__ with: <span class="math-inline">__MATH_INLINE_X__</span>
- Replace __MATH_DISPLAY_X__ with: <div class="math-display">__MATH_DISPLAY_X__</div>
- Keep ALL placeholders - they will be replaced with actual LaTeX later

EXERCISE FORMATTING:
- Format exercises as: <div class="exercise-item"><span class="exercise-label">a</span> <span class="math-inline">__MATH_INLINE_X__</span></div>
- Keep exercise structure: numbered problems, lettered sub-items
- Preserve all exercise content"""

        user_prompt = f"""Transform this IGCSE Mathematics content about "{title}" into beautiful HTML using Tailwind CSS classes.

ORIGINAL CONTENT (FULL TEXT - PRESERVE EVERYTHING):
{protected_markdown}

Requirements:
1. **PRESERVE ALL CONTENT**: Include every paragraph, example, exercise, problem, and solution
2. **PRESERVE ALL MATH PLACEHOLDERS**: Keep __MATH_INLINE_X__ and __MATH_DISPLAY_X__ exactly as shown
3. **PRESERVE ALL IMAGES**: Keep ![](images/...) references
4. Use Tailwind CSS classes like other subjects:
   - Headings: text-2xl font-bold mt-6 mb-4 text-left
   - Paragraphs: my-2 text-left (left-align all text)
   - Sections: proper spacing with mt-4, mb-4, text-left
   - Line height: Use leading-relaxed or line-height: 1.7 for readability
5. Format exercises clearly:
   - Exercise headings: text-xl font-semibold mt-4 mb-2 text-left
   - Exercise items: flex layout with labels, text-left alignment
   - Keep all exercise letters and numbers
   - Ensure exercise items are properly aligned
6. Style examples and key terms with colored boxes
7. Make it visually appealing with proper spacing and typography
8. Keep ALL original text - don't summarize or skip anything
9. TEXT ALIGNMENT: All text content must be left-aligned (text-left class). Only math displays should be centered.
10. Images: Ensure images are properly centered and responsive

Return ONLY the HTML content, no explanations or code blocks."""

        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.5,  # Balanced for structure and creativity
                    "max_tokens": 20000  # Large token limit for full content
                },
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                html_content = result['choices'][0]['message']['content']
                
                # Clean up HTML
                html_content = self._clean_html(html_content)
                html_content = self._strip_speaker_icons(html_content)
                html_content = self._strip_math_delimiters(html_content)
                
                # Fix image paths
                html_content = self._fix_image_paths(html_content)
                
                # Restore math expressions with MathJax
                html_content = self.restore_math_expressions(html_content, math_map)
                
                # Fix double-wrapped spans and clean up
                html_content = self._fix_math_wrapping(html_content)
                
                # Normalize exercise layout for clear numbering/labels
                html_content = self._format_exercises_html(html_content)
                
                # Ensure proper text alignment
                html_content = self._fix_text_alignment(html_content)
                
                # Add MathJax script
                html_content = self._add_mathjax(html_content)
                
                # If images got lost or corrupted, fallback to deterministic pipeline
                if "<img" not in html_content:
                    print("    ⚠️ AI output missing images - using fallback renderer")
                    return self._fallback_processing(markdown, title, math_map)
                
                # Extract summary and key terms
                summary = self._extract_summary(markdown, title)
                key_terms = self._extract_math_terms(markdown)
                
                return {
                    "html_content": html_content,
                    "summary": summary,
                    "key_terms": key_terms
                }
            else:
                print(f"    ⚠️ API error: {response.status_code}")
                print(f"    Response: {response.text[:300]}")
                
        except Exception as e:
            print(f"    ⚠️ Rewrite error: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback: basic conversion
        return self._fallback_processing(markdown, title, math_map)
    
    def _fix_math_wrapping(self, html: str) -> str:
        """Fix double-wrapped math spans and ensure proper formatting"""
        # Remove double-wrapped spans
        html = re.sub(r'<span class="math-inline"><span class="math-inline">(.*?)</span></span>', 
                     r'<span class="math-inline">\1</span>', html)
        html = re.sub(r'<div class="math-display"><div class="math-display">(.*?)</div></div>', 
                     r'<div class="math-display">\1</div>', html)
        
        # Ensure all math expressions are properly wrapped
        # Find any raw \(...\) that aren't wrapped
        html = re.sub(r'(?<!<span class="math-inline">)\\\(([^)]+)\\\)(?!</span>)', 
                     r'<span class="math-inline">\\(\1\\)</span>', html)
        
        # Find any raw \[...\] that aren't wrapped
        html = re.sub(r'(?<!<div class="math-display">)\\\[([^\]]+)\\\](?!</div>)', 
                     r'<div class="math-display">\\[\1\\]</div>', html, flags=re.DOTALL)
        
        return html
    
    def _fix_text_alignment(self, html: str) -> str:
        """Ensure all text elements have proper left alignment"""
        # Add text-left to paragraphs without alignment
        html = re.sub(r'<p\s+([^>]*?)(?<!text-left)(?<!text-center)(?<!text-right)([^>]*?)>', 
                     lambda m: f'<p {m.group(1)}{m.group(2)} style="text-align: left; line-height: 1.7;">' if 'style=' not in m.group(0) else m.group(0), html)
        
        # Add text-left to headings without alignment (except math displays)
        html = re.sub(r'<h([1-6])\s+([^>]*?)(?<!text-left)(?<!text-center)(?<!text-right)([^>]*?)>', 
                     lambda m: f'<h{m.group(1)} {m.group(2)}{m.group(3)} style="text-align: left;">' if 'style=' not in m.group(0) and 'math-display' not in m.group(0) else m.group(0), html)
        
        # Add text-left to lists
        html = re.sub(r'<ul\s+([^>]*?)(?<!text-left)([^>]*?)>', 
                     lambda m: f'<ul {m.group(1)}{m.group(2)} style="text-align: left;">' if 'style=' not in m.group(0) else m.group(0), html)
        html = re.sub(r'<ol\s+([^>]*?)(?<!text-left)([^>]*?)>', 
                     lambda m: f'<ol {m.group(1)}{m.group(2)} style="text-align: left;">' if 'style=' not in m.group(0) else m.group(0), html)
        
        # Add text-left to divs (except math-display which should be centered)
        html = re.sub(r'<div\s+([^>]*?)(?<!text-left)(?<!text-center)(?<!text-right)([^>]*?)(?<!math-display)([^>]*?)>', 
                     lambda m: f'<div {m.group(1)}{m.group(2)}{m.group(3)} style="text-align: left;">' if 'style=' not in m.group(0) and 'math-display' not in m.group(0) else m.group(0), html)
        
        return html
    
    def _structure_exercises(self, markdown: str) -> str:
        """Normalize exercise lines so labels and expressions stay together"""
        lines = [ln.rstrip() for ln in markdown.split('\n')]
        normalized = []
        i = 0
        label_re = re.compile(r'^[a-z]$|^[a-z]\\b', re.IGNORECASE)
        number_re = re.compile(r'^\\d+\\b')
        
        while i < len(lines):
            line = lines[i].strip()
            # Combine label-only line with next expression line
            if (label_re.match(line) or number_re.match(line)) and (i + 1 < len(lines)):
                next_line = lines[i + 1].strip()
                # If next line is not another label/number heading, merge
                if next_line and not label_re.match(next_line) and not number_re.match(next_line):
                    combined = f"{line} {next_line}".strip()
                    normalized.append(combined)
                    i += 2
                    continue
            normalized.append(line)
            i += 1
        
        return "\n".join(normalized)
    
    def _format_exercises_html(self, html: str) -> str:
        """Turn leading label lines (a, b, c, 1, 2, 3) into aligned exercise items"""
        # Convert paragraphs starting with label into exercise items
        def make_item(label: str, body: str) -> str:
            return (
                f'<div class="exercise-item">'
                f'<span class="exercise-label">{label.strip()}</span>'
                f'<span class="exercise-body">{body.strip()}</span>'
                f'</div>'
            )
        
        para_pattern = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL)
        
        def convert_paragraph(match):
            inner = match.group(1).strip()
            m = re.match(r'([a-zA-Z0-9]+)\s+(.*)', inner, re.DOTALL)
            if m:
                label = m.group(1)
                body = m.group(2)
                # Only treat as exercise label if it's a single letter or a pure number (e.g., a, b, c, 1, 2)
                if re.fullmatch(r'[a-zA-Z]', label) or re.fullmatch(r'\d+', label):
                    return make_item(label, body)
            return match.group(0)
        
        return para_pattern.sub(convert_paragraph, html)
    
    def _fix_image_paths(self, html: str) -> str:
        """Fix image paths to use /images/ route with proper styling"""
        def fix_img(match):
            full_tag = match.group(0)
            path = match.group(1)
            
            # Extract filename
            if path.startswith('/images/'):
                filename = path.replace('/images/', '')
            elif path.startswith('images/'):
                filename = path.replace('images/', '')
            else:
                filename = path
            
            # Ensure proper image tag with styling
            if 'class=' in full_tag:
                # Update existing class
                return re.sub(r'class=["\'][^"\']*["\']', 
                            r'class="my-6 mx-auto block max-w-full h-auto rounded-lg shadow-md"', 
                            full_tag.replace(path, f'/images/{filename}'))
            else:
                # Add class attribute
                return full_tag.replace(path, f'/images/{filename}').replace('<img', '<img class="my-6 mx-auto block max-w-full h-auto rounded-lg shadow-md"')
        
        # Fix img tags
        html = re.sub(r'<img\s+([^>]*?)src=["\']([^"\']+)["\']([^>]*?)>', fix_img, html)
        
        # Fix markdown image syntax
        def fix_markdown_img(m):
            alt = m.group(1)
            path = m.group(2)
            filename = path.replace('images/', '') if 'images/' in path else path
            return f'<img src="/images/{filename}" alt="{alt}" class="my-6 mx-auto block max-w-full h-auto rounded-lg shadow-md">'
        
        html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_markdown_img, html)
        return html
    
    def _clean_html(self, html: str) -> str:
        """Clean up HTML response"""
        if html.startswith("```html"):
            html = html[7:]
        if html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        return html.strip()
    
    def _add_mathjax(self, html: str) -> str:
        """Add MathJax script for rendering - ensure it actually renders"""
        mathjax = """
<script>
  // Configure MathJax BEFORE loading
  window.MathJax = {
    tex: {
      inlineMath: [['\\(', '\\)']],
      displayMath: [['\\[', '\\]']],
      processEscapes: true,
      processEnvironments: true
    },
    options: {
      skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
      ignoreHtmlClass: 'tex2jax_ignore',
      processHtmlClass: 'tex2jax_process'
    },
    startup: {
      ready: function() {
        MathJax.startup.defaultReady();
        // Process immediately
        if (MathJax.typesetPromise) {
          MathJax.typesetPromise().then(function() {
            console.log('MathJax rendered successfully');
          }).catch(function(err) {
            console.error('MathJax rendering error:', err);
          });
        }
      }
    }
  };
</script>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<script>
  // Force rendering after MathJax loads
  (function() {
    var attempts = 0;
    function renderMath() {
      attempts++;
      if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise().then(function() {
          console.log('MathJax typeset complete');
        }).catch(function(err) {
          console.error('MathJax error:', err);
          if (attempts < 10) {
            setTimeout(renderMath, 500);
          }
        });
      } else if (attempts < 20) {
        setTimeout(renderMath, 200);
      }
    }
    
    // Try immediately
    renderMath();
    
    // Also try on DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', renderMath);
    }
    
    // And after a delay
    setTimeout(renderMath, 2000);
  })();
</script>
<style>
/* Math Display */
.math-display { 
  margin: 1.5rem auto; 
  text-align: center; 
  overflow-x: auto; 
  padding: 1rem; 
  background: #f8fafc; 
  border-radius: 8px;
  display: block;
  max-width: 100%;
}
.math-inline { 
  display: inline; 
  padding: 0 3px; 
  vertical-align: baseline;
}
.MathJax { 
  font-size: 1.1em !important; 
}

/* Text Alignment and Spacing */
.prose, .prose p {
  text-align: left;
  line-height: 1.7;
  margin-bottom: 1rem;
}
.prose h1, .prose h2, .prose h3 {
  text-align: left;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}
.prose ul, .prose ol {
  text-align: left;
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}
.prose li {
  margin-bottom: 0.5rem;
  line-height: 1.7;
}

/* Exercise formatting */
.prose .exercise-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  text-align: left;
}
.prose .exercise-label {
  font-weight: 600;
  margin-right: 0.5rem;
  min-width: 1.5rem;
  text-align: left;
}

/* Images */
.prose img {
  display: block;
  margin: 1.5rem auto;
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Hide LaTeX code while MathJax processes */
.math-inline:not(:has(.MathJax)),
.math-display:not(:has(.MathJax)) {
  opacity: 0;
  transition: opacity 0.3s;
}
.math-inline .MathJax,
.math-display .MathJax {
  opacity: 1;
}
</style>
"""
        return html + mathjax

    def _strip_speaker_icons(self, html: str) -> str:
        """Remove any stray speaker/audio icons from AI output"""
        return re.sub(r'[🔊🔉🔈🔇]', '', html)

    def _strip_math_delimiters(self, html: str) -> str:
        """Remove LaTeX delimiters and dollars so math renders as plain text"""
        html = re.sub(r'<span class="math-inline">\\\((.*?)\\\)</span>', 
                      lambda m: f'<span class="math-inline math-plain">{m.group(1)}</span>', 
                      html, flags=re.DOTALL)
        html = re.sub(r'<div class="math-display">\\\[(.*?)\\\]</div>', 
                      lambda m: f'<div class="math-display math-plain">{m.group(1)}</div>', 
                      html, flags=re.DOTALL)
        html = re.sub(r'\$\$(.*?)\$\$', r'\1', html, flags=re.DOTALL)
        html = re.sub(r'\$([^\$]+)\$', r'\1', html)
        replacements = {
            r'\\times': 'x',
            r'\\div': '/',
            r'\\cdot': '·',
            r'\\pm': '±',
            r'\\mp': '∓',
            r'\\leq': '≤',
            r'\\geq': '≥',
            r'\\neq': '≠'
        }
        for k, v in replacements.items():
            html = html.replace(k, v)
        html = html.replace('\\', '')
        return html
    
    def _extract_summary(self, markdown: str, title: str) -> str:
        """Extract summary"""
        lines = markdown.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('!') and not line.startswith('$'):
                clean = re.sub(r'\$[^$]+\$', '', line)
                clean = re.sub(r'\$\$.*?\$\$', '', clean, flags=re.DOTALL)
                if clean and len(clean) > 20:
                    return clean[:200] + "..." if len(clean) > 200 else clean
        return f"Mathematics: {title}"
    
    def _extract_math_terms(self, markdown: str) -> str:
        """Extract mathematical terms"""
        terms = set()
        headings = re.findall(r'^#+\s+(.+)$', markdown, re.MULTILINE)
        for heading in headings[:5]:
            if len(heading) < 50:
                terms.add(heading.strip())
        return ", ".join(list(terms)[:10])
    
    def _fallback_processing(self, markdown: str, title: str, math_map: Dict) -> Dict:
        """Fallback: basic conversion with Tailwind classes"""
        protected, _ = self.protect_math_expressions(markdown)
        
        # Convert to HTML with Tailwind classes
        html = protected
        html = re.sub(r'^# (.+)$', r'<h1 class="text-2xl font-bold mt-6 mb-4" style="text-align: left;">\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2 class="text-xl font-semibold mt-4 mb-2" style="text-align: left;">\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3 class="text-lg font-semibold mt-3 mb-2" style="text-align: left;">\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong class="font-semibold">\1</strong>', html)
        html = self._fix_image_paths(html)
        
        # Paragraphs
        lines = html.split('\n')
        result = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('<'):
                result.append(line)
            else:
                result.append(f'<p class="my-2" style="text-align: left; line-height: 1.7;">{line}</p>')
        html = '\n'.join(result)
        
        # Restore math
        html = self.restore_math_expressions(html, math_map)
        html = self._strip_speaker_icons(html)
        html = self._strip_math_delimiters(html)
        
        # Normalize exercise layout for clear numbering/labels
        html = self._format_exercises_html(html)
        
        # Ensure proper text alignment
        html = self._fix_text_alignment(html)
        
        html = self._add_mathjax(html)
        
        return {
            "html_content": html,
            "summary": f"Mathematics: {title}",
            "key_terms": ""
        }
    
    def save_processed(self, raw_id: int, subtopic_id: str, result: Dict) -> int:
        """Save processed content"""
        self.conn.execute("DELETE FROM content_processed WHERE subtopic_id = ?", (subtopic_id,))
        cursor = self.conn.execute("""
            INSERT INTO content_processed 
            (raw_id, subtopic_id, html_content, summary, key_terms, processor_version)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (raw_id, subtopic_id, result["html_content"], result["summary"], 
              result["key_terms"], PROCESSOR_VERSION))
        self.conn.commit()
        return cursor.lastrowid
    
    def process(self, content: Dict) -> Dict:
        """Full pipeline"""
        subtopic_id = content['subtopic_id']
        title = content.get('title', 'Unknown')
        
        print(f"\n📐 Processing: {subtopic_id}")
        print(f"   Title: {title}")
        
        result = self.rewrite_math_content(content)
        processed_id = self.save_processed(content['id'], subtopic_id, result)
        
        print(f"   ✅ Processed: {len(result['html_content'])} chars HTML")
        
        return {
            "raw_id": content['id'],
            "processed_id": processed_id,
            "subtopic_id": subtopic_id,
            "html_length": len(result["html_content"]),
            "summary": result["summary"][:100]
        }
    
    def close(self):
        self.conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subtopic", type=str, help="Process by subtopic ID")
    args = parser.parse_args()
    
    rewriter = MathContentRewriterFinal()
    try:
        if args.subtopic:
            content = rewriter.get_content_by_subtopic(args.subtopic)
            if content:
                result = rewriter.process(content)
                print(f"\n✅ Done: {result}")
            else:
                print("❌ Content not found")
        else:
            parser.print_help()
    finally:
        rewriter.close()