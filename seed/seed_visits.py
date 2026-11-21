"""Seeder for Visits (DCR and Planned Visits - 35+ records per customer type)."""

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.modules.customers.models import Doctor, Chemist, Stockist, Hospital
from app.modules.dcr.models import DcrVisit, PlannedVisit, DcrPostCallAnalysis, DcrProductDetail
from app.modules.products.models import Product
from app.modules.users.models import User, Role
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="visits")
    if not dev:
        return result

    mr_role = session.query(Role).filter(Role.code == "MR").first()
    if mr_role:
        users = session.query(User).filter(User.role_id == mr_role.id).all()
    else:
        users = session.query(User).all()
    if not users:
        return result

    doctors = session.query(Doctor).filter(Doctor.is_deleted == False).all()  # noqa: E712
    chemists = session.query(Chemist).filter(Chemist.is_deleted == False).all()  # noqa: E712
    stockists = session.query(Stockist).filter(Stockist.is_deleted == False).all()  # noqa: E712
    hospitals = session.query(Hospital).filter(Hospital.is_deleted == False).all()  # noqa: E712

    today = date.today()
    now = datetime.utcnow()

    visit_plans = []

    # 1. Doctor Planned Visits (35 records)
    for i in range(min(35, len(doctors))):
        doc = doctors[i]
        user = users[i % len(users)]
        offset = (i % 7) - 3  # -3 to +3 days
        p_date = today + timedelta(days=offset)
        status = "COMPLETED" if offset < 0 else ("PLANNED" if offset >= 0 else "MISSED")
        visit_plans.append({
            "user_id": user.id,
            "customer_type": "DOCTOR",
            "doctor_id": doc.id,
            "chemist_id": None,
            "stockist_id": None,
            "hospital_id": None,
            "plan_date": p_date,
            "status": status,
            "priority": "HIGH" if i % 2 == 0 else "MEDIUM",
            "visit_purpose": "Product detailing & sample distribution" if i % 2 == 0 else "Monthly review & feedback",
            "client_uuid": f"seed-pv-doc-{doc.id}-{p_date.isoformat()}-{user.id}",
        })

    # 2. Chemist Planned Visits (35 records)
    for i in range(min(35, len(chemists))):
        chm = chemists[i]
        user = users[(i + 3) % len(users)]
        offset = (i % 7) - 3
        p_date = today + timedelta(days=offset)
        status = "COMPLETED" if offset < 0 else "PLANNED"
        visit_plans.append({
            "user_id": user.id,
            "customer_type": "CHEMIST",
            "doctor_id": None,
            "chemist_id": chm.id,
            "stockist_id": None,
            "hospital_id": None,
            "plan_date": p_date,
            "status": status,
            "priority": "MEDIUM",
            "visit_purpose": "POB booking & stock movement reconciliation",
            "client_uuid": f"seed-pv-chm-{chm.id}-{p_date.isoformat()}-{user.id}",
        })

    # 3. Stockist Planned Visits (35 records)
    for i in range(min(35, len(stockists))):
        stk = stockists[i]
        user = users[(i + 7) % len(users)]
        offset = (i % 7) - 3
        p_date = today + timedelta(days=offset)
        status = "COMPLETED" if offset < 0 else "PLANNED"
        visit_plans.append({
            "user_id": user.id,
            "customer_type": "STOCKIST",
            "doctor_id": None,
            "chemist_id": None,
            "stockist_id": stk.id,
            "hospital_id": None,
            "plan_date": p_date,
            "status": status,
            "priority": "HIGH",
            "visit_purpose": "Order closing, statement reconciliation & secondary sales review",
            "client_uuid": f"seed-pv-stk-{stk.id}-{p_date.isoformat()}-{user.id}",
        })

    # 4. Hospital Planned Visits (35 records)
    for i in range(min(35, len(hospitals))):
        hsp = hospitals[i]
        user = users[(i + 11) % len(users)]
        offset = (i % 7) - 3
        p_date = today + timedelta(days=offset)
        status = "COMPLETED" if offset < 0 else "PLANNED"
        visit_plans.append({
            "user_id": user.id,
            "customer_type": "HOSPITAL",
            "doctor_id": None,
            "chemist_id": None,
            "stockist_id": None,
            "hospital_id": hsp.id,
            "plan_date": p_date,
            "status": status,
            "priority": "HIGH",
            "visit_purpose": "Institutional tender review & pharmacy formulary inclusion",
            "client_uuid": f"seed-pv-hsp-{hsp.id}-{p_date.isoformat()}-{user.id}",
        })

    pv_mapping = {}
    for plan in visit_plans:
        existing = session.query(PlannedVisit).filter(PlannedVisit.client_uuid == plan["client_uuid"]).first()
        if not existing:
            pv = PlannedVisit(**plan)
            session.add(pv)
            session.flush()
            pv_mapping[plan["client_uuid"]] = pv.id
            result.created += 1
        else:
            pv_mapping[plan["client_uuid"]] = existing.id
            result.unchanged += 1

    # Generate at least 35 DCR Completed Visits for EACH Customer Type
    dcr_visits = []

    # 1. Doctor DCR Visits (35 records)
    for i in range(min(35, len(doctors))):
        doc = doctors[i]
        user = users[i % len(users)]
        day_offset = (i % 5)
        d_date = today - timedelta(days=day_offset)
        pv_key = f"seed-pv-doc-{doc.id}-{(today + timedelta(days=(i % 7) - 3)).isoformat()}-{user.id}"
        pv_id = pv_mapping.get(pv_key)

        status = "APPROVED" if day_offset > 2 else ("SUBMITTED" if day_offset > 0 else "DRAFT")
        pob = 3000.0 + (i * 350.0) if i % 2 == 0 else 0.0

        dcr_visits.append({
            "user_id": user.id,
            "customer_type": "DOCTOR",
            "doctor_id": doc.id,
            "chemist_id": None,
            "stockist_id": None,
            "hospital_id": None,
            "planned_visit_id": pv_id,
            "dcr_date": d_date,
            "call_time": now - timedelta(days=day_offset, hours=(i % 8) + 1),
            "call_duration_minutes": 15 + (i % 15),
            "visit_type": "INDEPENDENT" if i % 3 != 0 else "JOINT_WITH_MANAGER",
            "pob_amount": pob,
            "is_geofence_verified": (i % 6 != 0),
            "distance_to_customer_meters": 45.0 + (i * 3),
            "latitude": 28.6139 + (i * 0.005),
            "longitude": 77.2090 + (i * 0.005),
            "remarks": f"Detailed product efficacy discussion with Dr. {doc.full_name}.",
            "status": status,
            "client_uuid": f"seed-dv-doc-{doc.id}-{d_date.isoformat()}-{user.id}",
        })

    # 2. Chemist DCR Visits (35 records)
    for i in range(min(35, len(chemists))):
        chm = chemists[i]
        user = users[(i + 3) % len(users)]
        day_offset = (i % 5)
        d_date = today - timedelta(days=day_offset)
        pv_key = f"seed-pv-chm-{chm.id}-{(today + timedelta(days=(i % 7) - 3)).isoformat()}-{user.id}"
        pv_id = pv_mapping.get(pv_key)

        dcr_visits.append({
            "user_id": user.id,
            "customer_type": "CHEMIST",
            "doctor_id": None,
            "chemist_id": chm.id,
            "stockist_id": None,
            "hospital_id": None,
            "planned_visit_id": pv_id,
            "dcr_date": d_date,
            "call_time": now - timedelta(days=day_offset, hours=(i % 6) + 2),
            "call_duration_minutes": 12 + (i % 8),
            "visit_type": "INDEPENDENT",
            "pob_amount": 4500.0 + (i * 500.0),
            "is_geofence_verified": (i % 7 != 0),
            "distance_to_customer_meters": 30.0 + (i * 4),
            "latitude": 19.0760 + (i * 0.005),
            "longitude": 72.8777 + (i * 0.005),
            "remarks": f"Inventory audit & order booking completed at {chm.shop_name}.",
            "status": "APPROVED" if day_offset > 1 else "SUBMITTED",
            "client_uuid": f"seed-dv-chm-{chm.id}-{d_date.isoformat()}-{user.id}",
        })

    # 3. Stockist DCR Visits (35 records)
    for i in range(min(35, len(stockists))):
        stk = stockists[i]
        user = users[(i + 7) % len(users)]
        day_offset = (i % 4)
        d_date = today - timedelta(days=day_offset)
        pv_key = f"seed-pv-stk-{stk.id}-{(today + timedelta(days=(i % 7) - 3)).isoformat()}-{user.id}"
        pv_id = pv_mapping.get(pv_key)

        dcr_visits.append({
            "user_id": user.id,
            "customer_type": "STOCKIST",
            "doctor_id": None,
            "chemist_id": None,
            "stockist_id": stk.id,
            "hospital_id": None,
            "planned_visit_id": pv_id,
            "dcr_date": d_date,
            "call_time": now - timedelta(days=day_offset, hours=3),
            "call_duration_minutes": 30 + (i % 15),
            "visit_type": "INDEPENDENT",
            "pob_amount": 28000.0 + (i * 4000.0),
            "is_geofence_verified": True,
            "distance_to_customer_meters": 22.0,
            "latitude": 12.9716 + (i * 0.005),
            "longitude": 77.5946 + (i * 0.005),
            "remarks": f"Reconciled ledgers and booked wholesale stock for {stk.agency_name}.",
            "status": "APPROVED",
            "client_uuid": f"seed-dv-stk-{stk.id}-{d_date.isoformat()}-{user.id}",
        })

    # 4. Hospital DCR Visits (35 records)
    for i in range(min(35, len(hospitals))):
        hsp = hospitals[i]
        user = users[(i + 11) % len(users)]
        day_offset = (i % 4)
        d_date = today - timedelta(days=day_offset)
        pv_key = f"seed-pv-hsp-{hsp.id}-{(today + timedelta(days=(i % 7) - 3)).isoformat()}-{user.id}"
        pv_id = pv_mapping.get(pv_key)

        dcr_visits.append({
            "user_id": user.id,
            "customer_type": "HOSPITAL",
            "doctor_id": None,
            "chemist_id": None,
            "stockist_id": None,
            "hospital_id": hsp.id,
            "planned_visit_id": pv_id,
            "dcr_date": d_date,
            "call_time": now - timedelta(days=day_offset, hours=4),
            "call_duration_minutes": 25 + (i % 10),
            "visit_type": "INDEPENDENT",
            "pob_amount": 15000.0 + (i * 2500.0),
            "is_geofence_verified": True,
            "distance_to_customer_meters": 35.0,
            "latitude": 22.5726 + (i * 0.005),
            "longitude": 88.3639 + (i * 0.005),
            "remarks": f"Hospital OPD presentation and pharmacy drug rate contract review at {hsp.name}.",
            "status": "APPROVED",
            "client_uuid": f"seed-dv-hsp-{hsp.id}-{d_date.isoformat()}-{user.id}",
        })

    for dcr in dcr_visits:
        existing = session.query(DcrVisit).filter(DcrVisit.client_uuid == dcr["client_uuid"]).first()
        if not existing:
            dv = DcrVisit(**dcr)
            session.add(dv)
            result.created += 1
        else:
            result.unchanged += 1

    session.flush()

    # Seed post-call analysis and product details for all DCR visits
    products = session.query(Product).filter(Product.is_active == True).all()  # noqa: E712
    all_dcr = session.query(DcrVisit).all()
    for idx, dv in enumerate(all_dcr):
        existing_pca = session.query(DcrPostCallAnalysis).filter(DcrPostCallAnalysis.dcr_visit_id == dv.id).first()
        if not existing_pca:
            call_outcome = ["HIGHLY_INTERESTED", "MODERATE", "NOT_INTERESTED", "BUSY_RESCHEDULED"][idx % 4]
            commitment = ["HIGH", "MEDIUM", "LOW", "NIL"][idx % 4]
            if dv.customer_type == "DOCTOR":
                doc_feedback = "Doctor showed high interest in the latest clinical trial data and safety profile. Committed to trial on 5+ patients."
            elif dv.customer_type == "CHEMIST":
                doc_feedback = "Retail chemist confirmed steady Rx demand and placed request for immediate replenishment."
            elif dv.customer_type == "HOSPITAL":
                doc_feedback = "Hospital purchase committee reviewed formulary proposal and approved trial stocking."
            else:
                doc_feedback = "Stockist reconciled trade accounts and noted rising wholesale movement across secondary channels."

            pca = DcrPostCallAnalysis(
                dcr_visit_id=dv.id,
                call_outcome=call_outcome,
                doctor_feedback=doc_feedback,
                prescription_commitment=commitment,
                next_visit_date=dv.dcr_date + timedelta(days=14),
                follow_up_required=(idx % 2 == 0),
                follow_up_notes=f"Deliver updated scientific monograph and monitor shelf availability." if (idx % 2 == 0) else None,
            )
            session.add(pca)

        existing_pds = session.query(DcrProductDetail).filter(DcrProductDetail.dcr_visit_id == dv.id).all()
        if not existing_pds and products:
            p1 = products[idx % len(products)]
            p2 = products[(idx + 1) % len(products)]
            pd1 = DcrProductDetail(
                dcr_visit_id=dv.id,
                product_name=p1.name,
                sample_quantity=2 + (idx % 3),
                gift_quantity=1 if idx % 2 == 0 else 0,
                remarks="Product detailing conducted with visual aid presentation.",
            )
            pd2 = DcrProductDetail(
                dcr_visit_id=dv.id,
                product_name=p2.name,
                sample_quantity=1 + (idx % 2),
                gift_quantity=0,
                remarks="Discussed dosage advantages and competitive pricing.",
            )
            session.add(pd1)
            session.add(pd2)

    session.flush()
    return result
