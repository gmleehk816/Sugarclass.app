#!/usr/bin/env python3
"""
LLM Content Enhancer

Uses LLM to generate educational enhancements ONLY (objectives, key terms, questions, takeaways).
The main content is handled by markdown-to-html converter for 100% preservation.
"""

import sys
import json
import re
import importlib.util
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for api_config import
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import api_config
spec = importlib.util.spec_from_file_location("api_config", str(Path(__file__).parent.parent / "api_config.py"))
api_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_config)
make_api_call = api_config.make_api_call
get_api_config = api_config.get_api_config


class LLMEnhancer:
    """
    Generates educational enhancements using LLM without processing main content.
    This ensures no content is lost - only features are generated.
    """
    
    def __init__(self):
        config = get_api_config()
        self.api_config = config
        print(f"🔧 LLM Enhancer using: {config['model']} @ {config['url']}")
    
    def extract_enhancements(
        self, 
        raw_content: str, 
        subtopic_name: str,
        topic_name: str,
        subject_name: str
    ) -> Optional[Dict]:
        """
        Extract educational enhancements from content.
        
        Does NOT modify or process the main content - only generates:
        - Learning objectives
        - Key terms
        - Think About It questions
        - Key takeaways
        
        Args:
            raw_content: Original markdown content
            subtopic_name: Name of the subtopic
            topic_name: Parent topic name
            subject_name: Subject name for context
            
        Returns:
            Dictionary with enhancements or None
        """
        
        # Only send a sample for context (not full content to avoid summarization)
        context_sample = raw_content[:3000]  # First 3000 chars gives enough context
        
        prompt = f"""You are an expert educational content designer for IGCSE/GCSE {subject_name} students (ages 14-16).

Extract ONLY the educational enhancements from this textbook content. Do NOT return or rewrite the main content.

## Topic: {topic_name} > {subtopic_name}

## Content Sample (for context only):
{context_sample}

## Your Task:

Extract and return ONLY these 4 categories:

1. **Learning Objectives**: 3-5 bullet points of what students will learn
2. **Key Terms**: 3-5 important terms with brief 1-sentence definitions
3. **Think About It Questions**: 3-5 questions to test understanding
4. **Key Takeaways**: 5-8 bullet points summarizing the main ideas

## IMPORTANT:
- Return ONLY the enhancements, NOT the main content
- Keep each enhancement concise and focused
- Make objectives specific and measurable
- Questions should be open-ended and thought-provoking
- Takeaways should highlight the core concepts

Return ONLY valid JSON (no markdown code blocks):
{{
    "learning_objectives": ["objective1", "objective2", "objective3"],
    "key_terms": {{
        "term1": "definition1",
        "term2": "definition2",
        "term3": "definition3"
    }},
    "think_about_it_questions": ["question1", "question2", "question3"],
    "key_takeaways": ["takeaway1", "takeaway2", "takeaway3", "takeaway4", "takeaway5"]
}}"""

        try:
            messages = [{"role": "user", "content": prompt}]
            result = make_api_call(
                messages=messages,
                max_tokens=2000,  # Small limit since we only need enhancements
                temperature=0.5,
                auto_fallback=True
            )
            
            if result['success']:
                content = result['content']
                print(f"   ✅ Enhancements generated using {result['model']}")
                
                # Parse JSON response
                enhancements = self._parse_enhancements(content)
                
                if enhancements:
                    # Validate we got all 4 categories
                    required_categories = ['learning_objectives', 'key_terms', 'think_about_it_questions', 'key_takeaways']
                    missing = [cat for cat in required_categories if cat not in enhancements or not enhancements[cat]]
                    
                    if missing:
                        print(f"   ⚠️ Missing categories: {missing}")
                    
                    return enhancements
                else:
                    print(f"   ❌ Could not parse enhancements from response:")
                    print(f"      {content[:200]}...")
                    return None
                    
            else:
                print(f"❌ API Error: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ Error generating enhancements: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_enhancements(self, content: str) -> Optional[Dict]:
        """
        Parse enhancements from LLM response.
        Handles various response formats.
        """
        content = content.strip()
        
        # Try direct JSON parse first
        try:
            if content.startswith('{'):
                return json.loads(content)
        except:
            pass
        
        # Extract from markdown code blocks
        patterns = [
            r'```json\s*\n(.*?)```',  # ```json ... ```
            r'```\s*\n(.*?)```',      # ``` ... ```
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                
                # Clean up common JSON issues
                json_str = re.sub(r'\s+', ' ', json_str)
                json_str = json_str.replace('\n', ' ')
                
                try:
                    return json.loads(json_str)
                except:
                    continue
        
        # Try to extract JSON object directly
        brace_match = re.search(r'\{.*"learning_objectives".*\}', content, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except:
                pass
        
        return None
    
    def generate_fallback_enhancements(self, subtopic_name: str) -> Dict:
        """
        Generate basic fallback enhancements when LLM fails.
        """
        return {
            "learning_objectives": [
                f"Understand the key concepts in {subtopic_name}",
                "Apply knowledge to solve related problems",
                "Develop analytical and critical thinking skills"
            ],
            "key_terms": {
                subtopic_name: f"Main topic of this section"
            },
            "think_about_it_questions": [
                "How does this concept relate to real-world examples?",
                "What are the key principles you should remember?",
                "Can you explain this concept in your own words?"
            ],
            "key_takeaways": [
                f"Main concept: {subtopic_name}",
                "Key principles and guidelines",
                "Important formulas and relationships",
                "Practical applications",
                "Review and practice problems"
            ]
        }


# Convenience function for quick usage
def generate_enhancements(raw_content: str, subtopic_name: str, topic_name: str, subject_name: str) -> Optional[Dict]:
    """Quick function to generate enhancements."""
    enhancer = LLMEnhancer()
    return enhancer.extract_enhancements(raw_content, subtopic_name, topic_name, subject_name)


if __name__ == "__main__":
    """Test the enhancer"""
    import sqlite3
    from pathlib import Path
    
    # Get a sample from database
    db_path = Path(__file__).parent.parent.parent / 'database' / 'rag_content.db'
    conn = sqlite3.connect(db_path)
    
    # Get first business studies subtopic
    cursor = conn.execute("""
        SELECT cr.markdown_content, s.name as subject_name, t.name as topic_name, st.name as subtopic_name
        FROM content_raw cr
        JOIN subtopics st ON cr.subtopic_id = st.id
        JOIN topics t ON st.topic_id = t.id
        JOIN subjects s ON t.subject_id = s.id
        WHERE s.name LIKE '%Business%'
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        print("Testing LLM Enhancer with Business Studies sample...")
        print(f"Subtopic: {row[3]}")
        
        enhancements = generate_enhancements(row[0], row[3], row[2], row[1])
        
        if enhancements:
            print("\n✅ Enhancements generated:")
            print(f"\nLearning Objectives:")
            for obj in enhancements.get('learning_objectives', []):
                print(f"  • {obj}")
            
            print(f"\nKey Terms:")
            for term, definition in enhancements.get('key_terms', {}).items():
                print(f"  • {term}: {definition}")
            
            print(f"\nThink About It Questions:")
            for q in enhancements.get('think_about_it_questions', []):
                print(f"  • {q}")
            
            print(f"\nKey Takeaways:")
            for t in enhancements.get('key_takeaways', []):
                print(f"  • {t}")
        else:
            print("❌ Failed to generate enhancements")
    else:
        print("No sample found in database")