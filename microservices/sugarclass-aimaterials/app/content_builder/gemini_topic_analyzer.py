"""
Gemini-Powered Topic & Subtopic Analyzer
=========================================
Uses Gemini API to intelligently analyze full Markdown content
and generate high-quality topic/subtopic structure.

Features:
1. Reads complete Markdown files
2. Uses Gemini API to understand content structure
3. Identifies meaningful topics and subtopics
4. Filters out metadata, headers, and noise
5. Generates SQL INSERT statements for database
"""

import requests
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add parent path to import api_config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api_config import get_api_config

# Load API Configuration from central config
_api_config = get_api_config()
API_KEY = _api_config['key']
# Ensure full API URL path
_base_url = _api_config['url'].rstrip('/')
if not _base_url.endswith('/chat/completions'):
    API_URL = f"{_base_url}/v1/chat/completions" if '/v1' not in _base_url else f"{_base_url}/chat/completions"
else:
    API_URL = _base_url
MODEL = _api_config['model']


class GeminiTopicAnalyzer:
    """Intelligent topic/subtopic analyzer using Gemini API"""
    
    def __init__(self, api_key: str = API_KEY, model: str = MODEL):
        self.api_key = api_key
        self.model = model
        self.session = requests.Session()
    
    def analyze_markdown(self, markdown_content: str, subject_name: str = "Engineering") -> Dict:
        """
        Analyze full Markdown content and extract topic/subtopic structure
        
        Args:
            markdown_content: Complete markdown text
            subject_name: Subject name for context
            
        Returns:
            Dictionary with topics and subtopics structure
        """
        
        # Create intelligent prompt for Gemini - simplified output format
        prompt = f"""You are an expert educational content analyzer for {subject_name} curriculum.

Analyze this textbook content and extract ALL chapters and subtopics.

**RULES:**
1. Extract ONLY real educational topics (chapters, sections)
2. IGNORE: metadata, ISBN, page numbers, keywords, activities
3. Each topic = one chapter/unit
4. List ALL subtopics within each topic

**OUTPUT FORMAT (compact JSON):**
{{"topics":[{{"name":"Chapter Name","subtopics":[{{"name":"Subtopic 1"}},{{"name":"Subtopic 2"}}]}}]}}

**CONTENT:**
{markdown_content[:20000]}

Return ONLY the JSON, no explanation:"""

        try:
            response = self.session.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,  # Lower temperature for more consistent output
                    "max_tokens": 8000  # Increased for complete JSON structure
                },
                timeout=180  # Longer timeout for complete response
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract JSON from response (might be wrapped in markdown code blocks)
                # First try with proper closing ```
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
                elif '```json' in content:
                    # Try to extract everything after ```json (response may be truncated)
                    start_idx = content.find('```json') + 7
                    if content[start_idx:start_idx+1] == '\n':
                        start_idx += 1
                    # Find end or take rest
                    end_idx = content.find('\n```', start_idx)
                    if end_idx > 0:
                        content = content[start_idx:end_idx]
                    else:
                        content = content[start_idx:]
                elif '```' in content:
                    # Try without json tag
                    json_match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1)
                
                # Clean up truncated JSON if needed (try to make it valid)
                content = content.strip()
                
                # Try to parse, and if truncated, try to fix
                try:
                    structure = json.loads(content)
                except json.JSONDecodeError:
                    # Try to fix truncated JSON by completing arrays/objects
                    fixed_content = self._fix_truncated_json(content)
                    structure = json.loads(fixed_content)
                    
                return structure
            else:
                print(f"❌ API Error: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Error analyzing markdown: {e}")
            return None
    
    def _fix_truncated_json(self, json_str: str) -> str:
        """Try to fix truncated JSON by adding missing brackets and handling incomplete strings"""
        import re as regex
        
        # First, try to find the last complete topic entry
        # Look for patterns like }, followed by ], } to close the structure
        
        # Remove incomplete string at the end (e.g., "description": "Incomplete...)
        # Find last complete object by looking for complete "order": N patterns
        last_complete = json_str.rfind('"order":')
        if last_complete > 0:
            # Find the closing brace for this object
            end_search = json_str.find('}', last_complete)
            if end_search > 0:
                # Check if there's more content after that looks incomplete
                remaining = json_str[end_search+1:].strip()
                if remaining and not remaining.startswith(']') and not remaining.startswith('}'):
                    # There's incomplete content, truncate to last complete object
                    json_str = json_str[:end_search+1]
        
        # Count open/close brackets
        open_braces = json_str.count('{') - json_str.count('}')
        open_brackets = json_str.count('[') - json_str.count(']')
        
        # Remove any trailing comma or incomplete content
        json_str = json_str.rstrip(',\n\r\t ')
        
        # Check for unterminated string at the very end
        # Count quotes (ignoring escaped quotes)
        temp = json_str.replace('\\"', '')
        quote_count = temp.count('"')
        if quote_count % 2 != 0:
            # Odd number of quotes - find and close the last one
            # Find last quote and add closing quote after trimming
            last_quote = json_str.rfind('"')
            if last_quote > 0:
                # Find the start of this string value (previous quote)
                prev_quote = json_str.rfind('"', 0, last_quote)
                if prev_quote > 0:
                    # Truncate to before the incomplete string started, find the key
                    colon_pos = json_str.rfind(':', 0, prev_quote)
                    if colon_pos > 0:
                        json_str = json_str[:colon_pos+1] + '""'
        
        # Recalculate after potential string fix
        open_braces = json_str.count('{') - json_str.count('}')
        open_brackets = json_str.count('[') - json_str.count(']')
        
        # Remove trailing comma again
        json_str = json_str.rstrip(',\n\r\t ')
        
        # Add missing closing brackets in correct order (arrays first, then objects)
        # But we need to figure out the right nesting order
        # Simple approach: close subtopics array, then topic object, then topics array, then root
        json_str += ']' * open_brackets
        json_str += '}' * open_braces
        
        return json_str
    
    def validate_structure(self, structure: Dict) -> Tuple[bool, List[str]]:
        """
        Validate the extracted structure for quality
        
        Returns:
            (is_valid, list of issues)
        """
        issues = []
        
        if not structure or 'topics' not in structure:
            return False, ["Missing 'topics' key"]
        
        topics = structure['topics']
        
        if len(topics) == 0:
            issues.append("No topics found")
        
        for i, topic in enumerate(topics):
            # Check topic structure
            if 'name' not in topic:
                issues.append(f"Topic {i+1}: Missing 'name'")
            elif len(topic['name']) > 60:
                issues.append(f"Topic {i+1}: Name too long ({len(topic['name'])} chars)")
            
            # Check for metadata names
            bad_names = ['AQA', 'GCSE', 'KEY WORD', 'ACTIVITY', 'INTRODUCTION']
            if any(bad in topic.get('name', '').upper() for bad in bad_names):
                issues.append(f"Topic {i+1}: Contains metadata keyword: {topic['name']}")
            
            # Check subtopics
            subtopics = topic.get('subtopics', [])
            if len(subtopics) == 0:
                issues.append(f"Topic {i+1}: No subtopics")
            elif len(subtopics) == 1:
                issues.append(f"Topic {i+1}: Only one subtopic (consider merging)")
            elif len(subtopics) > 15:
                issues.append(f"Topic {i+1}: Too many subtopics ({len(subtopics)})")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def generate_sql(self, structure: Dict, subject_id: int) -> str:
        """
        Generate SQL INSERT statements for the structure
        
        Args:
            structure: Validated topic/subtopic structure
            subject_id: Database subject ID
            
        Returns:
            SQL statements as string
        """
        sql_statements = []
        sql_statements.append("-- Generated by Gemini Topic Analyzer")
        sql_statements.append(f"-- Subject ID: {subject_id}\n")
        
        for topic in structure.get('topics', []):
            topic_name = topic['name'].replace("'", "''")  # Escape quotes
            topic_desc = topic.get('description', '').replace("'", "''")
            topic_order = topic.get('order', 0)
            topic_type = topic.get('type', 'lesson')
            
            sql_statements.append(f"""
INSERT INTO topics (name, description, subject_id, order_num, type)
VALUES ('{topic_name}', '{topic_desc}', {subject_id}, {topic_order}, '{topic_type}');
""")
            
            # Get last inserted topic_id (using a variable)
            sql_statements.append("SET @last_topic_id = LAST_INSERT_ID();\n")
            
            for subtopic in topic.get('subtopics', []):
                subtopic_name = subtopic['name'].replace("'", "''")
                subtopic_desc = subtopic.get('description', '').replace("'", "''")
                subtopic_order = subtopic.get('order', 0)
                
                sql_statements.append(f"""
INSERT INTO subtopics (name, description, topic_id, order_num)
VALUES ('{subtopic_name}', '{subtopic_desc}', @last_topic_id, {subtopic_order});
""")
        
        return '\n'.join(sql_statements)


