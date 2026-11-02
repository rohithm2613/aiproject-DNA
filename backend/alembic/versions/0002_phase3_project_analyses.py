"""Phase 3: Create project_analyses table for Gemini AI analysis results

Revision ID: 0002_phase3_analyses
Revises: 0001_phase2_auth
Create Date: 2026-10-31 17:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_phase3_analyses'
down_revision: Union[str, None] = '0001_phase2_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'project_analyses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('project_summary', sa.Text(), nullable=False),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('proposed_solution', sa.Text(), nullable=False),
        sa.Column('primary_domain', sa.String(100), nullable=False),
        sa.Column('secondary_domains', sa.JSON(), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=False),
        sa.Column('user_technologies', sa.JSON(), nullable=False),
        sa.Column('recommended_technologies', sa.JSON(), nullable=False),
        sa.Column('objectives', sa.JSON(), nullable=False),
        sa.Column('target_users', sa.JSON(), nullable=False),
        sa.Column('project_type', sa.String(50), nullable=False),
        sa.Column('difficulty_level', sa.String(50), nullable=False),
        sa.Column('difficulty_reasoning', sa.Text(), nullable=False),
        sa.Column('requirements', sa.JSON(), nullable=False),
        sa.Column('assumptions', sa.JSON(), nullable=False),
        sa.Column('risks', sa.JSON(), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('analysis_status', sa.String(50), nullable=False, default='completed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_project_analyses_project_id', 'project_analyses', ['project_id'])
    op.create_index('ix_project_analyses_user_id', 'project_analyses', ['user_id'])

def downgrade() -> None:
    op.drop_index('ix_project_analyses_user_id', table_name='project_analyses')
    op.drop_index('ix_project_analyses_project_id', table_name='project_analyses')
    op.drop_table('project_analyses')

