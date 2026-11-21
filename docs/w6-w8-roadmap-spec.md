# Waves W6 to W8 - verification, field security and routes, sample stock

Place at `docs/w6-w8-roadmap-spec.md` in Mediateappweb and Mediateappbackend-api, together with docs/wave-rules.md. Run each wave: backend prompt first, then web prompt.


## 1. Review of the latest status summary

Kal ke kaam mein 14 modules live hue, aur ab 88 live, 17 baki bataye gaye hain. Dobara padhne par 10 baatein hamare reference screens aur docs se match nahi karti. Pehle inhe theek karna zaroori hai, nahi to naye kaam ke upar galat neev ban jayegi.

| No | What the summary says | Problem | What we do |
|---|---|---|---|
| 1 | Application Setting ko General Settings par redirect kiya | Reference mein Application Setting company profile hai (naam, code, area, phone, mobile, logo, signature) aur branding isi se aati hai. Redirect galat hai | W6: asli page banao |
| 2 | Meeting Master (cycle meetings aur reviews ka master) | Reference mein Meeting page Drafts, Applied, Received tiles wala workflow hai (agenda, start, end, created by) | W6: WorkflowInboxPage par rebuild ya verify |
| 3 | Calendar mein tour plans, leaves, holidays, meetings | Reference calendar ke har din mein counts dikhte hain (Doctor, Chemist, Stockist, New Doctor, New Chemist, New Stockist, Total POB). Ye counts nahi hain | W6: counts jodo, events rakho |
| 4 | 5 masters ke matlab (KYC docs, doctor types, vendors, hospital categories, gallery) | Ye maine aur agent ne andaze se likhe; in 5 pages ke screenshots nahi aaye. Supplier aur Product Gallery ke forms zyada bade honge | W6: seed values 'provisional' flag ke saath, Confirm action; screenshots maango |
| 5 | Reimbursement Processing with UTR, payment mode, payout API | PRD mein payroll aur finance out of scope hai; ye page reference mein dekha nahi gaya. Accounts jaisa koi role bhi nahi hai | W6: ise rakho lekin harden karo: sirf APPROVED, ek hi payout (idempotent), sirf ADMIN, audit, feature flag |
| 6 | Do backend AttributeError (call_type, city) terminal par aaye | Matlab endpoints ka real data par smoke test nahi tha | W6: har endpoint ka smoke matrix, regression tests |
| 7 | Group D mein '10 items' likhe | Asli list mein 11 routes hain. Financial Year Master Part 2 mein pehle hi specify tha (shayad bana ho). 'Import Product Master' asal mein 'Import Product Mappings' hai (sales files ke product naam map karna), bulk product upload nahi | W6 ka truth matrix sahi list dega |
| 8 | Std Route Chart = fixed weekly beat plan | Reference mein ye Drafts/Applied/Received tiles hai, shehron ke naam ke routes aur From/To employee aur territory. Weekly beat plan agent ka andaza hai; form nahi dikha | W7: nahi banana, WAITING_UI |
| 9 | Approve Mobile Registration = device whitelist | Reference page registrations ki list hai (reg code, name, designation, city, state, territory) bulk approve ya reject ke saath | W7: registration approval banao, device info optional |
| 10 | '88 live' ka hisaab | Ek hi item kaun live hai kaun nahi, evidence ke bina maanna theek nahi | W6: 105 items ka truth matrix aur route smoke |

> Ye ek teacher ki tarah check hai: agent ne 'sab pass' bola, lekin 10 jagah answer sheet reference se match nahi hui. Pehle unhe theek karo, phir nayi cheezein.


## 2. The remaining items, re-classified

