"""Seeder for Mapping Batches."""

import datetime as dt
import json
from sqlalchemy.orm import Session
from app.modules.mappings.models import MappingBatch, MappingBatchItem
from app.modules.territories.models import Territory
from app.modules.users.models import User
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="mapping_batches")
    existing = session.query(MappingBatch).first()
    if existing:
        result.unchanged = session.query(MappingBatch).count()
        return result

    users = session.query(User).all()
    territories = session.query(Territory).limit(10).all()
    if not users or not territories:
        return result

    target_user = users[0]
    now = dt.datetime.now(dt.timezone.utc)

    # 1. Create an APPLIED territory batch
    batch1 = MappingBatch(
        mode="TERRITORY",
        status="APPLIED",
        filters_json=json.dumps({"territory_ids": [t.id for t in territories[:5]], "target_employee_id": target_user.id}),
        target_employee_id=target_user.id,
        conflict_policy="SKIP",
        counts_json=json.dumps({"total_candidates": 5, "new_assignments": 5, "conflicts": 0}),
        applied_at=now - dt.timedelta(days=5),
    )
    session.add(batch1)
    session.flush()

    for t in territories[:5]:
        item = MappingBatchItem(
            batch_id=batch1.id,
            action="ASSIGN",
            employee_id=target_user.id,
            territory_id=t.id,
            before_state=None,
            after_state=json.dumps({"assigned_at": str(now - dt.timedelta(days=5))}),
        )
        session.add(item)
    result.created += 1

    # 2. Create a REVERTED territory batch
    batch2 = MappingBatch(
        mode="TERRITORY",
        status="REVERTED",
        filters_json=json.dumps({"territory_ids": [t.id for t in territories[5:8]], "target_employee_id": target_user.id}),
        target_employee_id=target_user.id,
        conflict_policy="REPLACE",
        counts_json=json.dumps({"total_candidates": 3, "new_assignments": 3, "conflicts": 1}),
        applied_at=now - dt.timedelta(days=2),
        reverted_at=now - dt.timedelta(days=1),
    )
    session.add(batch2)
    session.flush()

    for t in territories[5:8]:
        item = MappingBatchItem(
            batch_id=batch2.id,
            action="ASSIGN",
            employee_id=target_user.id,
            territory_id=t.id,
            before_state=None,
            after_state=json.dumps({"assigned_at": str(now - dt.timedelta(days=2))}),
        )
        session.add(item)
    result.created += 1

    session.flush()
    return result