def main():
    """Example usage"""
    print("🤖 Gemini Topic Analyzer - Demo\n")
    print("=" * 70)
    
    # Example: Load a markdown file
    markdown_file = Path(__file__).parent / "example_textbook.md"
    
    if not markdown_file.exists():
        print("⚠️ Create an example_textbook.md file to test")
        print("Using sample content instead...\n")
        
        sample_markdown = """
# Engineering Textbook

## Chapter 1: Introduction to Engineering
Engineering is the application of science and mathematics to solve real-world problems.

## Chapter 2: Materials Science
### 2.1 Properties of Materials
Materials have different properties like strength, durability, and conductivity.

### 2.2 Types of Materials
Common engineering materials include metals, polymers, and ceramics.

## Chapter 3: Manufacturing Processes
### 3.1 Casting
Casting is a manufacturing process where molten material is poured into a mold.

### 3.2 Machining
Machining involves removing material to create desired shapes.
"""
        markdown_content = sample_markdown
    else:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    
    # Analyze
    analyzer = GeminiTopicAnalyzer()
    print("📊 Analyzing markdown content with Gemini 3 Flash Preview...\n")
    
    structure = analyzer.analyze_markdown(markdown_content, subject_name="Engineering")
    
    if structure:
        print("✅ Analysis complete!\n")
        print(json.dumps(structure, indent=2, ensure_ascii=False))
        
        # Validate
        print("\n🔍 Validating structure...")
        is_valid, issues = analyzer.validate_structure(structure)
        
        if is_valid:
            print("✅ Structure is valid!")
        else:
            print(f"⚠️ Found {len(issues)} issues:")
            for issue in issues:
                print(f"   • {issue}")
        
        # Generate SQL
        print("\n📝 Generating SQL statements...\n")
        sql = analyzer.generate_sql(structure, subject_id=1)
        print(sql)
    else:
        print("❌ Analysis failed")


if __name__ == "__main__":
    main()
