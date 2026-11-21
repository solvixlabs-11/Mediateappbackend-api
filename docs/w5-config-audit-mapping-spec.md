# Web Wave W5 - System Configuration, Audit Trail and Mapping Wizard

Place at `docs/w5-config-audit-mapping-spec.md` in Mediateappweb and Mediateappbackend-api. Run the backend prompt first, then the web prompt.


## 1. Review of the proposed W5 (what was kept and what was corrected)

W5 ka idea sahi hai: configuration, audit trail aur bulk mapping admin portal ko complete karte hain. Lekin proposal mein 5 cheezein hamare project se match nahi karti thi. Unhe maine sudhara hai, warna Antigravity galat ya duplicate cheezein bana deta.

| No | Proposal said | Problem in our project | What this spec does |
|---|---|---|---|
| 1 | Routes /parameters/entry-config and /parameters/general-setting | Ye pages hum pehle hi bana chuke hain (Utility > Admin Panel > General Settings, Entry-Wise Configurations, Geofence Settings). Naye route banane se duplicate pages ho jate | Existing pages ko extend karo. Naya duplicate page nahi |
| 2 | Stockist geofence 250 m | Hamare PRD default: doctor aur hospital 200 m, chemist aur stockist 150 m. 250 m kahin tay nahi hua | Seed 150 m rakho (PRD ke hisaab se), value editable aur 'provisional' chip ke saath. Aap chaho to 250 kar do |
| 3 | Expense limits for MR, ABM, RBM | Hamare designation master mein ye naam nahi hain (seed: ADMIN, ARBH, BH, DBH, DIRECTOR, MD, MR, RBH, ZBM) | Designations master se dynamic aayenge. Koi designation ka naam code mein nahi |
| 4 | Limit amounts | Mediate ki asli policy hame nahi pata | Seed mein placeholder amounts, har row 'provisional' flag ke saath. Admin confirm karega |
| 5 | Beats se doctors/chemists link karna | Beat ya route ka entity abhi hamare data mein nahi hai (Std. Route Chart ka form screenshot nahi aaya) | Wizard sirf wahi karega jo model mein hai: territory assignment aur customer coverage. Beat step disabled rahega, 'waiting for Std Route Chart design' |
| 6 | Audit logs viewer | MR Buddy ke menu mein nahi hai, hamara apna add-on hai. Lekin rules.md (B-13) mein audit log pehle se zaroori hai | Rakho. Bas existing audit_logs table ko extend karo, nayi table nahi |

> Hum nayi ghar ki cheezein tab hi banate hain jab purani cheez wahan nahi ho. Jo pehle bana hai (settings, geofence, mapping page) use sudharte hain, duplicate nahi banate.


## 2. Scope and golden rules

- Sab kuch dynamic: settings ke groups, labels, units, limits, designation list, expense types, audit ke modules aur actions, filter options, columns, counts sab backend API se. UI mein koi number (jaise 200, 150), designation naam ya action naam hardcode nahi.
- Seed alag files mein (seed/ package, ek file ek kaam). Kam se kam 30 config records aur 30 audit records (hum 60+ target rakhte hain). Asli personal data nahi, audit ka dev data nakli (synthetic).
- Pehle inspect, phir code: agent pehle dekhega ki kya pehle se bana hai, aur sirf missing cheez banayega.
- Clean code: chhoti files, ek file ek kaam, reusable components, koi duplicate logic nahi, typed code, tests.
- Khud dobara check: kaam ke end mein agent ek verification protocol chalayega (section 6) aur evidence ke saath report dega. Fail hone par 'done' nahi bolega.
- Beta-testing ke baad aapke issues par agla kaam. Isliye agent ek test guide bhi banayega.


## 3. Data model and API (reuse first)


### 3.1 System configuration

