"""Seed script for App Releases / What's New."""

import json
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.releases.models import AppRelease


def seed_app_releases(db: Session):
    default_releases = [
        {
            "version": "v2.2.0",
            "title": "Promotional Sample Inventory & Field Security",
            "release_date": date(2026, 11, 21),
            "release_type": "MAJOR_RELEASE",
            "summary": "Enterprise promotional sample management with batch expiry validation, monthly quotas, and dispatch tracking.",
            "highlights_json": json.dumps([
                "Central Depot Sample Inward receipt with batch QC and expiry date tracking",
                "Monthly sample quota allocation per Medical Representative and product",
                "Physical courier dispatch and receipt acknowledgment workflow",
                "Multi-echelon enterprise stock ledger with batch aging drawer",
                "Mobile device registration approval and Tour Plan Locks",
            ]),
            "target_audience": "ALL",
            "is_published": True,
            "apk_download_url": "https://releases.mediatehealthcare.com/apk/mediate-mr-v2.2.0.apk",
        },
        {
            "version": "v2.1.0",
            "title": "Field Security, Approvals & Workflow Enhancements",
            "release_date": date(2026, 11, 20),
            "release_type": "WEB_UPDATE",
            "summary": "Mobile device whitelisting, soft visit deletion with side-effect rollback, and tour cutoff locks.",
            "highlights_json": json.dumps([
                "Mobile registration verification and account auto-activation",
                "Admin visit soft-delete utility with planned visit reversal",
                "Tour plan deadline lock for state/territory level compliance",
            ]),
            "target_audience": "ALL",
            "is_published": True,
            "apk_download_url": None,
        },
        {
            "version": "v2.0.0",
            "title": "Commercial Sales, Invoicing & Geofencing Suite",
            "release_date": date(2026, 11, 15),
            "release_type": "MAJOR_RELEASE",
            "summary": "Full commercial order management, sales targets, and GPS geofence parameter configuration.",
            "highlights_json": json.dumps([
                "Chemist and stockist order booking with real-time tax calculation",
                "Target entry and primary sales achievement tracking",
                "Dynamic geofence radius settings per clinic and pharmacy",
            ]),
            "target_audience": "ALL",
            "is_published": True,
            "apk_download_url": "https://releases.mediatehealthcare.com/apk/mediate-mr-v2.0.0.apk",
        },
    ]

    for item in default_releases:
        stmt = select(AppRelease).where(AppRelease.version == item["version"])
        existing = db.scalar(stmt)
        if not existing:
            rel = AppRelease(**item)
            db.add(rel)
    db.commit()
    print("[SEED] App releases seeded successfully.")
