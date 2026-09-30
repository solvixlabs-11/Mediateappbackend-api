# Architecture - Mediate Healthcare MR App

## 1. Overview
```
        Phone (React Native + Expo, TypeScript)
   Local SQLite cache + Outbox   |   SecureStore (tokens)
                     |
                  HTTPS (JSON, REST, /api/v1)
                     |
        FastAPI backend (Python, modular monolith)
   Auth | Users | Masters | Customers | Attendance | DCR | Approvals
   Tasks | Notifications | Reports | Maps | Products | Inventory | Orders | Sync
                     |
            SQLAlchemy 2.x + Alembic
                     |
   +-----------------+------------------+
   |                                    |
 SQL Server (all structured data)   Object storage (Azure Blob / S3)
                                    photos, receipts, PDFs, slides
```
Later and only if needed: Redis + Celery for heavy background jobs. Not in v1.

## 2. Stack (locked)
| Layer | Choice | Notes |
|---|---|---|
| Mobile | React Native + Expo (development build) + TypeScript strict | Android first |
| Navigation / data | React Navigation, TanStack Query, Zustand, Axios | Server state in Query, small client state in Zustand |
| Forms | react-hook-form + zod | Same rules as backend validation |
| Device | expo-location, expo-image-picker, expo-notifications, expo-secure-store, expo-sqlite, NetInfo, react-native-maps | Installed with `npx expo install` |
| Backend | Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic | REST only |
| Database | Microsoft SQL Server via pyodbc (ODBC Driver 18) | |
| Auth | JWT access 15 min + refresh with rotation, argon2 | |
| Files | StorageProvider: local (dev), Azure Blob or S3 (prod) | DB keeps metadata only |
| Export | openpyxl (Excel), reportlab (PDF) | |
| Scheduler | APScheduler in-process for reminders | Single instance limit, documented |
| Deploy | Docker, Nginx if needed | Same image in dev, staging, prod |

## 3. Expo decision and conditions
Decision D-01: use Expo with a **development build** (dev-client) from Phase 0. Expo Go is allowed only for a quick experiment, never for the main app.

| Condition | Rule |
|---|---|
| Workflow | Managed Expo with config plugins. Generate native folders with `npx expo prebuild` only when needed. Never hand-edit android/ or ios/ folders (they are generated) |
| Installing libraries | Always `npx expo install <package>` so versions match the Expo SDK. Adding a native library means a new development build |
| SDK upgrades | Upgrade only between phases, never mid-phase. Follow the Expo upgrade guide and run all tests |
| Running on phone | Build a development APK once (EAS cloud build, or `npx expo run:android` with USB debugging). Daily work: `npx expo start --dev-client`, scan QR with the installed dev app |
| Backend address | Phone cannot use localhost. Set `EXPO_PUBLIC_API_URL=http://<PC-LAN-IP>:8000` and run the backend on 0.0.0.0. Same Wi-Fi. Allow the port in the firewall |
| HTTP vs HTTPS | Plain http is for local dev builds only. Staging and production must use HTTPS. If Android blocks cleartext in a dev build, enable it with expo-build-properties for the development profile only |
| Maps | react-native-maps needs a Google Maps API key for Android, added in app.config.ts. Keep the key out of git (EAS secrets / env) |
| Push notifications | Need a development build and Firebase (FCM) credentials for Android. Test on a real phone, not an emulator |
| Background sync | Use the Expo background task API that matches the installed SDK (check current Expo docs before coding). Sync must also run on app foreground and on network regain, so background is a bonus, not the only trigger |
| Permissions | Declared in app.config.ts with clear usage texts: location (while in use), camera, photos, notifications |
| Build profiles (eas.json) | development (dev client, internal), preview (APK for testers), production (store build) |
| App identity | Name: Mediate MR. Package / bundle id (example): com.mediatehealthcare.mrapp. Confirm before first store build, it cannot change later |
| iOS | Needs an Apple Developer account (paid) for real-device builds. Start after Android is stable |
| Eject | Not planned. If truly needed, use prebuild, not a separate bare project |