| Item | Detail |
|---|---|
| Reuse | app_settings (typed settings) and geofence_settings from earlier phases; Settings page and Entry-wise Configurations page from Part 2 |
| Extend app_settings | group (GEOFENCE, GPS, ATTENDANCE, DCR, EXPENSE, NOTIFICATIONS, SECURITY, AUDIT, EXPORT), unit (m, min, hours, days, rows, time, none), min_value, max_value, allowed_options, help_text, is_provisional, updated_by, updated_at. Value types: BOOLEAN, INTEGER, DECIMAL, TEXT, TIME, SELECT, FORMULA |
| Extend geofence_settings | entity_type (DOCTOR, HOSPITAL, CHEMIST, STOCKIST), radius_m, min_accuracy_m, is_provisional, is_active |
| expense_limits (new) | designation_id, expense_type_id, daily_limit, monthly_limit, effective_from, is_provisional, is_active; unique on designation, expense type and effective_from; amounts DECIMAL(12,2) |
| Endpoints | GET /settings/groups (groups with settings and schema), GET /settings?group=&search=, PUT /settings/{key}, PUT /settings/bulk (all or nothing with per-key errors), GET /settings/{key}/history, POST /settings/{key}/confirm (clears provisional), GET/PUT /settings/geofence (extended), GET /expense-limits?designation_id=&expense_type_id=, PUT /expense-limits/bulk (matrix upsert), POST /expense-limits/{id}/confirm |
| Validation | Typed and range checked on the server; time as HH:MM; radius 10 to 5000 m; tolerance 0 to 180 min; limits not negative; monthly limit not below daily limit. Errors use the standard format with the field key |
| Consumers | geofence.verify reads geofence_settings; attendance late and mock flags read settings; expense submit checks expense_limits according to expense.limit_enforcement (OFF, WARN, BLOCK; default WARN: warning flag for the approver, no block). Every consumer reads through the SettingsService, never constants |


### 3.2 Seed list: configuration records (config seeders, always run)

Source batata hai ki value hamare docs se hai ya meri assumption hai. Assumption wali rows provisional flag ke saath seed hongi.

| No | Key | Value | Unit | Source |
|---|---|---|---|---|
| 1 | geofence DOCTOR radius | 200 | m | PRD Q7 |
| 2 | geofence HOSPITAL radius | 200 | m | PRD Q7 |
| 3 | geofence CHEMIST radius | 150 | m | PRD Q7 |
| 4 | geofence STOCKIST radius | 150 (proposal said 250) | m | PRD Q7, confirm |
| 5 | gps.min_accuracy_m | 50 | m | Assumption |
| 6 | gps.low_accuracy_warning_m | 100 | m | Assumption |
| 7 | gps.mock_location_action | FLAG (options FLAG, BLOCK) | select | PRD BR-13 |
| 8 | gps.mock_auto_flag_after_count | 3 | count | Assumption |
| 9 | attendance.late_after_time | 09:30 | time | Earlier docs default |
| 10 | attendance.late_tolerance_minutes | 15 | min | Assumption |
| 11 | attendance.punch_in_cutoff_time | 11:00 | time | Assumption |
| 12 | attendance.auto_close_after_hours | 16 | hours | Assumption |
| 13 | attendance.weekly_off_day | SUNDAY | select | PRD Q9 |
| 14 | dcr.require_checkin | true | boolean | PRD BR-03 |
| 15 | dcr.edit_window_hours | 24 | hours | PRD Q8 |
| 16 | dcr.morning_cutoff_time | 14:00 | time | Earlier assumption |
| 17 | expense.limit_enforcement | WARN (OFF, WARN, BLOCK) | select | Assumption |
| 18 | expense.receipt_required_above_amount | 500 | amount | Assumption |
| 19 | notifications.dcr_reminder_time | 18:00 | time | Assumption |
| 20 | notifications.followup_reminder_time | 09:00 | time | Assumption |
| 21 | security.login_max_attempts | 5 | count | rules S-01 (lockout) |
| 22 | security.lockout_minutes | 15 | min | Assumption |
| 23 | audit.retention_days | 730 | days | Assumption |
| 24 | export.max_rows | 50000 | rows | reports-spec |
| 25 | report.max_range_days | 92 | days | reports-spec |
| 26 to 61 | expense_limits: every designation of the master x every expense type | Placeholder amounts, all provisional | INR | Assumption, confirm with Mediate |

Total: 25 settings and geofence rows + designations x expense types limit rows (9 designations x 4 expense types = 36). Yaani 60 se zyada config records, jo 30 ki shart se zyada hai. Expense types agar backend mein pehle se nahi hain to seed_expense_types.py alag file mein banayega (daily allowance, travel, lodging, miscellaneous).


### 3.3 Audit trail

