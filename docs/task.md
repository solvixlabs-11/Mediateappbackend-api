# Tasks - Mediate Healthcare MR App

How to use: tick `[x]` when the task is finished AND its checks pass. Only work on the current phase. Backend phase N must be finished before mobile phase N starts. Task ids: P<phase>-B-<n> for backend, P<phase>-M-<n> for mobile.

Current phase: Phase R (mobile repair)
Legend: [ ] todo, [~] in progress, [x] done

## Phase -1: Before any code (owner tasks)
- [x] P-1-01 Create the six context files (prd, architecture, rules, design, task, memory) and copy them into docs/ of both repos
- [x] P-1-02 Create folders mr-backend and mr-mobile, run git init in both
- [x] P-1-03 Answer the open questions in prd.md section 10 (at least Q1 to Q5) and note answers in memory.md
- [x] P-1-04 Install tools: Python 3.12/3.14, Node LTS, Git, SQL Server, VS Code or Antigravity
- [x] P-1-05 Android phone ready: developer options and USB debugging on
- [ ] P-1-06 Create Expo account (for EAS builds)
- [ ] P-1-07 Google Maps API key for Android (keep private)
- [ ] P-1-08 Firebase project for push notifications (FCM) - can wait until Phase 6
- [x] P-1-09 Decide app package id (example com.mediatehealthcare.mrapp) and app name
- [x] P-1-10 Prepare company logo and brand colours (or use placeholders)
- [x] P-1-11 Give the kickoff prompt to the agent in each repo and review its summary

## Phase 0: Setup
Backend
- [x] P0-B-01 Project skeleton and folder structure from architecture.md
- [x] P0-B-02 Settings (.env), logging, error handlers, request id, /health
- [x] P0-B-03 DB base mixins, session, Alembic baseline
- [x] P0-B-04 Docker, docker-compose (API + SQL Server), Makefile, pyproject
- [x] P0-B-05 pytest setup with passing health test, ruff, mypy
- [x] P0-B-06 export_openapi script (make openapi)
Mobile
- [x] P0-M-01 Expo TypeScript project with dev-client, folder structure
- [x] P0-M-02 Theme tokens from design.md, shared components
- [x] P0-M-03 Axios client with refresh logic, auth store with SecureStore
- [x] P0-M-04 Navigation shell, role-based tab config, ErrorBoundary, Toast
- [x] P0-M-05 Offline foundation: sqlite init, outbox table, network hook
- [x] P0-M-06 gen:api script, lint, typecheck, jest
- [x] P0-M-07 Development build running in Expo dev client over LAN

## Phase 1: Auth, Users, Profile (features 1, 2, 33)
Backend
- [x] P1-B-01 Tables: roles, permissions, role_permissions, users, refresh_tokens, manager_mr_assignments, audit_logs, files
- [x] P1-B-02 Seed roles, permissions, admin user, dev sample users
- [x] P1-B-03 Register, login, refresh (rotation), logout, logout-all, me, change-password
- [x] P1-B-04 Login rate limit and lockout; audit events
- [x] P1-B-05 require_permission and core/scope.py
- [x] P1-B-06 Users CRUD, activate/deactivate, assign manager, manager MR list
- [x] P1-B-07 Profile endpoints and file upload with StorageProvider
- [x] P1-B-08 Tests (permission, scope) and openapi export
Mobile
- [~] P1-M-01 Splash, login, forced change password
- [x] P1-M-02 Session restore, refresh flow, permissions hook
- [~] P1-M-03 Role-based tabs with Coming Soon screens
- [x] P1-M-04 Profile screen with photo upload, logout, logout-all
- [~] P1-M-05 Users list/detail/create/edit, assign manager, My Team
- [~] P1-M-06 Tests, typecheck, lint; real-phone test of token expiry

## Phase 2: Masters and Customers (features 5, 29, 4, 3, 10, 11)
Backend
- [x] P2-B-01 Master tables and generic master endpoints, seed values
- [x] P2-B-02 Territories, assignments, customer coverage
- [x] P2-B-03 Hospitals and hospital_doctors mapping
- [x] P2-B-04 Doctors, chemists, stockists CRUD with filters and search
- [x] P2-B-05 Nearby endpoints using haversine
- [x] P2-B-06 Excel import with row-wise report
- [x] P2-B-07 Scope rules and tests; openapi export
Mobile
- [~] P2-M-01 Master data cache (works offline)
- [~] P2-M-02 EntityPicker and LocationCard (Use current location)
- [~] P2-M-03 Doctor, hospital, chemist, stockist list/detail/add-edit
- [~] P2-M-04 Admin masters and territories screens
- [~] P2-M-05 Nearby customers screen; tests

## Phase 3: Attendance and Geofence (features 6, 25)
Backend
- [x] P3-B-01 attendance table and geofence_settings
- [x] P3-B-02 geofence.verify service and endpoints
- [x] P3-B-03 Check-in, check-out, today, history, team, admin correction
- [x] P3-B-04 Accuracy and mock-location flags; tests with known coordinates
Mobile
- [x] P3-M-01 useLocation hook with permission flow
- [x] P3-M-02 Home check-in card and check-in/out flow
- [~] P3-M-03 Offline check-in via outbox
- [~] P3-M-04 Attendance history and team attendance
- [~] P3-M-05 Geofence settings screen (admin); real-phone GPS tests

