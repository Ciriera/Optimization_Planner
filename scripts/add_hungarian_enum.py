"""
Script to add 'hungarian' enum value to PostgreSQL algorithmtype enum.
This can be run directly if migrations are having issues.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.config import settings
from app.db.base import engine


async def add_hungarian_enum():
    """Add 'hungarian' value to algorithmtype enum if it doesn't exist."""
    async with engine.begin() as conn:
        # Check if the enum value already exists
        result = await conn.execute(text("""
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'hungarian' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'algorithmtype')
        """))
        
        if result.fetchone():
            print("✓ 'hungarian' enum value already exists in algorithmtype enum")
            return
        
        # Add the enum value
        try:
            await conn.execute(text("ALTER TYPE algorithmtype ADD VALUE IF NOT EXISTS 'hungarian'"))
            print("✓ Successfully added 'hungarian' to algorithmtype enum")
        except Exception as e:
            # IF NOT EXISTS is not available in all PostgreSQL versions
            # Try without it
            try:
                await conn.execute(text("ALTER TYPE algorithmtype ADD VALUE 'hungarian'"))
                print("✓ Successfully added 'hungarian' to algorithmtype enum")
            except Exception as e2:
                if 'already exists' in str(e2).lower() or 'duplicate' in str(e2).lower():
                    print("✓ 'hungarian' enum value already exists (checked via exception)")
                else:
                    print(f"✗ Error adding enum value: {e2}")
                    raise


if __name__ == "__main__":
    print("Adding 'hungarian' to algorithmtype enum...")
    asyncio.run(add_hungarian_enum())