## 4. Backend architecture
### 4.1 Layers (every module)
| File | Job | Never |
|---|---|---|
| router.py | Parse request, auth dependency, call service, return response_model | Business rules, DB queries |
| schemas.py | Pydantic in/out models | DB access |
| service.py | Business rules, validation, transactions, events | HTTP objects |
| repository.py | SQLAlchemy queries | Business or permission decisions |
| models.py | Tables | Logic |
| permissions.py / constants.py | Permission codes, enums | |
A module never reads another module's tables directly. It calls that module's service.

### 4.2 Module map
core, db, common, integrations (shared) and modules: auth, users, files, settings, masters, territories, hospitals, doctors, chemists, stockists, attendance, geofence, planning, dcr, followups, approvals, tours, expenses, leaves, tasks, notifications, meetings, joint_working, dashboard, reports, maps, products, promo_items, inventory, edetailing, orders, sync.

### 4.3 Request flow
```
Mobile -> Router (auth + permission) -> Service (rules, scope, transaction)
       -> Repository (SQL) -> SQL Server
Service -> domain event -> Notification service -> Push provider
```

## 5. Data architecture
### 5.1 Standard columns
id (BIGINT identity), client_uuid (nullable unique, mobile-created only), created_at, updated_at (UTC), created_by, updated_by, is_active, is_deleted, row_version.

### 5.2 Main relationships
```
roles -> users -> manager_mr_assignments
users -> attendance -> dcr_visits -> post_call_analysis -> follow_ups
territories -> customers (doctors, hospitals, chemists, stockists)
hospitals <-> doctors (hospital_doctors)
users -> planned_visits -> dcr_visits
dcr_visits -> dcr_product_lines / dcr_sample_lines / dcr_gift_lines
approval_workflows -> approval_steps ; approval_requests -> approval_actions
tour_plans / expenses / leave_requests -> approval_requests
promo_items -> stock_allocations -> inventory_ledger -> mr_stock_balances
products -> product_media ; presentations -> slides -> slide_views
orders -> order_items -> products
```

### 5.3 Data scoping (one central helper)
core/scope.py returns the allowed user ids for the caller: ADMIN all, MANAGER own team, MR self. Every query for scoped data uses it. No endpoint writes its own scope logic.

## 6. Authentication and authorization
1. Login returns access token (15 min) and refresh token (7-30 days).
2. App sends `Authorization: Bearer <access>`. On 401 it refreshes once (single-flight), then retries.
3. Refresh rotates: old token revoked, new pair issued. Reuse of an old token revokes the whole session family.
4. Logout revokes the refresh token; logout-all revokes every device.
5. Permissions are codes like `doctors:write`, loaded with `/auth/me`; the app hides actions, the server enforces them.

## 7. API contract flow
Backend exports `openapi.json` at the end of every phase (`make openapi`). Mobile runs `npm run gen:api` to generate TypeScript types. Mobile never hand-writes API types. Backend phase N must be done before mobile phase N starts.

Standard responses:
- List: `{ "items": [], "total": 0, "page": 1, "page_size": 20 }`
- Error: `{ "detail": "message", "code": "SOME_CODE", "errors": [] }`

## 8. Key subsystems
### 8.1 Geofence
common/geo.py implements haversine distance. geofence.verify(user point, customer point, radius) returns distance, radius and verified flag, taking GPS accuracy and missing customer coordinates into account. DCR submit calls it on the server and stores the result.

### 8.2 Approval engine
Generic tables drive Tour, Expense and Leave. Steps can be MANAGER, ROLE or USER with optional amount or day conditions. On the final decision the engine calls the owning module (on_approval_completed) and emits an event for notifications.

### 8.3 Inventory ledger
Append-only ledger plus a balance table with CHECK (balance >= 0). One transaction with row locking updates both. DCR submit distributes stock in the same transaction and is idempotent.

