"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-03-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from app.models.project import ProjectType, ProjectStatus
from app.models.instructor import InstructorType

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create instructor table
    op.create_table(
        'instructor',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.Enum(InstructorType), nullable=False),
        sa.Column('department', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('research_interests', sa.Text(), nullable=True),
        sa.Column('max_project_count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_instructor_email'), 'instructor', ['email'], unique=True)
    op.create_index(op.f('ix_instructor_id'), 'instructor', ['id'], unique=False)

    # Create student table
    op.create_table(
        'student',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('student_number', sa.String(length=20), nullable=False),
        sa.Column('department', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('gpa', sa.Float(), nullable=True),
        sa.Column('interests', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('student_number')
    )
    op.create_index(op.f('ix_student_email'), 'student', ['email'], unique=True)
    op.create_index(op.f('ix_student_id'), 'student', ['id'], unique=False)
    op.create_index(op.f('ix_student_student_number'), 'student', ['student_number'], unique=True)

    # Create project table
    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.Enum(ProjectType), nullable=False),
        sa.Column('status', sa.Enum(ProjectStatus), nullable=False),
        sa.Column('student_capacity', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('advisor_id', sa.Integer(), nullable=False),
        sa.Column('co_advisor_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['advisor_id'], ['instructor.id'], ),
        sa.ForeignKeyConstraint(['co_advisor_id'], ['instructor.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_id'), 'project', ['id'], unique=False)

    # Create keyword table
    op.create_table(
        'keyword',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keyword_id'), 'keyword', ['id'], unique=False)
    op.create_index(op.f('ix_keyword_name'), 'keyword', ['name'], unique=True)

    # Create association tables
    op.create_table(
        'project_student',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
        sa.PrimaryKeyConstraint('project_id', 'student_id')
    )

    op.create_table(
        'project_keyword',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('keyword_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.ForeignKeyConstraint(['keyword_id'], ['keyword.id'], ),
        sa.PrimaryKeyConstraint('project_id', 'keyword_id')
    )

    op.create_table(
        'instructor_keyword',
        sa.Column('instructor_id', sa.Integer(), nullable=False),
        sa.Column('keyword_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['instructor_id'], ['instructor.id'], ),
        sa.ForeignKeyConstraint(['keyword_id'], ['keyword.id'], ),
        sa.PrimaryKeyConstraint('instructor_id', 'keyword_id')
    )

    op.create_table(
        'student_keyword',
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('keyword_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
        sa.ForeignKeyConstraint(['keyword_id'], ['keyword.id'], ),
        sa.PrimaryKeyConstraint('student_id', 'keyword_id')
    )

def downgrade() -> None:
    # Drop association tables
    op.drop_table('student_keyword')
    op.drop_table('instructor_keyword')
    op.drop_table('project_keyword')
    op.drop_table('project_student')

    # Drop main tables
    op.drop_index(op.f('ix_keyword_name'), table_name='keyword')
    op.drop_index(op.f('ix_keyword_id'), table_name='keyword')
    op.drop_table('keyword')

    op.drop_index(op.f('ix_project_id'), table_name='project')
    op.drop_table('project')

    op.drop_index(op.f('ix_student_student_number'), table_name='student')
    op.drop_index(op.f('ix_student_id'), table_name='student')
    op.drop_index(op.f('ix_student_email'), table_name='student')
    op.drop_table('student')

    op.drop_index(op.f('ix_instructor_id'), table_name='instructor')
    op.drop_index(op.f('ix_instructor_email'), table_name='instructor')
    op.drop_table('instructor') 