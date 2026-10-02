# Rules - Mediate Healthcare MR App

These rules apply to every person and every AI agent working on this project, in both mr-backend and mr-mobile. If a rule conflicts with a chat instruction, stop and ask.

## 0. Session protocol (AI agent must follow)
1. Start of every session read in this order: memory.md, task.md, rules.md, then prd.md, architecture.md and design.md as needed.
2. Work on ONE phase and ONE task group at a time. Never start a later phase.
3. Before coding, write a short plan (files, tables, endpoints or screens) and then implement.
4. Do not invent features, tables or folders that are not in prd.md, architecture.md or task.md. If something is missing, propose it and wait.
5. End of every session: tick finished items in task.md, update the current state and any new decision in memory.md, and add a line to docs/CHANGELOG.md.
6. Never mark a task done unless lint, type check and tests pass for it.
7. If you find a mistake in earlier work, say so and fix it; do not hide it.

## 1. General
- R-01 Follow the folder structure in architecture.md exactly.
- R-02 Small functions, clear names, no dead code, no copy-paste duplication.
- R-03 No secrets in code or git. Use .env and .env.example.
- R-04 Comments explain why, not what. Public services have docstrings.
- R-05 English for code, names and comments. User-facing text lives in one strings file.
- R-06 Dates in UTC ISO-8601 on the wire. Show Asia/Kolkata on screen.
- R-07 Money and quantities use decimals, never floats.

## 2. Backend rules (mr-backend)
- B-01 Python 3.12, full type hints, mypy and ruff clean. No print(), use logging.
- B-02 Every feature is app/modules/<name>/ with router, schemas, service, repository, models, permissions, constants.
- B-03 Router is thin. Business rules and transactions live in service. SQL lives in repository.
- B-04 A module never touches another module's tables; call the other module's service.
- B-05 Config only through app/core/config.py.
- B-06 SQL Server tables are snake_case plural and have the standard columns from architecture.md section 5.1.
- B-07 Schema changes only through Alembic. One migration per phase or feature. Never edit an applied migration. create_all only in tests.
- B-08 Index foreign keys and every filter/search column. Lat/lng are DECIMAL(9,6).
- B-09 Permissions with require_permission("module:action"). Data scope only through core/scope.py.
- B-10 Validate all input with Pydantic. No raw SQL unless parameterized.
- B-11 Create endpoints for mobile-created data accept client_uuid and are idempotent.
- B-12 Stock changes only through inventory.service inside one transaction with row locking.
- B-13 Write audit_logs for auth events, approvals, master-data changes and stock changes.
- B-14 File uploads check mime type and size and go through StorageProvider.
- B-15 Notifications and push must never make the main request fail.
- B-16 No microservices, no Redis/Celery unless the owner asks.

## 3. Mobile rules (mr-mobile)
- M-01 TypeScript strict, no any. ESLint and tsc clean.
- M-02 Feature folders: src/features/<feature>/{api,hooks,screens,components,schemas,types}. Shared code only in src/shared.
- M-03 Screens show UI only. No Axios calls and no business logic in screens; use hooks and services.
- M-04 API types are generated from openapi.json (npm run gen:api). Never hand-write them. Never hardcode the API URL.
- M-05 Server state with TanStack Query; small client state with Zustand.
- M-06 Tokens only in expo-secure-store. Axios refreshes once on 401 (single-flight), then logs out on failure.
- M-07 Use theme tokens from design.md. No magic numbers, no scattered inline styles.
- M-08 Reuse shared components. Build a shared component instead of copy-pasting UI.
- M-09 Every list and screen has loading, empty, error (with retry) and pull-to-refresh states.
- M-10 Long lists use FlatList with pagination, keyExtractor and memoized rows.
- M-11 Forms use react-hook-form + zod with friendly messages.
- M-12 Every record created on the phone gets a client_uuid. Offline-capable actions go through the outbox and show a Pending badge.
- M-13 Location: ask permission with a reason, foreground only, save lat, lng, accuracy and time. Handle denied and GPS-off states.
- M-14 Compress images before upload (about 1600 px max).
- M-15 Install libraries only with `npx expo install`. New native library means a new development build; note it in memory.md.
- M-16 Never edit android/ or ios/ by hand. Use config plugins and app.config.ts.
- M-17 Never show raw server errors. Show friendly text.
- M-18 Every screen is a registered route in navigation/routes.ts with typed params. Modals only for dialogs and bottom sheets.
- M-19 No mock, demo or simulated data in production paths. Mocks only in src/mocks behind a flag and listed in docs/audit/missing-endpoints.md.
- M-20 Before and after screenshots in docs/ui-baseline/ for any screen touched; the UI look is frozen (frontend-spec section 2).
- M-21 Native library added: update the native library log and rebuild the development build the same day.
- M-22 A task is "done" only with evidence: command output, screenshot or device test note.

## 4. API rules
- A-01 Prefix /api/v1. Plural nouns. Correct status codes.
- A-02 Lists are paginated (page, page_size max 100) with filter, search and sort.
- A-03 Error format: `{ "detail": "...", "code": "SOME_CODE", "errors": [] }`.
- A-04 Every endpoint has response_model, summary, tags and documented errors.
- A-05 State changes are explicit actions: approve, reject, cancel, complete, submit.
- A-06 Export openapi.json at the end of each backend phase.

## 5. Security rules
- S-01 Passwords hashed with argon2. Login is rate limited.
- S-02 Access token 15 minutes; refresh token rotates and can be revoked.
- S-03 Scope tests are mandatory: an MR must never read another MR's data.
- S-04 HTTPS only in staging and production.
- S-05 No continuous background GPS. Location only when the user acts.
- S-06 Customer phone numbers and personal data are visible only inside the role scope.

## 6. Testing rules
- T-01 Backend: pytest for every module covering happy path, validation error, permission denied, scope check and idempotency where relevant.
- T-02 Mobile: Jest + React Native Testing Library for hooks and key components.
- T-03 Run before finishing a phase: backend ruff + mypy + pytest; mobile typecheck + lint + jest.
- T-04 Fix failing tests at the root cause. Never delete or skip a test to get green.
- T-05 Real-phone test list at the end of each mobile phase (login expiry, GPS denied, airplane mode, slow network).

## 7. Git rules
- G-01 Each repo is separate. Branch names: feature/<short-name>, fix/<short-name>.
- G-02 Small commits with clear messages: `feat(dcr): submit with geofence`.
- G-03 One tag per finished phase: phase-0, phase-1, ...
- G-04 Never commit .env, keys, build output or generated native folders.

## 8. Definition of Done (per phase)
| Check | Backend | Mobile |
|---|---|---|
| Quality | ruff + mypy clean | eslint + tsc clean |
| Tests | pytest green | jest green |
| Contract | openapi.json updated | gen:api run |
| Database | migration up and down tested | offline effects tested |
| Roles | ADMIN, MANAGER, MR checked | role-based tabs checked |
| States | correct status and error codes | loading, empty, error, refresh |
| Records | task.md, memory.md, CHANGELOG updated, tagged | task.md, memory.md, CHANGELOG updated, tagged |

## 9. Forbidden
- Business logic in routers or screens.
- Hand-written API types on mobile.
- Files stored in the database.
- Skipping Alembic, editing applied migrations.
- Direct stock balance updates outside the inventory service.
- Committing secrets.
- Starting a later phase early.
- Changing the locked stack without the owner's approval.

## 10. When unsure
Stop, list the options with pros and cons, recommend one, and wait for the owner. Record the answer in memory.md under Decisions.