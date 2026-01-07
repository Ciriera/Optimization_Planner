-- Add email column to instructors table
ALTER TABLE instructors ADD COLUMN IF NOT EXISTS email VARCHAR(200);
CREATE INDEX IF NOT EXISTS ix_instructors_email ON instructors(email);

-- Create notificationstatus enum type
DO $$ BEGIN
    CREATE TYPE notificationstatus AS ENUM ('pending', 'success', 'error', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create notification_logs table
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
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_notification_logs_id ON notification_logs(id);
CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_id ON notification_logs(instructor_id);
CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_email ON notification_logs(instructor_email);
CREATE INDEX IF NOT EXISTS ix_notification_logs_status ON notification_logs(status);















