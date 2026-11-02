"""Phase 2: Users authentication table and project ownership foreign key

Revision ID: 0001_phase2_auth
Revises: 
Create Date: 2026-10-31 17:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_phase2_auth'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('full_name', sa.String(150), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. Add user_id column and index to existing projects table safely
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(36), nullable=True))
        batch_op.create_foreign_key(
            'fk_projects_users_user_id',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_index('ix_projects_user_id', ['user_id'])

def downgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_index('ix_projects_user_id')
        batch_op.drop_constraint('fk_projects_users_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

