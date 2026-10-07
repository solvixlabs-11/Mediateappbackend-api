# Changelog - Mediate Healthcare MR Backend API

## [Phase 7] - Reports Engine & Export Infrastructure (2026-10-04)

### Added
- **Report Registry Engine (`app/modules/reports/`)**:
  - Modular class-based registry (`BaseReport`, `ReportRegistry`) with 14 production reports registered:
    - R01: `dcr_detailed` (DCR Detailed Report, date-wise grouping with subtotals)
    - R02: `daily_activity` (MR Daily Activity Summary)
    - R03: `customer_visits` (Customer-wise Visit History)
    - R04: `customer_coverage` (Customer Coverage Report, A/B/C tier reach)
    - R05: `mr_performance` (MR Monthly Performance vs Targets)
    - R06: `pending_late_dcr` (Pending & Late DCR Report)
    - R07: `geo_verification` (Geo-verification & Geofence Audit)
    - R08: `planned_vs_actual` (Planned vs Actual Route Analysis)
    - R09: `attendance` (Attendance & Shift Punctuality Report)
    - R10: `leave_report` (Leave Utilisation & Entitlement Report)
    - R11: `expense_report` (Expense Claims & Receipt Audit Report)
    - R12: `tour_plan_report` (Tour Plan & Route Deviation Report)
    - R13: `follow_up_report` (Customer Follow-up Task Aging Report)
    - R14: `approval_turnaround` (Managerial Decision & SLA Turnaround Report)
- **Targets Module (`app/modules/targets/`)**:
  - `targets` table for monthly field performance quotas (visits, doctor calls, chemist calls, primary and secondary sales).
  - Alembic migration `a1b2c3d4e5f6_phase7_targets.py` applied on SQL Server database.
  - Endpoints: `GET /api/v1/targets` and `PUT /api/v1/targets` (ADMIN and MANAGER).
- **Reports Endpoints (`app/modules/reports/router.py`)**:
  - `GET /api/v1/reports`: dynamic catalog filtered by caller role (`ADMIN`, `MANAGER`, `MR`).
  - `GET /api/v1/reports/{key}`: paged JSON with meta, columns, summary, items, and pagination.
  - `GET /api/v1/reports/{key}/export`: streaming file export (`?format=pdf` or `?format=xlsx`).
  - Backward-compatible dashboard endpoint `GET /api/v1/reports/dashboard`.
- **Strict Role Scoping (`core/scope.py`)**:
  - MR forced to self data only (`mr_id = user_id`); requesting other IDs returns `403` with code `REPORT_SCOPE_DENIED`.
  - MANAGER restricted to assigned team members; requesting outside team returns `403` with code `REPORT_SCOPE_DENIED`.
  - ADMIN has unrestricted global operational scope.
  - Audit logging row (`REPORT_EXPORT`) recorded on every file export.
- **Export Engines**:
  - **PDF Export (`app/modules/reports/pdf.py`)**: ReportLab generator with deep green `#0C5D46` header band, filter block, light green `#DCFCE7` KPI strip, zebra table with repeated headers, two-pass `NumberedCanvas` ("Page X of Y"), and bundled Unicode TTF font for Indian Rupee symbol (`₹`). Landscape orientation enabled for wide tables. R01 date-wise grouping with subtotals.
  - **Excel Export (`app/modules/reports/excel.py`)**: OpenPyXL generator with "Summary" and "Data" sheets (and "By Date" for R01), deep green header styling, freeze panes `A2`, auto-filters, custom column widths, and live Excel `SUM` formulas.
- **Validation**:
  - Maximum 92 days date range validation (`REPORT_RANGE_TOO_LARGE`).
  - Start date > end date validation (`INVALID_FILTER`).
  - Export row limit 50,000 records (`EXPORT_TOO_LARGE`).
  - Asia/Kolkata timezone normalization to exact UTC range.
- **Testing**:
  - Added comprehensive test suite `tests/test_report_engine_and_exports.py` covering registry, catalog, scoping, validations, JSON execution, PDF & Excel exports, empty results, targets CRUD, and 23:30 IST boundary.
  - 54 total passing pytest tests; mypy and ruff 100% green.

---

## [Phase 6] - Tasks, Notifications & Commercial Orders (2026-10-03)

### Added
- Tasks management with attachments and comments (`tasks`, `task_attachments`, `task_comments`).
- In-app notification center and real-time alerts (`notifications`).
- Product catalog and commercial order bookings (`products`, `orders`, `order_items`).

---

## [Phase 5] - Approvals, Tour Program, Expenses & Leaves (2026-10-02)

### Added
- **Approval Engine (`app/modules/approvals/`)**:
  - Multi-step approval request workflows (`approval_requests` and `approval_history` tables).
  - Manager inbox endpoint (`GET /api/v1/approvals/inbox`) scoped via `manager_mr_assignments`.
  - Pending approval count metric (`GET /api/v1/approvals/pending-count`).
  - Decision processing (`POST /api/v1/approvals/{id}/decision`) with **BR-08** mandatory comments on rejection.
