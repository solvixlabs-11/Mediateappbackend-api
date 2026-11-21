# W5 Backend Architecture & Codebase Inspection Report

**Date:** 2026-11-20  
**Wave:** W5 — System Configuration, Audit Trail and Mapping Wizard  
**Target:** `Mediateappbackend-api`  

---

## 1. Executive Summary

This inspection audits all existing tables, services, seeders, and routes in `Mediateappbackend-api` to determine what already exists and what must be extended or created for Wave W5 as specified in `docs/w5-config-audit-mapping-spec.md`.

---

## 2. Component-by-Component Findings

### 2.1 System Configuration & Geofence Settings
- **Current State:**
  - `app_settings` table: **Does NOT exist** in SQL Server (`mediate_mr_db`).
  - `geofence_settings` table: **Does NOT exist** in SQL Server (`mediate_mr_db`).
  - Current configuration uses static `.env` settings (`DEFAULT_GEOFENCE_DOCTOR_RADIUS_METERS=200.0`, `DEFAULT_GEOFENCE_CHEMIST_RADIUS_METERS=150.0`, `MAX_LOCATION_ACCURACY_THRESHOLD_METERS=100.0`) in `app/core/config.py`.
  - Master items store generic key-value configs for `GENERAL_SETTING`, `ENTRY_CONFIG`, and `APPLICATION_SETTING` in `master_items`.
- **What is Missing:**
  - Dedicated `app_settings` ORM model & table with columns: `key`, `group`, `value`, `value_type`, `unit`, `min_value`, `max_value`, `allowed_options`, `help_text`, `is_provisional`, `updated_by`, `updated_at`.
  - Dedicated `geofence_settings` ORM model & table with columns: `entity_type` (DOCTOR, HOSPITAL, CHEMIST, STOCKIST), `radius_m`, `min_accuracy_m`, `is_provisional`, `is_active`.
  - Dynamic `SettingsService` providing in-memory caching, cache invalidation, typed validation, and fallback to defaults.
  - Endpoints: `GET /settings/groups`, `GET /settings`, `PUT /settings/{key}`, `PUT /settings/bulk`, `GET /settings/{key}/history`, `POST /settings/{key}/confirm`, `GET /settings/geofence`, `PUT /settings/geofence`.
  - Setting history tracking (`setting_history` or audit trail integration).

### 2.2 Expense Types & Expense Limits
- **Current State:**
  - `expenses` table exists with `expense_type` column as `String(50)` (types: `DAILY_ALLOWANCE`, `TRAVEL_FARE`, `LODGING`, `MISCELLANEOUS`).
  - `expense_limits` table: **Does NOT exist** in SQL Server (`mediate_mr_db`).
  - `designations`: Seeded via `seed_designations.py` into `master_items` with `type="DESIGNATION"` (9 codes: `ADMIN`, `ARBH`, `BH`, `DBH`, `DIRECTOR`, `MD`, `MR`, `RBH`, `ZBM`).
- **What is Missing:**
  - `expense_limits` ORM model & table: `id`, `designation_id` (or designation code), `expense_type_id` (or code), `daily_limit`, `monthly_limit`, `effective_from`, `is_provisional`, `is_active`. Unique constraint on `(designation_id, expense_type_id, effective_from)`.
  - Endpoints: `GET /expense-limits`, `PUT /expense-limits/bulk` (matrix upsert), `POST /expense-limits/{id}/confirm`.
  - Enforcement logic in `ExpenseService.create_expense`: Read `expense.limit_enforcement` setting (`OFF`, `WARN`, `BLOCK`) from `SettingsService`. When limit exceeded:
    - If `BLOCK`: raise 422 error.
    - If `WARN`: attach warning flag in description/notes for approver, do not block.
    - If `OFF`: ignore limit checks.

### 2.3 Audit Logs & Auditing
- **Current State:**
  - `audit_logs` table exists with basic columns: `id`, `user_id`, `action`, `entity_type`, `entity_id`, `details`, `ip_address`, `user_agent`, `created_at`, `updated_at`, `created_by`, `updated_by`, `is_active`, `is_deleted`, `row_version`.
  - Existing callers: Only 3 files manually instantiate `AuditLog`:
    1. `app/modules/auth/repository.py` (line 155: login/refresh token)
    2. `app/modules/reports/service.py` (lines 287, 784: report export)
    3. `app/modules/users/service.py` (line 622: user update)
  - Missing audit calls across entire system:
    - Master data CRUD (the 14 masters + Part 2 masters)
    - Authentication: failed login attempts, logouts, force logouts
    - Permissions and role assignments
    - Approval / rejection actions
    - Settings changes & expense limit updates
    - Data imports & exports
    - Bulk territory/customer mapping batches
