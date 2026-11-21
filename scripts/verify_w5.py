"""Verification script for Wave W5 Backend deliverables."""

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from app.db.session import SessionLocal
from app.modules.common.models import AuditLog
from app.modules.expenses.models import ExpenseLimit
from app.modules.mappings.models import MappingBatch
from app.modules.settings.models import AppSetting, GeofenceSetting


def main() -> int:
    session = SessionLocal()
    try:
        app_settings_count = session.query(AppSetting).count()
        geofence_count = session.query(GeofenceSetting).count()
        limits_count = session.query(ExpenseLimit).count()
        audit_count = session.query(AuditLog).count()
        mappings_count = session.query(MappingBatch).count()

        total_config = app_settings_count + geofence_count + limits_count

        print("=" * 60)
        print("W5 BACKEND VERIFICATION REPORT")
        print("=" * 60)
        print(f"app_settings rows:      {app_settings_count}")
        print(f"geofence_settings rows: {geofence_count}")
        print(f"expense_limits rows:    {limits_count}")
        print(f"TOTAL CONFIG ROWS:      {total_config} (Threshold: >= 30)")
        print(f"audit_logs rows:        {audit_count} (Threshold: >= 30)")
        print(f"mapping_batches rows:   {mappings_count}")
        print("=" * 60)

        failed = False
        if total_config < 30:
            print(f"[FAIL] Config rows ({total_config}) is below mandatory minimum of 30!")
            failed = True
        else:
            print(f"[PASS] Config rows ({total_config}) meets mandatory >= 30 requirement.")

        if audit_count < 30:
            print(f"[FAIL] Audit log rows ({audit_count}) is below mandatory minimum of 30!")
            failed = True
        else:
            print(f"[PASS] Audit log rows ({audit_count}) meets mandatory >= 30 requirement.")

        if failed:
            return 1
        print("\nAll W5 database thresholds successfully verified!")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
