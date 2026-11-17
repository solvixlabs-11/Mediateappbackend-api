# Backend Audit Report — Mediate Healthcare MR API

> **Audit Date:** 2026-11-03  
> **Target:** `Mediateappbackend-api` (FastAPI + SQL Server)  
> **Auditor:** DeepMind AI Assistant  
> **Scope:** Stage 1 Audit Only (No source code modified)  
> **Status:** AUDIT COMPLETE — AWAITING "GO" FOR STAGE 2 FIXES

---

## Executive Summary

A comprehensive, zero-assumption audit of the Mediate Healthcare MR FastAPI backend was conducted against the architecture, product requirements (`BR-01` to `BR-16`), rules, and frontend specifications.

Key headline findings:
1. **16 P0 Vulnerabilities Identified:** Critical security issues include an unauthenticated `/auth/register` endpoint permitting anonymous ADMIN account creation, unauthenticated file binary download (`/files/{file_id}/download`), unauthorized approval decision processing (any MR can approve their own or any other request), wildcard CORS with credentials, and cross-rep IDOR data leaks on DCR visits, live field tracking, tour programs, expenses, and leaves.
2. **25 P1 Data & Behavioral Defects:** Missing standard audit columns (`is_deleted`, `is_active`, `row_version`), unindexed foreign keys, naive non-UTC timestamps across 36 database columns, financial and coordinate quantities defined as `FLOAT` instead of `DECIMAL`, hard deletes on tasks and notifications, broken check-in bypass (auto-checking in at `0.0, 0.0`), and lack of customer-specific geofence override columns.
3. **21 P2 API Quality, Drift & Operational Flaws:** Inconsistent pagination (`skip/limit` vs `page/page_size`), 4 unmodeled endpoints, 8 mypy errors, 9 ruff lint errors, Alembic model drift on targets and foreign key indexes, hardcoded dashboard targets, lack of a pinned dependency lock file, and lack of SQL Server automated testing.

---

## 1. Master Audit Issues Table