| Item (route) | Agent's meaning | Our reading | Decision |
|---|---|---|---|
| Sample Allocation | HO ya manager se MR ko quota | Stock movement HO to employee | W8 BUILD (our ledger design, provisional screens) |
| Sample Issue | MR doctor ya chemist ko sample deta hai | Issue type master (SAMPLE) suggests an issue entry with an issue type; flow not seen | W8 BUILD (provisional) |
| Sample Inward HO | Warehouse se HO stock entry | Stock added at head office | W8 BUILD |
| Std Route Chart | Fixed weekly beat plan | Tiles, town routes, from/to employee and territory; fields unseen | WAITING_UI |
| Tour Plan Lock | Cutoff date lock | Lock tour plan changes for a month or scope | W7 BUILD |
| Approve Mobile Registration | Device whitelist | Registration approval list | W7 BUILD |
| Delete My Visits | Test ya galat visits reset | Bulk soft delete by filters | W7 BUILD (with reversal of side effects) |
| Credit Notes, Credit Note New, Delivery Outward, Monthly Business, Secondary Sales, Incentive Master | Legacy ERP | Sales and finance data module | DEFERRED (decisions D1 and D4) |
| Financial Year Master | FY master | Already specified in Part 2 | W6 verify in the truth matrix |
| File Mapping Utility, Import Product Mappings, Master Bulk Update, SRC Transfer | Importers and utilities | Import mappings belong to sales imports; bulk update and transfer meanings unconfirmed | DEFERRED until sales decision and screenshots |


## 3. Standard Wave Rules

Har wave ke prompt ek hi file ko follow karte hain: docs/wave-rules.md (alag file bhi di gayi hai). Isme golden rules, inspect-first, seed rules, verification protocol aur reporting format hai. Naya point: endpoint smoke matrix aur route smoke, jo AttributeError jaise bugs ko aap tak aane se pehle pakadte hain.

| Part | What it says |
|---|---|
| Golden rules | Sab dynamic; seed alag files mein; koi personal data nahi; reuse before creating; anjaan screens ka matlab invent nahi |
| Stage 0 | Pehle inspect karke 'claim versus evidence' table |
| Build | Sirf wave ka scope; chhoti files; paginated lists; permissions; audit; transactions aur idempotency |
| Seeds | Alag files, idempotent, assumptions ke liye is_provisional, minimum counts ka script |
| Verify | ruff, mypy, pytest, seed twice, endpoint smoke matrix, check:static, route smoke, grep proof, self review, evidence docs, test guide |
| Report | Done tab jab har check pass ho; LIVE ka matlab real page, real API, role checks aur evidence |


## 4. Wave W6: verify and fix what exists

| Area | Backend | Web |
|---|---|---|
| Endpoint smoke | scripts/smoke_all_endpoints.py (every GET and every drill-down as 3 roles on seeded data); fix all 500 and wrong 403 or 404; regression tests for the two AttributeErrors | npm run smoke:routes for all 105 routes |
| Truth matrix | docs/audit/backend-endpoint-coverage.md | docs/audit/menu-status-matrix.md with the exact remaining items |
| Drill-down | Card count equals detail rows test; check visit type and call type naming | - |
| Reimbursement payout | Only APPROVED, idempotent, ADMIN only, audit, feature flag, tests | Page review: modes from API, UTR validation, double submit guard |
| 5 masters | is_provisional, confirm endpoints | Provisional chip and Confirm |
| Application Setting | Company profile API (if missing) | Real page with logo and signature, branding |
| Calendar | GET /calendar/month with counts and events | Counts in every day plus existing events |
| Meetings | Workflow inbox module | WorkflowInboxPage page |


#### BACKEND W6 - smoke matrix, payout review, calendar, company profile, provisional seeds

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, docs/wave-rules.md, docs/w6-w8-roadmap-spec.md (sections 1 and 4), docs/masters-spec-part2.md, docs/w5-config-audit-mapping-spec.md, docs/visits-summary-drilldown.md. Work ONLY inside Mediateappbackend-api. Follow docs/wave-rules.md completely (inspect first, no hardcoding, separate seed files, verification with evidence, say done only when every check passes).

GOAL: Wave W6 backend: verify and fix what was already built.

