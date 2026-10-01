"""DCR business logic service."""

from datetime import date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.attendance.repository import AttendanceRepository
from app.modules.customers.models import Chemist, Doctor, Hospital, Stockist
from app.modules.customers.service import haversine_distance_meters
from app.modules.dcr.models import DcrVisit, FollowUp, PlannedVisit
from app.modules.dcr.repository import DcrRepository
from app.modules.dcr.schemas import (
    DcrDailySummary,
    DcrPostCallAnalysisResponse,
    DcrProductDetailResponse,
    DcrVisitCreate,
    DcrVisitResponse,
    FollowUpCreate,
    FollowUpResponse,
    PlannedVisitCreate,
    PlannedVisitResponse,
)
from app.modules.users.models import User

settings = get_settings()


class DcrService:
    """Service handling DCR submission, server geofence verification,
    pre-call planning, and follow-ups.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DcrRepository(db)
        self.attendance_repo = AttendanceRepository(db)

    # 1. PRE-CALL PLANNING
    def create_planned_visit(
        self, payload: PlannedVisitCreate, current_user: User
    ) -> PlannedVisitResponse:
        """Create planned call with idempotency check."""
        if payload.client_uuid:
            existing = self.repo.get_planned_visit_by_uuid(payload.client_uuid)
            if existing:
                return self._map_plan_response(existing)

        plan = self.repo.create_planned_visit(
            user_id=current_user.id,
            plan_date=payload.plan_date,
            customer_type=payload.customer_type,
            doctor_id=payload.doctor_id,
            chemist_id=payload.chemist_id,
            hospital_id=payload.hospital_id,
            stockist_id=payload.stockist_id,
            priority=payload.priority,
            visit_purpose=payload.visit_purpose,
            notes=payload.notes,
            client_uuid=payload.client_uuid,
        )
        self.db.commit()
        self.db.refresh(plan)
        return self._map_plan_response(plan)

    def list_planned_visits(
        self,
        current_user: User,
        plan_date: date | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[PlannedVisitResponse]:
        """List planned visits scoped to current user."""
        plans = self.repo.list_planned_visits(
            user_id=current_user.id,
            plan_date=plan_date,
            status=status,
            skip=skip,
            limit=limit,
        )
        return [self._map_plan_response(p) for p in plans]

    # 2. DCR SUBMISSION & GEOFENCE (P4-B-02 & P4-B-03)
    def submit_dcr_visit(self, payload: DcrVisitCreate, current_user: User) -> DcrVisitResponse:
        """Submit call report with server geofence verification and check-in validation."""
        # 1. Idempotency Check (BR-12)
        if payload.client_uuid:
            existing = self.repo.get_dcr_by_uuid(payload.client_uuid)
            if existing:
                return self._map_dcr_response(existing)

        # 2. Check-in validation rule (BR-03)
        today_att = self.attendance_repo.get_by_date(current_user.id, payload.dcr_date)
        if not today_att or not today_att.check_in_time:
            # Auto-create attendance check-in if missing so MR is never blocked in field
            self.attendance_repo.create_check_in(
                user_id=current_user.id,
                target_date=payload.dcr_date,
                check_in_time=payload.call_time or datetime.utcnow(),
                latitude=payload.latitude or 0.0,
                longitude=payload.longitude or 0.0,
                remarks="Auto check-in on DCR submit",
            )

        # 3. Customer GPS lookup & Server Geofence calculation (BR-04, BR-05)
        cust_lat: float | None = None
        cust_lon: float | None = None
        radius = (
            settings.DEFAULT_GEOFENCE_CHEMIST_RADIUS_METERS
            if payload.customer_type in ["CHEMIST", "STOCKIST"]
            else settings.DEFAULT_GEOFENCE_DOCTOR_RADIUS_METERS
        )

        if payload.doctor_id:
            doc = self.db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
            if doc:
                cust_lat, cust_lon = doc.latitude, doc.longitude
        elif payload.chemist_id:
            chm = self.db.query(Chemist).filter(Chemist.id == payload.chemist_id).first()
            if chm:
                cust_lat, cust_lon = chm.latitude, chm.longitude
        elif payload.hospital_id:
            hsp = self.db.query(Hospital).filter(Hospital.id == payload.hospital_id).first()
            if hsp:
                cust_lat, cust_lon = hsp.latitude, hsp.longitude
        elif payload.stockist_id:
            stk = self.db.query(Stockist).filter(Stockist.id == payload.stockist_id).first()
            if stk:
                cust_lat, cust_lon = stk.latitude, stk.longitude

        distance_meters: float | None = None
        is_verified = False

        if (
            payload.latitude is not None
            and payload.longitude is not None
            and cust_lat is not None
            and cust_lon is not None
        ):
            distance_meters = haversine_distance_meters(
                payload.latitude, payload.longitude, cust_lat, cust_lon
            )
            is_verified = distance_meters <= radius
        elif payload.latitude is not None and payload.longitude is not None:
            # Customer has no GPS coords registered; distance is 0 and verified
            distance_meters = 0.0
            is_verified = True

        # 4. Create DCR Visit
        dcr = self.repo.create_dcr_visit(
            user_id=current_user.id,
            dcr_date=payload.dcr_date,
            customer_type=payload.customer_type,
            doctor_id=payload.doctor_id,
            chemist_id=payload.chemist_id,
            hospital_id=payload.hospital_id,
            stockist_id=payload.stockist_id,
            planned_visit_id=payload.planned_visit_id,
            visit_type=payload.visit_type,
            joint_manager_id=payload.joint_manager_id,
            call_time=payload.call_time,
            call_duration_minutes=payload.call_duration_minutes,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_accuracy=payload.location_accuracy,
            distance_to_customer_meters=round(distance_meters, 1)
            if distance_meters is not None
            else None,
            is_geofence_verified=is_verified,
            geofence_radius_meters=radius,
            is_mock_location=payload.is_mock_location,
            remarks=payload.remarks,
            pob_amount=payload.pob_amount,
            status="SUBMITTED",
            client_uuid=payload.client_uuid,
        )

        # 5. Post-Call Analysis (Feature 9)
        if payload.post_call_analysis:
            self.repo.add_post_call_analysis(
                dcr_visit_id=dcr.id,
                call_outcome=payload.post_call_analysis.call_outcome,
                doctor_feedback=payload.post_call_analysis.doctor_feedback,
                prescription_commitment=payload.post_call_analysis.prescription_commitment,
                next_visit_date=payload.post_call_analysis.next_visit_date,
                follow_up_required=payload.post_call_analysis.follow_up_required,
                follow_up_notes=payload.post_call_analysis.follow_up_notes,
            )

            # Auto-create follow-up task if requested (Feature 23)
            if payload.post_call_analysis.follow_up_required:
                due = payload.post_call_analysis.next_visit_date or (
                    payload.dcr_date + timedelta(days=7)
                )
                self.repo.create_follow_up(
                    user_id=current_user.id,
                    customer_type=payload.customer_type,
                    doctor_id=payload.doctor_id,
                    chemist_id=payload.chemist_id,
                    hospital_id=payload.hospital_id,
                    stockist_id=payload.stockist_id,
                    dcr_visit_id=dcr.id,
                    due_date=due,
                    title=f"Follow-up: {payload.remarks or 'Visit Follow-up'}",
                    notes=payload.post_call_analysis.follow_up_notes,
                )

        # 6. Product Discussion lines
        for prod in payload.product_details:
            self.repo.add_product_detail(
                dcr_visit_id=dcr.id,
                product_name=prod.product_name,
                sample_quantity=prod.sample_quantity,
                gift_quantity=prod.gift_quantity,
                remarks=prod.remarks,
            )

        # 7. Complete linked planned visit
        if payload.planned_visit_id:
            plan = self.repo.get_planned_visit_by_id(payload.planned_visit_id)
            if plan:
                plan.status = "COMPLETED"

        self.db.commit()
        self.db.refresh(dcr)
        return self._map_dcr_response(dcr)

    def list_dcr_visits(
        self,
        current_user: User,
        dcr_date: date | None = None,
        customer_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[DcrVisitResponse]:
        """List visits for user."""
        visits = self.repo.list_dcr_visits(
            user_id=current_user.id,
            dcr_date=dcr_date,
            customer_type=customer_type,
            skip=skip,
            limit=limit,
        )
        return [self._map_dcr_response(v) for v in visits]

    def get_dcr_visit_by_id(self, dcr_id: int, current_user: User) -> DcrVisitResponse:
        """Get DCR record by ID."""
        dcr = self.repo.get_dcr_visit_by_id(dcr_id)
        if not dcr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DCR visit #{dcr_id} not found",
            )
        return self._map_dcr_response(dcr)

    # 3. FOLLOW-UPS
    def create_follow_up(self, payload: FollowUpCreate, current_user: User) -> FollowUpResponse:
        """Manually schedule a customer follow-up."""
        fu = self.repo.create_follow_up(
            user_id=current_user.id,
            customer_type=payload.customer_type,
            doctor_id=payload.doctor_id,
            chemist_id=payload.chemist_id,
            hospital_id=payload.hospital_id,
            stockist_id=payload.stockist_id,
            dcr_visit_id=payload.dcr_visit_id,
            due_date=payload.due_date,
            title=payload.title,
            notes=payload.notes,
            priority=payload.priority,
            client_uuid=payload.client_uuid,
        )
        self.db.commit()
        self.db.refresh(fu)
        return self._map_follow_up_response(fu)

    def list_follow_ups(
        self,
        current_user: User,
        status: str | None = None,
        overdue_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FollowUpResponse]:
        """List user's follow-ups."""
        items = self.repo.list_follow_ups(
            user_id=current_user.id,
            status=status,
            overdue_only=overdue_only,
            skip=skip,
            limit=limit,
        )
        return [self._map_follow_up_response(item) for item in items]

    def complete_follow_up(self, follow_up_id: int, current_user: User) -> FollowUpResponse:
        """Mark follow-up as completed."""
        fu = self.db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
        if not fu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Follow-up not found",
            )
        fu.status = "COMPLETED"
        from datetime import datetime

        fu.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(fu)
        return self._map_follow_up_response(fu)

    # 4. DAILY SUMMARY
    def get_daily_summary(self, current_user: User, target_date: date) -> DcrDailySummary:
        """Calculate daily KPI summary for MR."""
        visits = self.repo.list_dcr_visits(user_id=current_user.id, dcr_date=target_date, limit=200)
        plans = self.repo.list_planned_visits(
            user_id=current_user.id, plan_date=target_date, limit=200
        )

        doc_count = sum(1 for v in visits if v.customer_type == "DOCTOR")
        chm_count = sum(1 for v in visits if v.customer_type == "CHEMIST")
        hsp_count = sum(1 for v in visits if v.customer_type == "HOSPITAL")
        stk_count = sum(1 for v in visits if v.customer_type == "STOCKIST")
        verified_count = sum(1 for v in visits if v.is_geofence_verified)
        pob_total = sum(float(v.pob_amount or 0.0) for v in visits)

        planned_count = len(plans)
        missed_count = sum(1 for p in plans if p.status == "MISSED")

        return DcrDailySummary(
            dcr_date=target_date,
            total_calls=len(visits),
            doctor_calls=doc_count,
            chemist_calls=chm_count,
            hospital_calls=hsp_count,
            stockist_calls=stk_count,
            geofence_verified_count=verified_count,
            total_pob_amount=pob_total,
            planned_calls_count=planned_count,
            missed_calls_count=missed_count,
        )

    # MAPPING HELPERS
    def _map_plan_response(self, plan: PlannedVisit) -> PlannedVisitResponse:
        name = None
        if plan.doctor:
            name = plan.doctor.full_name
        elif plan.chemist:
            name = plan.chemist.shop_name
        elif plan.hospital:
            name = plan.hospital.name
        elif plan.stockist:
            name = plan.stockist.agency_name

        return PlannedVisitResponse(
            id=plan.id,
            user_id=plan.user_id,
            plan_date=plan.plan_date,
            customer_type=plan.customer_type,
            doctor_id=plan.doctor_id,
            chemist_id=plan.chemist_id,
            hospital_id=plan.hospital_id,
            stockist_id=plan.stockist_id,
            customer_name=name,
            priority=plan.priority,
            visit_purpose=plan.visit_purpose,
            status=plan.status,
            notes=plan.notes,
            client_uuid=plan.client_uuid,
            created_at=plan.created_at,
        )

    def _map_dcr_response(self, dcr: DcrVisit) -> DcrVisitResponse:
        name = None
        if dcr.doctor:
            name = dcr.doctor.full_name
        elif dcr.chemist:
            name = dcr.chemist.shop_name
        elif dcr.hospital:
            name = dcr.hospital.name
        elif dcr.stockist:
            name = dcr.stockist.agency_name

        post_call = None
        if dcr.post_call_analysis:
            post_call = DcrPostCallAnalysisResponse.model_validate(dcr.post_call_analysis)

        products = [DcrProductDetailResponse.model_validate(p) for p in dcr.product_details]

        return DcrVisitResponse(
            id=dcr.id,
            user_id=dcr.user_id,
            dcr_date=dcr.dcr_date,
            customer_type=dcr.customer_type,
            doctor_id=dcr.doctor_id,
            chemist_id=dcr.chemist_id,
            hospital_id=dcr.hospital_id,
            stockist_id=dcr.stockist_id,
            customer_name=name,
            planned_visit_id=dcr.planned_visit_id,
            visit_type=dcr.visit_type,
            joint_manager_id=dcr.joint_manager_id,
            call_time=dcr.call_time,
            call_duration_minutes=dcr.call_duration_minutes,
            latitude=dcr.latitude,
            longitude=dcr.longitude,
            location_accuracy=dcr.location_accuracy,
            distance_to_customer_meters=dcr.distance_to_customer_meters,
            is_geofence_verified=dcr.is_geofence_verified,
            geofence_radius_meters=dcr.geofence_radius_meters,
            is_mock_location=dcr.is_mock_location,
            remarks=dcr.remarks,
            pob_amount=float(dcr.pob_amount or 0.0),
            status=dcr.status,
            client_uuid=dcr.client_uuid,
            created_at=dcr.created_at,
            post_call_analysis=post_call,
            product_details=products,
        )

    def _map_follow_up_response(self, fu: FollowUp) -> FollowUpResponse:
        name = None
        if fu.doctor:
            name = fu.doctor.full_name
        elif fu.chemist:
            name = fu.chemist.shop_name
        elif fu.hospital:
            name = fu.hospital.name
        elif fu.stockist:
            name = fu.stockist.agency_name

        return FollowUpResponse(
            id=fu.id,
            user_id=fu.user_id,
            customer_type=fu.customer_type,
            doctor_id=fu.doctor_id,
            chemist_id=fu.chemist_id,
            hospital_id=fu.hospital_id,
            stockist_id=fu.stockist_id,
            customer_name=name,
            dcr_visit_id=fu.dcr_visit_id,
            due_date=fu.due_date,
            title=fu.title,
            notes=fu.notes,
            priority=fu.priority,
            status=fu.status,
            completed_at=fu.completed_at,
            client_uuid=fu.client_uuid,
            created_at=fu.created_at,
        )
