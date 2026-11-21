"""Ordered master registry for database seeders.

Usage:
    python -m seed.seed_all
    python -m seed.seed_all --dev
    python -m seed.seed_all --only designations,divisions
    python -m seed.seed_all --skip doctors,chemists
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal

# Import seeders in strict dependency order
from seed import (
    seed_roles,
    seed_permissions,
    seed_designations,
    seed_divisions,
    seed_categories,
    seed_doctor_meeting_types,
    seed_visit_types,
    seed_qualifications,
    seed_specialities,
    seed_units,
    seed_issue_types,
    seed_leave_types,
    seed_financial_years,
    seed_general_settings,
    seed_entry_configs,
    seed_application_setting,
    seed_states,
    seed_cities,
    seed_areas,
    seed_territories,
    seed_users,
    seed_hospitals,
    seed_doctors,
    seed_chemists,
    seed_stockists,
    seed_products,
    seed_holidays,
    seed_report_definitions,
    seed_visits,
    seed_leaves,
    seed_tour_plans,
    seed_attendance,
    seed_orders,
    seed_system_settings,
    seed_geofence_settings,
    seed_expense_types,
    seed_expense_limits,
    seed_audit_logs,
    seed_mapping_batches,
    seed_mobile_registrations,
    seed_tour_plan_locks,
)

SEEDERS = [
    ("roles", seed_roles.run, False),
    ("permissions", seed_permissions.run, False),
    ("designations", seed_designations.run, False),
    ("divisions", seed_divisions.run, False),
    ("categories", seed_categories.run, False),
    ("doctor_meeting_types", seed_doctor_meeting_types.run, False),
    ("visit_types", seed_visit_types.run, False),
    ("qualifications", seed_qualifications.run, False),
    ("specialities", seed_specialities.run, False),
    ("units", seed_units.run, False),
    ("issue_types", seed_issue_types.run, False),
    ("leave_types", seed_leave_types.run, False),
    ("financial_years", seed_financial_years.run, False),
    ("general_settings", seed_general_settings.run, False),
    ("entry_configs", seed_entry_configs.run, False),
    ("application_setting", seed_application_setting.run, False),
    ("states", seed_states.run, False),
    ("cities", seed_cities.run, False),
    ("areas", seed_areas.run, False),
    ("territories", seed_territories.run, False),
    ("users", seed_users.run, False),
    ("hospitals", seed_hospitals.run, False),
    ("doctors", seed_doctors.run, False),
    ("chemists", seed_chemists.run, False),
    ("stockists", seed_stockists.run, False),
    ("products", seed_products.run, False),
    ("holidays", seed_holidays.run, False),
    ("report_definitions", seed_report_definitions.run, False),
    ("system_settings", seed_system_settings.run, False),
    ("geofence_settings", seed_geofence_settings.run, False),
    ("expense_types", seed_expense_types.run, False),
    ("expense_limits", seed_expense_limits.run, False),
    # Dev-only seeders
    ("visits", seed_visits.run, True),
    ("leaves", seed_leaves.run, True),
    ("tour_plans", seed_tour_plans.run, True),
    ("attendance", seed_attendance.run, True),
    ("orders", seed_orders.run, True),
    ("audit_logs", seed_audit_logs.run, True),
    ("mapping_batches", seed_mapping_batches.run, True),
    ("mobile_registrations", seed_mobile_registrations.run, True),
    ("tour_plan_locks", seed_tour_plan_locks.run, True),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Mediate Healthcare DB Seeder")
    parser.add_argument("--dev", action="store_true", help="Include synthetic development records")
    parser.add_argument("--only", type=str, default="", help="Comma-separated list of seeders to run")
    parser.add_argument("--skip", type=str, default="", help="Comma-separated list of seeders to skip")
    args = parser.parse_args()

    only_set = {s.strip().lower() for s in args.only.split(",") if s.strip()}
    skip_set = {s.strip().lower() for s in args.skip.split(",") if s.strip()}

    session = SessionLocal()
    print("=" * 70)
    print("🌱 Starting Mediate Healthcare Seed Engine...")
    print(f"Mode: {'DEVELOPMENT (--dev)' if args.dev else 'CONFIG ONLY'}")
    print("=" * 70)

    total_created = 0
    total_updated = 0
    total_unchanged = 0

    try:
        for name, seeder_fn, is_dev in SEEDERS:
            if only_set and name not in only_set:
                continue
            if name in skip_set:
                continue
            if is_dev and not args.dev:
                continue

            res = seeder_fn(session, dev=args.dev)
            session.commit()
            total_created += res.created
            total_updated += res.updated
            total_unchanged += res.unchanged
            print(f"  {res}")

        print("=" * 70)
        print(f"✅ Seeding Complete! Created: {total_created} | Updated: {total_updated} | Unchanged: {total_unchanged}")
        print("=" * 70)
    except Exception as e:
        session.rollback()
        print(f"❌ Error during seeding: {e}", file=sys.stderr)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
