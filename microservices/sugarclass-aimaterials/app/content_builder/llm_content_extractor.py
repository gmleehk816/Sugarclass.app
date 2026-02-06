"""
LLM Content Extractor - Smart Subtopic Extraction
=================================================
Uses Gemini LLM to intelligently extract subtopic content from chapter chunks.
Understands semantic boundaries, not just text search.

Author: TutorRAG Pipeline v2
Date: 2026-01-04
"""

import json
import re
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Add parent directory to path for api_config import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from api_config import make_api_call, get_api_config
except ImportError:
    # Fallback for direct script execution
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "api_config",
        str(Path(__file__).parent.parent / "api_config.py")
    )
    api_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_config)
    make_api_call = api_config.make_api_call
    get_api_config = api_config.get_api_config


@dataclass
class ExtractedSubtopic:
    """Represents extracted subtopic content"""
    title: str
    content: str
    found: bool = True
    complete: bool = True
    char_count: int = 0
    notes: str = ""


@dataclass
class ExtractionResult:
    """Result of chapter extraction"""
    chapter_number: int
    chapter_title: str
    subtopics: Dict[str, ExtractedSubtopic] = field(default_factory=dict)
    total_expected: int = 0
    total_found: int = 0
    total_complete: int = 0
    issues: List[str] = field(default_factory=list)
    raw_response: str = ""


class LLMContentExtractor:
    """
    Uses Gemini LLM to extract subtopic content from markdown chunks.
    """

    # Minimum content length to be considered valid
    MIN_CONTENT_LENGTH = 200

    # Maximum tokens for extraction
    MAX_TOKENS = 32000  # Larger for full content extraction

    # Temperature for consistent extraction
    TEMPERATURE = 0.2

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        verbose: bool = True
    ):
        """
        Initialize extractor.

        Args:
            max_retries: Number of retries on API failure
            retry_delay: Seconds to wait between retries
            verbose: Print progress messages
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verbose = verbose

        # Get API config
        config = get_api_config()
        self._log(f"Using API: {config.get('model', 'unknown')}")

    def _log(self, message: str):
        """Print message if verbose mode enabled"""
        if self.verbose:
            print(message)

    def _build_extraction_prompt(
        self,
        chapter_markdown: str,
        chapter_title: str,
        subtopics: List[str],
        subject_name: str
    ) -> str:
        """Build the LLM prompt for content extraction"""

        subtopics_list = '\n'.join([f"  {i+1}. {title}" for i, title in enumerate(subtopics)])

        prompt = f"""You are an expert textbook content extractor. Your task is to extract specific subtopic content from a textbook chapter.

## Subject: {subject_name}
## Chapter: {chapter_title}

## Subtopics to Extract:
{subtopics_list}

## Chapter Content (Markdown):
{chapter_markdown}

## Your Task:
Extract the COMPLETE content for each subtopic listed above from the chapter content.

## CRITICAL Instructions:
1. Extract the FULL original text - do NOT summarize or shorten
2. Include ALL text, examples, diagrams references, tables, formulas, and exercises
3. Each subtopic's content should start from its title/heading and end where the next subtopic begins
4. If a subtopic cannot be found in the content, set "found" to false
5. If the content appears incomplete or truncated, set "complete" to false
6. Preserve markdown formatting (headers, lists, tables, code blocks)

## Output Format:
Return ONLY valid JSON (no markdown code blocks, no explanation):
{{
  "extractions": [
    {{
      "subtopic_title": "Exact title from the list above",
      "found": true,
      "complete": true,
      "content": "Full extracted markdown content here...",
      "char_count": 1500,
      "notes": "Any observations about the extraction"
    }}
  ],
  "chapter_summary": {{
    "total_expected": {len(subtopics)},
    "total_found": 5,
    "total_complete": 4,
    "issues": ["List any problems encountered"]
  }}
}}

