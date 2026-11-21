# Wave W6 Backend Inspection Report (Stage 0: Inspect First)

**Date**: 2026-11-21  
**Author**: Antigravity  
**Repository**: `Mediateappbackend-api`  
**Standard**: Conforming to `docs/wave-rules.md` and `docs/w6-w8-roadmap-spec.md` Section 1 & 4.  

---

## 1. Executive Summary

Wave W6 is the **verification, hardening, and foundation correction wave**. Before proceeding to new functional waves (W7 Field Security and W8 Sample Stock Ledger), all discrepancies between previous session claims, reference screens, and code implementations must be inspected, documented with empirical evidence, and corrected.

---

## 2. Claim versus Evidence Audit (10 Discrepancy Checks)

The roadmap specification (`docs/w6-w8-roadmap-spec.md` Section 1) raised 10 specific questions on previous assertions. Here is the verified codebase inspection:

| No | Claim / Summary Statement | Reference / Spec Reality | Codebase Evidence & Finding | Action in Wave W6 |
|---|---|---|---|---|
| **1** | "Application Setting redirected to General Settings" | Reference app defines Application Setting as the Company Profile (Name, Code, Area, Phone, Mobile, Address, Logo, Signature) feeding report headers & branding. | `AppRoutes.tsx` had `<Route path="/utility/admin-panel/application-setting" element={<Navigate to="/utility/admin-panel/general-settings" replace />} />`. No backend `/company-profile` endpoint exists. | **Backend W6**: Implement `GET` & `PUT /company-profile` with file storage for logo/signature; expose branding in `/auth/config`. **Web W6**: Rebuild dedicated Company Profile page; remove redirect. |
| **2** | "Meeting Master configured as generic master item" | Reference Meeting module follows the Workflow Inbox pattern with 3 status tiles (Drafts with `+`, Applied, Received) and fields: Agenda, Start, End, Created By, Organiser. | Seeded as generic `CYCLE_MEETING` in `master_items`. No workflow inbox routing or dedicated meeting schema existed. | **Backend W6**: Implement meetings workflow service/endpoints or extend workflow service. **Web W6**: Rebuild on `WorkflowInboxPage`. |
| **3** | "My Calendar displays Tour Plans, Leaves, Holidays, Meetings" | Reference calendar requires per-day metric counts inside each date cell (Doctor, Chemist, Stockist, New Doctor, New Chemist, New Stockist, Total POB) alongside events. | Frontend rendered only event tags (`Tag color=...`); no day metric aggregation endpoint existed in backend. | **Backend W6**: Build `GET /calendar/month?employee_id=&year=&month=` returning per-day counts and calendar events. **Web W6**: Render cell counts. |
| **4** | "5 Secondary Masters fully defined" (Attachment, Doctor Type, Supplier, Hospital Category, Product Gallery) | Screen specifications for Supplier and Product Gallery have not been provided by project owner; seeded values are assumptions. | Seeded directly into `master_items` without provisional tracking. | **Backend W6**: Add `is_provisional` column to `master_items`, create `POST /masters/{type}/{id}/confirm` and bulk confirm; write `docs/waiting-ui/supplier-master.md` and `product-gallery-master.md`. |
| **5** | "Reimbursement Processing with UTR payout live" | Reimbursement payout is outside PRD scope (no Accounts role in v1). Payout endpoint was unhardened and lacked idempotency and feature flags. | `POST /expenses/{id}/payout` existed in `expenses/router.py`, writing to `rejection_reason` string. Lacked idempotency key, unique constraint, permission guard `expenses:payout`, and toggle setting. | **Backend W6**: Harden payout: only APPROVED claims, idempotent payout constraint/key, decimal amounts, API payment modes, UTR validation, `reimbursement.payout_enabled` setting, audit logging. |
| **6** | "Terminal AttributeErrors on DCR drilldown" | Two unhandled exceptions reached the user during drilldown: `DcrVisit` has no `call_type`, and `Doctor` has no `city`. | Root cause: safe relationship access was missing. Code was patched in place but lacked smoke matrix regression tests. | **Backend W6**: Create `scripts/smoke_all_endpoints.py`, add explicit regression unit tests, verify all 16 metrics card counts match row counts. |
| **7** | "Group D has 10 items" | Re-inspection of `navigation_items.json` reveals 11 distinct legacy/ERP routes in this group. | `find_unhandled.cjs` confirmed: Credit Notes (2), Delivery Outward, Monthly Business, Primary Sales, Secondary Sales, Stockist Wise Sales, Incentive Master, Financial Year Master, Importers (5). | **Backend W6**: Produce `docs/audit/backend-endpoint-coverage.md` for all 105 items; mark legacy ERP items as DEFERRED per D1/D4 decisions. |
| **8** | "Std Route Chart is a weekly beat plan" | Reference app displays Drafts/Applied/Received workflow tiles with town routes and From/To employee/territory; form fields unseen. | The agent assumed weekly beat plan without UI specification. | Mark **WAITING_UI**; create `docs/waiting-ui/std-route-chart.md`. |
| **9** | "Approve Mobile Registration is device whitelist" | Reference app displays registration applications (Reg Code, Name, Designation, City, State, Territory) with bulk Approve/Reject actions. | Backend lacked dedicated `mobile_registrations` model and endpoints. | Scheduled for **Wave W7 BUILD**. |
| **10** | "88 live count verified" | Needs verification against an empirical automated smoke matrix to ensure no hidden 500s or runtime crashes. | Smoke test missing for full OpenAPI inventory. | **Backend W6**: Execute `smoke_all_endpoints.py` across all roles (ADMIN, MANAGER, MR). |

