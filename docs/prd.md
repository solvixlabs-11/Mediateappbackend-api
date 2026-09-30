# PRD - Mediate Healthcare MR App

| Field | Value |
|---|---|
| Product | Mediate Healthcare MR App (Medical Representative field-force app) |
| Version | 1.0 (build scope) |
| Platforms | Android first, iOS next. One React Native (Expo) codebase |
| Backend | Python FastAPI + Microsoft SQL Server |
| Owner | (write project owner name here) |
| Related files | architecture.md, rules.md, design.md, task.md, memory.md |

## 1. Vision
Give every Medical Representative (MR) one reliable mobile app to plan their day, record every doctor/hospital/chemist/stockist visit with GPS proof, manage samples, orders, tour, expenses and leave, and give Managers and Admins a live, trustworthy view of field activity. The app must keep working with weak or no network.

## 2. Problem
- Visit records live in paper, Excel or WhatsApp, so they are incomplete and cannot be verified.
- Managers learn about team performance late and cannot check whether a visit really happened.
- Tour plan, expense and leave approvals are manual and slow.
- Sample and gift stock with each MR is not tracked, so stock goes missing and reports are wrong.
- Targets versus achievement are unclear.

## 3. Goals and success metrics
| Goal | Metric (target to confirm with owner) |
|---|---|
| MRs record visits digitally | 90% of visits recorded as DCR within the same day |
| Visits are verifiable | 80% of DCRs GPS-verified inside geofence |
| Faster approvals | Average approval time under 24 hours |
| Reliable offline use | 0 lost records; sync success rate above 99% |
| Stock accuracy | Sample/gift balance never negative; ledger always matches balance |
| Adoption | 95% of active MRs check in daily |
| Speed | Common screens open in under 2 seconds on a mid-range Android phone |

## 4. Users and roles
| Role | Who | Main jobs | Data scope |
|---|---|---|---|
| ADMIN | Head office / system owner | Manage users, masters, settings, approval matrix, stock allocation, all reports | All data |
| MANAGER | Area / regional manager | Track team, approve requests, assign tasks, joint working, team reports | Only assigned MRs |
| MR | Medical representative | Attendance, plan, DCR, follow-up, tour, expense, leave, orders, tasks | Only own data |

## 5. Scope
### In scope (v1)
All 35 features listed in section 6, delivered in 10 phases (see task.md). Android first; iOS build after Android is stable.
### Out of scope (v1)
- Continuous background GPS tracking (privacy). Team tracking uses check-in and visit points only.
- Payroll, salary, incentive calculation.
- Web admin portal (see Open Questions).
- Call recording, video calling.
- Third-party ERP/DMS integrations (only interfaces are prepared, feature 34).
- Multi-company / multi-tenant support.

## 6. Feature requirements
Feature numbers match the original feature list. "Must" = required in v1.

### 6.1 Foundation
| No | Feature | Must have | Acceptance criteria |
|---|---|---|---|
| 1 | Authentication and Security | Registration (admin-approved), login, logout, JWT access + refresh, refresh rotation and revocation, password hashing, role-based access | Expired access token refreshes silently; revoked or reused refresh token is rejected; wrong role gets 403; passwords never stored in plain text |
| 2 | User Management | Admin / Manager / MR users, create/edit, active/inactive, manager to MR assignment with history, user details | Deactivated user cannot log in; manager sees only assigned MRs; re-assignment keeps history |
| 33 | Profile | Profile details, photo, contact info, manager info, role info | MR can see own manager name and phone; photo is compressed before upload |

### 6.2 Masters and customers
| No | Feature | Must have | Acceptance criteria |
|---|---|---|---|
| 5 | Master Data | Specialization, category, priority, state, city, area, territory, other business dropdowns | Admin can add/edit/deactivate; inactive values are hidden in new forms but kept on old records |
| 29 | Territory and Planning | Territory and area assignment, customer coverage, daily/weekly/monthly planning | MR sees only customers in assigned territory or coverage list |
| 3 | Doctor Management | Add/edit, details, specialization, category, hospital, contact, address, GPS, active/inactive | Valid latitude/longitude required for geofence; searchable by name, specialization, territory |
| 4 | Hospital Management | Add/edit, details, address, contact, GPS, doctors mapping, active/inactive | A doctor can be mapped to many hospitals with one primary |
| 10 | Chemist Management | Master, contact, address, GPS, area/territory, active/inactive | Same list/search/scope rules as doctors |
| 11 | Stockist Management | Master, contact, address, GPS, area/territory, active/inactive | Same list/search/scope rules as doctors |

