"""Update instructor type field to use enum values

Revision ID: 0a9f254b3607
Revises: 0a9f254b3606
Create Date: 2023-07-02 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a9f254b3607'
down_revision = '0a9f254b3606'
branch_labels = None
depends_on = None


def upgrade():
    # Create a temporary mapping table for the conversion
    op.execute("""
    UPDATE instructors
    SET type = 'instructor'
    WHERE type = 'professor'
    """)
    
    op.execute("""
    UPDATE instructors
    SET type = 'assistant'
    WHERE type = 'research_assistant'
    """)


def downgrade():
    # Convert back to the original values
    op.execute("""
    UPDATE instructors
    SET type = 'professor'
    WHERE type = 'instructor'
    """)
    
    op.execute("""
    UPDATE instructors
    SET type = 'research_assistant'
    WHERE type = 'assistant'
    """) 