Extract now:"""

        return prompt

    def _parse_extraction_response(
        self,
        response: str,
        expected_subtopics: List[str]
    ) -> Dict[str, ExtractedSubtopic]:
        """Parse LLM response into ExtractedSubtopic objects"""

        extractions = {}

        try:
            # Try direct JSON parse first
            if response.strip().startswith('{'):
                data = json.loads(response.strip())
            else:
                # Try to extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    raise ValueError("No JSON found in response")

            # Process extractions
            for item in data.get('extractions', []):
                title = item.get('subtopic_title', '')
                content = item.get('content', '')

                extractions[title] = ExtractedSubtopic(
                    title=title,
                    content=content,
                    found=item.get('found', True),
                    complete=item.get('complete', True),
                    char_count=len(content),
                    notes=item.get('notes', '')
                )

            # Check for missing subtopics
            for expected_title in expected_subtopics:
                if expected_title not in extractions:
                    # Try fuzzy match
                    matched = False
                    for title in extractions.keys():
                        if expected_title.lower() in title.lower() or title.lower() in expected_title.lower():
                            # Rename to expected title
                            extractions[expected_title] = extractions.pop(title)
                            matched = True
                            break

                    if not matched:
                        extractions[expected_title] = ExtractedSubtopic(
                            title=expected_title,
                            content="",
                            found=False,
                            complete=False,
                            char_count=0,
                            notes="Not found in LLM extraction"
                        )

        except json.JSONDecodeError as e:
            self._log(f"    JSON parse error: {e}")
            # Return empty extractions with not-found status
            for title in expected_subtopics:
                extractions[title] = ExtractedSubtopic(
                    title=title,
                    content="",
                    found=False,
                    complete=False,
                    char_count=0,
                    notes=f"JSON parse failed: {str(e)[:50]}"
                )

        return extractions

    def extract_chapter_content(
        self,
        chapter_markdown: str,
        chapter_title: str,
        chapter_number: int,
        expected_subtopics: List[str],
        subject_name: str
    ) -> ExtractionResult:
        """
        Extract all subtopics from a chapter using LLM.

        Args:
            chapter_markdown: Raw chapter markdown content
            chapter_title: Chapter title from quality report
            chapter_number: Chapter number
            expected_subtopics: List of subtopic titles to extract
            subject_name: Subject name for context

        Returns:
            ExtractionResult with all extracted subtopics
        """
        self._log(f"\n  Extracting Chapter {chapter_number}: {chapter_title}")
        self._log(f"    Chapter size: {len(chapter_markdown):,} chars")
        self._log(f"    Expected subtopics: {len(expected_subtopics)}")

        result = ExtractionResult(
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            total_expected=len(expected_subtopics)
        )

        if not expected_subtopics:
            self._log(f"    No subtopics to extract, skipping")
            return result

        # Check if chapter is too large - may need chunking
        if len(chapter_markdown) > 100000:
            self._log(f"    WARNING: Large chapter ({len(chapter_markdown):,} chars)")
            self._log(f"    Consider splitting if extraction fails")

        # Build prompt
        prompt = self._build_extraction_prompt(
            chapter_markdown=chapter_markdown,
            chapter_title=chapter_title,
            subtopics=expected_subtopics,
            subject_name=subject_name
        )

        # Make API call with retry
        for attempt in range(1, self.max_retries + 1):
            try:
                self._log(f"    API call attempt {attempt}/{self.max_retries}...")

                api_result = make_api_call(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.MAX_TOKENS,
                    temperature=self.TEMPERATURE,
                    auto_fallback=True
                )

                if api_result.get('success'):
                    response_content = api_result.get('content', '')
                    result.raw_response = response_content

                    # Parse response
                    extractions = self._parse_extraction_response(
                        response_content,
                        expected_subtopics
                    )

                    result.subtopics = extractions
                    result.total_found = sum(1 for e in extractions.values() if e.found)
                    result.total_complete = sum(1 for e in extractions.values() if e.complete)

                    self._log(f"    Extracted: {result.total_found}/{result.total_expected} subtopics")
                    self._log(f"    Complete: {result.total_complete}/{result.total_found}")

                    # Check for issues
                    for title, ext in extractions.items():
                        if not ext.found:
                            result.issues.append(f"Not found: {title}")
                        elif ext.char_count < self.MIN_CONTENT_LENGTH:
                            result.issues.append(f"Too short ({ext.char_count} chars): {title}")
                        elif not ext.complete:
                            result.issues.append(f"Incomplete: {title}")

                    return result

                else:
                    error = api_result.get('error', 'Unknown error')
                    self._log(f"    API error: {error}")

                    if attempt < self.max_retries:
                        self._log(f"    Retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay)

            except Exception as e:
                self._log(f"    Exception: {type(e).__name__}: {e}")

                if attempt < self.max_retries:
                    self._log(f"    Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)

        # All retries failed
        result.issues.append("All API attempts failed")
        for title in expected_subtopics:
            result.subtopics[title] = ExtractedSubtopic(
                title=title,
                content="",
                found=False,
                complete=False,
                notes="API extraction failed"
            )

        return result

    def validate_extraction(
        self,
        extraction: ExtractedSubtopic,
        min_length: int = 200
    ) -> Tuple[bool, List[str]]:
        """
        Validate an extracted subtopic.

        Args:
            extraction: ExtractedSubtopic to validate
            min_length: Minimum acceptable content length

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if not extraction.found:
            issues.append("Content not found")
            return False, issues

        if extraction.char_count < min_length:
            issues.append(f"Content too short: {extraction.char_count} chars (min: {min_length})")

        if not extraction.complete:
            issues.append("Content may be incomplete")

        # Check for obvious problems
        if extraction.content:
            # Check if content looks like wrong chapter (has different chapter header)
            chapter_pattern = r'^#\s+\d+[.\s]'
            if re.search(chapter_pattern, extraction.content, re.MULTILINE):
                # Only flag if it's a different chapter number
                issues.append("May contain content from different chapter")

        is_valid = len(issues) == 0 or (
            extraction.found and
            extraction.char_count >= min_length and
            extraction.complete
        )

        return is_valid, issues


def test_extractor():
    """Test the LLM content extractor"""
    print("Testing LLMContentExtractor...")

    extractor = LLMContentExtractor(verbose=True)

    # Sample chapter content (abbreviated for test)
    sample_chapter = """
# 1 Making measurements

## 1.1 Measuring length and volume

In physics, we make measurements of many different lengths...

## 1.2 Density

The density of a substance is defined as its mass per unit volume...

## 1.3 Measuring time

Time can be measured using a stopwatch or digital timer...
"""

    expected_subtopics = [
        "Measuring length and volume",
        "Density",
        "Measuring time"
    ]

    result = extractor.extract_chapter_content(
        chapter_markdown=sample_chapter,
        chapter_title="Making measurements",
        chapter_number=1,
        expected_subtopics=expected_subtopics,
        subject_name="Physics"
    )

    print(f"\nExtraction Result:")
    print(f"  Found: {result.total_found}/{result.total_expected}")
    print(f"  Complete: {result.total_complete}")
    print(f"  Issues: {result.issues}")


if __name__ == "__main__":
    test_extractor()
