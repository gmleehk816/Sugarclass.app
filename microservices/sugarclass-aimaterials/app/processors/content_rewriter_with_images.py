"""
Content Rewriter with Image Generation
======================================
Rewrites raw markdown content into enhanced educational HTML using nano-banana API.
Generates educational diagrams and saves them locally for serving.

Pipeline:
1. Read raw content from content_raw table
2. Analyze content to determine what images would be helpful
3. Generate images using nano-banana API
4. Rewrite content with AI, embedding generated image paths
5. Save enhanced content to content_processed table
6. Save images to generated_images/ folder (served by Flask)

Usage:
    python content_rewriter_with_images.py --list           # Show unprocessed content
    python content_rewriter_with_images.py --id <id>        # Process specific content
    python content_rewriter_with_images.py --subtopic B2.01 # Process by subtopic ID
    python content_rewriter_with_images.py --topic B2       # Process all B2 subtopics
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

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

load_dotenv()

# Paths
APP_DIR = Path(__file__).parent.parent
PROJECT_ROOT = APP_DIR.parent
DB_PATH = PROJECT_ROOT / "database" / "rag_content.db"
GENERATED_IMAGES_DIR = APP_DIR / "static" / "generated_images"

# Ensure generated_images directory exists
GENERATED_IMAGES_DIR.mkdir(exist_ok=True)

# API Configuration - Use LLM_API settings from .env, fallback to nano-banana
API_KEY = os.getenv("LLM_API_KEY") or os.getenv("NANO_BANANA_API_KEY", "")
API_URL = os.getenv("LLM_API_URL") or os.getenv("NANO_BANANA_API_URL", "https://newapi.aisonnet.org/v1/chat/completions")
if API_URL and not API_URL.endswith('/chat/completions'):
    API_URL = API_URL.rstrip('/') + '/chat/completions'
MODEL = os.getenv("LLM_MODEL") or os.getenv("NANO_BANANA_MODEL", "nano-banana")

# Processor version
PROCESSOR_VERSION = "2.0-with-images"


def crop_whitespace(image_path: Path, padding: int = 10) -> bool:
    """
    Remove white/light borders from an image.
    Returns True if cropping was performed.
    """
    if not HAS_PIL:
        return False
    
    try:
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = img.load()
        width, height = img.size
        
        left, top, right, bottom = width, height, 0, 0
        threshold = 245
        
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y][:3] if isinstance(pixels[x, y], tuple) else (pixels[x, y], pixels[x, y], pixels[x, y])
                if r < threshold or g < threshold or b < threshold:
                    left = min(left, x)
                    top = min(top, y)
                    right = max(right, x)
                    bottom = max(bottom, y)
        
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(width, right + padding)
        bottom = min(height, bottom + padding)
        
        if left >= right or top >= bottom:
            return False
        
        reduction = (1 - (right - left) * (bottom - top) / (width * height)) * 100
        if reduction < 5:
            return False
        
        cropped = img.crop((left, top, right, bottom))
        cropped.save(image_path, quality=95)
        print(f"    ✂️ Cropped whitespace: {width}x{height} → {right-left}x{bottom-top}")
        return True
    except Exception as e:
        print(f"    ⚠️ Crop error: {e}")
        return False


class ImageGenerator:
    """Generate educational images using nano-banana API"""
    
    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
    
    def generate(self, prompt: str, filename: str) -> Optional[str]:
        """
        Generate an image and save locally.
        
        Args:
            prompt: Description of the image to generate
            filename: Local filename to save as (e.g., 'b2_01_diffusion.png')
            
        Returns:
            Local path relative to app/ folder (e.g., 'generated_images/b2_01_diffusion.png')
            or None if generation failed
        """
        print(f"    🎨 Generating: {prompt[:60]}...")
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=90
            )
            
            if response.status_code != 200:
                print(f"    ⚠️ API error: {response.status_code}")
                return None
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Extract image URL from markdown format ![image](URL)
            match = re.search(r'!\[.*?\]\((https://[^)]+)\)', content)
            if not match:
                print(f"    ⚠️ No image URL in response")
                return None
            
            url = match.group(1)
            print(f"    ✓ Generated: {url[:50]}...")
            
            # Download and save locally
            img_response = requests.get(url, timeout=30)
            if img_response.status_code != 200:
                print(f"    ⚠️ Failed to download image")
                return None
            
            # Save to generated_images folder
            img_path = GENERATED_IMAGES_DIR / filename
            with open(img_path, 'wb') as f:
                f.write(img_response.content)
            
            print(f"    💾 Saved: {filename}")
            
            # Auto-crop whitespace
            crop_whitespace(img_path)
            
            # Return path that Flask will serve
            return f"/generated_images/{filename}"
            
        except Exception as e:
            print(f"    ⚠️ Image generation error: {e}")
            return None


class ContentRewriterWithImages:
    """Rewrite content with AI-generated images"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.image_generator = ImageGenerator(API_KEY, API_URL, MODEL)
    
    def get_content_by_subtopic(self, subtopic_id: str) -> Optional[Dict]:
        """Get content by subtopic ID (partial match)"""
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
    
    def get_content_by_id(self, content_id: int) -> Optional[Dict]:
        """Get content by raw content ID"""
        query = """
            SELECT cr.id, cr.subtopic_id, cr.title, cr.char_count, cr.markdown_content,
                   s.name as subtopic_name, t.name as topic_name, t.type as subject_type
            FROM content_raw cr
            LEFT JOIN subtopics s ON cr.subtopic_id = s.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE cr.id = ?
        """
        row = self.conn.execute(query, (content_id,)).fetchone()
        return dict(row) if row else None
    
    def get_unprocessed_by_topic(self, topic_prefix: str) -> List[Dict]:
        """Get all unprocessed content for a topic"""
        query = """
            SELECT cr.id, cr.subtopic_id, cr.title, cr.char_count, cr.markdown_content,
                   s.name as subtopic_name, t.name as topic_name, t.type as subject_type
            FROM content_raw cr
            LEFT JOIN subtopics s ON cr.subtopic_id = s.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE cr.subtopic_id LIKE ?
            AND cr.id NOT IN (SELECT raw_id FROM content_processed WHERE processor_version = ?)
            ORDER BY cr.subtopic_id
        """
        rows = self.conn.execute(query, (f"%{topic_prefix}%", PROCESSOR_VERSION)).fetchall()
        return [dict(row) for row in rows]
    
    def get_unprocessed(self, limit: int = 20) -> List[Dict]:
        """Get all unprocessed content"""
        query = """
            SELECT cr.id, cr.subtopic_id, cr.title, cr.char_count, cr.markdown_content,
                   s.name as subtopic_name, t.name as topic_name, t.type as subject_type
            FROM content_raw cr
            LEFT JOIN subtopics s ON cr.subtopic_id = s.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE cr.id NOT IN (SELECT raw_id FROM content_processed)
            ORDER BY cr.subtopic_id
            LIMIT ?
        """
        rows = self.conn.execute(query, (limit,)).fetchall()
        return [dict(row) for row in rows]
    
    def analyze_content_for_images(self, content: Dict) -> List[Dict]:
        """
        Analyze content to determine what educational images would be helpful.
        
        Returns list of image specs: [{'prompt': ..., 'filename': ..., 'description': ...}]
        """
        markdown = content['markdown_content']
        subtopic_id = content['subtopic_id']
        title = content.get('title', '')
        subject_type = content.get('subject_type', 'Science')
        
        # Create a short ID for filenames (e.g., 'b2_01' from 'combined_science_0653_B2.01')
        short_id = re.search(r'([BCPbcp]\d+[._]\d+)', subtopic_id)
        short_id = short_id.group(1).lower().replace('.', '_') if short_id else hashlib.md5(subtopic_id.encode()).hexdigest()[:8]
        
        # Ask AI to suggest images
        prompt = f"""Analyze this educational content and suggest 2-3 educational diagrams that would help students understand the concepts.

Title: {title}
Subject: {subject_type}

Content:
{markdown[:3000]}

For each suggested image, provide:
1. A detailed prompt for generating an educational diagram (be specific about labels, colors, style)
2. A short description of what the image shows

Format your response as JSON:
{{
    "images": [
        {{
            "prompt": "Create a clear educational diagram showing...",
            "description": "Diagram showing..."
        }}
    ]
}}

Focus on:
- Scientific diagrams that illustrate key concepts
- Clear labels and annotations
- Simple, clean educational style suitable for IGCSE students (ages 14-16)
- Avoid complex 3D or photorealistic images"""

        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",  # Use text model for analysis
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                # Parse JSON from response
                json_match = re.search(r'\{[\s\S]*\}', ai_response)
                if json_match:
                    data = json.loads(json_match.group())
                    images = data.get('images', [])
                    
                    # Add filenames
                    for i, img in enumerate(images):
                        img['filename'] = f"{short_id}_img{i+1}.png"
                    
                    return images[:3]  # Max 3 images
        except Exception as e:
            print(f"    ⚠️ Image analysis error: {e}")
        
        # Fallback: generate generic images based on title
        return [
            {
                "prompt": f"Create a clear educational diagram illustrating the concept of {title}. Use simple shapes, clear labels, and a clean style suitable for IGCSE students.",
                "description": f"Main concept diagram for {title}",
                "filename": f"{short_id}_main.png"
            }
        ]
    
    def generate_images(self, image_specs: List[Dict]) -> Dict[str, str]:
        """
        Generate images based on specs.
        
        Returns dict mapping description to local path.
        """
        generated = {}
        
        for spec in image_specs:
            path = self.image_generator.generate(spec['prompt'], spec['filename'])
            if path:
                generated[spec['description']] = path
            time.sleep(2)  # Rate limiting
        
        return generated
    
    def rewrite_with_images(self, content: Dict, images: Dict[str, str]) -> Dict:
        """
        Rewrite content using AI, incorporating generated images.
        
        Args:
            content: Raw content dict
            images: Dict mapping description to image path
            
        Returns:
            Dict with html_content, summary, key_terms
        """
        markdown = content['markdown_content']
        title = content.get('title', 'Unknown')
        subject_type = content.get('subject_type', 'Science')
        
        # Build image HTML references
        image_html = ""
        for desc, path in images.items():
            image_html += f'\n<img src="{path}" alt="{desc}" class="edu-image">'
        
        system_prompt = """You are an expert educational content designer for IGCSE science students (ages 14-16).
Transform raw textbook markdown into engaging, visually-structured HTML content.

Design Principles:
1. Visual Learning: Use icons (emoji), clear sections, visual metaphors
2. Chunked Information: Break content into digestible cards/sections
3. Active Engagement: Include "Think About It" boxes, quick checks
4. Clear Hierarchy: Use headings, subheadings, visual separators
5. Key Terms Highlighted: Make definitions stand out with colored boxes
6. Real-World Connections: Add relatable examples

Output Format:
- Return clean HTML (no markdown, no code blocks)
- Use semantic HTML5 elements
- Include inline CSS for styling (modern, clean design)
- Use emoji icons sparingly for visual interest
- Create distinct sections with cards/boxes
- Style key terms with colored backgrounds
- IMPORTANT: Include the provided images in appropriate places with captions"""

        user_prompt = f"""Transform this IGCSE {subject_type} content about "{title}" into engaging HTML.

Original Content:
{markdown[:6000]}

GENERATED IMAGES TO INCLUDE (place these in relevant sections):
{image_html}

Requirements:
1. Create a visually appealing layout with distinct sections
2. Highlight KEY TERM definitions prominently (use colored boxes)
3. Keep all scientific accuracy from the original
4. Include questions but make them more engaging
5. Add 1-2 "Think About It" or "Real World Connection" boxes
6. Use a clean, modern design with cards and proper spacing
7. **INCLUDE ALL PROVIDED IMAGES** with styled containers and captions
8. Style images with: border-radius: 10px, box-shadow, max-width: 100%, centered, margin: 20px auto

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
                    "temperature": 0.7,
                    "max_tokens": 8000
                },
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                html_content = result['choices'][0]['message']['content']
                
                # Clean up HTML
                html_content = self._clean_html(html_content)
                
                # Extract summary and key terms
                summary = self._extract_summary(markdown, title)
                key_terms = self._extract_key_terms(markdown)
                
                return {
                    "html_content": html_content,
                    "summary": summary,
                    "key_terms": key_terms
                }
            else:
                print(f"    ⚠️ API error: {response.status_code}")
                
        except Exception as e:
            print(f"    ⚠️ Rewrite error: {e}")
        
        # Fallback
        return self._fallback_processing(markdown, title, images)
    
    def _clean_html(self, html: str) -> str:
        """Clean up HTML response"""
        # Remove code block markers
        if html.startswith("```html"):
            html = html[7:]
        if html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        return html.strip()
    
    def _extract_summary(self, markdown: str, title: str) -> str:
        """Extract a summary from content"""
        # Take first paragraph or sentence
        lines = markdown.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('!'):
                return line[:200] + "..." if len(line) > 200 else line
        return f"Content about {title}"
    
    def _extract_key_terms(self, markdown: str) -> str:
        """Extract key terms from content"""
        # Look for bold terms or terms after "Key term:" etc.
        terms = set()
        
        # Bold terms
        bold_matches = re.findall(r'\*\*([^*]+)\*\*', markdown)
        for match in bold_matches:
            if len(match) < 50:  # Reasonable term length
                terms.add(match.strip())
        
        # Terms after "Key term:" or similar
        key_matches = re.findall(r'[Kk]ey [Tt]erm[s]?:?\s*([^.\n]+)', markdown)
        for match in key_matches:
            terms.add(match.strip())
        
        return ", ".join(list(terms)[:10])
    
    def _fallback_processing(self, markdown: str, title: str, images: Dict[str, str]) -> Dict:
        """Fallback: basic markdown to HTML with images"""
        import html as html_lib
        
        content = html_lib.escape(markdown)
        content = re.sub(r'^# (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\n\n', '</p><p>', content)
        content = f'<p>{content}</p>'
        
        # Add images
        for desc, path in images.items():
            content += f'<div style="text-align:center;margin:20px 0;"><img src="{path}" alt="{desc}" style="max-width:100%;border-radius:10px;"><p style="font-style:italic;color:#666;">{desc}</p></div>'
        
        return {
            "html_content": content,
            "summary": f"Content about {title}",
            "key_terms": ""
        }
    
    def save_processed(self, raw_id: int, subtopic_id: str, result: Dict) -> int:
        """Save processed content to database"""
        # Delete existing processed content for this subtopic (to allow re-processing)
        self.conn.execute("DELETE FROM content_processed WHERE subtopic_id = ?", (subtopic_id,))
        
        cursor = self.conn.execute("""
            INSERT INTO content_processed 
            (raw_id, subtopic_id, html_content, summary, key_terms, processor_version)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            raw_id,
            subtopic_id,
            result["html_content"],
            result["summary"],
            result["key_terms"],
            PROCESSOR_VERSION
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def process(self, content: Dict, force_regenerate_images: bool = False) -> Dict:
        """
        Full pipeline: analyze → generate images → rewrite → save
        
        Args:
            content: Raw content dict
            force_regenerate_images: If True, regenerate images even if they exist
            
        Returns:
            Processing result dict
        """
        subtopic_id = content['subtopic_id']
        title = content.get('title', 'Unknown')
        
        print(f"\n📝 Processing: {subtopic_id}")
        print(f"   Title: {title}")
        
        # Step 1: Analyze content for images
        print("   📊 Analyzing content for images...")
        image_specs = self.analyze_content_for_images(content)
        print(f"   Found {len(image_specs)} image opportunities")
        
        # Step 2: Generate images
        print("   🎨 Generating images...")
        images = {}
        for spec in image_specs:
            # Check if image already exists
            img_path = GENERATED_IMAGES_DIR / spec['filename']
            if img_path.exists() and not force_regenerate_images:
                print(f"    ✓ Using existing: {spec['filename']}")
                images[spec['description']] = f"/generated_images/{spec['filename']}"
            else:
                path = self.image_generator.generate(spec['prompt'], spec['filename'])
                if path:
                    images[spec['description']] = path
                time.sleep(2)
        
        print(f"   Generated {len(images)} images")
        
        # Step 3: Rewrite content with images
        print("   ✍️ Rewriting content...")
        result = self.rewrite_with_images(content, images)
        
        # Step 4: Save to database
        print("   💾 Saving to database...")
        processed_id = self.save_processed(content['id'], subtopic_id, result)
        
        # Step 5: Save HTML preview file
        preview_file = APP_DIR / f"{subtopic_id.split('_')[-1].lower().replace('.', '_')}_rewritten.html"
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .edu-image {{ max-width: 100%; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); display: block; margin: 20px auto; }}
    </style>
