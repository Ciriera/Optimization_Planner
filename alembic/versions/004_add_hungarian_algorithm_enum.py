"""Add hungarian to algorithmtype enum

Revision ID: 004
Revises: 003
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add 'hungarian' value to algorithmtype enum in PostgreSQL.
    """
    # Check if we're using PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Check if the enum value already exists to avoid errors
        result = bind.execute(text("""
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'hungarian' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'algorithmtype')
        """)).fetchone()
        
        if not result:
            # ALTER TYPE ... ADD VALUE commits immediately in PostgreSQL
            # This is handled correctly by Alembic
            op.execute("ALTER TYPE algorithmtype ADD VALUE 'hungarian'")
    # For other databases (SQLite, etc.), enum values are stored as strings,
    # so no migration needed - the new values will be available when the application starts


def downgrade() -> None:
    """
    Note: PostgreSQL does not support removing enum values easily.
    This is a no-op as removing enum values requires recreating the enum type
    and all dependent tables, which is not recommended in production.
    """
    # PostgreSQL enum values cannot be easily removed
    # This would require:
    # 1. Creating a new enum without the value
    # 2. Altering all columns using the enum to use the new type
    # 3. Dropping the old enum
    # This is complex and risky, so we leave it as a no-op
    pass

