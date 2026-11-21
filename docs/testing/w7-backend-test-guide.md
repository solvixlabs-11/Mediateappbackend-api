# Wave W7 Backend Testing Guide

## Overview
This guide provides instructions for validating the Wave W7 features on the FastAPI backend:
- Mobile Device Registration Approvals
- Visit Soft Deletions & Atomic Rollbacks
- Tour Plan Lock Deadlines & Overrides

## Prerequisites
1. Activate virtual environment:
   ```powershell
   cd e:\Mediate\Mediateappbackend-api
   .\.venv\Scripts\Activate.ps1
   ```
2. Verify database connection to SQL Server `mediate_mr_db`.

## 1. Schema Migration & Verification
Run the migration script to verify schema consistency:
```powershell
python scripts/migrate_w7_schema.py
```
Expected output:
- `✓ Checked/Created mobile_registrations table`
- `✓ Checked/Added soft-delete columns to dcr_visits`
- `✓ Checked/Added soft-delete columns to planned_visits`
- `✓ Checked/Added soft-delete columns to follow_ups`
- `✓ Checked/Created tour_plan_locks table`

## 2. Seed Data Execution
Run synthetic seeds for mobile registrations and tour plan locks:
```powershell
python scripts/seed_all.py
```

## 3. Automated Endpoint Smoke Matrix
Execute the full 329-check endpoint smoke matrix:
```powershell
python scripts/smoke_all_endpoints.py
```
Expected output:
```text
SUMMARY: Total Checks: 329 | Failures: 0
```

## 4. Pytest Lifecycle Tests
Run dedicated W7 test cases:
```powershell
pytest tests/test_w7_features.py -v
```
Test cases executed:
1. `test_mobile_registrations_lifecycle`: Tests listing, bulk approve (enables user), and bulk reject.
2. `test_delete_my_visits_with_side_effects_and_restore`: Tests preview token generation, atomic soft delete, planned visit revert to PLANNED, follow-up cancellation, and restoration.
3. `test_tour_plan_lock_enforcement_and_admin_override`: Tests creation lock rejection with `TOUR_PLAN_LOCKED`, admin override with reason, and unlock.