### 6.3 Daily field work
| No | Feature | Must have | Acceptance criteria |
|---|---|---|---|
| 6 | GPS and Attendance | Daily check-in and check-out with GPS, address, date/time, history | One check-in per day; check-out only after check-in; works offline and syncs later |
| 25 | Geofencing | Compare MR and customer coordinates, distance, configurable radius, verified / not verified | Server makes the final verified decision; distance and radius are stored on the DCR |
| 8 | Pre-Call Planning | Planned visits, customer selection, purpose, products to discuss, priority, daily planning | A plan can start a DCR; unvisited past plans become MISSED |
| 7 | DCR / Call Reporting | Doctor, hospital, chemist, stockist visits; GPS verification; geofence; products promoted; samples; gifts; remarks; next visit date; follow-up | DCR needs a check-in that day (configurable); sample/gift quantity cannot exceed MR stock; a retried submit never duplicates |
| 9 | Post-Call Analysis | Outcome, products discussed, customer response, follow-up, next visit, remarks | Follow-up required creates a follow-up item |
| 23 | Follow-up and Reminders | Next visit, follow-up date, reminder, pending follow-ups, customer follow-up history | Pending and overdue lists; reminder notification on the due date |
| 30 | Meeting Management | Meeting, participants, date/time, location, notes, outcome | Participants are notified and can accept/decline |
| 31 | Joint Working | Manager + MR visit, observation, feedback, remarks, follow-up | Only a manager in scope can record; MR can read feedback on own visits |

### 6.4 Requests and approvals
| No | Feature | Must have | Acceptance criteria |
|---|---|---|---|
| 19 | Approval Management | Manager and admin approval, dynamic approval matrix, approve/reject, approval history | Admin can change steps without code change; reject needs a comment; full history visible |
| 16 | Tour Management | Tour planning, dates, locations, planned visits, status, approval | No overlapping tours for one MR; approved tour can fill the daily plan |
| 17 | Expense Management | Entry, type, amount, date, receipt, description, manager approval, history | Receipt required when the type demands it; amount cap enforced; monthly summary |
| 18 | Leave Management | Request, type, start/end, reason, approval/rejection, history | Balance and overlap checked; balance drops on approval and returns on cancel |

### 6.5 Collaboration
| No | Feature | Must have | Acceptance criteria |
|---|---|---|---|
| 20 | Task Management | Create, assign MR, priority, due date, status, completed/pending, overdue | Overdue tasks appear in their own list; manager assigns only to own team |
| 21 | Task Communication | Task chat, messages, replies, manager to MR communication | Only creator, assignee and admin can read the chat |
| 22 | Notifications | Task, leave, expense, tour, DCR reminder, follow-up reminder, system alerts (in-app + push) | Tapping a notification opens the related screen; push failure never breaks the main action |

### 6.6 Insight
| No | Feature | Must have | Acceptance criteria |
|---|---|---|---|
| 26 | Dashboard | Admin, Manager and MR dashboards: attendance, visits, orders, tasks, approvals, performance | Numbers match raw data; each role sees only its scope |
| 27 | Reports and Analytics | Attendance, DCR, visit, MR performance, product, sample/gift, order, expense, sales/target | Filters by date, MR, territory, status; scoped by role |
| 28 | Export | Excel and PDF export for attendance, DCR, orders, expenses, reports | File opens correctly; header shows title, filters, generated time |
| 24 | GIS / Maps | MR, doctor, hospital, visit and attendance locations, routes, visit history, team tracking | Team map uses check-in and visit points only; route shows ordered visits |

### 6.7 Products, stock and sales (built last)
| No | Feature | Must have | Acceptance criteria |
|---|---|---|---|
| 12 | Product Management | Product code, name, brand/company, category, composition, strength, description, active | Product code unique; inactive products hidden from new entries |
| 13 | Sample / Gift Management | Sample master, gift master, promotional material, stock allocation, MR stock, distribution, remaining stock | MR sees own remaining stock; distribution recorded against a DCR |
| 32 | Inventory | Allocation, MR inventory, distribution, balance, history, negative stock prevention | Balance can never go below zero, even with parallel requests |
| 14 | E-Detailing | Product presentation, visual aids, product info, images/slides, presentation tracking | Works offline from downloaded package; time per slide tracked |
| 15 | Orders | Chemist and stockist orders, product selection, quantity, history, status, PDF receipt | Order number unique; PDF receipt downloadable and shareable |

### 6.8 Platform
| No | Feature | Must have | Acceptance criteria |
|---|---|---|---|
| 35 | Offline / Sync | Offline data, local storage, pending sync, server sync, conflict handling | Airplane-mode work syncs on reconnect without duplicates; conflicts shown to the user |
| 34 | Future Integrations | Maps API, location services, third-party APIs, other business integrations | Provider interfaces exist so a service can be swapped without touching business code |

