"""
Quality Tracker for Rewriting Process

Tracks the quality of HTML content rewriting from raw markdown.
"""

import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

DB_PATH = str(Path(__file__).parent.parent.parent / 'database' / 'rag_content.db')


class RewritingQualityTracker:
    """Track and manage rewriting quality metrics."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def start_rewriting(self, subtopic_id: str, subject_name: str):
        """Mark rewriting as started."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO rewriting_quality
            (subtopic_id, subject_name, status)
            VALUES (?, ?, 'pending')
        """, (subtopic_id, subject_name))
        conn.commit()
        conn.close()
    
    def record_success(
        self,
        subtopic_id: str,
        raw_length: int,
        processed_length: int,
        html_content: str,
        processor_version: str = 'v1.0',
    ):
        """Record successful rewriting with quality metrics."""
        
        # Calculate compression ratio
        compression_ratio = (processed_length / raw_length * 100) if raw_length > 0 else 0
        
        # Analyze HTML content for required features
        features = self._analyze_html_content(html_content)
        
        # Calculate quality score
        quality_score = self._calculate_rewriting_score(
            compression_ratio,
            features
        )
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE rewriting_quality
            SET status = 'rewritten',
                rewritten_at = datetime('now'),
                quality_score = ?,
                raw_length = ?,
                processed_length = ?,
                compression_ratio = ?,
                has_learning_objectives = ?,
                has_key_terms = ?,
                has_questions = ?,
                has_takeaways = ?,
                error_message = NULL,
                processor_version = ?
            WHERE subtopic_id = ?
        """, (
            quality_score,
            raw_length,
            processed_length,
            compression_ratio,
            features['has_learning_objectives'],
            features['has_key_terms'],
            features['has_questions'],
            features['has_takeaways'],
            processor_version,
            subtopic_id
        ))
        conn.commit()
        conn.close()
    
    def record_failure(self, subtopic_id: str, error_message: str):
        """Record failed rewriting."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE rewriting_quality
            SET status = 'failed',
                rewritten_at = datetime('now'),
                quality_score = 0,
                error_message = ?
            WHERE subtopic_id = ?
        """, (error_message, subtopic_id))
        conn.commit()
        conn.close()
    
    def analyze_content_features(self, html_content: str) -> Dict:
        """Analyze HTML content and return feature flags."""
        return self._analyze_html_content(html_content)
    
    def _analyze_html_content(self, html: str) -> Dict:
        """Analyze HTML for required educational features."""
        html_lower = html.lower()
        
        return {
            'has_learning_objectives': any([
                'learning objective' in html_lower,
                'objectives' in html_lower,
                '你将学习' in html_lower,
            ]),
            'has_key_terms': any([
                len(re.findall(r'<span[^>]*key[^>]*', html, re.I)) > 0,
                len(re.findall(r'<strong[^>]*key[^>]*', html, re.I)) > 0,
                'key term' in html_lower,
            ]),
            'has_questions': any([
                len(re.findall(r'think about it', html_lower)) > 0,
                len(re.findall(r'question', html_lower)) > 0,
                '问题' in html_lower,
            ]),
            'has_takeaways': any([
                len(re.findall(r'key takeaway', html_lower)) > 0,
                '总结' in html_lower,
                '要点' in html_lower,
            ])
        }
    
    def _calculate_rewriting_score(self, compression_ratio: float, features: Dict) -> float:
        """Calculate quality score based on multiple factors."""
        score = 30.0  # Base score for having content
        
        # Compression ratio (penalize if too short)
        if compression_ratio > 30:
            score += 10.0
        if compression_ratio > 50:
            score += 10.0
        if compression_ratio < 10:
            score -= 20.0  # Penalize very short content
        
        # Feature presence
        if features['has_learning_objectives']:
            score += 10.0
        if features['has_key_terms']:
            score += 10.0
        if features['has_questions']:
            score += 10.0
        if features['has_takeaways']:
            score += 10.0
        
        return max(0.0, min(score, 100.0))
    
    def get_status(self, subtopic_id: str) -> Optional[Dict]:
        """Get rewriting status for a subtopic."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM rewriting_quality WHERE subtopic_id = ?
        """, (subtopic_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def get_subject_stats(self, subject_name: str) -> Dict:
        """Get rewriting statistics for a subject."""
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'rewritten' THEN 1 ELSE 0 END) as rewritten,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                AVG(quality_score) as avg_quality,
                AVG(raw_length) as avg_raw_length,
                AVG(processed_length) as avg_processed_length,
                AVG(compression_ratio) as avg_compression,
                AVG(has_learning_objectives) as pct_objectives,
                AVG(has_key_terms) as pct_terms,
                AVG(has_questions) as pct_questions,
                AVG(has_takeaways) as pct_takeaways
            FROM rewriting_quality
            WHERE subject_name = ?
        """, (subject_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total': result[0] or 0,
            'rewritten': result[1] or 0,
            'failed': result[2] or 0,
            'pending': result[3] or 0,
            'avg_quality': round(result[4] or 0, 1),
            'avg_raw_length': int(result[5] or 0),
            'avg_processed_length': int(result[6] or 0),
            'avg_compression': round(result[7] or 0, 1),
            'pct_objectives': round((result[8] or 0) * 100, 1),
            'pct_terms': round((result[9] or 0) * 100, 1),
            'pct_questions': round((result[10] or 0) * 100, 1),
            'pct_takeaways': round((result[11] or 0) * 100, 1),
        }
    
    def get_problematic_items(self, subject_name: Optional[str] = None, limit: int = 10) -> list:
        """Get items with low quality or compression issues."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        if subject_name:
            cursor = conn.execute("""
                SELECT * FROM rewriting_quality
                WHERE (status IN ('failed', 'needs_review') OR 
                       quality_score < 50 OR 
                       compression_ratio < 30)
                  AND subject_name = ?
                ORDER BY quality_score ASC, compression_ratio ASC
                LIMIT ?
            """, (subject_name, limit))
        else:
            cursor = conn.execute("""
                SELECT * FROM rewriting_quality
                WHERE status IN ('failed', 'needs_review') OR 
                      quality_score < 50 OR 
                      compression_ratio < 30
                ORDER BY quality_score ASC, compression_ratio ASC
                LIMIT ?
            """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results