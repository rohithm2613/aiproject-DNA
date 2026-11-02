"""Phase 4.1: Create research_papers table for multi-provider academic discovery

Revision ID: 0003_phase4_1_research_papers
Revises: 0002_phase3_analyses
Create Date: 2026-11-01 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0003_phase4_1_research_papers'
down_revision: Union[str, None] = '0002_phase3_analyses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'research_papers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('project_analyses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_paper_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('authors', sa.JSON(), nullable=False),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('publication_date', sa.String(50), nullable=True),
        sa.Column('venue', sa.String(255), nullable=True),
        sa.Column('doi', sa.String(255), nullable=True),
        sa.Column('arxiv_id', sa.String(100), nullable=True),
        sa.Column('citation_count', sa.Integer(), nullable=True),
        sa.Column('paper_url', sa.String(500), nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('open_access', sa.Boolean(), nullable=True),
        sa.Column('primary_category', sa.String(100), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id', 'provider', 'provider_paper_id', name='uq_project_provider_paper')
    )
    op.create_index('ix_research_papers_project_id', 'research_papers', ['project_id'])
    op.create_index('ix_research_papers_analysis_id', 'research_papers', ['analysis_id'])
    op.create_index('ix_research_papers_user_id', 'research_papers', ['user_id'])
    op.create_index('ix_research_papers_provider', 'research_papers', ['provider'])
    op.create_index('ix_research_papers_doi', 'research_papers', ['doi'])

def downgrade() -> None:
    op.drop_index('ix_research_papers_doi', table_name='research_papers')
    op.drop_index('ix_research_papers_provider', table_name='research_papers')
    op.drop_index('ix_research_papers_user_id', table_name='research_papers')
    op.drop_index('ix_research_papers_analysis_id', table_name='research_papers')
    op.drop_index('ix_research_papers_project_id', table_name='research_papers')
    op.drop_table('research_papers')

