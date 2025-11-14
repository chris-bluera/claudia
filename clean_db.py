#!/usr/bin/env python3
"""
Clean all Claudia database tables
Truncates all tables to start fresh
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
POSTGRES_USER = os.getenv('POSTGRES_USER', 'claudia')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5433')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'claudia')


async def clean_database():
    """Clean all tables in the claudia schema"""

    # Connect to database
    conn = await asyncpg.connect(
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB
    )

    try:
        print("🧹 Cleaning Claudia database...")

        # Truncate all tables in claudia schema (CASCADE removes dependent rows)
        tables = [
            'claudia.settings_snapshots',
            'claudia.tool_executions',
            'claudia.claude_sessions',
            'claudia.hook_executions',
            'claudia.hook_configs',
            'claudia.conversation_events'
        ]

        for table in tables:
            try:
                await conn.execute(f'TRUNCATE TABLE {table} CASCADE')
                print(f"  ✓ Cleaned {table}")
            except Exception as e:
                print(f"  ⚠ {table}: {e}")

        # Verify cleanup
        session_count = await conn.fetchval('SELECT COUNT(*) FROM claudia.claude_sessions')
        tool_count = await conn.fetchval('SELECT COUNT(*) FROM claudia.tool_executions')

        print(f"\n✅ Database cleaned!")
        print(f"   Sessions: {session_count}")
        print(f"   Tool executions: {tool_count}")

    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(clean_database())
