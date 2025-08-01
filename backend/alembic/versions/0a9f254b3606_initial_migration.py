"""Initial migration

Revision ID: 0a9f254b3606
Revises: 
Create Date: 2025-06-28 23:55:28.962419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a9f254b3606'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('instructors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('role', sa.String(), nullable=True),
    sa.Column('bitirme_count', sa.Integer(), nullable=True),
    sa.Column('ara_count', sa.Integer(), nullable=True),
    sa.Column('total_load', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_instructors_id'), 'instructors', ['id'], unique=False)
    op.create_index(op.f('ix_instructors_name'), 'instructors', ['name'], unique=False)
    op.create_index(op.f('ix_instructors_role'), 'instructors', ['role'], unique=False)
    op.create_table('projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('is_makeup', sa.Boolean(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('responsible_instructor_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['responsible_instructor_id'], ['instructors.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)
    op.create_index(op.f('ix_projects_title'), 'projects', ['title'], unique=False)
    op.create_index(op.f('ix_projects_type'), 'projects', ['type'], unique=False)
    op.create_table('project_instructor',
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('instructor_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['instructor_id'], ['instructors.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], )
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('project_instructor')
    op.drop_index(op.f('ix_projects_type'), table_name='projects')
    op.drop_index(op.f('ix_projects_title'), table_name='projects')
    op.drop_index(op.f('ix_projects_status'), table_name='projects')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
    op.drop_index(op.f('ix_instructors_role'), table_name='instructors')
    op.drop_index(op.f('ix_instructors_name'), table_name='instructors')
    op.drop_index(op.f('ix_instructors_id'), table_name='instructors')
    op.drop_table('instructors')
    # ### end Alembic commands ###
