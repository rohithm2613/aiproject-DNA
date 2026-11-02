"""Phase 4.6: Create patents table for Patent & Prior-Art Discovery Engine

Revision ID: 0008_phase4_6_patents
Revises: 0007_phase4_5_validation_reports
Create Date: 2026-11-01 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0008_phase4_6_patents'
down_revision: Union[str, None] = '0007_phase4_5_validation_reports'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'patents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('project_analyses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_patent_id', sa.String(255), nullable=False),
        sa.Column('publication_number', sa.String(100), nullable=False),
        sa.Column('application_number', sa.String(100), nullable=True),
        sa.Column('patent_number', sa.String(100), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('claims', sa.JSON(), nullable=False),
        sa.Column('inventors', sa.JSON(), nullable=False),
        sa.Column('assignees', sa.JSON(), nullable=False),
        sa.Column('filing_date', sa.String(50), nullable=True),
        sa.Column('publication_date', sa.String(50), nullable=True),
        sa.Column('grant_date', sa.String(50), nullable=True),
        sa.Column('priority_date', sa.String(50), nullable=True),
        sa.Column('jurisdiction', sa.String(10), nullable=True),
        sa.Column('patent_type', sa.String(50), nullable=True),
        sa.Column('cpc_classifications', sa.JSON(), nullable=False),
        sa.Column('ipc_classifications', sa.JSON(), nullable=False),
        sa.Column('patent_family_id', sa.String(100), nullable=True),
        sa.Column('legal_status', sa.String(50), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('raw_metadata', sa.JSON(), nullable=False),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id', 'publication_number', name='uq_project_patent_publication')
    )
    op.create_index('ix_patents_project_id', 'patents', ['project_id'])
    op.create_index('ix_patents_analysis_id', 'patents', ['analysis_id'])
    op.create_index('ix_patents_user_id', 'patents', ['user_id'])
    op.create_index('ix_patents_provider', 'patents', ['provider'])
    op.create_index('ix_patents_publication_number', 'patents', ['publication_number'])
    op.create_index('ix_patents_jurisdiction', 'patents', ['jurisdiction'])

def downgrade() -> None:
    op.drop_index('ix_patents_jurisdiction', table_name='patents')
    op.drop_index('ix_patents_publication_number', table_name='patents')
    op.drop_index('ix_patents_provider', table_name='patents')
    op.drop_index('ix_patents_user_id', table_name='patents')
    op.drop_index('ix_patents_analysis_id', table_name='patents')
    op.drop_index('ix_patents_project_id', table_name='patents')
    op.drop_table('patents')

