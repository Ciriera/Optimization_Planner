"""
Script to create notification_logs table and related structures.
This script can be run independently to set up the notification logging system.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import async_engine


async def create_notification_logs_table():
    """Create notification_logs table and related structures."""
    try:
        async with async_engine.begin() as conn:
            print("Creating notificationstatus enum type...")
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE notificationstatus AS ENUM ('pending', 'success', 'error', 'failed');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            print("✓ Enum type created or already exists")
            
            print("Creating notification_logs table...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS notification_logs (
                    id SERIAL PRIMARY KEY,
                    instructor_id INTEGER NOT NULL,
                    instructor_email VARCHAR(200) NOT NULL,
                    instructor_name VARCHAR(200),
                    planner_timestamp TIMESTAMP,
                    subject VARCHAR(500),
                    status notificationstatus NOT NULL,
                    error_message TEXT,
                    sent_at TIMESTAMP,
                    attempt_count INTEGER DEFAULT 0,
                    meta_data JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_notification_logs_instructor_id FOREIGN KEY (instructor_id) REFERENCES instructors(id)
                )
            """))
            print("✓ Table created or already exists")
            
            print("Creating indexes...")
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_id ON notification_logs(id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_id ON notification_logs(instructor_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_email ON notification_logs(instructor_email)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_status ON notification_logs(status)"))
            print("✓ Indexes created or already exist")
            
            # Check if email column exists in instructors table
            print("Checking instructors.email column...")
            await conn.execute(text("ALTER TABLE instructors ADD COLUMN IF NOT EXISTS email VARCHAR(200)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_instructors_email ON instructors(email)"))
            print("✓ Email column added or already exists")
            
            print("\n✅ Migration completed successfully!")
            print("The notification_logs table is now ready to use.")
            
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Notification Logs Table Migration Script")
    print("=" * 60)
    print()
    
    success = asyncio.run(create_notification_logs_table())
    
    if success:
        print("\n✅ All done! You can now use the notification logging system.")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)

