# Wave W6 Backend Verification Evidence

**Date**: 2026-11-21  
**Target**: Wave W6 Backend (Verification, Fixes, Reimbursement Payout Hardening, Provisional Seeds, Company Profile, Meetings Workflow, Calendar Month View).

---

## 1. Automated Smoke Matrix Results
Command:
```powershell
python scripts/smoke_all_endpoints.py
```
- **Total Endpoints Tested**: 320 checks across roles (`ADMIN`, `MANAGER`, `MR`)
- **500 Internal Server Errors**: 0
- **Unexpected 403 / 404 Errors**: 0
- **Summary**: `SUMMARY: Total Checks: 320 | Failures: 0`

---

## 2. Pytest Execution Evidence
Command:
```powershell
pytest
```
- **Passed Tests**: 76
- **Failed Tests**: 0
- **Execution Time**: 21.49s
- **Key Test Suites Added in Wave W6**:
  1. `tests/test_w6_regressions.py` (Visits Summary drilldowns, DCR visit type, Customer city traversal, smoke matrix assertion)
  2. `tests/test_expenses_payout.py` (Payout modes, permission check, UTR validation, idempotent repeat, status check)
  3. `tests/test_w6_features.py` (Provisional seeds, confirm endpoints, company profile CRUD, auth config branding, meetings workflow inbox, calendar month view)

---

## 3. Implemented Components Summary
1. **Reimbursement Payout Review**:
   - `ExpensePayout` model with unique constraint on `expense_id`.
   - `GET /api/v1/expenses/payout-modes` serving `["NEFT", "RTGS", "UPI", "CHEQUE", "CASH"]`.
   - Guarded for `APPROVED` status only.
   - Non-cash UTR validation enforced.
   - Idempotency key supported.
   - Feature flag `reimbursement.payout_enabled` supported.
2. **5 Provisional Masters**:
   - Added `is_provisional` boolean column to `master_items`.
   - Seeded `ATTACHMENT_TYPE`, `DOCTOR_TYPE`, `SUPPLIER`, `HOSPITAL_CATEGORY`, `PRODUCT_GALLERY` with `is_provisional=True`.
   - Added single confirm `POST /api/v1/masters/{type}/{id}/confirm` and bulk confirm `POST /api/v1/masters/{type}/confirm-bulk`.
   - Added waiting UI specifications in `docs/waiting-ui/supplier-master.md` and `docs/waiting-ui/product-gallery-master.md`.
3. **Application Setting (Company Profile)**:
   - Created `CompanyProfile` model and `company_profile` table.
   - Implemented `GET /api/v1/company-profile` and `PUT /api/v1/company-profile` (Admin only, audited).
   - Injected `company_name`, `company_code`, `logo_url` into `GET /api/v1/auth/config`.
4. **Meetings Workflow**:
   - Created `Meeting` model with standard audit and foreign keys to `users`.
   - Added `GET /api/v1/meetings/summary` (counts for Drafts with +, Applied, Received, Total).
   - Added `GET`, `POST`, `POST /submit`, `POST /approve`, `POST /reject`.
5. **Unified Calendar API**:
   - Implemented `GET /api/v1/calendar/month?employee_id=&year=&month=`.
   - Returns 28-31 day cells with daily operational counts (`doctor`, `chemist`, `stockist`, `new_doctor`, `new_chemist`, `new_stockist`, `total_pob`) and events (`holidays`, `leaves`, `tour_plan_days`, `meetings`).
