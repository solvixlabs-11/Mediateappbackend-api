"""phase5_approvals_tours_expenses_leaves

Revision ID: d6f55cc50d2a
Revises: a891f7c2301c
Create Date: 2026-10-02 23:48:26.730265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6f55cc50d2a'
down_revision: Union[str, Sequence[str], None] = 'a891f7c2301c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create Phase 5 Approval, Leave, Expense, and Tour tables."""
    # 1. Approval Requests
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False),
        sa.Column('total_steps', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_requests_entity_id'), 'approval_requests', ['entity_id'], unique=False)
    op.create_index(op.f('ix_approval_requests_entity_type'), 'approval_requests', ['entity_type'], unique=False)
    op.create_index(op.f('ix_approval_requests_id'), 'approval_requests', ['id'], unique=False)
    op.create_index(op.f('ix_approval_requests_requester_id'), 'approval_requests', ['requester_id'], unique=False)
    op.create_index(op.f('ix_approval_requests_status'), 'approval_requests', ['status'], unique=False)

    # 2. Approval History (NO ACTION to prevent SQL Server multiple cascade path error 1785)
    op.create_table(
        'approval_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('approver_id', sa.BigInteger(), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ondelete='NO ACTION'),
        sa.ForeignKeyConstraint(['request_id'], ['approval_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_history_approver_id'), 'approval_history', ['approver_id'], unique=False)
    op.create_index(op.f('ix_approval_history_id'), 'approval_history', ['id'], unique=False)
    op.create_index(op.f('ix_approval_history_request_id'), 'approval_history', ['request_id'], unique=False)

    # 3. Leave Balances
    op.create_table(
        'leave_balances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('casual_leave_balance', sa.Float(), nullable=False),
        sa.Column('sick_leave_balance', sa.Float(), nullable=False),
        sa.Column('earned_leave_balance', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leave_balances_id'), 'leave_balances', ['id'], unique=False)
    op.create_index(op.f('ix_leave_balances_user_id'), 'leave_balances', ['user_id'], unique=False)
    op.create_index(op.f('ix_leave_balances_year'), 'leave_balances', ['year'], unique=False)

    # 4. Expenses
    op.create_table(
        'expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('expense_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('receipt_file_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('approval_request_id', sa.Integer(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('client_uuid', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approval_request_id'], ['approval_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expenses_client_uuid'), 'expenses', ['client_uuid'], unique=True)
    op.create_index(op.f('ix_expenses_expense_date'), 'expenses', ['expense_date'], unique=False)
    op.create_index(op.f('ix_expenses_id'), 'expenses', ['id'], unique=False)
    op.create_index(op.f('ix_expenses_status'), 'expenses', ['status'], unique=False)
    op.create_index(op.f('ix_expenses_user_id'), 'expenses', ['user_id'], unique=False)

    # 5. Leave Requests
    op.create_table(
        'leave_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('leave_type', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('days_count', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('approval_request_id', sa.Integer(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('client_uuid', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approval_request_id'], ['approval_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leave_requests_client_uuid'), 'leave_requests', ['client_uuid'], unique=True)
    op.create_index(op.f('ix_leave_requests_end_date'), 'leave_requests', ['end_date'], unique=False)
    op.create_index(op.f('ix_leave_requests_id'), 'leave_requests', ['id'], unique=False)
    op.create_index(op.f('ix_leave_requests_start_date'), 'leave_requests', ['start_date'], unique=False)
    op.create_index(op.f('ix_leave_requests_status'), 'leave_requests', ['status'], unique=False)
    op.create_index(op.f('ix_leave_requests_user_id'), 'leave_requests', ['user_id'], unique=False)

    # 6. Tour Programs
    op.create_table(
        'tour_programs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('total_days', sa.Integer(), nullable=False),
        sa.Column('route_details', sa.String(length=255), nullable=True),
        sa.Column('objectives', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('approval_request_id', sa.Integer(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approval_request_id'], ['approval_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='NO ACTION'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tour_programs_end_date'), 'tour_programs', ['end_date'], unique=False)
    op.create_index(op.f('ix_tour_programs_id'), 'tour_programs', ['id'], unique=False)
    op.create_index(op.f('ix_tour_programs_start_date'), 'tour_programs', ['start_date'], unique=False)
    op.create_index(op.f('ix_tour_programs_status'), 'tour_programs', ['status'], unique=False)
    op.create_index(op.f('ix_tour_programs_user_id'), 'tour_programs', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema: drop Phase 5 tables in reverse order."""
    op.drop_table('tour_programs')
    op.drop_table('leave_requests')
    op.drop_table('expenses')
    op.drop_table('leave_balances')
    op.drop_table('approval_history')
    op.drop_table('approval_requests')
