# Visits Summary Drill-down (addendum to web-admin-inventory.md section 3)

Place at `docs/visits-summary-drilldown.md` in Mediateappweb and Mediateappbackend-api. Run its prompts AFTER the Visits Summary prompts of docs/web-admin-inventory.md. No personal data listed.


## 1. What was seen

Home page ke Visits Summary mein har employee card ke andar ki har metric row clickable hai. Row par click karne se uske peeche ki poori detail khulti hai (drill-down). Screenshot mein ek row (New Stockist Visits) neele background ke saath highlight hai, yaani hover ya selected state.

- Card ke andar ki list scroll hoti hai (12 se zyada rows), aur rows ke label ka rang alag hai: counts neele, Doctor Call Average aur Missing Doctor hare, Total POB lal.
- Click karne par kya khulta hai (popup, side panel ya naya page) ka screenshot abhi nahi aaya. Neeche ki design meri assumption hai: side drawer.
- Ye drill-down ek reusable cheez honi chahiye: ek metric = ek detail, wahi component sab metrics ke liye.

> Card ek 'summary' hai. Kisi number par dabane se pata chalta hai ki wo number kin records se bana. Jaise 'Doctor Visits 6' par dabaoge to wo 6 visits ki list khulegi.


## 2. Metric to detail mapping

Har metric ke peeche ki detail. 'Kind' batata hai ki detail kis shakl mein dikhegi: TABLE (list), RECORD (ek record ki detail, map ke saath) ya TIMELINE (din ka sequence).

| No | Metric (row label) | Opens (probable) | Kind | Columns or content | Data now? |
|---|---|---|---|---|---|
| 1 | Chemist Visits | Chemist visits of the date range for that employee | TABLE | Date, time, chemist, owner, area, city, visit type, address, verified | Yes |
| 2 | New Chemist Visits | Chemists newly added by the employee in the range, with the first visit | TABLE | Visit date, name, owner, mobile, city, area, approval status | Yes (customer approval state) |
| 3 | Doctor Visits | Doctor visits | TABLE | Date, time, doctor, speciality, category, area, city, visit type, address, verified | Yes |
| 4 | New Doctor Visits | Doctors newly added by the employee | TABLE | Visit date, name, mobile, city, area, approval status | Yes (customer approval state) |
| 5 | Stockist Visits | Stockist visits | TABLE | Date, time, stockist, owner, city, area, address, verified | Yes |
| 6 | New Stockist Visits | Stockists newly added | TABLE | Visit date, name, owner, mobile, city, area, approval status | Yes (customer approval state) |
| 7 | Doctor Call Average | Day by day doctor calls behind the average | TABLE | Date, doctor calls, working or not, running average | Yes |
| 8 | Missing Doctor | Assigned doctors not visited in the period | TABLE | Doctor, category, speciality, area, city, last visit date, days since | Yes |
| 9 | Punching In Time | The check-in record | RECORD | Time, address, latitude, longitude, accuracy, map pin, mock flag | Yes |
| 10 | First Call Time | The first visit of the day | RECORD | Time, customer, type, address, verified, distance, map pin | Yes |
| 11 | Last Call Time | The last visit of the day | RECORD | Same as first call | Yes |
| 12 | Punchout Time | The check-out record | RECORD | Time, address, latitude, longitude, accuracy, map pin | Yes |
| 13 | Morning Call Details | Calls in the morning slot | TABLE | Same columns as visits | Yes (cut-off setting) |
| 14 | Evening Calls | Calls in the evening slot | TABLE | Same columns as visits | Yes (cut-off setting) |
| 15 | Work Duration | The working day as a sequence | TIMELINE | Punch in, each call with time gaps, punch out, total hours | Yes |
| 16 | Total POB | Orders behind the total (red row) | TABLE | Order no, customer, type, date, quantity, value | After Phase 8 (orders) |


## 3. Backend contract

| Item | Detail |
|---|---|
| Endpoint | GET /api/v1/dashboard/visits-summary/{employee_id}/metrics/{metric_key} with the same filters as the summary (from, to, divisions, state, territory) plus page and page_size |
| metric_key | chemist_visits, new_chemist_visits, doctor_visits, new_doctor_visits, stockist_visits, new_stockist_visits, doctor_call_average, missing_doctor, punch_in_time, first_call_time, last_call_time, punch_out_time, morning_calls, evening_calls, work_duration, total_pob |
| Response | { meta: { title, kind (TABLE, RECORD, TIMELINE), columns, filters, generated_at, data_as_of }, rows (TABLE), record (RECORD with fields and optional location), events (TIMELINE), total, page, page_size }. Titles and column labels come from the backend |
| Export | GET .../metrics/{metric_key}/export?format=xlsx with the same filters (assumption, confirm) |
| Same numbers | The count on the card and the number of rows in the detail must always match for the same filters (test it) |
| Scope | ADMIN all, MANAGER own team, MR self through core/scope.py; an employee outside scope returns REPORT_SCOPE_DENIED |
| Not available | total_pob before orders exist returns kind TABLE with status COMING_SOON and a reason, never invented rows |
| Settings | Morning and evening cut-off, missing doctor period and call average period come from settings with documented defaults |
| Performance | Detail queries are paginated and indexed (visit date, employee, customer); fast on 200,000 synthetic visits |


## 4. Web behaviour