1. ENDPOINT SMOKE MATRIX: write scripts/smoke_all_endpoints.py. It reads the OpenAPI schema, logs in as ADMIN, MANAGER and MR on the seeded database (make seed-dev), and calls every GET endpoint (path ids resolved from seeded data, list endpoints with page_size 5) and every Visits Summary drill-down metric for several employees. It prints a table (method, path, role, status) and FAILS on any 500 or unexpected 403 or 404 (document the expected ones). Fix every failure at the root cause. Two bugs already reached the owner at runtime (DcrVisit has no attribute call_type, Doctor has no attribute city): add regression tests for them and a pytest that runs the smoke matrix.
2. DRILL-DOWN CORRECTNESS: for each of the 16 metrics prove with a test that the card count equals the number of detail rows. Check the naming of visit type versus call type against the DCR model and the Visit Type master (call types such as group promotional call) and write any confusion in docs/audit/w6-backend-findings.md. Do not rename columns.
3. REIMBURSEMENT PAYOUT REVIEW: POST /expenses/{id}/payout was built without being in the spec. Inspect and harden it: only for APPROVED expenses; one payout per expense (unique constraint plus idempotency key; a repeated call returns the same payout, never a second one); amounts DECIMAL; payment modes served by the API (master or enum list); UTR or reference required for non-cash modes; permission expenses:payout for ADMIN only (do not invent a new role); audit log; a setting reimbursement.payout_enabled (default true) that disables the feature; tests for every rule. Write in docs/audit that payout tracking is outside the original PRD and needs the owner's confirmation.
4. PROVISIONAL SEEDS: the five masters (attachment types, doctor types, suppliers, hospital categories, product gallery) were seeded with sample values based on assumptions, not on reference screens. Add is_provisional (true for seeded rows) to those tables with a migration, add POST /masters/{type}/{id}/confirm and a bulk confirm, and make the seeders set the flag. Do not change the values. For suppliers and product gallery write docs/waiting-ui/supplier-master.md and docs/waiting-ui/product-gallery-master.md with the questions about their real fields.
5. APPLICATION SETTING: it is the company profile (company name, code, area, phone, mobile, address, logo, signature) and feeds branding and report headers (docs/masters-spec-part2.md section 3). Verify with tests if it exists; if it is missing, or only a redirect exists, implement GET and PUT /company-profile with logo and signature through /files, and public branding in GET /auth/config.
6. CALENDAR AND MEETINGS: implement GET /calendar/month?employee_id=&year=&month= returning for every day the counts (doctor, chemist, stockist, new doctor, new chemist, new stockist, total_pob which is null until orders exist) and the events (holidays, leaves, tour plan days, meetings); default employee is the current user; scoped by role. Verify that meetings follow the workflow inbox pattern (summary of drafts, applied and received, plus view-all; list columns agenda, start, end, created by, organiser) and fix it if it was built as a plain master.
7. COVERAGE DOCUMENT: write docs/audit/backend-endpoint-coverage.md: for each of the 105 menu items (docs/web-admin-inventory.md plus the W5 additions) list the endpoints it uses and the test that covers it; mark items with no endpoint.
8. Seeds: any new seed goes in its own file, idempotent, registered in seed_all.py; no personal data.
FINISH exactly as docs/wave-rules.md says: docs/audit/w6-backend-verification.md with evidence, docs/testing/w6-backend-test-guide.md, make openapi, update CHANGELOG, task.md and memory.md.
```


#### WEB W6 - truth matrix, route smoke, company profile, calendar counts, meeting page

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, frontend-spec.md, docs/wave-rules.md, docs/w6-w8-roadmap-spec.md (sections 1 and 4), docs/masters-spec-part2.md, docs/web-admin-inventory.md. Work ONLY inside Mediateappweb. Run npm run gen:api first (backend W6 must be finished). Follow docs/wave-rules.md completely.

GOAL: Wave W6 web: truth audit and fixes.

1. MENU TRUTH MATRIX: write docs/audit/menu-status-matrix.md with ALL 105 menu items: key, label, route, status (LIVE, PARTIAL, STUB, WAITING_UI, DECISION, DEFERRED), page component, API endpoints it calls, and the test or screenshot that proves it. LIVE only for a real page with a real API that works for ADMIN with evidence. Earlier summaries said 88 live and 17 pending but described a different list (group D has 11 routes, not 10; Financial Year Master was already specified): reconcile and list the exact remaining items.
2. ROUTE SMOKE: add npm run smoke:routes (Playwright if available, otherwise vitest against the running backend): visit every one of the 105 routes as ADMIN, and as MANAGER and MR to check permissions; fail on a blank page, console error, unhandled rejection, failed request or any 5xx; print a table and write docs/audit/route-smoke-report.md. Fix every failure.
3. STATUS VOCABULARY: the ComingSoon page shows the item name, group and one status: STUB, WAITING_UI (show the questions from docs/waiting-ui/<key>.md), DECISION or DEFERRED. No silent redirects: Application Setting must not redirect to General Settings.
4. APPLICATION SETTING: build the company profile page (list of one company with view and edit; company name, code, area, phone, mobile, address; logo and signature upload with preview) and feed the branding of the login page, top bar and sidebar header from the API.
5. MY CALENDAR: keep the events (tour plans, leaves, holidays, meetings) and ADD, inside every day cell, the per-day counts of the reference app (Doctor, Chemist, Stockist, New Doctor, New Chemist, New Stockist, Total POB) from GET /calendar/month; employee selector (default own records, options from the API); previous and next month; a day click opens the agenda and the counts. Everything from the API.
6. MEETING PAGE: it must follow the workflow inbox pattern (tiles Drafts with a + button, Applied, Received, plus View all meetings; columns agenda, start, end, created by, organiser; search by agenda; status coloured rows). If it was built as a plain master, rebuild it on WorkflowInboxPage.
7. PROVISIONAL CHIPS: on the five masters show a Provisional chip on seeded rows with Confirm actions (single and bulk) that call the confirm endpoints.
8. REIMBURSEMENT PROCESSING: review the page: only APPROVED claims can be paid; payment modes come from the API; UTR validation for non-cash modes; double submit prevention; confirmation dialog; clear messages (already paid, not approved, feature disabled); permission expenses:payout.
FINISH exactly as docs/wave-rules.md says: docs/audit/w6-web-verification.md with evidence, screenshots in docs/ui/w6/, docs/testing/w6-web-test-guide.md, update task.md and memory.md.
```


