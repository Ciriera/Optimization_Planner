"""update_instructor_fields

Revision ID: 4a6c3fd8e921
Revises: update_instructor_type
Create Date: 2023-11-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a6c3fd8e921'
down_revision = 'update_instructor_type'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns
    op.add_column('instructors', sa.Column('department', sa.String(), nullable=True))
    op.add_column('instructors', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_instructor_user', 'instructors', 'users', ['user_id'], ['id'])
    
    # Rename 'role' column to 'type'
    op.alter_column('instructors', 'role', new_column_name='type')
    
    # Update existing values to new format
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE instructors 
            SET type = CASE 
                WHEN type = 'hoca' THEN 'instructor' 
                WHEN type = 'aras_gor' THEN 'assistant' 
                WHEN type = 'professor' THEN 'instructor'
                WHEN type = 'research_assistant' THEN 'assistant'
                ELSE 'instructor' 
            END
            """
        )
    )


def downgrade():
    # Rename 'type' column back to 'role'
    op.alter_column('instructors', 'type', new_column_name='role')
    
    # Update values back to old format
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE instructors 
            SET role = CASE 
                WHEN role = 'instructor' THEN 'hoca' 
                WHEN role = 'assistant' THEN 'aras_gor'
                ELSE 'hoca' 
            END
            """
        )
    )
    
    # Drop the new columns
    op.drop_constraint('fk_instructor_user', 'instructors', type_='foreignkey')
    op.drop_column('instructors', 'user_id')
    op.drop_column('instructors', 'department') 