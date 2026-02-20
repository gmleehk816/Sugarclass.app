import os
import sys
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

# Mocking parts of admin_v8 and dependencies for local testing
def test_structure_enhanced():
    # Structural lines extraction logic (copied from admin_v8.py)
    def extract_structural_lines(markdown_content: str):
        lines = markdown_content.split('\n')
        structural_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line: continue
            is_heading = (
                line.startswith('#') or 
                line.startswith('**') or 
                re.match(r'^\d+(?:\.\d+)+\s', line) or
                re.match(r'^\d+\s+[A-Z]', line) or
                re.match(r'^(?:Chapter|Part|Unit|Section|Module|Topic|Lesson)\s', line, re.IGNORECASE) or
                (line.isupper() and len(line) > 8 and len(line) < 100 and re.search(r'[A-Z]', line)) or # CAPS
                (len(line) < 85 and re.match(r'^[A-Z0-9]', line)) # Short
            )
            if is_heading:
                structural_lines.append(f"{i}: {line}")
        return structural_lines

    # Sample markdown with complex 3-level structure
    markdown = """
SECTION 1: COMPUTER SYSTEMS
1 Data representation
1.1 Number systems
Lorem ipsum...
1.2 Text, sound and images
More text...
2 Data transmission
2.1 Types and methods of data transmission
3 Hardware
3.1 Computer architecture
3.1.1 CPU architecture
Actually 3.1.1 is 3rd level, we want to compress it.
"""

    # Mock TOC from PDF
    toc_data = [
        {'level': 1, 'title': 'SECTION 1: COMPUTER SYSTEMS'},
        {'level': 2, 'title': '1 Data representation'},
        {'level': 3, 'title': '1.1 Number systems'},
        {'level': 3, 'title': '1.2 Text, sound and images'},
        {'level': 2, 'title': '2 Data transmission'},
        {'level': 3, 'title': '2.1 Types and methods of data transmission'},
        {'level': 2, 'title': '3 Hardware'},
        {'level': 3, 'title': '3.1 Computer architecture'},
        {'level': 4, 'title': '3.1.1 CPU architecture'}
    ]

    struct_lines = extract_structural_lines(markdown)
    print("EXTRACTED STRUCTURAL LINES:")
    for sl in struct_lines:
        print(sl)
    
    # Verify that the important lines are present
    titles_found = [l.split(': ', 1)[1] for l in struct_lines]
    expected = [
        "SECTION 1: COMPUTER SYSTEMS",
        "1 Data representation",
        "1.1 Number systems",
        "1.2 Text, sound and images",
        "2 Data transmission",
        "2.1 Types and methods of data transmission",
        "3 Hardware",
        "3.1 Computer architecture",
        "3.1.1 CPU architecture"
    ]
    
    missing = [e for e in expected if e not in titles_found]
    if missing:
        print(f"\nFAILED: Missing structural lines: {missing}")
    else:
        print("\nSUCCESS: All expected structural lines extracted correctly.")

if __name__ == "__main__":
    test_structure_enhanced()