## 5. Wave W7: field security and tour plan lock

| Item | Backend | Web |
|---|---|---|
| Approve Mobile Registration | mobile_registrations: reg code, employee, designation, territory, optional device info, status; bulk approve and reject; activates the account; audit; feeds pending count | Page: states and cities multi-select, status, table with checkboxes, Approve and Reject with confirmation and per-row result |
| Delete My Visits | Preview with count and sample; delete with reason, preview token, max 5,000; soft delete; reverses side effects (planned visit back to PLANNED, follow-ups cancelled, stock reversed through the ledger when it exists); restore within a setting; ADMIN only; audit | Filters, preview count, reason, typed confirmation, result, restore list |
| Tour Plan Lock | tour_plan_locks (scope ALL, TERRITORY, EMPLOYEE; month; cutoff; status; reason); tour plan service blocks create, edit and submit with TOUR_PLAN_LOCKED; admin override with reason; scheduled auto lock from a setting | Lock list, lock and unlock dialogs, history, lock banner on tour plan pages |
| Std Route Chart | Not built. docs/waiting-ui/std-route-chart.md with questions | WAITING_UI page |


#### BACKEND W7 - registrations, delete my visits, tour plan lock

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, docs/wave-rules.md, docs/w6-w8-roadmap-spec.md (section 5), docs/masters-spec-part2.md (sections 5 to 7), docs/w5-config-audit-mapping-spec.md. Work ONLY inside Mediateappbackend-api. Follow docs/wave-rules.md completely. Wave W6 must be finished first.

GOAL: Wave W7 backend: mobile registration approval, Delete My Visits, Tour Plan Lock.

