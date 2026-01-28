#!/usr/bin/env python3
"""
Database initialization script for AI Examiner
This script creates all tables in the database
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db

if __name__ == "__main__":
    print("🚀 Initializing AI Examiner Database...")
    try:
        asyncio.run(init_db())
        print("✅ Database initialization complete!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