| Item | Detail |
|---|---|
| Reuse | audit_logs from Phase 1. First inspect its columns and where rows are written |
| Extend (migration) | module, action, entity_type, entity_id, user_id, channel (WEB, MOBILE, SYSTEM), ip_address, user_agent, request_id, result (SUCCESS, FAILED), summary, before_json, after_json (masked), created_at. Indexes on created_at, user_id, module, action, entity |
| One recorder | A single AuditService.record(...) used everywhere. No endpoint writes audit rows its own way. Add missing calls for master data changes (the 14 masters and the Part 2 masters), logins and failed logins, logouts and force logout, permission and role changes, approvals and rejections, settings and expense limit changes, imports and exports, mapping batches |
| Masking | Never store passwords, tokens, OTPs, secret keys or full phone numbers in before and after; mask them. Test it |
| Append only | No update or delete endpoint for audit rows. Test that none exists. Retention job removes only rows older than audit.retention_days (a scheduled job, itself audited) |
| Endpoints | GET /audit/logs (filters: user_id, module, action, entity_type, entity_id, result, channel, date_from, date_to, search; sort; page, page_size up to 100), GET /audit/logs/{id}, GET /audit/meta (lists of modules, actions, channels, results and users that appear, from the data and registry), POST /audit/logs/export?format=xlsx/pdf (same filters, row limit, and the export is itself audited) |
| Access | audit:read and audit:export for ADMIN only; MANAGER and MR get 403 |
| Actions (from the API, not hardcoded in UI) | CREATE, UPDATE, DELETE, ACTIVATE, DEACTIVATE, APPROVE, REJECT, LOGIN, LOGIN_FAILED, LOGOUT, FORCE_LOGOUT, PERMISSION_CHANGE, SETTINGS_CHANGE, IMPORT, EXPORT, MAPPING_APPLY, MAPPING_REVERT |


### 3.4 Mapping wizard

| Item | Detail |
|---|---|
| Reuse | territory_assignments and customer_coverage (Phase 2). Existing menu item Employee Mappings is the home of the wizard |
| New tables | mapping_batches (id, mode TERRITORY or CUSTOMER, status DRAFT, APPLIED, REVERTED, filters_json, target_employee_id, conflict_policy, counts, created_by, applied_at, reverted_at) and mapping_batch_items (batch_id, action ASSIGN or UNASSIGN, employee_id, territory_id or customer_type and customer_id, before_state, after_state) |
| Modes | TERRITORY: assign or unassign territories for employees. CUSTOMER: assign or unassign doctors, hospitals, chemists, stockists to an employee by territory, state, city, area, customer type, division |
| Endpoints | POST /mappings/preview (creates a DRAFT batch with counts, conflicts and a sample), POST /mappings/{id}/apply, POST /mappings/{id}/revert, GET /mappings (history, filters), GET /mappings/{id} (items, paged) |
| Rules | Dry run first. Conflict policy SKIP, REPLACE or ADD (customers already covered by another employee). Maximum 20,000 items per batch. One transaction. Unassign sets an end date, never deletes (BR-11). Revert restores the before state when nothing changed since; otherwise it reports the conflicts. Scope: ADMIN all, MANAGER only inside own team. Every apply and revert is audited |
| Beats | No beat entity exists yet. Do NOT create one. Return capabilities beats=false from GET /mappings/capabilities so the web can show the step as disabled |


### 3.5 Seed files for W5 (one file each, registered in seed_all.py)

| File | Runs | Content |
|---|---|---|
| seed_system_settings.py (+ data/system_settings.json) | always | The 21 settings of section 3.2 (rows 5 to 25) with group, unit, min, max, help text, provisional flag |
| seed_geofence_settings.py (+ data/geofence_settings.json) | always | Rows 1 to 4 |
| seed_expense_types.py (+ data/expense_types.json) | always, only if the table is empty | Daily allowance, travel, lodging, miscellaneous |
| seed_expense_limits.py (+ data/expense_limits.json) | always | Every designation from the master x every expense type, placeholder amounts, provisional |
| seed_audit_logs.py | --dev only | At least 60 synthetic events over 30 days: logins and failed logins, master create, update and delete, approvals and rejections, permission changes, settings changes, exports, mapping batches. Synthetic users only, fixed random seed, masked values |
| seed_mapping_batches.py | --dev only | A few applied and reverted batches with items |


## 4. Web UI

