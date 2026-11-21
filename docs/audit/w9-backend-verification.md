# Wave W9 Backend Verification Report: Financial Years & What's New Releases

**Date:** 2026-11-21  
**Auditor:** Senior Backend Architecture & API Engineering  
**Scope:** Wave W9 Backend Implementation & Integration  
**Result:** **100% PASSED** (362/362 Smoke Endpoint Checks, 84/84 Full Pytests, 0 Regressions)

---

## 1. Executive Summary

Wave W9 introduces corporate financial year governance and in-app system changelog engine:
1. **Financial Years (`financial_years`)**: Corporate fiscal periods (e.g. `2024-2025`, `2025-2026`, `2026-2027`) with strict validation ($start\_date < end\_date$), exclusive single `is_current` fiscal year activation, and indexing for tour plans and sales performance.
2. **App Releases & What's New (`app_releases`)**: System version changelogs, feature highlights array, audience targeting (`ALL`, `ADMIN`, `MR`, `MANAGER`), and APK download links for mobile field representatives.

---

## 2. Implemented Endpoints & Schemas

| Method | Endpoint Path | Role Permissions | Description |
|---|---|---|---|
| `GET` | `/api/v1/financial-years` | Authenticated | List all corporate fiscal years with search and pagination |
| `GET` | `/api/v1/financial-years/current` | Authenticated | Retrieve the active current financial operating year |
| `GET` | `/api/v1/financial-years/{id}` | Authenticated | Retrieve fiscal year details by ID |
| `POST` | `/api/v1/financial-years` | `settings:write` | Create new fiscal year with date ordering validation |
| `PUT` | `/api/v1/financial-years/{id}` | `settings:write` | Update fiscal year parameters |
| `POST` | `/api/v1/financial-years/{id}/set-current` | `settings:write` | Set year as current (atomically unsetting previous) |
| `GET` | `/api/v1/releases` | Authenticated | List published product release notes |
| `GET` | `/api/v1/releases/latest` | Authenticated | Fetch latest release note for banners or modal |
| `GET` | `/api/v1/releases/{id}` | Authenticated | Get full changelog details |
| `POST` | `/api/v1/releases` | `settings:write` | Publish new app/web release note |
| `PUT` | `/api/v1/releases/{id}` | `settings:write` | Update release note |

---

## 3. Verification Test Evidence

### A. Endpoint Smoke Matrix (`scripts/smoke_all_endpoints.py`)
```
SUMMARY: Total Checks: 362 | Failures: 0
Status: 100% PASS
```

### B. Automated Pytest Suites (`pytest tests/`)
```
tests/test_w9_financial_years_and_releases.py .. [100%]
Full Suite: 84 passed, 187 warnings in 28.79s (0 failures)
```

---

## 4. Database Schema Migrations

Executed `scripts/migrate_w9_schema.py` against SQL Server `mediate_mr_db`:
- Table `financial_years` created with indexes `ix_financial_years_code`, `ix_financial_years_is_current`, `ix_financial_years_is_active`.
- Table `app_releases` created with indexes `ix_app_releases_version`, `ix_app_releases_release_date`, `ix_app_releases_is_published`.
- Seeded default baseline data via `seed_financial_years` and `seed_app_releases`.
