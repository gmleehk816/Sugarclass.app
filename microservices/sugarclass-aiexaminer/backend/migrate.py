#!/usr/bin/env python3
"""
Simple migration script to update database schema without Alembic
"""
import asyncio
import sys
import os
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine

async def migrate():
    print("🔄 Running manual migrations for AI Examiner...")
    
    async with engine.begin() as conn:
        # 1. Add collection_id to materials if missing
        try:
            await conn.execute(text("ALTER TABLE materials ADD COLUMN IF NOT EXISTS collection_id VARCHAR"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_materials_collection_id ON materials (collection_id)"))
            print("✅ Added collection_id to materials table")
        except Exception as e:
            print(f"ℹ️ Note on collection_id: {e}")

        # 2. Add session_id to materials if missing (just in case)
        try:
            await conn.execute(text("ALTER TABLE materials ADD COLUMN IF NOT EXISTS session_id VARCHAR"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_materials_session_id ON materials (session_id)"))
            print("✅ Added session_id to materials table")
        except Exception as e:
            print(f"ℹ️ Note on session_id: {e}")

        # 3. Create collections table if it doesn't exist
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS collections (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ Ensured collections table exists")
        except Exception as e:
            print(f"ℹ️ Note on collections table: {e}")

        # 4. Add source_text to quizzes if missing (just in case)
        try:
            await conn.execute(text("ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS source_text VARCHAR"))
            print("✅ Added source_text to quizzes table")
        except Exception as e:
            print(f"ℹ️ Note on source_text: {e}")

        # 5. Add session_id to quizzes if missing
        try:
            await conn.execute(text("ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS session_id VARCHAR"))
            print("✅ Added session_id to quizzes table")
        except Exception as e:
            print(f"ℹ️ Note on quizzes session_id: {e}")

        # 6. Add session_id to progress if missing
        try:
            await conn.execute(text("ALTER TABLE progress ADD COLUMN IF NOT EXISTS session_id VARCHAR"))
            print("✅ Added session_id to progress table")
        except Exception as e:
            print(f"ℹ️ Note on progress session_id: {e}")

    print("🏁 Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
