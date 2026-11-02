"""Phase 4.3: Create repository_analyses and innovation_gaps tables

Revision ID: 0005_phase4_3_repo_analysis
Revises: 0004_phase4_2_github_repos
Create Date: 2026-11-01 09:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0005_phase4_3_repo_analysis'
down_revision: Union[str, None] = '0004_phase4_2_github_repos'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create repository_analyses table
    op.create_table(
        'repository_analyses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('github_repo_id', sa.String(36), sa.ForeignKey('github_repositories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('repo_full_name', sa.String(255), nullable=False),
        sa.Column('readme_present', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('readme_url', sa.String(500), nullable=True),
        sa.Column('readme_size', sa.Integer(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('problem_statement', sa.Text(), nullable=True),
        sa.Column('detected_technologies', sa.JSON(), nullable=False),
        sa.Column('architecture', sa.JSON(), nullable=False),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('similarity', sa.JSON(), nullable=False),
        sa.Column('analysis_status', sa.String(50), nullable=False, server_default='completed'),
        sa.Column('analysis_mode', sa.String(50), nullable=False, server_default='ai_enhanced'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id', 'github_repo_id', name='uq_project_repo_analysis'),
    )
    op.create_index('ix_repository_analyses_project_id', 'repository_analyses', ['project_id'])
    op.create_index('ix_repository_analyses_github_repo_id', 'repository_analyses', ['github_repo_id'])
    op.create_index('ix_repository_analyses_user_id', 'repository_analyses', ['user_id'])
    op.create_index('ix_repository_analyses_repo_full_name', 'repository_analyses', ['repo_full_name'])
    op.create_index('ix_repository_analyses_analysis_status', 'repository_analyses', ['analysis_status'])

    # 2. Create innovation_gaps table
    op.create_table(
        'innovation_gaps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gap_title', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('why_it_matters', sa.Text(), nullable=False),
        sa.Column('suggested_implementation', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('confidence_level', sa.String(20), nullable=False),
        sa.Column('supporting_evidence', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_innovation_gaps_project_id', 'innovation_gaps', ['project_id'])
    op.create_index('ix_innovation_gaps_user_id', 'innovation_gaps', ['user_id'])
    op.create_index('ix_innovation_gaps_category', 'innovation_gaps', ['category'])
    op.create_index('ix_innovation_gaps_priority', 'innovation_gaps', ['priority'])

def downgrade() -> None:
    op.drop_table('innovation_gaps')
    op.drop_table('repository_analyses')

