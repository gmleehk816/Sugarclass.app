"""
Quality Tracker for Ingestion Process

Tracks the quality of raw content ingestion from markdown files to database.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

DB_PATH = str(Path(__file__).parent.parent.parent / 'database' / 'rag_content.db')


class IngestionQualityTracker:
    """Track and manage ingestion quality metrics."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def start_ingestion(self, subtopic_id: str, subject_name: str):
        """Mark ingestion as started."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO ingestion_quality
            (subtopic_id, subject_name, status)
            VALUES (?, ?, 'pending')
        """, (subtopic_id, subject_name))
        conn.commit()
        conn.close()
    
    def record_success(
        self,
        subtopic_id: str,
        content_length: int,
        quality_score: Optional[float] = None,
    ):
        """Record successful ingestion with quality metrics."""
        
        # Calculate quality score if not provided
        if quality_score is None:
            quality_score = self._calculate_ingestion_score(content_length)
        
        # Determine if content is valid
        content_valid = 1 if content_length > 100 else 0
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE ingestion_quality
            SET status = 'ingested',
                ingested_at = datetime('now'),
                quality_score = ?,
                content_length = ?,
                content_valid = ?,
                error_message = NULL
            WHERE subtopic_id = ?
        """, (quality_score, content_length, content_valid, subtopic_id))
        conn.commit()
        conn.close()
    
    def record_failure(self, subtopic_id: str, error_message: str):
        """Record failed ingestion."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE ingestion_quality
            SET status = 'failed',
                ingested_at = datetime('now'),
                quality_score = 0,
                error_message = ?
            WHERE subtopic_id = ?
        """, (error_message, subtopic_id))
        conn.commit()
        conn.close()
    
    def _calculate_ingestion_score(self, content_length: int) -> float:
        """Calculate quality score based on content length."""
        score = 50.0  # Base score for having content
        
        if content_length > 1000:
            score += 20.0
        if content_length > 5000:
            score += 10.0
        if content_length > 10000:
            score += 20.0
        
        return min(score, 100.0)
    
    def get_status(self, subtopic_id: str) -> Optional[Dict]:
        """Get ingestion status for a subtopic."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM ingestion_quality WHERE subtopic_id = ?
        """, (subtopic_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def get_subject_stats(self, subject_name: str) -> Dict:
        """Get ingestion statistics for a subject."""
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'ingested' THEN 1 ELSE 0 END) as ingested,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                AVG(quality_score) as avg_quality,
                AVG(content_length) as avg_length
            FROM ingestion_quality
            WHERE subject_name = ?
        """, (subject_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total': result[0] or 0,
            'ingested': result[1] or 0,
            'failed': result[2] or 0,
            'pending': result[3] or 0,
            'avg_quality': round(result[4] or 0, 1),
            'avg_length': int(result[5] or 0)
        }
    
    def get_problematic_items(self, subject_name: Optional[str] = None, limit: int = 10) -> list:
        """Get items that need review or failed."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        if subject_name:
            cursor = conn.execute("""
                SELECT * FROM ingestion_quality
                WHERE status IN ('failed', 'needs_review') AND subject_name = ?
                ORDER BY quality_score ASC, subtopic_id
                LIMIT ?
            """, (subject_name, limit))
        else:
            cursor = conn.execute("""
                SELECT * FROM ingestion_quality
                WHERE status IN ('failed', 'needs_review')
                ORDER BY quality_score ASC, subtopic_id
                LIMIT ?
            """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results