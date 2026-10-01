"""DCR database repository."""

from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from app.modules.dcr.models import (
    DcrPostCallAnalysis,
    DcrProductDetail,
    DcrVisit,
    FollowUp,
    PlannedVisit,
)


class DcrRepository:
    """Repository handling database operations for DCR, Planning, and Follow-ups."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # 1. PLANNED VISITS
    def get_planned_visit_by_id(self, plan_id: int) -> PlannedVisit | None:
        """Fetch planned visit by ID."""
        return self.db.query(PlannedVisit).filter(PlannedVisit.id == plan_id).first()

    def get_planned_visit_by_uuid(self, client_uuid: str) -> PlannedVisit | None:
        """Fetch plan by client_uuid for idempotency."""
        return self.db.query(PlannedVisit).filter(PlannedVisit.client_uuid == client_uuid).first()

    def create_planned_visit(
        self,
        user_id: int,
        plan_date: date,
        customer_type: str,
        doctor_id: int | None = None,
        chemist_id: int | None = None,
        hospital_id: int | None = None,
        stockist_id: int | None = None,
        priority: str = "MEDIUM",
        visit_purpose: str | None = None,
        notes: str | None = None,
        client_uuid: str | None = None,
    ) -> PlannedVisit:
        """Create a planned customer call."""
        plan = PlannedVisit(
            user_id=user_id,
            plan_date=plan_date,
            customer_type=customer_type,
            doctor_id=doctor_id,
            chemist_id=chemist_id,
            hospital_id=hospital_id,
            stockist_id=stockist_id,
            priority=priority,
            visit_purpose=visit_purpose,
            notes=notes,
            client_uuid=client_uuid,
        )
        self.db.add(plan)
        self.db.flush()
        return plan

    def list_planned_visits(
        self,
        user_id: int | None = None,
        plan_date: date | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[PlannedVisit]:
        """List planned visits with filters."""
        query = self.db.query(PlannedVisit)
        if user_id:
            query = query.filter(PlannedVisit.user_id == user_id)
        if plan_date:
            query = query.filter(PlannedVisit.plan_date == plan_date)
        if status:
            query = query.filter(PlannedVisit.status == status)
        return (
            query.options(
                joinedload(PlannedVisit.doctor),
                joinedload(PlannedVisit.chemist),
                joinedload(PlannedVisit.hospital),
                joinedload(PlannedVisit.stockist),
            )
            .order_by(PlannedVisit.plan_date.desc(), PlannedVisit.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # 2. DCR VISITS
    def get_dcr_visit_by_id(self, dcr_id: int) -> DcrVisit | None:
        """Fetch DCR visit by ID with relations."""
        return (
            self.db.query(DcrVisit)
            .options(
                joinedload(DcrVisit.doctor),
                joinedload(DcrVisit.chemist),
                joinedload(DcrVisit.hospital),
                joinedload(DcrVisit.stockist),
                joinedload(DcrVisit.post_call_analysis),
                joinedload(DcrVisit.product_details),
            )
            .filter(DcrVisit.id == dcr_id)
            .first()
        )

    def get_dcr_by_uuid(self, client_uuid: str) -> DcrVisit | None:
        """Fetch DCR visit by client_uuid for idempotency."""
        return (
            self.db.query(DcrVisit)
            .options(
                joinedload(DcrVisit.doctor),
                joinedload(DcrVisit.chemist),
                joinedload(DcrVisit.hospital),
                joinedload(DcrVisit.stockist),
                joinedload(DcrVisit.post_call_analysis),
                joinedload(DcrVisit.product_details),
            )
            .filter(DcrVisit.client_uuid == client_uuid)
            .first()
        )

    def create_dcr_visit(
        self,
        user_id: int,
        dcr_date: date,
        customer_type: str,
        doctor_id: int | None = None,
        chemist_id: int | None = None,
        hospital_id: int | None = None,
        stockist_id: int | None = None,
        planned_visit_id: int | None = None,
        visit_type: str = "INDEPENDENT",
        joint_manager_id: int | None = None,
        call_time: datetime | None = None,
        call_duration_minutes: int = 15,
        latitude: float | None = None,
        longitude: float | None = None,
        location_accuracy: float | None = None,
        distance_to_customer_meters: float | None = None,
        is_geofence_verified: bool = False,
        geofence_radius_meters: float = 200.0,
        is_mock_location: bool = False,
        remarks: str | None = None,
        pob_amount: float = 0.0,
        status: str = "SUBMITTED",
        client_uuid: str | None = None,
    ) -> DcrVisit:
        """Create primary DCR visit row."""
        dcr = DcrVisit(
            user_id=user_id,
            dcr_date=dcr_date,
            customer_type=customer_type,
            doctor_id=doctor_id,
            chemist_id=chemist_id,
            hospital_id=hospital_id,
            stockist_id=stockist_id,
            planned_visit_id=planned_visit_id,
            visit_type=visit_type,
            joint_manager_id=joint_manager_id,
            call_time=call_time or datetime.utcnow(),
            call_duration_minutes=call_duration_minutes,
            latitude=latitude,
            longitude=longitude,
            location_accuracy=location_accuracy,
            distance_to_customer_meters=distance_to_customer_meters,
            is_geofence_verified=is_geofence_verified,
            geofence_radius_meters=geofence_radius_meters,
            is_mock_location=is_mock_location,
            remarks=remarks,
            pob_amount=pob_amount,
            status=status,
            client_uuid=client_uuid,
        )
        self.db.add(dcr)
        self.db.flush()
        return dcr

    def add_post_call_analysis(
        self,
        dcr_visit_id: int,
        call_outcome: str,
        doctor_feedback: str | None = None,
        prescription_commitment: str = "HIGH",
        next_visit_date: date | None = None,
        follow_up_required: bool = False,
        follow_up_notes: str | None = None,
    ) -> DcrPostCallAnalysis:
        """Attach post-call analysis."""
        analysis = DcrPostCallAnalysis(
            dcr_visit_id=dcr_visit_id,
            call_outcome=call_outcome,
            doctor_feedback=doctor_feedback,
            prescription_commitment=prescription_commitment,
            next_visit_date=next_visit_date,
            follow_up_required=follow_up_required,
            follow_up_notes=follow_up_notes,
        )
        self.db.add(analysis)
        self.db.flush()
        return analysis

    def add_product_detail(
        self,
        dcr_visit_id: int,
        product_name: str,
        sample_quantity: int = 0,
        gift_quantity: int = 0,
        remarks: str | None = None,
    ) -> DcrProductDetail:
        """Add product discussion/sample line item."""
        detail = DcrProductDetail(
            dcr_visit_id=dcr_visit_id,
            product_name=product_name,
            sample_quantity=sample_quantity,
            gift_quantity=gift_quantity,
            remarks=remarks,
        )
        self.db.add(detail)
        self.db.flush()
        return detail

    def list_dcr_visits(
        self,
        user_id: int | None = None,
        dcr_date: date | None = None,
        customer_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[DcrVisit]:
        """List DCR visits with filters."""
        query = self.db.query(DcrVisit)
        if user_id:
            query = query.filter(DcrVisit.user_id == user_id)
        if dcr_date:
            query = query.filter(DcrVisit.dcr_date == dcr_date)
        if customer_type:
            query = query.filter(DcrVisit.customer_type == customer_type)
        return (
            query.options(
                joinedload(DcrVisit.doctor),
                joinedload(DcrVisit.chemist),
                joinedload(DcrVisit.hospital),
                joinedload(DcrVisit.stockist),
                joinedload(DcrVisit.post_call_analysis),
                joinedload(DcrVisit.product_details),
            )
            .order_by(DcrVisit.dcr_date.desc(), DcrVisit.call_time.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # 3. FOLLOW-UPS
    def create_follow_up(
        self,
        user_id: int,
        customer_type: str,
        due_date: date,
        title: str,
        doctor_id: int | None = None,
        chemist_id: int | None = None,
        hospital_id: int | None = None,
        stockist_id: int | None = None,
        dcr_visit_id: int | None = None,
        notes: str | None = None,
        priority: str = "MEDIUM",
        client_uuid: str | None = None,
    ) -> FollowUp:
        """Create follow-up reminder."""
        fu = FollowUp(
            user_id=user_id,
            customer_type=customer_type,
            doctor_id=doctor_id,
            chemist_id=chemist_id,
            hospital_id=hospital_id,
            stockist_id=stockist_id,
            dcr_visit_id=dcr_visit_id,
            due_date=due_date,
            title=title,
            notes=notes,
            priority=priority,
            status="PENDING",
            client_uuid=client_uuid,
        )
        self.db.add(fu)
        self.db.flush()
        return fu

    def list_follow_ups(
        self,
        user_id: int,
        status: str | None = None,
        overdue_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FollowUp]:
        """List follow-ups."""
        query = self.db.query(FollowUp).filter(FollowUp.user_id == user_id)
        if status:
            query = query.filter(FollowUp.status == status)
        if overdue_only:
            query = query.filter(FollowUp.due_date < date.today(), FollowUp.status == "PENDING")
        return (
            query.options(
                joinedload(FollowUp.doctor),
                joinedload(FollowUp.chemist),
                joinedload(FollowUp.hospital),
                joinedload(FollowUp.stockist),
            )
            .order_by(FollowUp.due_date.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
