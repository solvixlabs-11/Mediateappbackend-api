# Wave W7 Backend Verification Report

## 1. Summary
- **Wave**: W7 (Field Security, Device Approvals, Soft Deletes, Tour Plan Locks)
- **Status**: PASSED (100% Green)
- **Database**: SQL Server `mediate_mr_db`
- **Total Endpoint Checks**: 329
- **Failures**: 0
- **Pytest Suite**: 82 passed, 0 failed

## 2. Implemented Features
1. **Mobile Registrations Lifecycle & Security**
   - Tables: `mobile_registrations`
   - Endpoints:
     - `GET /api/v1/mobile-registrations`: Filtered listing with status, designation, territory, device, and pagination.
     - `POST /api/v1/mobile-registrations/approve`: Bulk approval activating user account (`is_active = True`) with device binding.
     - `POST /api/v1/mobile-registrations/reject`: Bulk rejection with mandatory audit remarks.
   - Summary Metric: `/api/v1/users/summary` feeds real-time `pending_registrations` count from `mobile_registrations`.
   - Seeding: 35 synthetic mobile registration records seeded.

2. **Delete My Visits (Atomic Soft-Delete with Reversion & Retention)**
   - Tables: Added `deleted_at`, `deleted_by_id`, `deletion_reason`, `deletion_token` to `dcr_visits`, `planned_visits`, and `follow_ups`.
   - Endpoints:
     - `POST /api/v1/admin/visits/delete-preview`: Previews matching visits, computes side-effects, generates cryptographic 15-minute TTL preview token.
     - `POST /api/v1/admin/visits/delete`: Atomically soft-deletes visits (max 5,000 limit), reverts linked planned visits from `COMPLETED` to `PLANNED`, sets linked follow-ups to `CANCELLED`, records comprehensive audit logs.
     - `POST /api/v1/admin/visits/restore`: Allows restoring soft-deleted batches within the 30-day retention window.
   - Security: Protected by `visits:delete` permission check.

3. **Tour Plan Locks (Multi-Scope Deadlines & Freeze Enforcement)**
   - Tables: `tour_plan_locks`
   - Scopes: `ALL`, `TERRITORY`, `EMPLOYEE` with monthly/financial year cutoffs.
   - Endpoints:
     - `GET /api/v1/tour-plan-locks`: Active and historical locks list.
     - `POST /api/v1/tour-plan-locks`: Create lock with scope and cutoff date.
     - `POST /api/v1/tour-plan-locks/{id}/unlock`: Admin unlock with mandatory reason.
     - `GET /api/v1/tour-plan-locks/history`: Audited lock/unlock history.
   - Enforcement: `check_tour_lock()` in `tours/service.py` blocks creation, updating, or submission of tour plans when locked, raising HTTP 400 `TOUR_PLAN_LOCKED`, unless administrative override is provided with justification.
   - Seeding: 16 synthetic lock records seeded.

4. **Standard Route Chart Specification**
   - Created `docs/waiting-ui/std-route-chart.md` specifying data contracts, travel distance, allowance rates, territory mapping, and clarifying UX flow.

## 3. Test & Smoke Matrix Results
- `smoke_all_endpoints.py`:
  - Total Checks: 329
  - Failures: 0
  - Roles Verified: ADMIN (200), MANAGER (Scoped/200), MR (403/Forbidden for admin-only endpoints as designed).
- Unit Tests: `pytest tests/test_w7_features.py`:
  - `test_mobile_registrations_lifecycle` -> PASSED
  - `test_delete_my_visits_with_side_effects_and_restore` -> PASSED
  - `test_tour_plan_lock_enforcement_and_admin_override` -> PASSED
- Full Test Suite: All 82 test cases passed.
