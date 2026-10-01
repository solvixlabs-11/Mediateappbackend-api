"""phase3_4_attendance_dcr_planning

Revision ID: a891f7c2301c
Revises: 7790c3bd304b
Create Date: 2026-10-02 00:35:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a891f7c2301c'
down_revision: str | Sequence[str] | None = '7790c3bd304b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. attendances
    op.create_table(
        'attendances',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PRESENT'),
        sa.Column('check_in_time', sa.DateTime(), nullable=True),
        sa.Column('check_in_latitude', sa.Float(), nullable=True),
        sa.Column('check_in_longitude', sa.Float(), nullable=True),
        sa.Column('check_in_address', sa.String(length=255), nullable=True),
        sa.Column('check_in_accuracy', sa.Float(), nullable=True),
        sa.Column('check_in_mock_flag', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('check_out_time', sa.DateTime(), nullable=True),
        sa.Column('check_out_latitude', sa.Float(), nullable=True),
        sa.Column('check_out_longitude', sa.Float(), nullable=True),
        sa.Column('check_out_address', sa.String(length=255), nullable=True),
        sa.Column('check_out_accuracy', sa.Float(), nullable=True),
        sa.Column('check_out_mock_flag', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('total_work_minutes', sa.Integer(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('client_uuid', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_attendances_id'), 'attendances', ['id'], unique=False)
    op.create_index(op.f('ix_attendances_user_id'), 'attendances', ['user_id'], unique=False)
    op.create_index(op.f('ix_attendances_date'), 'attendances', ['date'], unique=False)
    op.create_index(op.f('ix_attendances_client_uuid'), 'attendances', ['client_uuid'], unique=True)

    # 2. planned_visits
    op.create_table(
        'planned_visits',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_date', sa.Date(), nullable=False),
        sa.Column('customer_type', sa.String(length=50), nullable=False),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True),
        sa.Column('chemist_id', sa.Integer(), sa.ForeignKey('chemists.id', ondelete='SET NULL'), nullable=True),
        sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('stockist_id', sa.Integer(), sa.ForeignKey('stockists.id', ondelete='SET NULL'), nullable=True),
        sa.Column('priority', sa.String(length=50), server_default='MEDIUM', nullable=False),
        sa.Column('visit_purpose', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='PLANNED', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('client_uuid', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_planned_visits_id'), 'planned_visits', ['id'], unique=False)
    op.create_index(op.f('ix_planned_visits_user_id'), 'planned_visits', ['user_id'], unique=False)
    op.create_index(op.f('ix_planned_visits_plan_date'), 'planned_visits', ['plan_date'], unique=False)
    op.create_index(op.f('ix_planned_visits_status'), 'planned_visits', ['status'], unique=False)
    op.create_index(op.f('ix_planned_visits_client_uuid'), 'planned_visits', ['client_uuid'], unique=True)

    # 3. dcr_visits
    op.create_table(
        'dcr_visits',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dcr_date', sa.Date(), nullable=False),
        sa.Column('customer_type', sa.String(length=50), nullable=False),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True),
        sa.Column('chemist_id', sa.Integer(), sa.ForeignKey('chemists.id', ondelete='SET NULL'), nullable=True),
        sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('stockist_id', sa.Integer(), sa.ForeignKey('stockists.id', ondelete='SET NULL'), nullable=True),
        sa.Column('planned_visit_id', sa.Integer(), sa.ForeignKey('planned_visits.id', ondelete='SET NULL'), nullable=True),
        sa.Column('visit_type', sa.String(length=50), server_default='INDEPENDENT', nullable=False),
        sa.Column('joint_manager_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('call_time', sa.DateTime(), nullable=False),
        sa.Column('call_duration_minutes', sa.Integer(), server_default='15', nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location_accuracy', sa.Float(), nullable=True),
        sa.Column('distance_to_customer_meters', sa.Float(), nullable=True),
        sa.Column('is_geofence_verified', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('geofence_radius_meters', sa.Float(), server_default='200.0', nullable=False),
        sa.Column('is_mock_location', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('pob_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='SUBMITTED', nullable=False),
        sa.Column('client_uuid', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_dcr_visits_id'), 'dcr_visits', ['id'], unique=False)
    op.create_index(op.f('ix_dcr_visits_user_id'), 'dcr_visits', ['user_id'], unique=False)
    op.create_index(op.f('ix_dcr_visits_dcr_date'), 'dcr_visits', ['dcr_date'], unique=False)
    op.create_index(op.f('ix_dcr_visits_status'), 'dcr_visits', ['status'], unique=False)
    op.create_index(op.f('ix_dcr_visits_client_uuid'), 'dcr_visits', ['client_uuid'], unique=True)

    # 4. dcr_post_call_analyses
    op.create_table(
        'dcr_post_call_analyses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('dcr_visit_id', sa.Integer(), sa.ForeignKey('dcr_visits.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('call_outcome', sa.String(length=50), server_default='HIGHLY_INTERESTED', nullable=False),
        sa.Column('doctor_feedback', sa.Text(), nullable=True),
        sa.Column('prescription_commitment', sa.String(length=50), server_default='HIGH', nullable=False),
        sa.Column('next_visit_date', sa.Date(), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('follow_up_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_dcr_post_call_analyses_id'), 'dcr_post_call_analyses', ['id'], unique=False)

    # 5. dcr_product_details
    op.create_table(
        'dcr_product_details',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('dcr_visit_id', sa.Integer(), sa.ForeignKey('dcr_visits.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_name', sa.String(length=150), nullable=False),
        sa.Column('sample_quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('gift_quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('remarks', sa.String(length=255), nullable=True),
    )
    op.create_index(op.f('ix_dcr_product_details_id'), 'dcr_product_details', ['id'], unique=False)
    op.create_index(op.f('ix_dcr_product_details_dcr_visit_id'), 'dcr_product_details', ['dcr_visit_id'], unique=False)

    # 6. follow_ups
    op.create_table(
        'follow_ups',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_type', sa.String(length=50), nullable=False),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True),
        sa.Column('chemist_id', sa.Integer(), sa.ForeignKey('chemists.id', ondelete='SET NULL'), nullable=True),
        sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('stockist_id', sa.Integer(), sa.ForeignKey('stockists.id', ondelete='SET NULL'), nullable=True),
        sa.Column('dcr_visit_id', sa.Integer(), sa.ForeignKey('dcr_visits.id', ondelete='SET NULL'), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=50), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('client_uuid', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_follow_ups_id'), 'follow_ups', ['id'], unique=False)
    op.create_index(op.f('ix_follow_ups_user_id'), 'follow_ups', ['user_id'], unique=False)
    op.create_index(op.f('ix_follow_ups_due_date'), 'follow_ups', ['due_date'], unique=False)
    op.create_index(op.f('ix_follow_ups_status'), 'follow_ups', ['status'], unique=False)
    op.create_index(op.f('ix_follow_ups_client_uuid'), 'follow_ups', ['client_uuid'], unique=True)


def downgrade() -> None:
    op.drop_table('follow_ups')
    op.drop_table('dcr_product_details')
    op.drop_table('dcr_post_call_analyses')
    op.drop_table('dcr_visits')
    op.drop_table('planned_visits')
    op.drop_table('attendances')