| Page | Where | What |
|---|---|---|
| System Configuration | Existing General Settings page (Utility > Admin Panel). Geofence Settings menu opens the Geofence tab | Tabs for the setting groups, all from GET /settings/groups. Typed controls from value_type, unit shown, min and max validation, help text, provisional chip with a Confirm action, per-setting history drawer, unsaved-changes guard, bulk save with a preview of the changes, per-field server errors |
| Expense Limits | New menu item under Reimbursement | Matrix: designations (rows) x expense types (columns) from the API, inline editing of daily and monthly limits, provisional chips, filter by designation, bulk save with a diff preview, confirm provisional values |
| Audit Trail | New menu item Utility > Admin Panel > Audit Trail | Filters (user, module, action, entity, result, channel, date range, search) with options from GET /audit/meta; server-side paginated table; detail drawer with who, when, IP, channel, summary and a before and after diff; export; shareable link by audit id; empty, loading, error states |
| Mapping Wizard | Existing Employee Mappings page | Steps: 1 choose mode and source filters, 2 choose target employee or territory, 3 preview with counts, conflicts table and conflict policy, 4 confirm and apply, 5 result with Undo. Beat step visible but disabled with the reason from capabilities. History tab of past batches with Revert |

- All options, labels and units come from the API. The web code has no designation names, no action names, no numbers like 200 or 150, no module list.
- Reuse the existing MasterPage, filter and table components; do not copy code between pages.
- Menu items are added only in menu.config.ts with permissions (settings:read, settings:write, expense_limits:read, expense_limits:write, audit:read, audit:export, mappings:read, mappings:write).


## 5. Prompts


#### BACKEND W5 - configuration, expense limits, audit trail, mapping wizard, seeds

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, architecture.md, frontend-spec.md, docs/masters-spec-part1.md, docs/masters-spec-part2.md (section 2 seed structure, section 4 settings), docs/web-admin-inventory.md, docs/w5-config-audit-mapping-spec.md. Work ONLY inside Mediateappbackend-api. Do not change other folders.

