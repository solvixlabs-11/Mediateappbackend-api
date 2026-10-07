"""phase7_targets

Revision ID: a1b2c3d4e5f6
Revises: f8a91b234c5d
Create Date: 2026-10-04 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f8a91b234c5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create targets table for monthly MR performance targets."""
    op.create_table(
        'targets',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('visit_target', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('doctor_call_target', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chemist_call_target', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('primary_sales_target', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.0'),
        sa.Column('secondary_sales_target', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.0'),
        sa.Column('client_uuid', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year', 'month', name='uq_target_user_year_month'),
    )
    op.create_index(op.f('ix_targets_user_id'), 'targets', ['user_id'], unique=False)
    op.create_index(op.f('ix_targets_year'), 'targets', ['year'], unique=False)
    op.create_index(op.f('ix_targets_month'), 'targets', ['month'], unique=False)
    op.create_index(op.f('ix_targets_client_uuid'), 'targets', ['client_uuid'], unique=True)


def downgrade() -> None:
    """Drop targets table."""
    op.drop_index(op.f('ix_targets_client_uuid'), table_name='targets')
    op.drop_index(op.f('ix_targets_month'), table_name='targets')
    op.drop_index(op.f('ix_targets_year'), table_name='targets')
    op.drop_index(op.f('ix_targets_user_id'), table_name='targets')
    op.drop_table('targets')
