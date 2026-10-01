# Memory - Mediate Healthcare MR App

Living memory of the project. The AI agent reads this file first in every session and updates it at the end. Keep it short, true and current. Write facts, not chat.

## How to use
- Read at session start. Update at session end.
- Keep only things that matter for later work. Move old details to the Changelog.
- If something here conflicts with code, say so and fix whichever is wrong.
- Each repo keeps its own copy. Update only your own side (backend or mobile), and record what you need from the other side under Dependencies.

## Project identity
| Item | Value |
|---|---|
| Product | Mediate Healthcare MR App |
| This repo | (mr-backend or mr-mobile) |
| Stack | Python FastAPI + SQL Server, React Native + Expo (dev build) + TypeScript |
| Roles | ADMIN, MANAGER, MR |
| Build order | Phases P0 to P9, products and samples last |
| Context files | prd.md, architecture.md, rules.md, design.md, task.md, memory.md |

## Current state
| Item | Value |
|---|---|
| Current phase | P6 (Tasks, Chat, Notifications, Meetings) |
| Last finished task | P5-B-05 / P5-M-05 (Phase 5 Approvals, Tour, Expense, Leave 100% Complete) |
| Next task | P6-B-01 (Tasks, summary, overdue logic) |
| Backend last finished phase | Phase 5 Complete (35/35 tests passing) |
| Mobile last finished phase | Phase 5 Complete (0 typecheck errors) |
| Last openapi.json export | Phase 5 Approvals, Tours, Expenses, Leaves (2026-10-02) |
| Last git tag | none |

## Locked decisions
| ID | Decision | Date |
|---|---|---|
| D-01 | Expo development build (not Expo Go, not bare CLI) | project start |
| D-02 | Modular monolith, no microservices | project start |
| D-03 | SQL Server database | project start |
| D-04 | No Redis/Celery in v1; APScheduler for reminders | project start |
| D-05 | Files in object storage, metadata in DB | project start |
| D-06 | JWT access 15 min + rotating refresh tokens | project start |
| D-07 | Mobile API types generated from backend openapi.json | project start |
| D-08 | client_uuid on mobile-created records, idempotent creates | project start |
| D-09 | Server decides geofence result | project start |
| D-10 | Inventory is an append-only ledger; never negative | project start |
| D-11 | Products and samples built last; DCR uses placeholder columns first | project start |
| D-12 | No continuous background GPS tracking | project start |
| D-13 | Android first, iOS after P9 | project start (confirm Q3) |
| D-14 | Created fresh SQL Server database `mediate_mr_db` for clean Phase 1-9 migrations | 2026-09-30 |

## Answers to open questions (fill from prd.md section 10)
| Q | Answer |
|---|---|
| Q1 Web admin needed? | Phone only for v1; web admin considered after P9 |
| Q2 Number of users | 1,000 MRs design target |
| Q3 Android / iOS | Android first, iOS after P9 |
| Q4 Languages | English only in v1 |
| Q5 Extra roles | 3 roles (ADMIN, MANAGER, MR); manager hierarchy handled by manager_id |
| Q6 Order prices | Quantity only; rate fields optional |
| Q7 Geofence radius | 200 m for doctors/hospitals, 150 m for chemists/stockists |
| Q8 DCR edit window | 24 hours |
| Q9 Holidays and weekly off | Sunday off, holiday list managed by admin |
| Q10 Brand colours and logo | Placeholder teal and navy theme (#0E8C7F, #12355B) |

## Environment (no secrets here)
| Item | Value |
|---|---|
| Backend local URL | http://192.168.1.18:8000 |
| Mobile env variable | EXPO_PUBLIC_API_URL |
| Database (local) | SQL Server (SQLEXPRESS), database: mediate_healthcare |
| App package id | com.mediatehealthcare.mrapp |
| Expo SDK version | 57.0.26 |
| Python / Node versions | Python 3.14.6 / Node v24.16.0 |
| Storage provider (dev) | local folder |
Secrets live in .env and EAS secrets only.

## Conventions discovered
(Add short notes here when a real convention is settled, for example naming of permission codes, enum values, date formats used in the API.)
- Permission code format: module:action (example doctors:write)
- Error format: { detail, code, errors }
- List format: { items, total, page, page_size }
- Task ids: P<phase>-B-<n> backend, P<phase>-M-<n> mobile

## Dependencies between repos
| Needed by | Needed from | What | Status |
|---|---|---|---|
| mobile P0 | backend P0 | openapi.json exported | ready |
| mobile P1 | backend P1 | openapi.json with auth and users | pending |

## Known issues and tech debt
| ID | Issue | Phase found | Plan |
|---|---|---|---|
| (none yet) | | | |

## Native library log (mobile only)
Every native library added needs a new development build. Record it here.
| Library | Added in phase | Dev build rebuilt |
|---|---|---|
| expo-dev-client | P0 | pending dev build |
| expo-secure-store | P0 | pending dev build |
| expo-sqlite | P0 | pending dev build |
| @react-native-community/netinfo | P0 | pending dev build |
| react-native-screens | P0 | pending dev build |
| react-native-safe-area-context | P0 | pending dev build |

## Session log
Add one line per session: date, what was done, what is next.
- 2026-09-30: Pre-start tasks P-1-01, P-1-02, P-1-03 completed. Phase 0 Backend (P0-B-01 to P0-B-06) completed: FastAPI modular monolith skeleton, settings, logging, standard exception handlers, request id middleware, db mixins & session, Alembic baseline, Dockerfile, docker-compose, Makefile, pytest tests passing, ruff & mypy clean, openapi.json exported. Next: Mobile Phase 0 (P0-M-01).
- 2026-09-30: Phase 0 Mobile (P0-M-01 to P0-M-06) completed: Expo TypeScript project with dev-client, design system tokens (#0E8C7F teal, #12355B navy), shared UI components (Button, Card, StatusChip, ScreenContainer, Header, Toast, ErrorBoundary, StateViews), Axios client with single-flight token refresh, useAuthStore with SecureStore, 5-tab role-based navigators (MR, Manager, Admin) with ComingSoon placeholders, SQLite outbox table with WAL mode, useNetwork hook, and openapi-typescript type generation script passing strict typecheck. Next: P0-M-07 (LAN verification with phone).

## Changelog
- v0.0 Context files created.
- v0.1 Phase 0 Backend setup complete.
- v0.2 Phase 0 Mobile setup complete.