## Phase 4: Plan, DCR, Post-call, Follow-up (features 8, 7, 9, 23)
Backend
- [x] P4-B-01 planned_visits and products placeholder table (no FK)
- [x] P4-B-02 dcr_visits, product/sample/gift lines (no FK), post_call_analysis
- [x] P4-B-03 DCR submit with server geofence and check-in rule
- [x] P4-B-04 follow_ups, history, customer timeline
- [x] P4-B-05 Missed-plan job, idempotency tests; openapi export
Mobile
- [x] P4-M-01 Today screen and Plan visit
- [x] P4-M-02 DCR multi-step form with drafts (products step disabled)
- [~] P4-M-03 Post-call analysis screen
- [~] P4-M-04 Follow-ups tabs and customer history timeline
- [~] P4-M-05 Offline outbox for plan, DCR, follow-up; tests

## Phase 5: Approvals, Tour, Expense, Leave (features 19, 16, 17, 18)
Backend
- [x] P5-B-01 Approval engine tables, matrix endpoints, callbacks, events
- [x] P5-B-02 Tours with overlap rule and apply-to-plan
- [x] P5-B-03 Expenses with receipts, caps, monthly summary
- [x] P5-B-04 Leaves with balances, overlap and cancel rules
- [x] P5-B-05 Tests including matrix conditions; openapi export
Mobile
- [~] P5-M-01 Approvals inbox, detail, approve/reject
- [~] P5-M-02 Approval matrix screen (admin)
- [x] P5-M-03 Tour planner
- [x] P5-M-04 Expense entry with receipt camera
- [~] P5-M-05 Leave apply, balances, history; My Requests view

## Phase R: Mobile repair (before Phase 6)
- [x] R0 Freeze, tag pre-repair, baseline and audit files
- [x] R1 Environment and native modules, new dev build if needed
- [x] R2 Contract sync with latest openapi.json
- [x] R3 Auth and session cleanup
- [x] R4 Navigation refactor (modals to screens)
- [ ] R5 Screen audit and fixes
- [ ] R6 Build missing screens of Phases 1-5
- [ ] R7 Real-phone test pass
- [ ] R8 Close out docs and tag mobile-repair-1

## Phase 6: Tasks, Chat, Notifications, Meetings, Joint Working (features 20, 21, 22, 30, 31)
Backend
- [ ] P6-B-01 Tasks, summary, overdue logic
- [ ] P6-B-02 Task chat with polling and ChatTransport abstraction
- [ ] P6-B-03 Notifications, device tokens, PushProvider (Expo)
- [ ] P6-B-04 Event hooks from tasks, approvals, reminders
- [ ] P6-B-05 APScheduler reminder jobs
- [ ] P6-B-06 Meetings and joint working
- [ ] P6-B-07 Tests; openapi export
Mobile
- [ ] P6-M-01 Tasks lists and detail with status change
- [ ] P6-M-02 Task chat
- [ ] P6-M-03 Push registration and deep links; notification center
- [ ] P6-M-04 Meetings screens
- [ ] P6-M-05 Joint working form

## Phase 7: Dashboard, Reports, Export, Maps (features 26, 27, 28, 24)
Backend
- [ ] P7-B-01 targets table and endpoints
- [x] P7-B-02 Dashboard endpoints (MR, manager, admin)
- [ ] P7-B-03 Report registry and core reports
- [ ] P7-B-04 Excel and PDF export
- [ ] P7-B-05 Maps endpoints (team, route, customers, visits)
- [ ] P7-B-06 Tests; openapi export
Mobile
- [x] P7-M-01 Dashboards per role (Admin/Manager Live Field Activity Section 8.2 & MR Dashboard)
- [ ] P7-M-02 Reports screens with filters
- [ ] P7-M-03 Export download and share
- [ ] P7-M-04 Team map, route map, customers map, visits map
- [ ] P7-M-05 Targets screen

## Phase 8: Products, Samples, Inventory, E-Detailing, Orders (features 12, 13, 32, 14, 15)
Backend
- [ ] P8-B-01 Brands, categories, products, media, import
- [ ] P8-B-02 promo_items (sample, gift, material)
- [ ] P8-B-03 Inventory ledger, balances, allocation, return, adjust
- [ ] P8-B-04 Migration adding foreign keys to DCR and plan lines; stock check on DCR submit
- [ ] P8-B-05 Presentations, slides, detailing sessions
- [ ] P8-B-06 Orders with PDF receipt
- [ ] P8-B-07 Product, sample, order, stock reports and dashboard KPIs
- [ ] P8-B-08 Concurrency test for negative stock; openapi export
Mobile
- [ ] P8-M-01 Product catalog
- [ ] P8-M-02 My stock and allocation screens
- [ ] P8-M-03 Enable DCR products, samples, gifts with live stock check
- [ ] P8-M-04 E-detailing viewer with offline package
- [ ] P8-M-05 Orders create, history, PDF share
- [ ] P8-M-06 Product/sample/order reports UI

## Phase 9: Offline Sync, Integrations, Hardening, Release (features 35, 34)
Backend
- [ ] P9-B-01 Sync pull and push with conflict policy
- [ ] P9-B-02 Integration provider interfaces and API-key auth
- [ ] P9-B-03 Rate limits, headers, CORS, readiness endpoint
- [ ] P9-B-04 Production Docker, CI workflow, backup notes
- [ ] P9-B-05 Load test notes for sync and DCR
Mobile
- [ ] P9-M-01 Local repositories and full outbox sync engine
- [ ] P9-M-02 Sync status and conflict screens
- [ ] P9-M-03 Media pre-download and upload queue
- [ ] P9-M-04 EAS build profiles, icons, splash, permission texts
- [ ] P9-M-05 Error reporting hook, final polish, real-phone test matrix
- [ ] P9-M-06 Preview APK to testers, then production build

## Backlog (ideas, not approved)
- Web admin portal for bulk work
- Hindi / Gujarati languages
- Dark mode
- WebSocket chat
- iOS release