import os
import sys
import json
from dotenv import load_dotenv

# Add app directory to path so we can import admin_v8
sys.path.append(r"e:\PROGRAMMING\Projects\Sugarclass.app\microservices\sugarclass-aimaterials\app")
load_dotenv(r"e:\PROGRAMMING\Projects\Sugarclass.app\microservices\sugarclass-aimaterials\.env")

from admin_v8 import _llm_detect_structure

def test_extraction():
    # Find a test markdown file
    md_dir = r"e:\PROGRAMMING\Projects\Sugarclass.app\database\processing"
    
    test_file = None
    for root, dirs, files in os.walk(md_dir):
        for f in files:
            if f.endswith('.md'):
                test_file = os.path.join(root, f)
                break
        if test_file:
            break
            
    if not test_file:
        print("No test file found.")
        return
        
    print(f"Testing on: {test_file}")
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    print(f"File size: {len(content)} chars, {len(content.split(chr(10)))} lines")
    
    def log(level, msg):
        print(f"[{level}] {msg}")
        
    print("Extracting structure...")
    structure = _llm_detect_structure(content, log)
    
    print("\nResult:")
    print(json.dumps(structure, indent=2))

if __name__ == "__main__":
    test_extraction()
