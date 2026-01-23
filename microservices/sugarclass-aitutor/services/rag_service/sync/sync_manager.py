"""
Sync Manager for tracking synchronization between database and Qdrant.
This module provides functionality to check sync status and manually trigger syncs.
"""

import os
import hashlib
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


class SyncManager:
    """
    Manages synchronization between PostgreSQL database and Qdrant vector store.
    Tracks which files have been ingested and provides sync status reporting.
    """
    
    def __init__(
        self,
        db_url: str,
        qdrant_url: str,
        qdrant_collection: str = "aitutor_documents",
        materials_path: str = "/app/materials"
    ):
        """
        Initialize the Sync Manager.
        
        Args:
            db_url: PostgreSQL connection URL
            qdrant_url: Qdrant server URL
            qdrant_collection: Qdrant collection name
            materials_path: Path to materials directory
        """
        self.db_url = db_url
        self.qdrant_url = qdrant_url
        self.qdrant_collection = qdrant_collection
        self.materials_path = materials_path
        
        # Initialize clients
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self._db_connection = None
        
    def _get_db_connection(self):
        """Get or create database connection."""
        if self._db_connection is None or self._db_connection.closed:
            self._db_connection = psycopg2.connect(self.db_url)
        return self._db_connection
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def _get_file_info(self, file_path: str) -> Dict:
        """
        Get file information including hash, size, and modification time.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            return {
                "file_path": file_path,
                "file_hash": self._get_file_hash(file_path),
                "file_size": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime)
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    def get_sync_status(self) -> Dict:
        """
        Get current sync status between database and Qdrant.
        
        Returns:
            Dictionary containing sync status information
        """
        result = {
            "database_status": {},
            "qdrant_status": {},
            "sync_status": {},
            "files_status": []
        }
        
        try:
            # Get database status
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Count tracked files
            cursor.execute("SELECT COUNT(*) as total FROM sync_status")
            result["database_status"]["total_tracked_files"] = cursor.fetchone()["total"]
            
            # Count synced files
            cursor.execute("SELECT COUNT(*) as synced FROM sync_status WHERE sync_status = 'synced'")
            result["database_status"]["synced_files"] = cursor.fetchone()["synced"]
            
            # Count failed files
            cursor.execute("SELECT COUNT(*) as failed FROM sync_status WHERE sync_status = 'failed'")
            result["database_status"]["failed_files"] = cursor.fetchone()["failed"]
            
            # Get Qdrant collection status
            collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
            result["qdrant_status"]["collection_name"] = self.qdrant_collection
            result["qdrant_status"]["total_points"] = collection_info.points_count
            result["qdrant_status"]["indexed_points"] = collection_info.indexed_vectors_count
            
            # Get database collection status
            cursor.execute(
                "SELECT * FROM qdrant_collection_status WHERE collection_name = %s",
                (self.qdrant_collection,)
            )
            collection_status = cursor.fetchone()
            
            if collection_status:
                result["database_status"]["qdrant_point_count"] = collection_status["point_count"]
                result["database_status"]["last_synced"] = collection_status["last_synced"].isoformat() if collection_status["last_synced"] else None
            
            # Determine sync status
            db_points = result["database_status"].get("qdrant_point_count", 0)
            qdrant_points = result["qdrant_status"]["total_points"]
            
            if db_points == qdrant_points:
                result["sync_status"]["status"] = "synced"
                result["sync_status"]["message"] = "Database and Qdrant are in sync"
            else:
                result["sync_status"]["status"] = "out_of_sync"
                result["sync_status"]["message"] = f"Database: {db_points} points, Qdrant: {qdrant_points} points"
                result["sync_status"]["difference"] = qdrant_points - db_points
            
            # Get recent sync events
            cursor.execute("""
                SELECT * FROM sync_events 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            result["sync_status"]["recent_events"] = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            result["error"] = str(e)
        
        return result
    
    def check_files_sync(self, file_paths: Optional[List[str]] = None) -> Dict:
        """
        Check sync status for specific files or all files in materials path.
        
        Args:
            file_paths: Optional list of specific files to check. If None, scans all files.
            
        Returns:
            Dictionary with file sync status
        """
        result = {
            "total_files_checked": 0,
            "synced_files": [],
            "modified_files": [],
            "new_files": [],
            "missing_files": [],
            "error_files": []
        }
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all tracked files from database
            cursor.execute("SELECT file_path, file_hash, last_modified FROM sync_status")
            tracked_files = {row["file_path"]: row for row in cursor.fetchall()}
            
            # Determine which files to check
            files_to_check = []
            
            if file_paths:
                # Check specific files
                for fp in file_paths:
                    full_path = os.path.join(self.materials_path, fp)
                    if os.path.exists(full_path):
                        files_to_check.append(full_path)
            else:
                # Scan all files in materials path
                for root, _, files in os.walk(self.materials_path):
                    for file in files:
                        if file.endswith(('.pdf', '.txt', '.md', '.docx')):
                            files_to_check.append(os.path.join(root, file))
            
            result["total_files_checked"] = len(files_to_check)
            
            # Check each file
            for file_path in files_to_check:
                try:
                    # Get current file info
                    file_info = self._get_file_info(file_path)
                    
                    if not file_info:
                        result["error_files"].append({
                            "file_path": file_path,
                            "error": "Could not get file info"
                        })
                        continue
                    
                    # Check if file is tracked
                    if file_path in tracked_files:
                        tracked_file = tracked_files[file_path]
                        
                        # Check if file has been modified
                        if tracked_file["file_hash"] != file_info["file_hash"]:
                            result["modified_files"].append({
                                "file_path": file_path,
                                "last_tracked": tracked_file["last_modified"].isoformat(),
                                "current_modified": file_info["last_modified"].isoformat(),
                                "needs_sync": True
                            })
                        else:
                            result["synced_files"].append({
                                "file_path": file_path,
                                "last_synced": tracked_file["last_modified"].isoformat()
                            })
                    else:
                        # New file
                        result["new_files"].append({
                            "file_path": file_path,
                            "file_size": file_info["file_size"],
                            "last_modified": file_info["last_modified"].isoformat(),
                            "needs_sync": True
                        })
                        
                except Exception as e:
                    logger.error(f"Error checking file {file_path}: {e}")
                    result["error_files"].append({
                        "file_path": file_path,
                        "error": str(e)
                    })
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error checking files sync: {e}")
            result["error"] = str(e)
        
        return result
    
    def get_sync_events(
        self,
        limit: int = 50,
        event_type: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> List[Dict]:
        """
        Get sync events from the database.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            file_path: Filter by file path
            
        Returns:
            List of sync events
        """
        events = []
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM sync_events WHERE 1=1"
            params = []
            
            if event_type:
                query += " AND event_type = %s"
                params.append(event_type)
            
            if file_path:
                query += " AND file_path = %s"
                params.append(file_path)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            events = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error getting sync events: {e}")
        
        return events
    
    def update_qdrant_status(self):
        """
        Update Qdrant collection status in database.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Get current Qdrant collection info
            collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
            
            # Update database
            cursor.execute("""
                INSERT INTO qdrant_collection_status 
                (collection_name, point_count, indexed_count, last_synced)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (collection_name) 
                DO UPDATE SET 
                    point_count = EXCLUDED.point_count,
                    indexed_count = EXCLUDED.indexed_count,
                    last_synced = NOW(),
                    updated_at = NOW()
            """, (
                self.qdrant_collection,
                collection_info.points_count,
                collection_info.indexed_vectors_count
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated Qdrant status: {collection_info.points_count} points")
            
        except Exception as e:
            logger.error(f"Error updating Qdrant status: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self._db_connection and not self._db_connection.closed:
            self._db_connection.close()
            self._db_connection = None
