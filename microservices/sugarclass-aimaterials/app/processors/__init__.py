"""
Processors Module
=================
Pluggable processors for the AI Tutor Knowledge Base.

Available processors:
- ContentBuilder: Enhance markdown with AI-generated images
- ExerciseGenerator: Generate MCQs from content (TODO)
- ExamProcessor: Extract Q&A from exam papers (TODO)
"""

from .content_builder import ContentBuilder, process_folder

__all__ = ['ContentBuilder', 'process_folder']
