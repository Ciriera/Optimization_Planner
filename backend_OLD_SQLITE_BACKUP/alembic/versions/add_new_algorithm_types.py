"""Add new algorithm types

Revision ID: add_new_algorithm_types
Revises: 3dcfa0bc7632
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_new_algorithm_types'
down_revision: Union[str, None] = '3dcfa0bc7632'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new algorithm types to the enum
    # Note: PostgreSQL enum values can be added with:
    # ALTER TYPE algorithmtype ADD VALUE 'hybrid_cpsat_tabu_nsga';
    # ALTER TYPE algorithmtype ADD VALUE 'lexicographic_advanced';
    
    # For SQLite, we need to recreate the table with new enum values
    # This is a simplified approach - in production you'd want to handle this more carefully
    
    # Check if we're using PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # PostgreSQL: Add new enum values
        op.execute("ALTER TYPE algorithmtype ADD VALUE 'hybrid_cpsat_tabu_nsga'")
        op.execute("ALTER TYPE algorithmtype ADD VALUE 'lexicographic_advanced'")
    else:
        # SQLite: Enum values are stored as strings, so no migration needed
        # The new values will be available when the application starts
        pass


def downgrade() -> None:
    # PostgreSQL: Remove enum values (this is complex and not recommended)
    # SQLite: No action needed
    pass
