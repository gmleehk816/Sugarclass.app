"""
Automated Data Synchronization Agent

A LangChain-based autonomous agent that:
1. Monitors SQLite database for changes
2. Automatically migrates new content to PostgreSQL
3. Syncs updated content to Qdrant vector database
4. Maintains consistency across all data stores

This agent runs continuously as a background service.
"""

import asyncio
import logging
import os
import time
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.tools import tool as lc_tool
    from langchain_core.messages import SystemMessage
    AgentExecutor_available = True
except ImportError:
    AgentExecutor = None
    create_tool_calling_agent = None
    ChatPromptTemplate = None
    MessagesPlaceholder = None
    SystemMessage = None
    lc_tool = None
    AgentExecutor_available = False

# Create a simple decorator wrapper if langchain not available
class tool:
    """Simple decorator wrapper for tools when LangChain is not available."""
    def __init__(self, func):
        self.func = func
        
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
        
    def __getattr__(self, name):
        return getattr(self.func, name)

import sqlite3
import asyncpg
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================
# Tools for the Data Sync Agent
# ============================================

@tool
def detect_sqlite_changes() -> str:
    """
    Detect if SQLite database has been modified since last check.
    
    Returns:
        JSON string with change status and file metadata.
    """
    sqlite_db_path = os.getenv(
        "SQLITE_SOURCE_PATH",
        os.path.join(os.getenv("CONTENT_SOURCE_PATH", ""), "rag_content.db")
    )
    
    if not os.path.exists(sqlite_db_path):
        return json.dumps({
            "status": "error",
            "message": f"SQLite database not found at {sqlite_db_path}"
        })
    
    # Get file modification time
    mtime = os.path.getmtime(sqlite_db_path)
    mtime_str = datetime.fromtimestamp(mtime).isoformat()
    
    # Calculate file hash for content comparison
    file_hash = hashlib.md5()
    with open(sqlite_db_path, 'rb') as f:
        file_hash.update(f.read())
    
    # Check last processed hash (stored in writable tmp directory)
    import tempfile
    hash_dir = tempfile.gettempdir()
    hash_file = os.path.join(hash_dir, f"rag_content_{hashlib.md5(sqlite_db_path.encode()).hexdigest()}.last_hash")
    
    if not os.path.exists(hash_file):
        # First run or hash file missing
        with open(hash_file, 'w') as f:
            f.write(file_hash.hexdigest())
        
        return json.dumps({
            "status": "new",
            "message": "First run - will process all content",
            "file_hash": file_hash.hexdigest(),
            "last_modified": mtime_str
        })
    
    # Read last processed hash
    with open(hash_file, 'r') as f:
        last_hash = f.read().strip()
    
    # Compare hashes
    current_hash = file_hash.hexdigest()
    
    if current_hash != last_hash:
        # Database has changed
        with open(hash_file, 'w') as f:
            f.write(current_hash)
        
        return json.dumps({
            "status": "changed",
            "message": "SQLite database has been modified",
            "file_hash": current_hash,
            "last_modified": mtime_str,
            "previous_hash": last_hash
        })
    
    return json.dumps({
        "status": "unchanged",
        "message": "No changes detected",
        "file_hash": current_hash,
        "last_modified": mtime_str
    })


@tool
async def run_migration() -> str:
    """
    Migrate new content from SQLite to PostgreSQL.
    
    Returns:
        JSON string with migration results (records migrated, errors).
    """
    try:
        # Import from project root
        import importlib.util
        import sys
        
        # Load the migration module from project root
        spec = importlib.util.spec_from_file_location(
            "migrate_sqlite_to_postgres",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                         "migrate_sqlite_to_postgres.py")
        )
        migrate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migrate_module)
        
        # Run migration directly (already async)
        result = await migrate_module.migrate_data()
        
        return json.dumps({
            "status": "success",
            "message": "Migration completed successfully",
            "records_migrated": 0,  # The function doesn't return this
            "errors": 0
        })
    
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Migration failed: {str(e)}"
        })