- Clickable rows: pointer cursor, hover highlight (a light tint from our theme, like the highlight seen), a small chevron, keyboard focus and Enter to open. Rows with value null or COMING_SOON show a tooltip instead of opening.
- Detail drawer (assumption): opens from the right with the employee photo, name, territory, the metric title, the date range, and the content by kind: TABLE (paginated, sortable, sticky header), RECORD (key-value list plus a small map with the pin), TIMELINE (vertical events).
- Buttons in the drawer: Close, Download Excel (when the API offers it), and Open full page (route /home/employee/:employeeId/:metric with the filters in the query string so the link can be shared or bookmarked).
- Everything comes from the API (titles, columns, rows). No metric title or column is hardcoded in the web code; the card's row labels also come from the summary response.
- Loading skeleton, empty state, error with Retry. Works with 500+ employees on the home page (cards are virtualized or paginated).


## 5. Prompts

Ye prompts Visits Summary ke pehle wale prompts (web-admin-inventory.md) ke baad chalane hain. Dev data ke liye seed files pehle se hain (seed_visits.py aur baaki); naye data ke liye alag seed file ban sakti hai, ek badi file nahi.


#### BACKEND D - Visits Summary drill-down endpoint

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, architecture.md, docs/web-admin-inventory.md (section 3), docs/visits-summary-drilldown.md. Work ONLY inside Mediateappbackend-api. Do not change other folders.

GOLDEN RULES: Everything is dynamic from the database through the API; titles, column labels and rows come from the backend. Seed data only in the seed/ package, one file per seeder; no real personal data; synthetic data only.

GOAL: Add the drill-down of the Visits Summary cards: one endpoint per employee and metric, as described in sections 2 and 3 of docs/visits-summary-drilldown.md.

1. Implement GET /api/v1/dashboard/visits-summary/{employee_id}/metrics/{metric_key} for the 16 metric keys, with the same filters as the summary endpoint (from, to, divisions, state, territory) plus page and page_size. Response shape: meta (title, kind TABLE or RECORD or TIMELINE, columns, filters, generated_at, data_as_of), rows for TABLE, record for RECORD (fields plus latitude, longitude, accuracy, address), events for TIMELINE, total, page, page_size. Put each metric in its own small file under app/modules/dashboard/metrics/ (one metric = one file) with a registry.
2. The count shown on the card and the number of rows of the detail must be produced by the SAME query logic (share one query builder per metric) so they can never disagree. Add a test that compares them for every metric on seed data.
3. Scope with core/scope.py (ADMIN all, MANAGER own team, MR self); REPORT_SCOPE_DENIED for an employee outside the scope. Settings (morning and evening cut-off, missing doctor period, call average period) are read from the settings service with documented defaults, never hardcoded.
4. total_pob (and any metric whose data does not exist yet) returns status COMING_SOON with a reason and no rows. Never invent numbers.
5. Optional Excel export GET .../export?format=xlsx with the same filters (styled header, same columns); add it for TABLE metrics.
6. Performance: paginated, indexed on visit date, employee and customer; measure with 200,000 synthetic visits. Add or extend a seed file (for example seed/seed_visits.py) so synthetic data covers every metric (new customers, missing doctors, first and last calls, attendance with locations).
7. Tests: each metric (columns, rows, kind), card count equals detail rows, scope for three roles, empty range, IST boundary, pagination, COMING_SOON for total_pob. Run ruff, mypy, pytest until green. make openapi. Update docs/CHANGELOG.md, task.md and memory.md with evidence. Do not start other features.
```


#### WEB D - clickable metric rows and detail drawer

```text
Read first (E:\Mediate root): memory.md, task.md, rules.md, frontend-spec.md, docs/web-admin-inventory.md (section 3), docs/visits-summary-drilldown.md. Work ONLY inside Mediateappweb. Do not change other folders.

GOLDEN RULES: Everything on screen comes dynamically from the backend API (npm run gen:api first, generated types only). No metric title, column, label or number is hardcoded. No mock data in production paths. Use our theme tokens.

GOAL: Make every metric row inside the employee cards of the Visits Summary home page clickable and show its full detail (docs/visits-summary-drilldown.md).

1. Clickable rows: pointer cursor, hover tint from the theme, a small chevron, keyboard focus and Enter to open. Rows whose value is null or whose status is COMING_SOON show a tooltip with the reason and do not open.
2. MetricDetailDrawer (opens from the right): header with employee photo, name, territory, metric title (from the API), and the date range. Body by meta.kind: TABLE (paginated server-side, sortable, sticky header, columns from the API), RECORD (key-value fields and a small map with the pin when latitude and longitude exist), TIMELINE (vertical events with times and gaps). Loading skeleton, empty state, error with Retry.
3. Drawer buttons: Close, Download Excel (only when the API offers export), and Open full page. The full page route is /home/employee/:employeeId/:metric with the filters in the query string; opening that link directly must load the same detail (shareable and bookmarkable). Browser back closes the drawer or returns to the home page correctly.
4. The card must show the metric labels and values from the summary response (no fixed list in code). The scrollable list inside the card keeps working; the home page stays smooth with 500+ employees (virtualized or paginated cards).
5. Permissions and scope are enforced by the backend; show friendly messages for REPORT_SCOPE_DENIED and COMING_SOON.
6. Tests (vitest): row click opens the drawer, each kind renders from a sample response, null and COMING_SOON rows do not open, deep link loads, back button. Run lint, typecheck, test and build until green. Save screenshots in docs/ui/. Update task.md and memory.md. Do not start other features.
```
