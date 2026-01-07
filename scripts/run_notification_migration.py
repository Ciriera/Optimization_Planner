"""
Script to manually run notification migration.
This adds email column to instructors and creates notification_logs table.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Run notification migration manually"""
    # Create database connection
    database_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        try:
            print("Adding email column to instructors table...")
            conn.execute(text("ALTER TABLE instructors ADD COLUMN IF NOT EXISTS email VARCHAR(200)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_instructors_email ON instructors(email)"))
            
            print("Creating notificationstatus enum type...")
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE notificationstatus AS ENUM ('pending', 'success', 'error', 'failed');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            print("Creating notification_logs table...")
            conn.execute(text("""
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
                    attempt_count INTEGER,
                    meta_data JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_notification_logs_instructor_id FOREIGN KEY (instructor_id) REFERENCES instructors(id)
                )
            """))
            
            print("Creating indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_id ON notification_logs(id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_id ON notification_logs(instructor_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_email ON notification_logs(instructor_email)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_status ON notification_logs(status)"))
            
            # Commit transaction
            trans.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise
    
    engine.dispose()

if __name__ == "__main__":
    run_migration()