- **Tour Program (`app/modules/tours/`)**:
  - Tour Program management (`tour_programs` table).
  - Validation rule **BR-09**: strict prevention of overlapping tours for the same MR.
  - Automatic creation of linked approval requests for reporting managers on submit.
  - Endpoints: `POST /api/v1/tours/`, `GET /api/v1/tours/`, `GET /api/v1/tours/upcoming`.
- **Expense Claims (`app/modules/expenses/`)**:
  - Daily field expense claim records (`expenses` table) supporting `DAILY_ALLOWANCE`, `TRAVEL_FARE`, `LODGING`, and `MISCELLANEOUS`.
  - Receipt attachment metadata and client UUID idempotency.
  - Monthly summary endpoint (`GET /api/v1/expenses/summary`) aggregating Total Claimed, Approved, Pending, and Rejected.
  - Integrated approval hook propagating manager comments on rejection.
- **Leave Management (`app/modules/leaves/`)**:
  - Leave balances and applications (`leave_balances` and `leave_requests` tables).
  - Annual entitlement tracking for Casual (CL), Sick (SL), and Earned (EL) leaves.
  - Full-day and half-day (0.5) support.
  - Rule **BR-09**: no overlapping leave periods.
  - Rule **BR-10**: balance validation, automatic balance deduction on approval, and reversal on cancellation.
- **Testing**:
  - Added `tests/test_approvals_tour_expense_leave.py` covering end-to-end multi-step approval workflows, overlap validations, expense claims, and balance deduction logic (35 total passing pytest tests).

---

## [Phase 4] - Daily Call Report (DCR), Visit Planning & Follow-ups (2026-10-01)

### Added
- **DCR & Visits (`app/modules/dcr/`)**:
  - `planned_visits`, `dcr_visits`, `dcr_details`, `post_call_analysis`, and `follow_ups` tables.
  - Multi-step visit logging: customer selection, geo-tagging, purpose, discussion notes, samples, and chemist orders.
  - Server-side geofence verification and auto-completion of scheduled visit plans.
  - Automated follow-up task generator for Doctors and Chemists.
  - Daily summary endpoint (`GET /api/v1/dcr/summary`) returning calls completed, planned count, chemist orders, and POB total.
  - Test suite `tests/test_dcr.py`.

---

## [Phase 3] - Attendance & Geofencing (2026-10-01)

### Added
- **Attendance Module (`app/modules/attendance/`)**:
  - `attendance` table with GPS tracking (`check_in_time`, `check_out_time`, latitude, longitude, accuracy, mock flag, address, work duration).
  - Today status endpoint (`GET /api/v1/attendance/today`) and history (`GET /api/v1/attendance/history`).
  - Strict idempotency: 409 conflict returned for duplicate check-ins on same day with differing client UUID.
  - Reverse geocoding and mock location detection flags.

---

## [Phase 2] - Masters, Territories & Customers (2026-10-01)

### Added
- **Masters Module (`app/modules/masters/`)**:
  - Generic master items and hierarchical geographical tables (`states`, `cities`, `areas`).
  - Bulk dropdowns endpoint (`GET /api/v1/masters/bulk-dropdowns`).
- **Territories Module (`app/modules/territories/`)**:
  - `territories`, `territory_areas`, and `user_territory_assignments`.
- **Customers Module (`app/modules/customers/`)**:
  - `doctors`, `hospitals`, `chemists`, `stockists`, and hospital doctor mappings.
  - Haversine radius queries for nearby customers (`GET /api/v1/customers/nearby`).
  - Excel bulk import endpoints.

---

## [Phase 1] - Authentication & Security (2026-09-30)

### Added
- **Database Schema**: Phase 1 tables: `roles`, `permissions`, `role_permissions`, `users`, `manager_mr_assignments`, `refresh_tokens`, `audit_logs`, `files`.
- **Alembic Baseline**: Initial migration `411b81995e29_phase1_auth_users_baseline`.
- **Seeding Script**: Initial roles (`ADMIN`, `MANAGER`, `MR`), full permission matrix, and default demo accounts.
- **Core Security**: Argon2 password hashing, JWT access token issuing (15m expiry), and SHA-256 hashed refresh tokens (30d expiry).
- **Session & Token Rotation**: Refresh token single-flight rotation with token family reuse breach detection.
- **Rate Limiting & Lockout**: 5 consecutive failed attempts trigger a 15-minute account lockout.
- **Audit Logging**: Recorded events for login success/failure, account lockout, logout, logout-all, and password change.
- **Auth Endpoints**: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/logout-all`, `GET /auth/me`, `POST /auth/change-password`, `POST /auth/register`.
- **Testing**: Automated pytest tests passing with 100% coverage on auth lifecycles.
