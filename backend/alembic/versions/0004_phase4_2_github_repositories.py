"""Phase 4.2: Create github_repositories table for GitHub existing project discovery

Revision ID: 0004_phase4_2_github_repos
Revises: 0003_phase4_1_research_papers
Create Date: 2026-11-01 08:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0004_phase4_2_github_repos'
down_revision: Union[str, None] = '0003_phase4_1_research_papers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'github_repositories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('project_analyses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('github_repository_id', sa.BigInteger(), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('owner_login', sa.String(150), nullable=False),
        sa.Column('owner_type', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('html_url', sa.String(500), nullable=False),
        sa.Column('homepage', sa.String(500), nullable=True),
        sa.Column('language', sa.String(100), nullable=True),
        sa.Column('languages', sa.JSON(), nullable=False),
        sa.Column('topics', sa.JSON(), nullable=False),
        sa.Column('stargazers_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('forks_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('watchers_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('open_issues_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('default_branch', sa.String(100), nullable=True),
        sa.Column('created_at', sa.String(50), nullable=True),
        sa.Column('updated_at', sa.String(50), nullable=True),
        sa.Column('pushed_at', sa.String(50), nullable=True),
        sa.Column('license_name', sa.String(150), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('fork', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('visibility', sa.String(50), nullable=False, server_default='public'),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('search_query', sa.String(255), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at_db', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id', 'github_repository_id', name='uq_project_github_repo')
    )
    op.create_index('ix_github_repositories_project_id', 'github_repositories', ['project_id'])
    op.create_index('ix_github_repositories_analysis_id', 'github_repositories', ['analysis_id'])
    op.create_index('ix_github_repositories_user_id', 'github_repositories', ['user_id'])
    op.create_index('ix_github_repositories_github_repository_id', 'github_repositories', ['github_repository_id'])
    op.create_index('ix_github_repositories_full_name', 'github_repositories', ['full_name'])
    op.create_index('ix_github_repositories_language', 'github_repositories', ['language'])

def downgrade() -> None:
    op.drop_index('ix_github_repositories_language', table_name='github_repositories')
    op.drop_index('ix_github_repositories_full_name', table_name='github_repositories')
    op.drop_index('ix_github_repositories_github_repository_id', table_name='github_repositories')
    op.drop_index('ix_github_repositories_user_id', table_name='github_repositories')
    op.drop_index('ix_github_repositories_analysis_id', table_name='github_repositories')
    op.drop_index('ix_github_repositories_project_id', table_name='github_repositories')
    op.drop_table('github_repositories')

