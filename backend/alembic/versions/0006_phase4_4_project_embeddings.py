"""Phase 4.4: Create project_embeddings table for semantic embeddings and vector similarity

Revision ID: 0006_phase4_4_embeddings
Revises: 0005_phase4_3_repo_analysis
Create Date: 2026-11-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.models.project_embedding import VectorType

revision: str = '0006_phase4_4_embeddings'
down_revision: Union[str, None] = '0005_phase4_3_repo_analysis'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # If running on PostgreSQL, enable pgvector extension if available
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        try:
            op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception:
            pass

    op.create_table(
        'project_embeddings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_record_id', sa.String(100), nullable=False),
        sa.Column('embedding', VectorType(384), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id', 'source_type', 'source_record_id', 'model_name', name='uq_project_embedding_source'),
    )
    op.create_index('ix_project_embeddings_project_id', 'project_embeddings', ['project_id'])
    op.create_index('ix_project_embeddings_user_id', 'project_embeddings', ['user_id'])
    op.create_index('ix_project_embeddings_source_type', 'project_embeddings', ['source_type'])
    op.create_index('ix_project_embeddings_source_record_id', 'project_embeddings', ['source_record_id'])
    op.create_index('ix_project_embeddings_model_name', 'project_embeddings', ['model_name'])
    op.create_index('ix_project_embeddings_content_hash', 'project_embeddings', ['content_hash'])

def downgrade() -> None:
    op.drop_table('project_embeddings')