1. MOBILE REGISTRATIONS (if not already built per Backend B of docs/masters-spec-part2.md): table mobile_registrations (registration code = employee code, employee, designation, territory, optional device info such as hashed device id, model and app version, requested_at, status PENDING, APPROVED, REJECTED, decided_by, decided_at, comment). GET list with filters (state_ids, city_ids, status, search) and pagination; POST /mobile-registrations/approve and /reject with ids (bulk, per-row result); approving activates the account and binds the device when device info exists; rejecting keeps the account inactive; audit; the pending count feeds /users/summary. One employee may have several registrations.
2. DELETE MY VISITS: POST /admin/visits/delete-preview (filters: employees, cities, areas, date range, visit type) returns the count, a sample and a preview_token; POST /admin/visits/delete with the token, a required reason and a maximum of 5,000 visits per run. SOFT delete only (BR-11). Handle side effects in ONE transaction: the planned visit returns to PLANNED, follow-ups created by the visit are cancelled, sample and gift stock distributed by the visit is reversed through the inventory ledger with REVERSAL entries if the ledger exists (otherwise record it in docs/audit and add the hook for Wave W8). POST /admin/visits/restore within the number of days given by a setting. Permission visits:delete for ADMIN only; audit with the reason.
3. TOUR PLAN LOCK: table tour_plan_locks (scope ALL, TERRITORY or EMPLOYEE, scope_id, month, financial_year, cutoff date, status LOCKED or UNLOCKED, reason, created_by, unlocked_by, unlocked_at). Endpoints: list, create, unlock, history. The tour plan service must check locks on create, edit and submit and return TOUR_PLAN_LOCKED with the reason and who locked; an admin override needs a reason and is audited. A setting tour_plan.default_cutoff_day and a scheduled job that locks automatically (idempotent, audited).
4. STD ROUTE CHART: do NOT build. Write docs/waiting-ui/std-route-chart.md with the questions (fields, distance and travel mode, approval flow, meaning of from and to employee and territory).
5. SEEDS (separate files): seed_mobile_registrations.py (dev, at least 30 synthetic rows with mixed statuses), seed_tour_plan_locks.py (dev, at least 12 locks, locked and unlocked, different scopes), config keys for the new settings in the system settings JSON. Idempotent, registered in seed_all.py.
6. Tests: bulk approve and reject with valid and invalid ids, device binding, soft delete with every side effect and restore, preview token reuse and expiry, lock enforcement on create, edit and submit, override, scheduled lock idempotency, scope for MANAGER and MR, audit rows. Extend scripts/smoke_all_endpoints.py with every new endpoint.
FINISH exactly as docs/wave-rules.md says: docs/audit/w7-backend-verification.md, docs/testing/w7-backend-test-guide.md, make openapi, CHANGELOG, task.md, memory.md.
```


#### WEB W7 - registrations, delete my visits, tour plan lock

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, frontend-spec.md, docs/wave-rules.md, docs/w6-w8-roadmap-spec.md (section 5), docs/masters-spec-part2.md (sections 5 to 7). Work ONLY inside Mediateappweb. Run npm run gen:api first. Follow docs/wave-rules.md completely. Wave W6 must be finished first.

GOAL: Wave W7 web: Approve Mobile Registration, Delete My Visits, Tour Plan Lock, Std Route Chart status.

1. APPROVE MOBILE REGISTRATION: filters for states and cities (multi-selects; cities depend on states; options from the API) and a status dropdown; a table with row checkboxes and select-all for the filtered result; columns REG. CODE, NAME, DESIGNATION, CITY, STATE, TERRITORY and the device info when present; Approve and Reject buttons with a confirmation dialog (reject asks for a comment) and a per-row result summary; server-side pagination.
2. DELETE MY VISITS: filters (employees multi-select, cities, areas, date range, visit type); a Preview step that shows the count and a sample; a Delete step that needs a reason and a typed confirmation word; a result summary; a Restore tab listing recent deletions with restore. Make the destructive nature clear. ADMIN only.
3. TOUR PLAN LOCK: a list of locks (scope, month, cutoff, status, who and when) with filters; Lock dialog (scope ALL, TERRITORY or EMPLOYEE with pickers, month and financial year, cutoff, reason); Unlock with a reason; history per lock; show a clear lock banner and blocked-action messages (TOUR_PLAN_LOCKED with the reason) on the tour plan pages.
4. STD ROUTE CHART: show the WAITING_UI status with the questions from docs/waiting-ui/std-route-chart.md. Do not build a form.
5. All options, labels and counts come from the API; nothing hardcoded; permissions registrations:approve, visits:delete, tour_plan_locks:read and write; friendly messages for every backend error code.
6. Tests (vitest): bulk selection and result summary, preview-then-delete flow with typed confirmation, lock dialog scopes and error banner. Update docs/ui/w7/ screenshots.
FINISH exactly as docs/wave-rules.md says: docs/audit/w7-web-verification.md, docs/testing/w7-web-test-guide.md, task.md, memory.md.
```


## 6. Wave W8: sample stock (allocation, issue, inward HO)

