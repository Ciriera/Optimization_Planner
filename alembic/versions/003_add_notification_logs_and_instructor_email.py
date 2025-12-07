"""Add notification logs table and instructor email field

Revision ID: 003
Revises: 002
Create Date: 2025-11-23 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '97448a6eb206'  # Revises the latest migration that removed email column
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add notification_logs table and email field to instructors table.
    """
    
    # Add email column to instructors table
    op.add_column('instructors', sa.Column('email', sa.String(200), nullable=True))
    op.create_index(op.f('ix_instructors_email'), 'instructors', ['email'], unique=False)
    
    # Create notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instructor_id', sa.Integer(), nullable=False),
        sa.Column('instructor_email', sa.String(200), nullable=False),
        sa.Column('instructor_name', sa.String(200), nullable=True),
        sa.Column('planner_timestamp', sa.DateTime(), nullable=True),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('status', sa.Enum('pending', 'success', 'error', 'failed', name='notificationstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=True),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['instructor_id'], ['instructors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_logs_id'), 'notification_logs', ['id'], unique=False)
    op.create_index(op.f('ix_notification_logs_instructor_id'), 'notification_logs', ['instructor_id'], unique=False)
    op.create_index(op.f('ix_notification_logs_instructor_email'), 'notification_logs', ['instructor_email'], unique=False)
    op.create_index(op.f('ix_notification_logs_status'), 'notification_logs', ['status'], unique=False)


def downgrade() -> None:
    """
    Remove notification_logs table and email field from instructors.
    """
    op.drop_index(op.f('ix_notification_logs_status'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_instructor_email'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_instructor_id'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_id'), table_name='notification_logs')
    op.drop_table('notification_logs')
    
    op.drop_index(op.f('ix_instructors_email'), table_name='instructors')
    op.drop_column('instructors', 'email')
    
    # Drop enum type if it exists
    op.execute("DROP TYPE IF EXISTS notificationstatus")