| ID | Area | Severity | File:Line | Problem | Proposed Fix |
|---|---|:---:|---|---|---|
| **AUD-001** | Security / Auth | **P0** | `app/modules/auth/router.py:181` | `POST /api/v1/auth/register` is unauthenticated and accepts arbitrary `role_code`. Any anonymous actor can register an active `ADMIN` account. | Restrict endpoint with `current_user: User = Depends(require_permission("users:write"))` or disable public self-registration. |
| **AUD-002** | Security / Data Leak | **P0** | `app/modules/files/router.py:48` | `GET /api/v1/files/{file_id}/download` has NO authentication. Any external user can iterate `file_id` and download expense receipts, medical documents, and photos. | Add `current_user: User = Depends(get_current_user)` and verify user has access to the linked entity (or is Admin/Manager). |
| **AUD-003** | Security / IDOR | **P0** | `app/modules/approvals/service.py:84` | `POST /api/v1/approvals/{request_id}/decision` does not verify that caller is an authorized manager or Admin. An MR can approve their own leave, expense, or tour, or reject anyone else's. | Enforce that caller's role is `ADMIN` or caller is the assigned active manager of `req.requester_id`. Reject self-approval. |
| **AUD-004** | Security / CORS | **P0** | `app/main.py:65` & `.env:7` | CORS is configured with `allow_origins=["*"]` and `allow_credentials=True`. This is invalid per CORS standards and allows cross-origin credential theft. | Specify explicit whitelisted origins in `.env` (e.g. `http://localhost:5173`, `http://192.168.1.18:8000`). Never allow `*` when credentials are True. |
| **AUD-005** | Security / IDOR | **P0** | `app/modules/dcr/service.py:248` | `GET /api/v1/dcr/visits/{visit_id}` ignores `current_user` and performs no scope/ownership check. Any MR can read any other MR's DCR calls. | Check that `dcr.user_id == current_user.id` or user is Admin/team Manager using `core/scope.py`. Return 403 on scope denial. |
| **AUD-006** | Security / IDOR | **P0** | `app/modules/dcr/service.py:297` | `POST /api/v1/dcr/follow-ups/{follow_up_id}/complete` has no ownership verification. Any MR can mark another MR's follow-up complete. | Check that `fu.user_id == current_user.id` or user has supervisory permissions. |
| **AUD-007** | Security / Scope Leak | **P0** | `app/modules/users/service.py:451` | `GET /api/v1/users/live-tracking` does not filter users by caller's scope context. Any MR calling this endpoint receives GPS coordinates for all field reps company-wide (violates BR-01). | Apply `core/scope.py`: MR gets self, Manager gets team, Admin gets all. |
| **AUD-008** | Security / IDOR | **P0** | `app/modules/tours/service.py:89` | `GET /api/v1/tours/{tour_id}` does not verify scope. Any MR can view any other MR's complete tour program. | Enforce `tour.user_id == current_user.id` or caller is assigned manager/Admin. |
| **AUD-009** | Security / Scope Leak | **P0** | `app/modules/tours/service.py:85` | `GET /api/v1/tours` assigns `user_id = None` if `role_code in ("ADMIN", "MANAGER")`. A manager sees all tours company-wide instead of only their team (violates BR-01). | Scope manager queries using `context.team_member_ids` via `core/scope.py`. |
| **AUD-010** | Security / Scope Leak | **P0** | `app/modules/expenses/service.py:92` | `GET /api/v1/expenses` assigns `user_id = None` for Managers. Managers can inspect financial expense claims and bank details of all employees across the firm. | Scope manager queries to `context.team_member_ids` via `core/scope.py`. |
| **AUD-011** | Security / Scope Leak | **P0** | `app/modules/leaves/service.py:170` | `GET /api/v1/leaves` assigns `user_id = None` for Managers. A manager sees leave applications for all employees in all regions. | Scope manager queries to `context.team_member_ids` via `core/scope.py`. |
| **AUD-012** | Security / IDOR | **P0** | `app/modules/approvals/service.py:74` | `GET /api/v1/approvals/{request_id}` ignores caller identity and allows any user to inspect any approval request. | Check that caller is the requester, assigned manager, or Admin. |
| **AUD-013** | Security / Mass Assignment | **P0** | `app/modules/users/service.py:182` | `PUT /api/v1/users/{user_id}` allows setting `role_code` and `password` without scope validation. A manager with `users:write` can elevate users to `ADMIN`. | Restrict role modifications and password changes to `ADMIN` only; validate manager scope. |
| **AUD-014** | Security / RBAC Bypass | **P0** | `app/modules/products/router.py:78,94` | `POST /api/v1/products` and `POST /api/v1/products/{id}/visual-aids` require only `get_current_user` instead of `require_permission("products:write")`. Any MR can create products or modify visual aids. | Add `require_permission("products:write")`. |
| **AUD-015** | Security / RBAC Bypass | **P0** | `app/modules/notifications/router.py:63` | `POST /api/v1/notifications` requires only `get_current_user`. Any MR can broadcast arbitrary notifications to any user ID. | Add `require_permission("notifications:write")` or restrict broadcast to Admin. |
| **AUD-016** | Security / Config | **P0** | `app/core/config.py:59` | `SECRET_KEY` has a hardcoded default string and does not fail fast in production if unset or weak. | Validate `SECRET_KEY` on startup; fail fast if length < 32 or equals default when `ENVIRONMENT != "development"`. |
| **AUD-017** | Security / Headers | **P1** | `app/main.py:61` | FastAPI app lacks HTTP security headers (HSTS, X-Content-Type-Options, X-Frame-Options, Content-Security-Policy). | Add a security headers middleware to inject standard OWASP headers. |
| **AUD-018** | Security / Exposure | **P1** | `app/main.py:55-57` | `/docs`, `/redoc`, and `/openapi.json` are exposed unconditionally across all environments. | Disable `docs_url` and `redoc_url` when `ENVIRONMENT == "production"` unless explicitly enabled via config flag. |
| **AUD-019** | Security / Config | **P1** | `app/core/config.py:25` | `DEBUG: bool = True` defaults to True. If omitted from `.env` in production, debug mode remains on. | Default `DEBUG = False`; validate that `DEBUG` cannot be True when `ENVIRONMENT == "production"`. |
| **AUD-020** | Security / Brute Force | **P1** | `app/modules/auth/service.py:83` | Login rate limiting only tracks failed attempts on recognized user emails; no IP-based rate limiting exists. | Add IP-based rate limit middleware (e.g. max 10 failed attempts/minute per IP). |
| **AUD-021** | Security / Leak | **P1** | `app/core/security.py:109` | `decode_access_token` leaks raw `JWTError` exceptions to client (`Token validation failed: {exc}`). | Return a generic `"Token validation failed or expired"` message. |
| **AUD-022** | Security / DoS | **P1** | `app/modules/files/service.py:56` | `await file.read()` buffers entire upload into RAM before validating file size. Large uploads can crash the worker process. | Stream file chunks and reject immediately when byte counter exceeds `MAX_FILE_SIZE_BYTES`. |
| **AUD-023** | Security / Validation | **P1** | `app/modules/files/service.py:47` | File upload relies solely on client-supplied `content_type` header; no magic byte/header verification is performed. | Validate initial magic bytes for PNG, JPEG, WEBP, and PDF. |
| **AUD-024** | Data Integrity / Drift | **P1** | `app/db/__init__.py:1` | `Target` model (`app.modules.targets.models`) is not imported into `app/db/__init__.py`. `alembic check` flags `targets` as a removed table. | Import `app.modules.targets.models` into `app/db/__init__.py`. |
| **AUD-025** | Data Correctness / Money | **P1** | `expenses`, `orders`, `products` models | Money amounts (`expenses.amount`, `orders.total_amount`, `order_items.unit_price`, `products.mrp`, `products.gst_rate`) and leave balances use `FLOAT` (violates R-07). | Change column types to `DECIMAL(12, 2)` or `NUMERIC(12, 2)` and Pydantic schemas to `Decimal`. |
| **AUD-026** | Data Correctness / Coordinates | **P1** | `attendances`, `doctors`, `hospitals`, `chemists`, `stockists`, `dcr_visits` | Latitude and longitude are defined as `FLOAT` instead of `DECIMAL(9, 6)` (violates B-08). | Change column types to `DECIMAL(9, 6)` in SQLAlchemy models and Alembic migration. |
| **AUD-027** | Data Architecture | **P1** | Multiple models | `attendances`, `dcr_visits`, `planned_visits`, `expenses`, `leaves`, `tours`, `orders`, `tasks`, `approval_requests` lack standard columns (`is_deleted`, `is_active`, `row_version`, and `client_uuid` on `orders` and `tours`) (violates B-06). | Inherit `StandardAuditMixin` across all domain entity models. |
| **AUD-028** | Data Correctness / Idempotency | **P1** | All tables with `client_uuid` | `client_uuid` has an index but NO database UNIQUE constraint, permitting duplicate records on concurrent retries (violates BR-12). | Add `UniqueConstraint("client_uuid")` in SQLAlchemy models and Alembic migration. |
| **AUD-029** | Data Correctness / Timestamps | **P1** | 36 columns across models | 36 DateTime columns lack `timezone=True`. Code uses `datetime.utcnow()` returning offset-naive datetimes (violates R-06, BR-16). | Set `DateTime(timezone=True)` on all timestamp columns; replace `utcnow()` with `datetime.now(UTC)`. |
| **AUD-030** | Performance / DB | **P1** | 6 foreign key columns | `dcr_visits.joint_manager_id`, `dcr_post_call_analyses.dcr_visit_id`, `follow_ups.dcr_visit_id`, `expenses.approval_request_id`, `leave_requests.approval_request_id`, `tour_programs.approval_request_id` lack indexes (violates B-08). | Add indexes in models and generate Alembic migration. |
| **AUD-031** | Business Rule / BR-03 | **P1** | `app/modules/dcr/service.py:94` | BR-03 requires check-in before DCR. Code auto-creates fake attendance check-ins at `(0.0, 0.0)` instead of rejecting or checking admin toggle. | Check if attendance check-in exists; if missing and enforce-check-in setting is enabled, raise `HTTPException(400, "Daily check-in required before submitting DCR")`. |
| **AUD-032** | Business Rule / BR-05 | **P1** | `app/modules/customers/models.py` | Customer models lack `geofence_radius_meters` override columns, preventing customer-level overrides. | Add nullable `geofence_radius_meters: Mapped[float | None]` to `Doctor`, `Chemist`, `Hospital`, `Stockist`. |
| **AUD-033** | Business Rule / BR-06 | **P1** | `app/modules/dcr/router.py` | No endpoint exists to edit a submitted DCR within the 24-hour edit window or for admin correction with audit log. | Implement `PUT /api/v1/dcr/visits/{id}` with 24-hour window check and `POST /api/v1/dcr/visits/{id}/admin-correct`. |
| **AUD-034** | Business Rule / BR-11 | **P1** | `tasks/repository.py:27`, `notifications/repository.py:53` | `delete_task` and `delete_notification` execute `db.delete()` (hard delete) instead of soft deletion (violates BR-11). | Set `is_deleted = True` and filter `is_deleted == False` on queries. |
| **AUD-035** | Business Rule / BR-12 | **P1** | `app/modules/dcr/service.py:259` | `create_follow_up` accepts `client_uuid` but does not query for existing records before inserting. Duplicate retries create duplicate rows. | Query `get_by_client_uuid(payload.client_uuid)` and return existing record if present. |
| **AUD-036** | Business Rule / BR-13 | **P1** | `dcr/service.py:146`, `attendance/service.py:59` | Mock GPS (`is_mock_location == True`) is silently accepted and marked `is_geofence_verified=True`. Low accuracy is not compared against threshold. | If `is_mock_location` is True or `accuracy > MAX_THRESHOLD`, set `is_geofence_verified=False` and flag record. |
| **AUD-037** | Concurrency / Logic | **P1** | `customers/repository.py:25` | Customer codes (`_next_code`) are generated via `db.query().count()`, causing unique constraint collisions under concurrent creation. | Use database sequence or atomic identity-based code generation. |
| **AUD-038** | Performance / N+1 | **P2** | `app/modules/users/service.py:89` | `list_users` executes 2 queries per user row to fetch manager details, generating 102 queries for a 50-user page. | Eager-load active manager assignments using `selectinload` or joined queries. |
| **AUD-039** | Database / Pool | **P2** | `app/db/session.py:17` | Engine lacks `pool_recycle` setting. SQL Server drops idle connections after timeouts, causing unhandled disconnections. | Add `pool_recycle=1800` to `create_engine`. |
| **AUD-040** | Database / Transactions | **P2** | `app/db/session.py:28` | `get_db()` dependency does not execute `db.rollback()` on exception. Dirty transactions can return to the connection pool. | Wrap yield in `try ... except: db.rollback(); raise finally: db.close()`. |
| **AUD-041** | Code Quality / Type Check | **P1** | `app/modules/users/service.py:455,513`, `reports/definitions/` | 8 mypy type errors found in 3 files (`UserTerritory` attribute error, `profile_picture_url` attribute error, etc.). | Fix incorrect model import to `UserTerritoryAssignment`, fix attribute names, and resolve type annotations. |
| **AUD-042** | Code Quality / Lint | **P1** | `app/modules/users/service.py`, `reports/definitions/` | 9 ruff lint errors found (unused imports, ambiguous variable `l`, unformatted import block, `== True` comparisons). | Run `ruff check --fix` and clean up imports and variable names. |
| **AUD-043** | API Quality / Pagination | **P2** | Multiple modules | Inconsistent pagination parameters: `users` and `reports` use `page/page_size`, while others use `skip/limit` and return bare arrays (violates A-02). | Standardize all list endpoints to `{ items: [], total: int, page: int, page_size: int }`. |
| **AUD-044** | API Quality / Limit Cap | **P2** | `tasks`, `notifications`, `products`, `orders` | Query parameters allow `limit` up to 200 (violates rule of max 100). | Update parameter validators to `le=100`. |
| **AUD-045** | API Quality / Response Model | **P2** | 4 endpoints | `GET /files/{id}/download`, `DELETE /notifications/{id}`, `DELETE /tasks/{id}`, `GET /reports/{key}/export` lack `response_model` declarations (violates A-04). | Declare appropriate response models or response classes. |
| **AUD-046** | API Quality / Untyped JSON | **P2** | `customers`, `territories`, `notifications` | Endpoints return raw `dict` or `list` (`map_doctor_to_hospital`, `unassign_user`, `mark_all_read`). | Replace with typed Pydantic models (`MessageResponse`, etc.). |
| **AUD-047** | Business Logic / Hardcoded Targets | **P2** | `dashboard/service.py:311` | MR dashboard hardcodes `visits_target=12` and `monthly_target=240` rather than querying `targets` table. | Query `TargetService` for the authenticated MR's monthly target. |
| **AUD-048** | Observability / Logging | **P2** | `app/core/logging.py:15` | Log formatter does not include `request_id`, hindering trace correlation across requests. | Use a logging filter or contextvar to inject `request_id` into all log output. |
| **AUD-049** | Dynamic Data Gap | **P1** | `masters/schemas.py:53` | `MasterBulkDropdownsResponse` omits expense types, leave types, work types, visit types, status lists, cities, areas, and territories. | Expand bulk dropdown schema and service to include all required master lists. |
| **AUD-050** | Dynamic Data Gap | **P1** | Frontend Screen S58 | `/settings/geofence` and system settings table/endpoints do not exist. | Create `app/modules/settings` module with geofence, edit window, and expense cap settings. |
| **AUD-051** | Dynamic Data Gap | **P1** | Frontend Screen S42 | `/attendance/team` endpoint is missing. | Implement `/attendance/team` endpoint scoped to manager's team. |
| **AUD-052** | Dynamic Data Gap | **P1** | Frontend Screens S10, S13 | Frontend spec expects `/planned-visits/daily`; backend only exposes `/dcr/plans`. | Add `/dcr/plans/daily` route alias matching frontend spec expectations. |
| **AUD-053** | Dynamic Data Gap | **P1** | Frontend Screens S39, S43 | Map telemetry endpoints (`/maps/team-locations`, `/maps/mr/{id}/route`) are missing. | Create `app/modules/maps` with scoped location and route polyline endpoints. |
| **AUD-054** | Dynamic Data Gap | **P1** | Frontend Screen S57 | `/approvals/workflows` is missing. | Implement approval workflow matrix configuration endpoints for Admin. |
| **AUD-055** | Dynamic Data Gap | **P1** | Frontend Screens S33, S60 | `/inventory/my-stock` and stock allocation endpoints are missing. | Implement `app/modules/inventory` ledger and balance endpoints. |
| **AUD-056** | Dynamic Data Gap | **P1** | Frontend Screens S35, S61 | `/presentations` slide-show admin endpoints are missing. | Add presentations module or endpoints wrapping visual aids. |
| **AUD-057** | Dynamic Data Gap | **P1** | Frontend Screens S32, S48 | `/meetings` and `/joint-working` endpoints are missing. | Implement meetings and joint working observation endpoints. |
| **AUD-058** | Test Architecture | **P1** | `tests/conftest.py:19` | Test suite runs exclusively against in-memory SQLite (`sqlite:///:memory:`). No tests run against SQL Server. | Add SQL Server test database capability in `conftest.py` enabled via environment flag. |
| **AUD-059** | Test Coverage | **P1** | 24 endpoints | 24 endpoints have no test coverage in `tests/`, including approval decisions, hospital CRUD, and user management. | Write test cases covering happy path, validation, 403 forbidden, and scope checks. |
| **AUD-060** | Operations / Lockfile | **P2** | Repository Root | No pinned dependency lock file (`requirements.txt`, `poetry.lock`) exists; `pyproject.toml` contains only unpinned `>=` constraints. | Generate and commit a pinned `requirements.lock` or `requirements.txt`. |
| **AUD-061** | Operations / Pytest Cov | **P2** | Virtual Environment | `pytest-cov` is not installed; `pytest --cov=app` fails. | Add `pytest-cov` to dev dependencies. |
| **AUD-062** | Deprecation Warning | **P2** | `app/core/security.py:17` | `passlib 1.7.4` emits deprecation warnings on Python 3.12+ when querying `argon2.__version__`. | Pin direct `argon2-cffi` hasher or silence warning via pytest/passlib configuration. |