</head>
<body>
{result['html_content']}
</body>
</html>""")
        print(f"   📄 Preview saved: {preview_file.name}")
        
        return {
            "raw_id": content['id'],
            "processed_id": processed_id,
            "subtopic_id": subtopic_id,
            "images_generated": len(images),
            "html_length": len(result["html_content"]),
            "summary": result["summary"][:100]
        }
    
    def close(self):
        self.conn.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Rewrite content with AI-generated images")
    parser.add_argument("--list", action="store_true", help="List unprocessed content")
    parser.add_argument("--id", type=int, help="Process by raw content ID")
    parser.add_argument("--subtopic", type=str, help="Process by subtopic ID (e.g., B2.01)")
    parser.add_argument("--topic", type=str, help="Process all subtopics for a topic (e.g., B2)")
    parser.add_argument("--regenerate", action="store_true", help="Force regenerate images")
    parser.add_argument("--limit", type=int, default=5, help="Max items to process")
    
    args = parser.parse_args()
    
    rewriter = ContentRewriterWithImages()
    
    try:
        if args.list:
            content_list = rewriter.get_unprocessed(limit=20)
            print(f"\n📋 Unprocessed Content ({len(content_list)} items):")
            print("-" * 60)
            for c in content_list:
                print(f"  [{c['id']}] {c['subtopic_id']}")
                print(f"      {c['title'][:50]}... ({c['char_count']} chars)")
        
        elif args.subtopic:
            content = rewriter.get_content_by_subtopic(args.subtopic)
            if content:
                result = rewriter.process(content, force_regenerate_images=args.regenerate)
                print(f"\n✅ Result: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Subtopic '{args.subtopic}' not found")
        
        elif args.id:
            content = rewriter.get_content_by_id(args.id)
            if content:
                result = rewriter.process(content, force_regenerate_images=args.regenerate)
                print(f"\n✅ Result: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Content ID {args.id} not found")
        
        elif args.topic:
            content_list = rewriter.get_unprocessed_by_topic(args.topic)
            if content_list:
                print(f"\n🔄 Processing {min(len(content_list), args.limit)} items for topic '{args.topic}'...")
                for content in content_list[:args.limit]:
                    result = rewriter.process(content, force_regenerate_images=args.regenerate)
                    print(f"   ✅ {content['subtopic_id']}")
            else:
                print(f"❌ No unprocessed content for topic '{args.topic}'")
        
        else:
            parser.print_help()
    
    finally:
        rewriter.close()


if __name__ == "__main__":
    main()