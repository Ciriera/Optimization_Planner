"""Add algorithm_runs table

Revision ID: 3dcfa0bc7632
Revises: 6a6042f40ff6
Create Date: 2025-06-29 00:09:37.104589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3dcfa0bc7632'
down_revision: Union[str, None] = '6a6042f40ff6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