---

## 3. Detailed Inspection of W6 Backend Tasks

### 3.1 Endpoint Smoke Matrix & Regression Suite
- **Current State**: `pytest` has tests for specific modules (`tests/test_health.py`, `tests/test_w5_config.py`, etc.), but lacks an automated crawler testing every OpenAPI GET endpoint and every Visits Summary drilldown metric across roles.
- **Required**:
  1. `scripts/smoke_all_endpoints.py`: Authenticate as `admin@mediate.com`, `manager1@mediate.com`, `mr1@mediate.com`. Call all GET endpoints, resolving dynamic IDs (`employee_id`, `id`) from seeded database. Fail on any 500 or unexpected 403/404.
  2. Regression test `tests/test_w6_regressions.py`:
     - Test drilldown on `chemist_visits`, `doctor_visits`, `stockist_visits` confirming `visit_type` is read without `AttributeError: 'DcrVisit' object has no attribute 'call_type'`.
     - Test `new_doctor_visits`, `new_chemist_visits`, `new_stockist_visits` confirming safe `area.city.name` traversal without `AttributeError: 'Doctor' object has no attribute 'city'`.
     - Test that for all 16 metrics in `VisitsSummaryResponse`, the summary integer equals the length of rows returned by `get_metric_drilldown`.

### 3.2 Reimbursement Payout Hardening
- **Current State**:
  - `ExpensePayoutRequest` schema in `expenses/schemas.py`.
  - `POST /api/v1/expenses/{id}/payout` in `expenses/router.py`.
  - Method `process_payout` in `expenses/service.py` sets `exp.status = "PAID"` and stores payout details in `rejection_reason`.
- **Gaps**:
  - Can payout non-approved expenses (must enforce `status == "APPROVED"`).
  - No database-level idempotency or unique payout record (repeated call would duplicate or overwrite).
  - Payment modes are hardcoded strings in schema (`NEFT`, `RTGS`, `UPI`, `CHEQUE`, `CASH`).
  - No permission check for `expenses:payout` (must be restricted to `ADMIN`).
  - No feature flag `reimbursement.payout_enabled` in `app_settings`.
- **Required Implementation**:
  - Add `ExpensePayout` model or structured payout fields with `idempotency_key` unique constraint.
  - Require `reimbursement.payout_enabled` setting (default `true`).
  - Enforce permission `expenses:payout`.