---

## 2. Detailed Findings by Check Area

### A. Endpoint Matrix & IDOR Assessment
- **Matrix Script:** Created at `scripts/endpoint_matrix.py`. Scans 122 registered routes.
- **Unauthenticated Endpoints Found:**
  1. `POST /api/v1/auth/register` (P0 — Allows unauthorized registration of any role, including Admin).
  2. `GET /api/v1/files/{file_id}/download` (P0 — Allows public binary download of any file).
- **IDOR Audit:**
  - `GET /api/v1/dcr/visits/{visit_id}`: No scope check; any MR can view any other MR's DCR calls.
  - `POST /api/v1/dcr/follow-ups/{follow_up_id}/complete`: No ownership check; any MR can close another MR's follow-up.
  - `POST /api/v1/approvals/{request_id}/decision`: No check that approver is authorized for the requester; allows self-approval.
  - `GET /api/v1/tours/{tour_id}`: No scope check.
  - `GET /api/v1/tours`, `GET /api/v1/expenses`, `GET /api/v1/leaves`: All assign `user_id = None` for Managers, leaking all company-wide records to any manager.
  - `GET /api/v1/users/live-tracking`: Returns all field staff coordinates without checking caller scope.

### B. Security & Authentication
- **JWT Secret:** Default fallback in `app/core/config.py:59` allows insecure default if omitted from `.env`. Must fail fast on startup in production.
- **Algorithm:** Fixed to `HS256`.
- **Token Types:** Access tokens have `"type": "access"`. Refresh tokens are random url-safe strings hashed with SHA-256 in the database.
- **Access Expiry:** 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 15`).
- **Refresh Rotation:** Implemented with family tracking and revocation on reuse detection.
- **Deactivated Access:** Enforced in `get_current_user` dependency via database check on every request.
- **Argon2:** Time cost 2, memory cost 65536, parallelism 2.
- **Login Rate Limit:** User-level lockout after 5 failed attempts for 15 minutes. Missing IP-level rate limiting.
- **Error Messages:** Returns `"Invalid email or password"` for both missing user and wrong password.
- **Session Revocation:** Password change revokes all active refresh tokens.
- **CORS:** Uses `allow_origins=["*"]` with `allow_credentials=True` (P0).
- **Security Headers:** Missing entirely.
- **Docs Exposure:** Swagger UI and ReDoc exposed unconditionally.
- **Stack Traces:** Exception handlers do not leak stack traces, but `decode_access_token` leaks raw `JWTError` messages.
- **File Upload:** MIME check relies only on client header; file read buffers entire payload into memory.

### C. Data Correctness & Business Rules (BR-01 to BR-16)

#### Business Rule Compliance Matrix

| Rule | Description | Code Location | Test Location | Status |
|---|---|---|---|:---:|
| **BR-01** | MR sees own; Manager sees team; Admin sees all | `app/core/scope.py` | `tests/test_users.py`, `tests/test_report_engine_and_exports.py` | **PARTIAL** (Leaked in tours, expenses, leaves, live-tracking) |
| **BR-02** | 1 check-in & 1 check-out per user per day | `app/modules/attendance/service.py:43` | `tests/test_dcr.py:test_attendance_lifecycle` | **PASS** |
| **BR-03** | DCR requires check-in (admin can toggle) | `app/modules/dcr/service.py:94` | `tests/test_dcr.py` | **FAIL** (Auto-creates fake check-in at 0,0) |
| **BR-04** | Server decides geofence verified/not | `app/modules/dcr/service.py:143` | `tests/test_dcr.py:test_dcr_visit_flow_with_geofence` | **PARTIAL** (Missing coords faked as verified) |
| **BR-05** | Geofence default per type + customer override | `app/modules/dcr/service.py:110` | None | **FAIL** (Customer override column missing) |
| **BR-06** | Submitted DCR editable only in edit window | None | None | **FAIL** (Endpoint missing) |
| **BR-07** | Sample/gift stock never negative; ledger only | None | None | **FAIL** (Inventory module missing) |
| **BR-08** | Approvals follow matrix; reject needs comment | `app/modules/approvals/service.py:112` | `tests/test_approvals_tour_expense_leave.py` | **PARTIAL** (Reject comment checked, but no matrix or auth) |
| **BR-09** | Tour plans & leaves cannot overlap | `leaves/service.py:70`, `tours/service.py:50` | `tests/test_approvals_tour_expense_leave.py` | **PASS** |
| **BR-10** | Leave balance reduced on approve, restored on cancel | `approvals/service.py:147`, `leaves/service.py:153` | `tests/test_approvals_tour_expense_leave.py` | **PASS** |
| **BR-11** | Records never hard-deleted; use soft delete | `tasks/repository.py:27`, `notifications/repo.py:53` | None | **FAIL** (Tasks & notifications hard deleted) |
| **BR-12** | Mobile records carry client_uuid; idempotent | Multiple services | `tests/test_dcr.py` | **PARTIAL** (Follow-up, tour, order omit check; no DB unique constraint) |
| **BR-13** | Mock or low-accuracy GPS flagged on attendance/DCR | `attendance/service.py`, `dcr/service.py` | None | **FAIL** (Mock GPS accepted as verified; accuracy threshold ignored) |
| **BR-14** | Deactivated users lose access immediately | `users/service.py:241`, `dependencies.py:49` | `tests/test_users.py:test_user_deactivation_immediate_revocation` | **PASS** |
| **BR-15** | Inactive master values stay visible on old records | Customer & DCR models | `tests/test_masters.py` | **PASS** (Values stored denormalized/strings) |
| **BR-16** | Timestamps stored in UTC, shown in Asia/Kolkata | `reports/utils.py` | `tests/test_report_engine_and_exports.py` | **PARTIAL** (36 DB columns naive; code uses deprecated `utcnow()`) |

### D. API Quality
- **Error Format:** `{ "detail": "...", "code": "...", "errors": [] }` standard is registered and working across exception handlers.
- **Status Codes:** Mostly correct (`201` for creates, `404` for missing, `403` for forbidden), but several DELETE routes return `200` with ad-hoc dictionary responses rather than `204 No Content`.
- **Response Models:** 4 routes lack `response_model`; 3 routes return raw untyped `dict`.
- **OpenAPI Export:** Verified; exports cleanly to all target locations via `scripts/export_openapi.py`.

### E. Dynamic Data Support (Screen Matrix Check)

For each screen in `frontend-spec.md` Section 4:
- **S01–S05 (Common):** `/auth/me`, `/auth/login`, `/auth/change-password`, `/users/me/profile`, `/notifications` exist.
- **S06–S08 (Sync & Offline):** `/sync/push`, `/sync/pull` are missing (Phase 9 scope).
- **S10, S13 (MrHome, TodayPlan):** `/planned-visits/daily` missing; `/dcr/plans` exists with date query.
- **S12 (AttendanceHistory):** `/attendance/history` exists but lacks standard pagination and tests.
- **S21 (PostCall):** Standalone `/dcr/{id}/post-call` missing (bundled into visit create).
- **S32 (Meetings):** `/meetings` endpoint missing.
- **S33, S60 (Stock):** `/inventory/my-stock` and allocation endpoints missing.
- **S35, S61 (Presentations):** `/presentations` endpoints missing.
- **S39, S43 (Maps):** `/maps/mr/{id}/route` and `/maps/team-locations` missing.
- **S42 (Team Attendance):** `/attendance/team` endpoint missing.
- **S48 (Joint Working):** `/joint-working` endpoint missing.
- **S57 (Approval Matrix):** `/approvals/workflows` missing.
- **S58 (Geofence Settings):** `/settings/geofence` missing.

### F. Operations
- **Startup Settings:** Settings do not validate or fail fast on missing environment variables.
- **SQL Server Connection:** SQLEXPRESS connection was verified on port 1433. However, pyodbc login handshake takes ~45s in this hypervisor environment, causing default 30s timeouts unless `login_timeout=60` is set. `pool_recycle` is missing.
- **Alembic:**
  - `alembic upgrade head` succeeded from fresh baseline through all 7 migrations.
  - `alembic check` detected model drift: `targets` table was flagged as removed due to missing import in `app/db/__init__.py`, along with missing index declarations on foreign keys.
  - `alembic downgrade -1` succeeded cleanly.
- **Seed Script:** `scripts/seed_rich_data.py` was inspected and verified to be idempotent using existence queries.
- **Dependencies:** Python 3.14.6 is in use. No lockfile (`requirements.lock` or `poetry.lock`) exists; only unpinned `>=` constraints in `pyproject.toml`.

### G. Test Suite & Code Quality
- **Ruff:** 9 lint errors found (unused imports, ambiguous variable `l`, unformatted import block, `== True` comparisons).
- **Mypy:** 8 typecheck errors found (`UserTerritory` attribute error, `profile_picture_url` attribute error, etc.).
- **Pytest:** 55 passed in 9.95s with 62 deprecation warnings (`datetime.utcnow()` and `passlib/argon2`).
- **Database Engine in Tests:** Tests run exclusively against in-memory SQLite (`sqlite:///:memory:`). No tests run against SQL Server.

---

## 3. What Could Not Be Verified

1. **Docker Image Build:** Docker CLI is not installed on this host (`docker: The term 'docker' is not recognized`).
2. **Automated Test Coverage Metric:** `pytest-cov` is not installed in the virtual environment.
3. **Automated Tests Against SQL Server:** The test harness in `tests/conftest.py` is hardcoded to SQLite and lacks a configuration toggle for SQL Server.

---

## 4. Next Steps

Per user instructions:
- **STAGE 1 IS COMPLETE.** Source code has NOT been modified.
- **AWAITING USER MESSAGE "GO"** to begin STAGE 2 (Fixing P0, P1, P2 issues with tests).

