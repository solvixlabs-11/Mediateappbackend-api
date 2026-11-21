"""w5_settings_audit_limits_mappings

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-20 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. app_settings
    op.create_table(
        'app_settings',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('group', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('value_type', sa.String(length=30), nullable=False),
        sa.Column('unit', sa.String(length=30), nullable=True),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('allowed_options', sa.Text(), nullable=True),
        sa.Column('help_text', sa.String(length=255), nullable=True),
        sa.Column('is_provisional', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('client_uuid', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name='uq_app_settings_key')
    )
    op.create_index('ix_app_settings_key', 'app_settings', ['key'], unique=False)
    op.create_index('ix_app_settings_group', 'app_settings', ['group'], unique=False)

    # 2. geofence_settings
    op.create_table(
        'geofence_settings',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('radius_m', sa.Float(), nullable=False),
        sa.Column('min_accuracy_m', sa.Float(), server_default='50.0', nullable=False),
        sa.Column('is_provisional', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('client_uuid', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entity_type', name='uq_geofence_entity_type')
    )
    op.create_index('ix_geofence_settings_entity_type', 'geofence_settings', ['entity_type'], unique=False)

    # 3. setting_history
    op.create_table(
        'setting_history',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=False),
        sa.Column('changed_by', sa.BigInteger(), nullable=True),
        sa.Column('change_summary', sa.String(length=255), nullable=True),
        sa.Column('client_uuid', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_setting_history_key', 'setting_history', ['key'], unique=False)

    # 4. expense_limits
    op.create_table(
        'expense_limits',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column('designation_id', sa.BigInteger(), nullable=True),
        sa.Column('designation_code', sa.String(length=50), nullable=False),
        sa.Column('expense_type_id', sa.BigInteger(), nullable=True),
        sa.Column('expense_type_code', sa.String(length=50), nullable=False),
        sa.Column('daily_limit', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('monthly_limit', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('is_provisional', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('client_uuid', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('designation_code', 'expense_type_code', 'effective_from', name='uq_exp_limit')
    )
    op.create_index('ix_expense_limits_designation', 'expense_limits', ['designation_code'], unique=False)
    op.create_index('ix_expense_limits_type', 'expense_limits', ['expense_type_code'], unique=False)

    # 5. Extend audit_logs
    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.add_column(sa.Column('module', sa.String(length=50), server_default='SYSTEM', nullable=False))
        batch_op.add_column(sa.Column('channel', sa.String(length=20), server_default='WEB', nullable=False))
        batch_op.add_column(sa.Column('request_id', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('result', sa.String(length=20), server_default='SUCCESS', nullable=False))
        batch_op.add_column(sa.Column('summary', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('before_json', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('after_json', sa.Text(), nullable=True))
        batch_op.create_index('ix_audit_logs_module', ['module'], unique=False)
        batch_op.create_index('ix_audit_logs_created_at', ['created_at'], unique=False)

    # 6. mapping_batches
    op.create_table(
        'mapping_batches',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column('mode', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='DRAFT', nullable=False),
        sa.Column('filters_json', sa.Text(), nullable=True),
        sa.Column('target_employee_id', sa.BigInteger(), nullable=True),
        sa.Column('conflict_policy', sa.String(length=20), server_default='SKIP', nullable=False),
        sa.Column('counts_json', sa.Text(), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reverted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('client_uuid', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mapping_batches_status', 'mapping_batches', ['status'], unique=False)
    op.create_index('ix_mapping_batches_target', 'mapping_batches', ['target_employee_id'], unique=False)

    # 7. mapping_batch_items
    op.create_table(
        'mapping_batch_items',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column('batch_id', sa.BigInteger(), nullable=False),
        sa.Column('action', sa.String(length=30), nullable=False),
        sa.Column('employee_id', sa.BigInteger(), nullable=False),
        sa.Column('territory_id', sa.BigInteger(), nullable=True),
        sa.Column('customer_type', sa.String(length=30), nullable=True),
        sa.Column('customer_id', sa.BigInteger(), nullable=True),
        sa.Column('before_state', sa.Text(), nullable=True),
        sa.Column('after_state', sa.Text(), nullable=True),
        sa.Column('client_uuid', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['batch_id'], ['mapping_batches.id'], ondelete='CASCADE')
    )
    op.create_index('ix_mapping_batch_items_batch_id', 'mapping_batch_items', ['batch_id'], unique=False)
    op.create_index('ix_mapping_batch_items_emp', 'mapping_batch_items', ['employee_id'], unique=False)


def downgrade() -> None:
    op.drop_table('mapping_batch_items')
    op.drop_table('mapping_batches')
    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.drop_column('after_json')
        batch_op.drop_column('before_json')
        batch_op.drop_column('summary')
        batch_op.drop_column('result')
        batch_op.drop_column('request_id')
        batch_op.drop_column('channel')
        batch_op.drop_column('module')
    op.drop_table('expense_limits')
    op.drop_table('setting_history')
    op.drop_table('geofence_settings')
    op.drop_table('app_settings')
