"""
Content Builder Processor
=========================
Reads markdown content from MinerU output, analyzes it, and enhances with AI-generated images.

Uses nano-banana API for image generation.
"""

import os
import re
import json
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_KEY = os.getenv("NANO_BANANA_API_KEY", "sk-puvdcYfbp2Wu0Zyswmv6JiVOWEchC8Lr8K19LzbRqFr4ZuOp")
API_URL = os.getenv("NANO_BANANA_API_URL", "https://newapi.aisonnet.org/v1/chat/completions")
MODEL = os.getenv("NANO_BANANA_MODEL", "nano-banana")

# Paths
APP_DIR = Path(__file__).parent.parent
PROJECT_ROOT = APP_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
MATERIALS_OUTPUT = OUTPUT_DIR / "materials_output"


class ContentBuilder:
    """
    Processes markdown content and enhances it with AI-generated images.
    
    Workflow:
    1. Parse markdown to identify sections/topics
    2. Extract key concepts that need visualization
    3. Generate educational images using nano-banana API
    4. Insert images into enhanced markdown
    5. Save enhanced content
    """
    
    def __init__(self):
        self.api_key = API_KEY
        self.api_url = API_URL
        self.model = MODEL
        self.generated_images_dir = APP_DIR / "static" / "ai_generated"
        self.generated_images_dir.mkdir(parents=True, exist_ok=True)
    
    def process_content(self, content_path: Path, output_folder: Path) -> Dict:
        """
        Main entry point: Process a markdown file and enhance with AI images.
        
        Args:
            content_path: Path to the markdown file (from MinerU)
            output_folder: Where to save enhanced content
            
        Returns:
            Dict with processing results
        """
        print(f"📖 Processing: {content_path}")
        
        # Read original content
        with open(content_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Step 1: Analyze content structure
        sections = self._parse_sections(markdown_content)
        print(f"   Found {len(sections)} sections")
        
        # Step 2: Identify concepts needing images
        concepts = self._extract_concepts(sections)
        print(f"   Identified {len(concepts)} concepts for visualization")
        
        # Step 3: Generate images for each concept
        generated_images = []
        for concept in concepts[:5]:  # Limit to 5 images per content
            image_result = self._generate_image_for_concept(concept, output_folder)
            if image_result:
                generated_images.append(image_result)
                print(f"   🖼️ Generated image for: {concept['title']}")
        
        # Step 4: Enhance markdown with images
        enhanced_content = self._enhance_markdown(markdown_content, generated_images)
        
        # Step 5: Save enhanced content
        enhanced_path = output_folder / "content_enhanced.md"
        with open(enhanced_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        # Save original as backup
        original_path = output_folder / "content_original.md"
        with open(original_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Update metadata
        result = {
            "processed_at": datetime.now().isoformat(),
            "original_file": str(content_path),
            "sections_found": len(sections),
            "concepts_identified": len(concepts),
            "images_generated": len(generated_images),
            "output_files": {
                "enhanced": "content_enhanced.md",
                "original": "content_original.md",
                "images": [img["filename"] for img in generated_images]
            }
        }
        
        print(f"   ✅ Enhanced content saved with {len(generated_images)} AI images")
        return result
    
    def _parse_sections(self, markdown: str) -> List[Dict]:
        """Parse markdown into sections based on headings"""
        sections = []
        
        # Split by headings (# ## ###)
        heading_pattern = r'^(#{1,3})\s+(.+)$'
        lines = markdown.split('\n')
        
        current_section = {"level": 0, "title": "Introduction", "content": []}
        
        for line in lines:
            match = re.match(heading_pattern, line)
            if match:
                # Save previous section
                if current_section["content"]:
                    current_section["text"] = '\n'.join(current_section["content"])
                    sections.append(current_section)
                
                # Start new section
                level = len(match.group(1))
                title = match.group(2).strip()
                current_section = {"level": level, "title": title, "content": []}
            else:
                current_section["content"].append(line)
        
        # Don't forget last section
        if current_section["content"]:
            current_section["text"] = '\n'.join(current_section["content"])
            sections.append(current_section)
        
        return sections
    
    def _extract_concepts(self, sections: List[Dict]) -> List[Dict]:
        """
        Extract key concepts that would benefit from visualization.
        
        Looks for:
        - Scientific terms and definitions
        - Processes (photosynthesis, digestion, etc.)
        - Structures (cell, organ, etc.)
        - Comparisons
        """
        concepts = []
        
        # Keywords that indicate visualizable concepts
        visual_keywords = [
            # Biology
            'cell', 'organ', 'tissue', 'system', 'structure', 'diagram',
            'process', 'cycle', 'flow', 'movement', 'transport',
            'photosynthesis', 'respiration', 'digestion', 'circulation',
            'reproduction', 'growth', 'nutrition', 'excretion',
            'diffusion', 'osmosis', 'enzyme', 'protein',
            # Chemistry
            'atom', 'molecule', 'reaction', 'bond', 'element', 'compound',
            'acid', 'base', 'solution', 'mixture',
            # Physics
            'force', 'energy', 'wave', 'circuit', 'motion', 'pressure',
            'electricity', 'magnetism', 'light', 'sound'
        ]
        
        for section in sections:
            title_lower = section.get("title", "").lower()
            text = section.get("text", "")
            
            # Check if section title contains visual keywords
            for keyword in visual_keywords:
                if keyword in title_lower or keyword in text.lower()[:500]:
                    concepts.append({
                        "title": section["title"],
                        "keyword": keyword,
                        "context": text[:300],  # First 300 chars for context
                        "section_level": section["level"]
                    })
                    break  # One concept per section
        
        return concepts
    
    def _generate_image_for_concept(self, concept: Dict, output_folder: Path) -> Optional[Dict]:
        """
        Generate an educational image for a concept using nano-banana API.
        
        Args:
            concept: Dict with title, keyword, context
            output_folder: Where to save the image
            
        Returns:
            Dict with image info or None if failed
        """
        # Create educational prompt
        prompt = self._create_image_prompt(concept)
        
        try:
            # Call nano-banana API
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract image URL from response
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                image_url = self._extract_image_url(content)
                
                if image_url:
                    # Generate filename
                    safe_title = re.sub(r'[^\w\s-]', '', concept["title"])[:30]
                    safe_title = safe_title.replace(' ', '_').lower()
                    filename = f"ai_{safe_title}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png"
                    
                    # Save image reference (or download if needed)
                    images_dir = output_folder / "images"
                    images_dir.mkdir(exist_ok=True)
                    
                    return {
                        "concept": concept["title"],
                        "keyword": concept["keyword"],
                        "prompt": prompt,
                        "image_url": image_url,
                        "filename": filename,
                        "local_path": str(images_dir / filename)
                    }
            else:
                print(f"   ⚠️ API error: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Image generation failed: {e}")
        
        return None
    
    def _create_image_prompt(self, concept: Dict) -> str:
        """Create an educational image prompt for the concept"""
        keyword = concept["keyword"]
        title = concept["title"]
        context = concept.get("context", "")[:200]
        
        # Educational image prompt template
        prompt = f"""Generate an educational illustration for students about "{title}".

Topic: {keyword}
Context: {context}

Requirements:
- Clear, colorful educational diagram style
- Suitable for secondary school students (ages 14-18)
- Include labels and annotations
- Use bright, engaging colors
- Scientific accuracy is important
- No text that could be misspelled - use simple labels only

Style: Modern educational textbook illustration, clean vector-like graphics."""

        return prompt
    
    def _extract_image_url(self, content: str) -> Optional[str]:
        """Extract image URL from API response content"""
        # Look for markdown image syntax: ![...](URL)
        md_pattern = r'!\[.*?\]\((https?://[^\)]+)\)'
        match = re.search(md_pattern, content)
        if match:
            return match.group(1)
        
        # Look for plain URL
        url_pattern = r'(https?://[^\s\)\"\']+\.(?:png|jpg|jpeg|gif|webp))'
        match = re.search(url_pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _enhance_markdown(self, markdown: str, images: List[Dict]) -> str:
        """
        Enhance markdown by inserting AI-generated images at appropriate locations.
        """
        if not images:
            return markdown
        
        enhanced = markdown
        
        # Add AI images section at the top
        ai_section = "\n\n## 🤖 AI-Generated Illustrations\n\n"
        ai_section += "> These images were automatically generated to help visualize key concepts.\n\n"
        
        for img in images:
            ai_section += f"### {img['concept']}\n\n"
            ai_section += f"![{img['concept']}]({img['image_url']})\n\n"
            ai_section += f"*AI-generated illustration for: {img['keyword']}*\n\n"
        
        # Insert after first heading
        first_heading = re.search(r'^#\s+.+$', enhanced, re.MULTILINE)
        if first_heading:
            insert_pos = first_heading.end()
            enhanced = enhanced[:insert_pos] + ai_section + enhanced[insert_pos:]
        else:
            enhanced = ai_section + enhanced
        
        return enhanced


def process_folder(folder_path: Path) -> Dict:
    """
    Process all content.md files in a folder and its subfolders.
    """
    builder = ContentBuilder()
    results = []
    
    for content_file in folder_path.rglob("content.md"):
        output_folder = content_file.parent
        try:
            result = builder.process_content(content_file, output_folder)
            results.append({"path": str(content_file), "status": "success", **result})
        except Exception as e:
            results.append({"path": str(content_file), "status": "error", "error": str(e)})
    
    return {"processed": len(results), "results": results}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Content Builder - Enhance markdown with AI images")
    parser.add_argument("--path", type=str, help="Path to content.md or folder to process")
    parser.add_argument("--test", action="store_true", help="Run test with sample content")
    
    args = parser.parse_args()
    
    if args.test:
        # Test with existing content
        test_path = OUTPUT_DIR / "test"
        if test_path.exists():
            print("🧪 Running test on output/test folder...")
            results = process_folder(test_path)
            print(json.dumps(results, indent=2))
        else:
            print("❌ No test folder found at output/test")
    elif args.path:
        path = Path(args.path)
        if path.is_file():
            builder = ContentBuilder()
            result = builder.process_content(path, path.parent)
            print(json.dumps(result, indent=2))
        elif path.is_dir():
            results = process_folder(path)
            print(json.dumps(results, indent=2))
    else:
        # Process all materials_output
        print("🔄 Processing all content in materials_output...")
        results = process_folder(MATERIALS_OUTPUT)
        print(json.dumps(results, indent=2))
