"""Seeder for Territories (32 across India)."""

from sqlalchemy.orm import Session
from app.modules.masters.models import State
from app.modules.territories.models import Territory
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="territories")
    states = {s.code: s for s in session.query(State).all()}
    mh_id = states.get("MH", State(id=1)).id if states else 1
    gj_id = states.get("GJ", State(id=1)).id if states else 1
    ka_id = states.get("KA", State(id=1)).id if states else 1
    dl_id = states.get("DL", State(id=1)).id if states else 1
    tn_id = states.get("TN", State(id=1)).id if states else 1
    ts_id = states.get("TS", State(id=1)).id if states else 1
    wb_id = states.get("WB", State(id=1)).id if states else 1
    up_id = states.get("UP", State(id=1)).id if states else 1
    rj_id = states.get("RJ", State(id=1)).id if states else 1
    mp_id = states.get("MP", State(id=1)).id if states else 1

    territories_def = [
        ("T-MUM-01", "Mumbai Central & South", "Mumbai HQ", mh_id),
        ("T-MUM-02", "Mumbai Western Suburbs", "Andheri HQ", mh_id),
        ("T-MUM-03", "Mumbai Eastern Suburbs & Thane", "Thane HQ", mh_id),
        ("T-MUM-04", "Navi Mumbai & Panvel", "Vashi HQ", mh_id),
        ("T-PUN-01", "Pune Urban Core", "Pune HQ", mh_id),
        ("T-PUN-02", "Pune PCMC & Industrial", "Pimpri HQ", mh_id),
        ("T-NAG-01", "Nagpur Metro & Vidarbha", "Nagpur HQ", mh_id),
        ("T-NSK-01", "Nashik North & Khandesh", "Nashik HQ", mh_id),
        ("T-AUR-01", "Aurangabad & Marathwada", "Aurangabad HQ", mh_id),
        ("T-KOL-01", "Kolhapur & South Maharashtra", "Kolhapur HQ", mh_id),
        ("T-AMD-01", "Ahmedabad Metro", "Ahmedabad HQ", gj_id),
        ("T-AMD-02", "Ahmedabad Rural & Gandhinagar", "Gandhinagar HQ", gj_id),
        ("T-SUR-01", "Surat & South Gujarat", "Surat HQ", gj_id),
        ("T-BRD-01", "Vadodara Central", "Vadodara HQ", gj_id),
        ("T-RJK-01", "Rajkot & Saurashtra", "Rajkot HQ", gj_id),
        ("T-BLR-01", "Bengaluru Central & East", "Bengaluru HQ", ka_id),
        ("T-BLR-02", "Bengaluru South & West", "Jayanagar HQ", ka_id),
        ("T-BLR-03", "Bengaluru North & Hebbal", "Yelahanka HQ", ka_id),
        ("T-MYS-01", "Mysuru & Old Mysuru Zone", "Mysuru HQ", ka_id),
        ("T-MNG-01", "Mangaluru & Coastal Karnataka", "Mangaluru HQ", ka_id),
        ("T-DEL-01", "Delhi NCR Central", "Connaught Place HQ", dl_id),
        ("T-DEL-02", "South Delhi & Saket", "Nehru Place HQ", dl_id),
        ("T-DEL-03", "East Delhi & Noida Border", "Laxmi Nagar HQ", dl_id),
        ("T-CHN-01", "Chennai Metro Central", "T Nagar HQ", tn_id),
        ("T-CHN-02", "Chennai North & Ambattur", "Anna Nagar HQ", tn_id),
        ("T-HYD-01", "Hyderabad Central & Banjara", "Banjara Hills HQ", ts_id),
        ("T-HYD-02", "Secunderabad & Cyberabad", "Hitec City HQ", ts_id),
        ("T-CCU-01", "Kolkata Central & Park Street", "Kolkata HQ", wb_id),
        ("T-LKO-01", "Lucknow Central & Gomti Nagar", "Lucknow HQ", up_id),
        ("T-JPR-01", "Jaipur Metro & C-Scheme", "Jaipur HQ", rj_id),
        ("T-IND-01", "Indore Commercial Core", "Indore HQ", mp_id),
        ("T-BHO-01", "Bhopal Central", "Bhopal HQ", mp_id),
    ]

    for code, name, hq, state_id in territories_def:
        existing = session.query(Territory).filter(Territory.code == code).first()
        if existing:
            changed = False
            if existing.name != name:
                existing.name = name
                changed = True
            if existing.headquarters != hq:
                existing.headquarters = hq
                changed = True
            if existing.is_deleted:
                existing.is_deleted = False
                existing.is_active = True
                changed = True
            if changed:
                result.updated += 1
            else:
                result.unchanged += 1
        else:
            t = Territory(
                code=code,
                name=name,
                headquarters=hq,
                state_id=state_id,
                is_active=True,
            )
            session.add(t)
            result.created += 1

    session.flush()
    return result
