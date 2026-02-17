import sys
from pathlib import Path

# Add the app directory to sys.path
sys.path.append(str(Path(__file__).parent / "microservices" / "sugarclass-aimaterials" / "app"))

from processors.content_processor_v8 import ContentSplitter

test_markdown = """
# Chapter 1: Introduction to Music
This is some chapter intro text.

## 1.1 Elements of Music
Content for 1.1.

## 1.2 History of Notation
Content for 1.2.

# Chapter 2: Instrumental Music
Intro for chapter 2.

## 2.1 Strings
Content for 2.1.

## No Number Subtopic
Content for a subtopic without numbers.

# No Number Chapter
Content for a chapter without numbers.

## Another Subtopic
More content.
"""

def test_splitter():
    splitter = ContentSplitter(test_markdown)
    subtopics = splitter.split()
    
    print(f"Total subtopics found: {len(subtopics)}")
    for i, st in enumerate(subtopics, 1):
        print(f"{i}. [{st.get('num', 'N/A')}] {st['title']}")
        # print(f"   Content preview: {st['content'][:50]}...")

    if len(subtopics) == 5:
        print("\nVerification SUCCESS: All 5 subtopics detected!")
    else:
        print(f"\nVerification FAILED: Expected 5 subtopics, found {len(subtopics)}")

if __name__ == "__main__":
    test_splitter()