GOLDEN RULES: Everything is dynamic and comes from the database through the API. No setting value, designation name, action name, module name or number is hardcoded in application code. All initial data is seeded by the seed/ package: one file per seeder, config values in seed/data/*.json, registered in seed/seed_all.py, idempotent. No real personal data anywhere; development data is synthetic. Code must be clean: small files, one responsibility per file, no duplicated logic, full type hints, no print(), reuse existing services.

GOAL: Backend for Wave W5 as specified in docs/w5-config-audit-mapping-spec.md: system configuration, expense limits per designation, audit trail, mapping wizard.

STAGE 0 - INSPECT FIRST (no code changes): write docs/audit/w5-inspection.md listing what already exists and what is missing: app_settings and the settings service, geofence_settings, expense_types and expense submit, the designations master, the audit_logs columns and every place audit rows are written (and every place they are missing: masters, logins, permission changes, approvals, settings, imports, exports), territory_assignments, customer_coverage, the seed package. Reuse everything that exists; create only what is missing. Do not create duplicate tables.
STAGE 1 - SETTINGS: extend app_settings and geofence_settings as in section 3.1 with one Alembic migration; implement the endpoints of section 3.1 (groups, list, update, bulk with all-or-nothing and per-key errors, history, confirm provisional, geofence extended). Typed server-side validation. Route every read through SettingsService with caching and cache invalidation on update. Audit every change.
STAGE 2 - EXPENSE LIMITS: expense_limits table and endpoints of section 3.1 (list, matrix bulk upsert, confirm). Designations and expense types come from their masters. Wire expense submit to check the limits according to expense.limit_enforcement (OFF, WARN, BLOCK; default WARN means a warning flag for the approver and no block). Add tests for all three modes.
STAGE 3 - AUDIT: extend audit_logs as in section 3.3 with a migration (indexes included). Create ONE AuditService.record(...) and replace any ad-hoc audit writes with it. Add the missing audit calls listed in your inspection (masters of Part 1 and Part 2, logins and failed logins, logout and force logout, permission and role changes, approvals, settings, expense limits, imports, exports, mapping batches). Mask sensitive values (passwords, tokens, secrets, full phone numbers) before storing before_json and after_json. Endpoints: GET /audit/logs with the filters of section 3.3, GET /audit/logs/{id}, GET /audit/meta, POST /audit/logs/export. Append only: there must be no update or delete endpoint. A scheduled retention job deletes only rows older than audit.retention_days and is itself audited. Access audit:read and audit:export for ADMIN only.
STAGE 4 - MAPPING WIZARD API: tables mapping_batches and mapping_batch_items and the endpoints of section 3.4 (preview, apply, revert, history, detail, capabilities with beats=false). Dry run first; conflict policies SKIP, REPLACE, ADD; maximum 20,000 items; one transaction; unassign sets an end date and never deletes; revert restores the before state or reports conflicts; scope through core/scope.py; audit every apply and revert. Do NOT create a beat or route entity.
STAGE 5 - CONSUMERS: make geofence.verify, the attendance late and mock-GPS flags and the DCR edit window read their values from SettingsService (no constants). Keep existing behaviour identical when the seeded defaults are used; add regression tests.
STAGE 6 - SEEDS (separate files, section 3.5 of the spec): seed_system_settings.py, seed_geofence_settings.py, seed_expense_types.py (only if empty), seed_expense_limits.py (every designation x every expense type, placeholder amounts, is_provisional true), seed_audit_logs.py (dev only, at least 60 synthetic events over 30 days), seed_mapping_batches.py (dev only). Config seeds must create at least 30 records (the plan gives 60+), audit seed at least 30 (plan gives 60+). Register them in seed_all.py in dependency order. Running seed_all twice must change nothing the second time.
STAGE 7 - VERIFY (mandatory, do not skip): (a) run ruff, mypy and pytest and fix everything; (b) write scripts/verify_w5.py that prints the number of rows in app_settings (W5 groups), geofence_settings, expense_limits and audit_logs and fails if config rows are below 30 or audit rows below 30; (c) run make seed-dev twice and prove idempotency; (d) run a grep that proves no designation names, action names or setting numbers are hardcoded in app code (list the command and result); (e) start the server and use scripts/smoke_test.py (extend it) to call every new endpoint as ADMIN, MANAGER and MR and prove: MANAGER and MR get 403 on audit and settings writes, mapping scope works, masked values never appear in the audit output; (f) review your own diff against rules.md and list any violation you fixed; (g) make openapi. Write docs/audit/w5-backend-verification.md with the command outputs as evidence, the list of assumptions, and the list of open questions. If any check fails, say so and fix it; never report done while a check fails.
FINISH: update docs/CHANGELOG.md, task.md and memory.md, and write docs/testing/w5-backend-test-guide.md (manual steps with example calls for each endpoint) so the owner can test.
```


#### WEB W5 - configuration, expense limits, audit trail, mapping wizard

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, frontend-spec.md, docs/masters-spec-part2.md, docs/reports-spec.md, docs/web-admin-inventory.md, docs/w5-config-audit-mapping-spec.md. Work ONLY inside Mediateappweb. Do not change other folders. Run npm run gen:api first (backend W5 must be finished) and use generated types only.

GOLDEN RULES: Everything on screen comes dynamically from the backend API. NO setting value, unit, label of business data, designation name, expense type, action name, module name, filter option, column or number (such as 200 or 150) is hardcoded in the web code. No mock data in production paths. All initial data is seeded by the backend. Code must be clean: small files, one responsibility per file, reuse the existing MasterPage, filter, table and drawer components, no duplicated logic, strict TypeScript without any, strings in one place.

GOAL: Web side of Wave W5 as specified in docs/w5-config-audit-mapping-spec.md section 4.

STAGE 0 - INSPECT FIRST (no code changes): write docs/audit/w5-web-inspection.md describing the existing General Settings, Entry-wise Configurations, Geofence Settings and Employee Mappings pages and the shared components you will reuse. Do NOT create duplicate pages or routes; extend the existing ones. Only Expense Limits and Audit Trail are new menu items.
STAGE 1 - SYSTEM CONFIGURATION (extend the existing General Settings page): tabs for the groups from GET /settings/groups; each setting rendered by value_type (switch, number with min and max, text, time picker, select with allowed options, formula with server validation errors), with unit, help text, provisional chip and a Confirm action, a history drawer per setting, dirty tracking with an unsaved-changes guard, Save all with a preview of the changes, per-field errors from the server, loading, empty and error states. The Geofence Settings menu item opens the Geofence tab (radius and accuracy per customer type, all rows from the API).
STAGE 2 - EXPENSE LIMITS (new page under Reimbursement): a matrix with designations as rows and expense types as columns, both from the API; inline editing of daily and monthly limits with validation (not negative, monthly not below daily); provisional chips; filter by designation; Save with a diff preview; Confirm provisional values; permissions expense_limits:read and write.
STAGE 3 - AUDIT TRAIL (new page Utility > Admin Panel > Audit Trail): filters user, module, action, entity type and id, result, channel, date range and search, with options from GET /audit/meta; server-side paginated and sortable table (time in Asia/Kolkata, user, module, action, entity, result, channel); detail drawer with summary, IP, request id and a before and after diff in which masked values are shown as masked; export (Excel and PDF) with progress; a shareable link by audit id; loading, empty and error states; permissions audit:read and audit:export. No edit or delete controls anywhere.
STAGE 4 - MAPPING WIZARD (on the existing Employee Mappings page): a stepper: 1 mode (Territory or Customer) and source filters, 2 target employee or territory, 3 preview (counts, conflicts table, conflict policy SKIP, REPLACE or ADD), 4 confirm and apply, 5 result with Undo. A History tab lists past batches with details and Revert. The Beat step is shown disabled with the reason returned by GET /mappings/capabilities (beats=false). Show clear messages for conflicts and for the 20,000 item limit. Permissions mappings:read and write.
STAGE 5 - MENU AND PERMISSIONS: add only Expense Limits and Audit Trail to menu.config.ts with their permission codes; hide pages and buttons the user may not use; route guard with a friendly Not allowed page.
STAGE 6 - VERIFY (mandatory, do not skip): (a) run lint, typecheck, test and build and fix everything; (b) run npm run check:static (create it if missing: it must fail on hardcoded designation names, action names, setting numbers and large business data arrays outside src/mocks) and show the output; (c) grep proof that none of the values 200, 150, 250, MR, ABM, RBM, ARBH, RBH, CREATE, UPDATE, DELETE, APPROVE appear as business data in src (list the command and result); (d) run the app against the seeded backend and walk through every new screen as ADMIN, MANAGER and MR, check that MANAGER and MR cannot open audit and settings writes, save screenshots of each screen in docs/ui/w5/; (e) review your own diff against rules.md and list the violations you fixed; (f) write tests (vitest) for the typed setting controls, the matrix editor, audit filters and diff view, and the wizard steps including conflicts and undo. Write docs/audit/w5-web-verification.md with the outputs as evidence, assumptions and open questions. If any check fails, say so and fix it; never report done while a check fails.
FINISH: update task.md and memory.md, and write docs/testing/w5-web-test-guide.md (step by step manual test for each screen, with expected results) so the owner can test.
```


## 6. Verification protocol (what the agent must prove)

| Check | Backend | Web |
|---|---|---|
| Build and tests | ruff, mypy, pytest green | lint, typecheck, vitest, build green |
| Seed counts | scripts/verify_w5.py: config rows 30 or more, audit rows 30 or more | Screens show those rows from the API |
| Idempotent seeds | make seed-dev twice, nothing changes | - |
| No hardcoding | grep proof in app code | npm run check:static and grep proof in src |
| Roles | MANAGER and MR get 403 on audit and settings writes; scope correct | Same pages hidden or blocked for MANAGER and MR |
| Masking | Passwords, tokens, secrets and phones masked in audit output | Diff view shows masked values as masked |
| Self review | Own diff checked against rules.md, violations fixed | Same |
| Evidence | docs/audit/w5-backend-verification.md | docs/audit/w5-web-verification.md and screenshots |
| Test guides | docs/testing/w5-backend-test-guide.md | docs/testing/w5-web-test-guide.md |


## 7. After the task: how to report test issues

Jab aap test karo aur issue mile, mujhe ye format mein bhejo, taaki agla fix seedha ho:

- Screen aur role: kaun si screen, kaun sa login (ADMIN, MANAGER, MR).
- Steps: 1, 2, 3.
- Expected aur actual: kya hona chahiye tha aur kya hua.
- Error text: red screen ya console ka text, Network tab ka response (token chhupa ke).
- Screenshot.
- Test guide (docs/testing/w5-*.md) ke step number bhi likh do.


### Decisions you can make now

| No | Question | Default used in the seed |
|---|---|---|
| 1 | Stockist geofence radius 150 m ya 250 m? | 150 m (PRD) |
| 2 | Expense limits ki asli rakam kya hain? | Placeholder, provisional chip, aap confirm karoge |
| 3 | Expense limit enforcement: sirf warning ya block? | WARN |
| 4 | Audit logs kitne din rakhne hain? | 730 din |
| 5 | Beat ya route ka concept kab? (Std. Route Chart ke screenshots chahiye) | Wizard mein beat step disabled |

> Pehle backend, phir web. Dono ke end mein agent khud evidence ke saath check karega. Phir aap test guide se test karo aur issues mujhe bhejo.