- **What is Missing:**
  - Extend `AuditLog` model with: `module`, `channel` (WEB, MOBILE, SYSTEM), `request_id`, `result` (SUCCESS, FAILED), `summary`, `before_json`, `after_json`. Indexes on `created_at`, `user_id`, `module`, `action`, `entity_type`.
  - Unified `AuditService.record(...)` with automated sensitive data masking (passwords, tokens, OTPs, phone numbers, secret keys).
  - Endpoints: `GET /audit/logs` (paginated, sorted, filtered by user, module, action, entity, result, channel, date range), `GET /audit/logs/{id}`, `GET /audit/meta` (distinct metadata), `POST /audit/logs/export`.
  - Retention cleanup job based on `audit.retention_days`.
  - Strict RBAC: ADMIN only for `audit:read` and `audit:export` (MANAGER and MR receive 403). Append-only design (zero PUT/DELETE endpoints).

### 2.4 Mapping Wizard
- **Current State:**
  - `user_territory_assignments` table exists for employee-to-territory mapping (`user_id`, `territory_id`, `assigned_at`, `unassigned_at`).
  - Customer tables (`doctors`, `chemists`, `stockists`, `hospitals`) contain direct `territory_id` and `area_id` foreign keys.
  - `mapping_batches` and `mapping_batch_items` tables: **Do NOT exist**.
- **What is Missing:**
  - `mapping_batches` table: `id`, `mode` (`TERRITORY`, `CUSTOMER`), `status` (`DRAFT`, `APPLIED`, `REVERTED`), `filters_json`, `target_employee_id`, `conflict_policy` (`SKIP`, `REPLACE`, `ADD`), `counts_json`, `created_by`, `applied_at`, `reverted_at`.
  - `mapping_batch_items` table: `id`, `batch_id`, `action` (`ASSIGN`, `UNASSIGN`), `employee_id`, `territory_id`, `customer_type`, `customer_id`, `before_state`, `after_state`.
  - Endpoints: `GET /mappings/capabilities` (`beats=false`), `POST /mappings/preview`, `POST /mappings/{id}/apply`, `POST /mappings/{id}/revert`, `GET /mappings`, `GET /mappings/{id}`.
  - Unassign sets `unassigned_at` timestamp (soft unassign, never delete).
  - Dry-run validation with 20,000 item batch limit.

### 2.5 Dynamic Consumers
- **Current State:**
  - `dcr/service.py`: Uses `settings.DEFAULT_GEOFENCE_DOCTOR_RADIUS_METERS` and `settings.DEFAULT_GEOFENCE_CHEMIST_RADIUS_METERS`.
  - `customers/service.py`: Same hardcoded settings.
  - `attendance`: No dynamic cutoff time or late tolerance checks.
- **What is Missing:**
  - Wire `dcr.service` and `customers.service` to `SettingsService.get_geofence_radius(entity_type)`.
  - Wire `attendance.service` to `SettingsService` for `attendance.late_after_time`, `attendance.late_tolerance_minutes`, and `gps.mock_location_action`.

---

## 3. Seed Package Architecture & Requirements

To comply with the rule of $\ge 30$ records per category and zero static data:
1. `seed_system_settings.py`: 21 system settings across 9 groups (`GEOFENCE`, `GPS`, `ATTENDANCE`, `DCR`, `EXPENSE`, `NOTIFICATIONS`, `SECURITY`, `AUDIT`, `EXPORT`).
2. `seed_geofence_settings.py`: 4 geofence records (`DOCTOR`, `HOSPITAL`, `CHEMIST`, `STOCKIST`).
3. `seed_expense_types.py`: 4 standard expense types if empty (`DAILY_ALLOWANCE`, `TRAVEL_FARE`, `LODGING`, `MISCELLANEOUS`).
4. `seed_expense_limits.py`: 9 designations $\times$ 4 expense types = **36 limits** ($\ge 30$ threshold met).
5. `seed_audit_logs.py`: **60+ synthetic audit events** over the past 30 days across all action types (`CREATE`, `UPDATE`, `DELETE`, `APPROVE`, `REJECT`, `LOGIN`, `LOGIN_FAILED`, `LOGOUT`, `SETTINGS_CHANGE`, `EXPORT`, `MAPPING_APPLY`).
6. `seed_mapping_batches.py`: Seed sample applied and reverted mapping batches.

All seeders will be registered in `seed_all.py` in dependency order and will be strictly idempotent.