Ye stock logic hai, galti mehengi padti hai. Isliye ye ek alag wave hai, concurrency tests ke saath. Screens ke fields reference mein nahi dekhe gaye, isliye forms provisional hain. Ledger ka design hamare architecture.md (section 8.3) ke hisaab se hai aur UI badalne par bhi wahi rahega.

| Movement | Stock effect | Who (provisional) |
|---|---|---|
| INWARD_HO | Head office stock + | ADMIN |
| ALLOCATE | Head office -, employee + | ADMIN, MANAGER for own team |
| ISSUE | Employee - (to a customer or with an issue type from the Issue Type master) | ADMIN or MANAGER for the team; MR through the mobile visit |
| RETURN | Employee -, head office + | ADMIN, MANAGER |
| ADJUST | Plus or minus with a reason | ADMIN |
| REVERSAL | Undo of an earlier movement (for example a deleted visit) | System |


#### BACKEND W8 - sample stock ledger

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, architecture.md (section 8.3 inventory ledger), docs/wave-rules.md, docs/w6-w8-roadmap-spec.md (section 6), docs/masters-spec-part2.md, docs/w5-config-audit-mapping-spec.md. Work ONLY inside Mediateappbackend-api. Follow docs/wave-rules.md completely. Waves W6 and W7 must be finished first.

GOAL: Wave W8 backend: sample stock management (Sample Inward HO, Sample Allocation, Sample Issue).

STAGE 0: inspect what exists (promo_items for samples and gifts, products, units, issue types, any inventory tables, DCR sample lines and how the visit submit treats stock). Reuse; create only what is missing. Write docs/audit/w8-inspection.md.
1. LEDGER: append-only inventory_ledger and a balance table stock_balances (item_id, holder_type HO or EMPLOYEE, holder_id nullable for HO, balance DECIMAL) with CHECK (balance >= 0). Movement types INWARD_HO, ALLOCATE, ISSUE, RETURN, ADJUST, REVERSAL. Every movement runs in ONE transaction with row locking (UPDLOCK, HOLDLOCK) that writes the ledger rows and updates the balances together; no other code updates balances. Idempotency key (client_uuid) so a repeated request never posts twice. Quantities DECIMAL, never float. ISSUE takes an issue type from the Issue Type master and a customer (doctor, chemist, stockist) or an employee; REVERSAL references the original movement and can only be done once.
2. ENDPOINTS: POST /inventory/inward-ho, /allocate, /issue, /return, /adjust (reason required), /reversal; GET /inventory/ho-stock, /inventory/employee/{id}, /inventory/ledger (filters item, holder, type, date, employee, customer; paginated), /inventory/summary (totals per item and holder). Permissions (provisional, document them): inward and adjust ADMIN only; allocate ADMIN and MANAGER (employees of own team only); issue ADMIN and MANAGER for the team; MR only through their own visit. Errors INSUFFICIENT_STOCK (with the available quantity), ITEM_NOT_FOUND, DUPLICATE_REQUEST. Show total value of an issue only when the setting sample_issue.show_total_value is true (value from the product price fields; document the assumption).
3. DCR AND DELETE MY VISITS: if the DCR submit does not yet post ISSUE movements for sample and gift lines, add it inside the same transaction as the submit (idempotent). Make Delete My Visits (Wave W7) post REVERSAL entries through this ledger.
4. SEEDS (separate files): seed_stock_inward.py (dev, at least 30 inward entries across at least 10 items), seed_stock_allocations.py (dev, at least 40 allocations), seed_stock_issues.py (dev, at least 40 issues with issue types). Built through the real service functions so the ledger and balances stay consistent. Idempotent and registered in seed_all.py.
5. INVARIANT SCRIPT: scripts/verify_stock_invariants.py checks for every item that HO plus all employee balances equals inward minus issued plus reversals and adjustments, that no balance is negative, and that every ledger row has a valid reference. It must pass on the seeded data and in the tests.
6. TESTS: all movements, insufficient stock, idempotent repeat, reversal once only, permissions and scope for ADMIN, MANAGER and MR, and a CONCURRENCY test that fires at least 50 parallel allocations and issues against the same small stock and proves the balance never goes negative and the totals stay exact. Extend scripts/smoke_all_endpoints.py. Run everything until green.
FINISH exactly as docs/wave-rules.md says: docs/audit/w8-backend-verification.md with the outputs of the invariant script and the concurrency test, docs/testing/w8-backend-test-guide.md, make openapi, CHANGELOG, task.md, memory.md.
```


#### WEB W8 - sample inward, allocation, issue, stock views

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, frontend-spec.md, docs/wave-rules.md, docs/w6-w8-roadmap-spec.md (section 6), docs/masters-spec-part2.md. Work ONLY inside Mediateappweb. Run npm run gen:api first. Follow docs/wave-rules.md completely. Backend W8 must be finished first.

GOAL: Wave W8 web: Sample Inward HO, Sample Allocation, Sample Issue, plus stock views. The forms are provisional because the reference screens were not seen: build only the fields below and mark the pages Provisional in docs; send me screenshots later to refine.

1. SAMPLE INWARD HO: list of inward entries (date, item, quantity, reference note, who) with filters and server-side pagination; Add form (date, item picker, quantity, reference note); idempotent submit (disable the button, send an idempotency key). ADMIN only.
2. SAMPLE ALLOCATION: list of allocations with filters (employee, item, date); Add form with employee picker, one or more items with quantities, and the AVAILABLE head office stock shown live per item; block quantities above the available stock before submit and show INSUFFICIENT_STOCK errors from the server; MANAGER limited to own team (server-enforced).
3. SAMPLE ISSUE: list of issues with filters (employee, customer, issue type, item, date); Add form with employee picker, customer picker (doctor, chemist, stockist), issue type (from the Issue Type master via the API), items and quantities, available stock of the employee shown live, and the total value shown only when the API says so (setting sample_issue.show_total_value). Provide a Reverse action (with a reason) that calls the reversal endpoint.
4. STOCK VIEWS: a Head Office Stock tab and an Employee Stock tab (balances per item), and a Ledger tab with filters and pagination; all from the API; no stock number is calculated in the web code.
5. Everything dynamic: items, employees, customers, issue types, quantities, values, units and messages come from the API. Friendly messages for INSUFFICIENT_STOCK (show available), DUPLICATE_REQUEST, permission errors. Confirmation dialogs for submit and reverse. Works with thousands of ledger rows (server-side only).
6. Tests (vitest): forms with live stock check, insufficient stock error, idempotent double click, reverse flow, value hidden when the setting is off. Screenshots in docs/ui/w8/.
FINISH exactly as docs/wave-rules.md says: docs/audit/w8-web-verification.md, docs/testing/w8-web-test-guide.md, task.md, memory.md.
```


