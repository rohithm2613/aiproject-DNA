"""Phase 4.5: Create project_validation_reports table for RAG validation engine

Revision ID: 0007_phase4_5_validation_reports
Revises: 0006_phase4_4_embeddings
Create Date: 2026-11-01 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0007_phase4_5_validation_reports'
down_revision: Union[str, None] = '0006_phase4_4_embeddings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'project_validation_reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('project_analyses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('report_status', sa.String(50), nullable=False, server_default='completed'),
        sa.Column('report_json', sa.JSON(), nullable=False),
        sa.Column('evidence_manifest', sa.JSON(), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False, server_default='gemini-2.5-flash'),
        sa.Column('retrieval_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_project_validation_reports_project_id', 'project_validation_reports', ['project_id'])
    op.create_index('ix_project_validation_reports_analysis_id', 'project_validation_reports', ['analysis_id'])
    op.create_index('ix_project_validation_reports_user_id', 'project_validation_reports', ['user_id'])
    op.create_index('ix_project_validation_reports_proj_version', 'project_validation_reports', ['project_id', 'version'])

def downgrade() -> None:
    op.drop_index('ix_project_validation_reports_proj_version', table_name='project_validation_reports')
    op.drop_index('ix_project_validation_reports_user_id', table_name='project_validation_reports')
    op.drop_index('ix_project_validation_reports_analysis_id', table_name='project_validation_reports')
    op.drop_index('ix_project_validation_reports_project_id', table_name='project_validation_reports')
    op.drop_table('project_validation_reports')