### 3.3 Provisional Seeds & Confirmation Mechanism
- **Current State**: `master_items` table has columns `id, type, code, name, description, sort_order, is_active, created_at, updated_at, client_uuid`.
- **Gaps**: No `is_provisional` boolean column exists.
- **Required Implementation**:
  - Add `is_provisional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)` to `MasterItem`.
  - Migration / alter column script.
  - Seeders for `ATTACHMENT_TYPE`, `DOCTOR_TYPE`, `SUPPLIER`, `HOSPITAL_CATEGORY`, `PRODUCT_GALLERY` set `is_provisional = True`.
  - Endpoints:
    - `POST /api/v1/masters/{type}/{id}/confirm`
    - `POST /api/v1/masters/{type}/confirm-bulk` (takes list of IDs).
  - Write `docs/waiting-ui/supplier-master.md` and `docs/waiting-ui/product-gallery-master.md`.

### 3.4 Company Profile (`Application Setting`)
- **Current State**: Does not exist in backend.
- **Required Implementation**:
  - Table `company_profile`:
    - `id`, `company_name`, `company_code`, `area`, `address`, `city`, `state`, `pincode`, `phone`, `mobile`, `email`, `website`, `logo_file_id`, `signature_file_id`.
  - Service & Endpoints:
    - `GET /api/v1/company-profile`: Returns company profile data with logo & signature download URLs.
    - `PUT /api/v1/company-profile`: Updates company profile (ADMIN only), audits changes.
    - Expose public branding (company name, logo URL) in `GET /api/v1/auth/config`.

### 3.5 Calendar & Meetings Workflow
- **Current State**:
  - `GET /calendar/month` does not exist.
  - Meeting is stored as generic `CYCLE_MEETING` in `master_items`.
- **Required Implementation**:
  - Schema & Endpoint `GET /api/v1/calendar/month`:
    - Parameters: `employee_id: int | None`, `year: int`, `month: int`.
    - Returns:
      - `days`: list of day objects with date, day of week, and counts:
        - `doctor_visits_count`
        - `chemist_visits_count`
        - `stockist_visits_count`
        - `new_doctor_visits_count`
        - `new_chemist_visits_count`
        - `new_stockist_visits_count`
        - `total_pob`: `Decimal | None`
      - `events`: list of event objects:
        - `HOLIDAY` (from `holidays` table)
        - `LEAVE` (from `leave_applications` where status == APPROVED)
        - `TOUR_PLAN` (from `tour_plans` / `tour_plan_days`)
        - `MEETING` (from `meetings` workflow)
  - Meetings Workflow:
    - Table `meetings`: `id`, `title/agenda`, `meeting_type`, `start_datetime`, `end_datetime`, `location`, `organiser_id`, `created_by_id`, `status` (`DRAFT`, `APPLIED`, `APPROVED`, `REJECTED`), `notes`.
    - Workflow integration: Summary tiles (Drafts, Applied, Received) + List items.

### 3.6 Endpoint Coverage Audit Document
- Write `docs/audit/backend-endpoint-coverage.md`:
  - List all 105 MR Buddy menu items.
  - Map each item to its corresponding backend API endpoints and tests.
  - Clearly identify LIVE, WAITING_UI, and DEFERRED items.

---

## 4. Execution Sequence for Backend W6

```
Step 1: Write docs/audit/w6-inspection.md (Complete)
Step 2: Add regression tests for AttributeErrors & drilldown 16 metrics equality
Step 3: Build scripts/smoke_all_endpoints.py & execute smoke matrix
Step 4: Harden Reimbursement Payout (idempotent, approved only, setting flag, audit)
Step 5: Add is_provisional column to master_items, seed update, and confirmation endpoints
Step 6: Implement Company Profile module (models, router, auth/config branding)
Step 7: Implement Calendar Month API & Meetings Workflow Inbox module
Step 8: Write docs/audit/backend-endpoint-coverage.md
Step 9: Run verification protocol (pytest, ruff, smoke matrix, make openapi)
```