## 7. Deferred and waiting

| Item | Why waiting | What I need |
|---|---|---|
| Std Route Chart | Fields and flow not seen | Screenshots of the + form, the detail (i) view and one received application |
| Supplier Master, Product Gallery Master | Real fields not seen (5 masters were built on assumptions) | Add and Edit forms of both, and the info popup |
| Reimbursement (payout) | Not in the reference screens seen | Screenshots of the Reimbursement pages (the second Monthly Expense item too), and your decision whether payout tracking is wanted |
| Credit Notes, Delivery Outward, Monthly Business, Secondary Sales, Incentive Master | Sales and finance module | Decisions D1 (which menus Mediate really uses) and D4 (where sales data comes from), then entry forms |
| File Mapping Utility, Import Column and Product Mappings, Master Bulk Update, SRC Transfer | Tied to sales imports; meanings unconfirmed | Their screens after the click, and D4 |
| Track Report View | Tracking decision D3 | Your decision (visit points only, or periodic points with consent) |


## 8. How to test and report

- Har wave ke end mein agent docs/testing/wN-*-test-guide.md banayega. Usi ke steps se test karo.
- Issue mile to ye format mein bhejo: Screen aur role, Steps, Expected aur actual, Error text ya Network response, Screenshot, test guide ka step number.
- Pehle W6 (verify aur fix), phir W7, phir W8. Backend prompt pehle, web baad mein.
- Agent ka 'done' tab maano jab uske verification docs mein command outputs ka evidence ho.

> W6 safai hai, W7 field security aur routes, W8 sample stock. Baki items ya to screenshots ka intezaar kar rahe hain ya aapke faisle ka.