## 7. Business rules
- BR-01 An MR sees only own data; a Manager sees only assigned MRs; an Admin sees all.
- BR-02 One check-in and one check-out per user per day.
- BR-03 A DCR requires a check-in for that day (admin can switch this off).
- BR-04 The server decides geofence Verified / Not verified; the phone only shows a preview.
- BR-05 Geofence radius has a default per customer type and an optional override per customer.
- BR-06 A submitted DCR can be edited only inside a configurable edit window; later changes need admin correction with audit log.
- BR-07 Sample and gift stock can never be negative. Stock changes only through the inventory ledger.
- BR-08 Approvals follow the approval matrix; reject needs a comment; every action is logged.
- BR-09 Tour plans of one MR cannot overlap; leave requests cannot overlap.
- BR-10 Leave balance is reduced on approval and restored on cancellation.
- BR-11 Records are never hard-deleted; use is_active or is_deleted.
- BR-12 Every record created on the phone carries a client_uuid; repeating the same request never creates a duplicate.
- BR-13 Mock or low-accuracy GPS is flagged on attendance and DCR, not silently accepted.
- BR-14 Deactivated users lose access immediately (tokens revoked).
- BR-15 Master values that are inactive stay visible on old records.
- BR-16 All timestamps are stored in UTC and shown in Asia/Kolkata.

## 8. Non-functional requirements
| Area | Requirement |
|---|---|
| Performance | List screens load first page in under 2 s on 4G; API p95 under 500 ms for normal endpoints |
| Offline | Attendance, plan, DCR, follow-up, orders and e-detailing work offline; data is never lost on app kill |
| Security | Argon2 passwords, short-lived access tokens, rotating refresh tokens, RBAC, central data scoping, HTTPS only in production, audit logs |
| Privacy | GPS only at check-in, check-out and visit time; permission asked with a clear reason; no hidden tracking |
| Reliability | Idempotent writes, transactions for stock and approvals, daily database backup with tested restore |
| Usability | One-hand use, large touch targets, works outdoors (high contrast), simple language |
| Compatibility | Android 8+ first; iOS 15+ later; small and large screens |
| Maintainability | Modular monolith, typed code, tests per module, migrations for every DB change |
| Localization | English first; all text kept in one place so Hindi/Gujarati can be added |
| Scale (assumption) | Design for up to about 1,000 MRs and 100,000 visits per month; confirm with owner |

## 9. Release plan
| Phase | Content | Features |
|---|---|---|
| P0 | Setup of both projects | foundation |
| P1 | Auth, users, profile | 1, 2, 33 |
| P2 | Masters and customers | 5, 29, 4, 3, 10, 11 |
| P3 | Attendance and geofence | 6, 25 |
| P4 | Plan, DCR, post-call, follow-up | 8, 7, 9, 23 |
| P5 | Approvals, tour, expense, leave | 19, 16, 17, 18 |
| P6 | Tasks, chat, notifications, meetings, joint working | 20, 21, 22, 30, 31 |
| P7 | Dashboard, reports, export, maps | 26, 27, 28, 24 |
| P8 | Products, samples, inventory, e-detailing, orders | 12, 13, 32, 14, 15 |
| P9 | Offline sync, integrations, hardening, release | 35, 34 |

## 10. Assumptions and open questions
Answer these before or during Phase 1. Put the answers in memory.md under Decisions.
| No | Question | Default if not answered |
|---|---|---|
| Q1 | Will Admin work only on the phone, or do you also need a web admin panel for bulk work (imports, big reports)? | Phone only for v1; web admin considered after P9 |
| Q2 | How many users at launch and in one year? | 1,000 MRs design target |
| Q3 | Android only at launch or iOS also? | Android first, iOS after P9 |
| Q4 | Which languages? | English only in v1 |
| Q5 | Are there more roles (ASM, RM, ZM) with different levels? | 3 roles; manager hierarchy handled by manager_id |
| Q6 | Do orders have prices, or quantity only? | Quantity only; rate fields optional |
| Q7 | Geofence default radius? | 200 m for doctors/hospitals, 150 m for chemists/stockists |
| Q8 | DCR edit window after submit? | 24 hours |
| Q9 | Working days, holidays and weekly off rules for leave? | Sunday off, holiday list managed by admin |
| Q10 | Company name, logo and brand colours? | Placeholder teal and navy theme |

## 11. Glossary
| Term | Meaning |
|---|---|
| MR | Medical Representative, the field employee |
| DCR | Daily Call Report, the record of one visit |
| HQ / Territory | The MR's headquarters and assigned area |
| Geofence | Virtual circle around a customer used to verify the MR was really there |
| Joint Working | A manager visits customers together with an MR and records observations |
| E-Detailing | Showing product slides on the phone during a visit |
| Stockist | Wholesale distributor of medicines |
| Chemist | Retail medical shop |
| Sample / Gift | Free promotional items given to doctors and tracked in stock |
| Outbox | Local queue of actions done offline, waiting to sync |