### 8.4 Notifications
Domain events create in-app notifications and send push through PushProvider (Expo push). Push failure is logged and ignored. APScheduler runs reminder jobs (DCR pending, follow-up due, overdue tasks).

### 8.5 Files
POST /files validates type and size, stores through StorageProvider, saves metadata. Other APIs use file_id. Images are compressed on the phone before upload.

### 8.6 Reports and export
Report registry: each report has filters, query, columns and title. JSON for screens, xlsx or pdf for export. Large exports are limited and streamed.

### 8.7 Maps
Backend returns points (team locations, routes, customers, visits). The phone draws them with react-native-maps. No continuous tracking in v1.

## 9. Offline and sync architecture
```
User action -> local SQLite cache (optimistic) + Outbox row (client_uuid)
Network back / app foreground / pull-to-refresh
  -> Sync engine: push outbox (POST /sync/push) then pull changes (GET /sync/pull?since=)
```
| Topic | Rule |
|---|---|
| Idempotency | Same client_uuid never creates two records; server answers DUPLICATE |
| Push result per item | APPLIED, DUPLICATE, CONFLICT (server copy returned), REJECTED (error code) |
| Conflicts | Master data: server wins. Mobile-created records: client wins only if row_version matches base_version, otherwise user chooses Keep mine or Use server |
| Validation | Sync uses the same services as normal APIs, so no rule is bypassed |
| Pull | By updated_at with tombstones for deleted rows, scoped by role, paged |
| Offline features | Attendance, planned visits, DCR, follow-ups, orders, detailing sessions, expense drafts, task status |
| Cached for reading | Masters, customers, products, presentations, today's plan |
| Foundation from Phase 0 | client_uuid, updated_at, row_version on every mobile-created table; outbox table and network hook in the app |

## 10. Environments and deployment
| Env | Purpose | Notes |
|---|---|---|
| Local | Development | docker-compose: API + SQL Server; phone connects over LAN |
| Staging | Testing with testers (preview APK) | HTTPS, separate database |
| Production | Live | HTTPS, backups, monitoring |
Secrets only in .env / secret store, never in git. Same Docker image everywhere.

## 11. Observability and operations
Structured logs with request id, /health and /ready endpoints, audit_logs table (auth events, approvals, master changes, stock changes), daily database backup with a tested restore, error reporting hook on mobile (Sentry-ready).

## 12. Decision log
| ID | Decision | Reason |
|---|---|---|
| D-01 | Expo development build, not Expo Go, not bare CLI | Native features needed, less native maintenance |
| D-02 | Modular monolith, no microservices | Simple, one team |
| D-03 | SQL Server | Relational data, existing experience |
| D-04 | No Redis/Celery in v1 | Not needed yet; APScheduler is enough |
| D-05 | Files in object storage | Keep DB fast |
| D-06 | JWT access + rotating refresh | Secure, works offline-friendly |
| D-07 | OpenAPI generates mobile types | Two repos stay in sync |
| D-08 | client_uuid + idempotent creates | Safe offline retries |
| D-09 | Server decides geofence result | Phone data can be faked |
| D-10 | Inventory as append-only ledger | Auditable, no negative stock |
| D-11 | Products and samples built last; DCR uses placeholders first | Matches build order |
| D-12 | No continuous background tracking | Privacy and battery |

## 13. Risks
| Risk | Impact | Mitigation |
|---|---|---|
| Fake or mock GPS | False verification | Accuracy check, mock flag, server-side decision, manager review |
| Sync conflicts | Wrong data | Versioning, conflict screen, tests |
| Android battery/background limits | Background sync unreliable | Also sync on foreground and network regain |
| AI agent drifts from structure | Messy code | rules.md, phase prompts, review each phase |
| Scope too large | Delays | Strict phases, done-check per phase |
| Stock race conditions | Negative stock | Row locking, CHECK constraint, concurrency test |