@tool
async def sync_to_vector_db() -> str:
    """
    Sync PostgreSQL content to Qdrant vector database.
    
    Returns:
        JSON string with sync results (chunks synced, time taken).
    """
    try:
        # Use the existing vector store sync
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "vector_store_sync",
            os.path.join(os.path.dirname(__file__), '..', 'database', 'vector_store_sync.py')
        )
        vector_store_sync = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vector_store_sync)
        VectorStoreSync = vector_store_sync.VectorStoreSync
        
        # Run in asyncio (already in async context)
        async def sync():
            content_db_url = os.getenv(
                "CONTENT_DB_URL",
                "postgresql://tutor:tutor_content_pass@localhost:5433/tutor_content"
            )
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            collection_name = os.getenv("QDRANT_COLLECTION", "aitutor_documents")
            
            # Load embedding model
            embedding_model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
            embedding_model = SentenceTransformer(embedding_model_name)
            
            # Initialize sync service
            sync_service = VectorStoreSync(
                content_db_url=content_db_url,
                qdrant_url=qdrant_url,
                collection_name=collection_name,
                embedding_model=embedding_model,
                embedding_dim=int(os.getenv("EMBEDDING_DIM", "384")),
                chunk_size=1000,
                chunk_overlap=200
            )
            
            await sync_service.connect()
            
            # Get stats before
            stats_before = await sync_service.get_statistics()
            
            # Sync only new/changed records (not force rebuild)
            stats = await sync_service.sync_embeddings(force_rebuild=False, batch_size=50)
            
            # Get stats after
            stats_after = await sync_service.get_statistics()
            
            await sync_service.close()
            
            return {
                "status": "success",
                "message": "Vector sync completed",
                "documents_processed": stats['processed'],
                "new_chunks": stats['new'],
                "chunks_created": stats['chunks_created'],
                "errors": stats['errors'],
                "qdrant_points_before": stats_before['points_count'],
                "qdrant_points_after": stats_after['points_count']
            }
        
        result = await sync()
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Vector sync error: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Vector sync failed: {str(e)}"
        })


@tool
async def check_sync_status() -> str:
    """
    Check the current synchronization status across all systems.
    
    Returns:
        JSON string with status of SQLite, PostgreSQL, Qdrant, and Redis.
    """
    try:
        # SQLite status
        sqlite_db_path = os.getenv(
            "SQLITE_SOURCE_PATH",
            os.path.join(os.getenv("CONTENT_SOURCE_PATH", ""), "rag_content.db")
        )
        sqlite_status = {
            "exists": os.path.exists(sqlite_db_path),
            "path": sqlite_db_path
        }
        
        if sqlite_status["exists"]:
            try:
                conn = sqlite3.connect(sqlite_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM content_raw")
                sqlite_record_count = cursor.fetchone()[0]
                conn.close()
                sqlite_status["record_count"] = sqlite_record_count
            except Exception as e:
                logger.warning(f"Could not query SQLite: {e}")
                sqlite_status["record_count"] = 0
        
        # PostgreSQL status - use async properly
        content_db_url = os.getenv(
            "CONTENT_DB_URL",
            "postgresql://tutor:tutor_content_pass@localhost:5433/tutor_content"
        )
        
        try:
            conn = await asyncpg.connect(content_db_url)
            postgres_count = await conn.fetchval("SELECT COUNT(*) FROM syllabus_hierarchy")
            await conn.close()
            postgres_status = {
                "connected": True,
                "record_count": postgres_count
            }
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
            postgres_status = {
                "connected": False,
                "record_count": 0
            }
        
        # Qdrant status
        qdrant_status = {
            "connected": False,
            "points_count": 0,
            "collection": "unknown"
        }
        
        try:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            collection_name = os.getenv("QDRANT_COLLECTION", "aitutor_documents")
            
            client = QdrantClient(url=qdrant_url)
            collection_info = client.get_collection(collection_name)
            qdrant_status = {
                "connected": True,
                "points_count": collection_info.points_count,
                "collection": collection_name
            }
        except Exception as e:
            logger.error(f"Qdrant connection error: {e}")
        
        # Redis status
        redis_status = {
            "connected": False,
            "db_size": 0
        }
        
        try:
            import redis
            redis_host = os.getenv("REDIS_HOST", "tutor-redis")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            redis_status = {
                "connected": r.ping(),
                "db_size": r.dbsize()
            }
        except Exception as e:
            logger.warning(f"Redis connection error: {e}")
        
        # Calculate sync status
        sync_percentage = 0
        if postgres_status.get("connected") and qdrant_status.get("connected"):
            # Assume ~3 chunks per record
            sync_percentage = (qdrant_status["points_count"] / max(1, postgres_count * 3)) * 100
        
        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "sqlite": sqlite_status,
            "postgresql": postgres_status,
            "qdrant": qdrant_status,
            "redis": redis_status,
            "sync_percentage": min(100, round(sync_percentage, 2)),
            "overall_status": "synced" if sync_percentage >= 90 else "out_of_sync"
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Status check failed: {str(e)}"
        })


# ============================================
# Data Sync Agent
# ============================================

class DataSyncAgent:
    """
    Autonomous agent for data synchronization.
    Monitors SQLite and maintains consistency across PostgreSQL, Qdrant, and Redis.
    """
    
    def __init__(self, llm):
        """
        Initialize the data sync agent.
        
        Args:
            llm: Language model for decision making
        """
        self.llm = llm
        self.check_interval = int(os.getenv("SYNC_CHECK_INTERVAL", "60"))  # seconds
        self.running = False
        self.agent_executor = None
        
        # Build agent
        if AgentExecutor and create_tool_calling_agent:
            self._build_agent()
        else:
            logger.warning("LangChain agent components not available, using manual sync")
    
    def _build_agent(self):
        """Build the LangChain agent executor."""
        tools = [detect_sqlite_changes, run_migration, sync_to_vector_db, check_sync_status]
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an automated data synchronization agent. Your job is to:

1. Monitor the SQLite database for changes
2. Automatically migrate new content to PostgreSQL
3. Sync updated content to Qdrant vector database
4. Report status and handle errors gracefully

When you detect changes:
1. Check if SQLite has been updated
2. Run migration to PostgreSQL
3. Sync new content to Qdrant
4. Verify all systems are in sync

Be efficient and silent when everything is in sync. Only report when action is taken or errors occur."""),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
        ])
        
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5
        )
        logger.info("Data sync agent initialized")
    
    async def run_cycle(self) -> bool:
        """
        Run one synchronization cycle.
        
        Returns:
            True if sync was performed, False if no changes detected.
        """
        try:
            # Update healthcheck file
            import tempfile
            healthcheck_file = os.path.join(tempfile.gettempdir(), "sync_agent_health")
            with open(healthcheck_file, 'w') as f:
                f.write(f"{datetime.now().isoformat()}\n")

            if self.agent_executor:
                # Use LangChain agent
                result = await self.agent_executor.ainvoke({
                    "input": "Check for database changes and sync if necessary",
                    "chat_history": []
                })
                logger.info(f"Agent cycle completed: {result['output'][:100]}")
                return True
            else:
                # Manual sync workflow
                # 1. Check for changes first
                change_result = json.loads(detect_sqlite_changes())
                
                if change_result["status"] == "unchanged":
                    # No changes detected, skip sync
                    logger.debug(f"No changes detected in SQLite database")
                    return False
                
                logger.info(f"Changes detected: {change_result['message']}")
                    
                # 2. Run migration
                logger.info("Running migration...")
                migration_result = json.loads(await run_migration())
                logger.info(f"Migration: {migration_result['message']}")
                
                if migration_result["status"] == "success":
                    # 3. Sync to vector DB
                    logger.info("Syncing to vector database...")
                    sync_result = json.loads(await sync_to_vector_db())
                    logger.info(f"Sync: {sync_result['message']}")
                
                # 4. Check status
                status_result = await check_sync_status()
                logger.info(f"Sync status: {status_result['sync_percentage']}% - {status_result['overall_status']}")
                return True
        
        except Exception as e:
            logger.error(f"Sync cycle error: {e}")
            return False
    
    async def start(self):
        """Start the continuous sync agent."""
        self.running = True
        interval_hours = self.check_interval / 3600
        logger.info(f"Starting data sync agent (check interval: {self.check_interval}s = {interval_hours:.1f} hours)")
        
        # Create healthcheck file path
        import tempfile
        healthcheck_file = os.path.join(tempfile.gettempdir(), "sync_agent_health")
        
        while self.running:
            try:
                # Run sync cycle (updates healthcheck file)
                synced = await self.run_cycle()
                
                if synced:
                    logger.info(f"Sync completed. Sleeping for {interval_hours:.1f} hours until next check...")
                else:
                    logger.info(f"No changes. Sleeping for {interval_hours:.1f} hours until next check...")
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("Sync agent stopped")
                break
            except Exception as e:
                logger.error(f"Sync agent error: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the sync agent."""
        self.running = False
        logger.info("Stopping data sync agent")


# ============================================
# SQLite File Watcher (Alternative to Polling)
# ============================================

class SQLiteFileWatcher(FileSystemEventHandler):
    """Watch for SQLite file modifications."""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = 0
    
    def on_modified(self, event):
        """Handle file modification event."""
        if event.is_directory:
            return
        
        if not event.src_path.endswith('.db'):
            return
        
        # Debounce - only trigger if last modification was > 1 second ago
        current_time = time.time()
        if current_time - self.last_modified > 1:
            logger.info(f"SQLite database modified: {event.src_path}")
            self.last_modified = current_time
            self.callback()


async def start_file_watcher(callback):
    """Start file system watcher for SQLite database."""
    sqlite_path = os.getenv(
        "CONTENT_SOURCE_PATH",
        "C:/Users/gmhome/SynologyDrive/coding/tutorrag/database"
    )
    
    observer = Observer()
    watcher = SQLiteFileWatcher(callback)
    observer.schedule(watcher, sqlite_path, recursive=False)
    observer.start()
    
    logger.info(f"File watcher started for {sqlite_path}")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()


# ============================================
# Main Entry Point
# ============================================

async def main():
    """Main entry point for the data sync agent."""
    logger.info("=" * 70)
    logger.info("AUTOMATED DATA SYNC AGENT")
    logger.info("=" * 70)
    
    # Initialize LLM
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    
    try:
        if llm_provider == "openai_compatible":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("LLM_API_KEY"),
                base_url=os.getenv("LLM_API_BASE"),
                temperature=0
            )
        else:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0
            )
        
        logger.info(f"LLM initialized: {os.getenv('LLM_MODEL')}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        logger.info("Using manual sync mode (no LLM)")
        llm = None
    
    # Create agent
    agent = DataSyncAgent(llm)
    
    # Run initial sync
    logger.info("Running initial sync...")
    await agent.run_cycle()
    
    # Start continuous sync
    await agent.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Data sync agent stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
