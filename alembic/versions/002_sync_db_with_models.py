"""Sync database with models

Revision ID: 002
Revises: 001
Create Date: 2025-10-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Database'i model yapisiyla senkronize et.
    """
    
    # ============================================================================
    # INSTRUCTORS TABLOSU GUNCELLEMELERI
    # ============================================================================
    
    # 1. 'role' kolonunu 'type' olarak yeniden adlandir
    op.alter_column('instructors', 'role', new_column_name='type', existing_type=sa.String())
    
    # 2. 'department' kolonunu ekle (nullable)
    op.add_column('instructors', sa.Column('department', sa.String(), nullable=True))
    
    # 3. 'user_id' kolonunu ekle
    op.add_column('instructors', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # 4. user_id foreign key ekle
    op.create_foreign_key(
        'fk_instructors_user_id', 
        'instructors', 
        'users', 
        ['user_id'], 
        ['id']
    )
    
    # ============================================================================
    # PROJECTS TABLOSU GUNCELLEMELERI
    # ============================================================================
    
    # 1. 'responsible_instructor_id' kolonunu 'responsible_id' olarak yeniden adlandir
    op.alter_column('projects', 'responsible_instructor_id', 
                    new_column_name='responsible_id', 
                    existing_type=sa.Integer())
    
    # 2. Eksik kolonlari ekle
    op.add_column('projects', sa.Column('description', sa.String(), nullable=True))
    op.add_column('projects', sa.Column('student_capacity', sa.Integer(), default=1, nullable=True))
    op.add_column('projects', sa.Column('second_participant_id', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('third_participant_id', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('advisor_id', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('co_advisor_id', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('is_active', sa.Boolean(), default=True, nullable=True))
    op.add_column('projects', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('projects', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # 3. Foreign key'leri ekle
    op.create_foreign_key(
        'fk_projects_second_participant_id',
        'projects',
        'instructors',
        ['second_participant_id'],
        ['id']
    )
    
    op.create_foreign_key(
        'fk_projects_third_participant_id',
        'projects',
        'instructors',
        ['third_participant_id'],
        ['id']
    )
    
    op.create_foreign_key(
        'fk_projects_advisor_id',
        'projects',
        'instructors',
        ['advisor_id'],
        ['id']
    )
    
    op.create_foreign_key(
        'fk_projects_co_advisor_id',
        'projects',
        'instructors',
        ['co_advisor_id'],
        ['id']
    )
    
    # 4. Mevcut verilere default degerler ata
    op.execute("""
        UPDATE projects 
        SET student_capacity = 1, 
            is_active = true, 
            created_at = NOW(), 
            updated_at = NOW()
        WHERE student_capacity IS NULL
    """)


def downgrade() -> None:
    """
    Geri alma islemleri.
    """
    
    # Projects tablosu geri alma
    op.drop_constraint('fk_projects_co_advisor_id', 'projects', type_='foreignkey')
    op.drop_constraint('fk_projects_advisor_id', 'projects', type_='foreignkey')
    op.drop_constraint('fk_projects_third_participant_id', 'projects', type_='foreignkey')
    op.drop_constraint('fk_projects_second_participant_id', 'projects', type_='foreignkey')
    
    op.drop_column('projects', 'updated_at')
    op.drop_column('projects', 'created_at')
    op.drop_column('projects', 'is_active')
    op.drop_column('projects', 'co_advisor_id')
    op.drop_column('projects', 'advisor_id')
    op.drop_column('projects', 'third_participant_id')
    op.drop_column('projects', 'second_participant_id')
    op.drop_column('projects', 'student_capacity')
    op.drop_column('projects', 'description')
    
    op.alter_column('projects', 'responsible_id', 
                    new_column_name='responsible_instructor_id', 
                    existing_type=sa.Integer())
    
    # Instructors tablosu geri alma
    op.drop_constraint('fk_instructors_user_id', 'instructors', type_='foreignkey')
    op.drop_column('instructors', 'user_id')
    op.drop_column('instructors', 'department')
    op.alter_column('instructors', 'type', new_column_name='role', existing_type=sa.String())

