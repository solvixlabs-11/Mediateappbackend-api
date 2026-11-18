# Reports Catalog v3 - union of all reports seen in the reference apps

Place at `docs/reports-catalog-v3.md` in Mediateappweb and Mediateappbackend-api. It REPLACES docs/reports-catalog.md and sections 2 and 5 of docs/reports-spec.md. The engine, scope, export, PDF and Excel design sections of docs/reports-spec.md still apply. Built from: web Excel Reports page (19), web Detail Report menu (18, 15 filter forms seen), mobile report list (26), three web utility report pages. No personal data is listed.


## 1. Purpose and golden rules

Reports ab asli banane hain: dekhna (view), Excel aur PDF download, role ke hisaab se. Maine web ki Excel Reports list (19), Detail Report menu (18), mobile ki 26 reports aur 3 utility pages ko milaya. Duplicate hata kar 48 reports bane.

- Ek hi report engine sab ke liye. Har report ka alag page ya alag form nahi. Filter form schema se banega (backend deta hai).
- Sab dynamic: report ki list, naam, group, filter fields, dropdown options, columns, summary, 'data as of' sab API se. UI mein koi report ka naam ya filter hardcode nahi.
- Seed alag file mein: seed/seed_report_definitions.py aur seed/data/report_definitions.json. Report ka code (query) ek report = ek file, ek badi file nahi.
- Jo report ka data abhi nahi hai wo catalog mein 'Coming soon' tag ke saath dikhegi, nakli numbers kabhi nahi.
- Scope server par: MR apna, Manager apni team, Admin sab (view aur export dono mein).


## 2. What the reference reports pages show

| Part | What is seen | Our requirement |
|---|---|---|
| Reports page (web) | Title 'EXCEL REPORTS'. Search box, a NAME dropdown, table SR. and NAME with 19 report names, page size 20, 'Showing 1 to 19 of 19 Entries' | Catalog list from the API: search, group filter, status tag, page size |
| What a click does | Not seen | Open the filter form of that report, then View, Download Excel or PDF (assumption, confirm) |
| Detail Report menu (web) | 18 items; each page is a filter form with an orange button and a blue download button; 15 forms seen | All through the same runner screen, selected by report key |
| Filter style | Labels like 'Month *', 'FY *', 'From-To Date *' (mandatory marked). Many multi-selects say 'By default all ... are considered as selected' | Empty multi-select means all inside the user's scope |
| Outputs | Orange button (probably view on screen), blue button (download). Target vs Achievement has only download. Outstanding shows 'Last updated data ' | View, Excel, PDF; meta.data_as_of shown when the API sends it |
| Mobile | A plain list of 26 report names | Same catalog endpoint and the same schema-driven filters |


## 3. Filter field types (schema driven)

Har report ke filters ek JSON schema se aate hain. Backend ye field types support karega; web (aur baad mein mobile) har type ke liye ek component banayega.

| Type | Seen in | Behaviour |
|---|---|---|
| date_range | From-To Date* (default today) | Two dates, presets allowed, mandatory flag |
| date | Outstanding (Date*), Track Report (Date*) | Single date |
| time | Track Report start and end time | HH:MM |
| month + year | Month*, Year* (stepper) | Month dropdown and year stepper |
| financial_year | FY*, Prev. FY* | Options from the Financial Year master |
| multi_select | Employees, Divisions, Designations, States, Cities, Areas, Territories (child), Specialities, Product types, Products, Stockists, Chemists | Options loaded from the API with search; empty = all in scope; 'at least one' flag for some reports |
| select (single) | Employee, Territory*, Status*, Report type*, Filter, Detail or Summary, Outstanding type* | Options from the API or from the report schema |
| toggle yes/no | Value, Qty, Primary, Secondary (Target vs Achievement) | Yes or No |
| dependent selects | Cities depend on states, areas on cities | Options endpoint accepts parent ids |


## 4. The unified catalog (48 reports)

Seen in: W = web Excel Reports list, D = web Detail Report menu, M = mobile list, U = web utility page. Status: NOW data exists after Phase 5 and the masters, P8 needs products, stock or orders, SALES needs sales and finance data (decision D4), DECISION needs your decision, ASK meaning unknown. '(standard)' means the form was not seen and the standard filters are used.


### Field activity

| No | Report (name as seen) | Seen in | Probable output | Filters | Status |
|---|---|---|---|---|---|
| 1 | Daily Call Report (MR Wise Call Summary) / Daily Work Report | D, M | Per employee per day: doctor, chemist, stockist calls, new customers, first and last call time, hours | Month*, Year*, Status*, Employees, Divisions, Designations, State | NOW |
| 2 | MR Wise Visit Detail / MR Wise Visits | D, M | Every visit with its details, grouped by employee and date | Month*, FY*, Employees (one or more) | NOW |
| 3 | MR_DailyPunching | W, M | Punch in and punch out time and place per day | Date range, Employees (standard) | NOW |
| 4 | MR_Wise_Attendence_Report | W, M | Month matrix P, A, L, W with totals | Month, Employees (standard) | NOW |
| 5 | MR_Wise_Visits_Analysis | W, M | Visits split by customer type, averages, verified % | Date range, Employees (standard) | NOW |
| 6 | MR_Designation_Wise_Visits_Analysis | W, M | Visits grouped by designation | Date range, Designations (standard) | NOW |
| 7 | MR_Wise_Doctor_Chemist_Call | W, M | Doctor, chemist and stockist calls per employee | Date range, Employees (standard) | NOW |
| 8 | MR Wise PromotionalCall | M | Calls of the promotional call type (product columns once products exist) | Date range, Employees, Visit type (standard) | NOW |
| 9 | MR_Deviation_Report | W, M | Planned versus actual (outside tour plan, unplanned, missed) | Date range, Employees (standard) | NOW |
| 10 | Pending DCR Details | W | Days with check-in but missing or late visit reports | Date range, Employees (standard) | NOW |
| 11 | MR_Wise_Details | W | Unclear (employee wise details) | not seen | ASK |
| 12 | Management_Summary_Report | W | Summary numbers per territory or employee for a period (definition to confirm) | not seen (assume date range, territory) | NOW |
| 13 | MR_Wise_Not_Login_WEB | W | Active employees who did not log in on the web in the period | Date range (standard) | NOW |
| 14 | Track Report View | D | Movement points of one employee between start and end time | Date*, Start time*, End time*, Employee | DECISION |
| 15 | K.M. Report | D | Kilometres travelled per day (method to confirm) | From-To date*, Employee (single) | NOW |


### Doctor and customer analysis

| No | Report (name as seen) | Seen in | Probable output | Filters | Status |
|---|---|---|---|---|---|
| 16 | MR_Doctor_Wise_Monthly_Summary | W, M | Doctor x day visit counts for a month | Month, Employees (standard) | NOW |
| 17 | MR_DoctorWise_Yearly_Summary | W | Doctor x month visit counts for a financial year | FY, Employees (standard) | NOW |
| 18 | MR_Wise_Not_Seen_Doctor | W, M | Doctors not visited in the period | Date range, Employees (standard) | NOW |
| 19 | MR Wise DocSp Wise Stats | M | Specialization wise doctors, visits, coverage | Date range, Employees, Specialities (standard) | NOW |
| 20 | MR Wise Doctor Category Wise Report | M | Category wise assigned, visited, coverage | Date range, Employees (standard) | NOW |
| 21 | Doctor Type Wise Report / MR Wise Doctor Type Wise | D, M | Visits and coverage by doctor type | From-To date*, Employees | NOW |
| 22 | Doctor List | M | Doctor master listing | State, City, Territory, Speciality, Status (standard) | NOW |
| 23 | Chemist List | M | Chemist master listing | State, City, Territory, Status (standard) | NOW |
| 24 | Territory Hierarchy Report | D | Territory tree with employees and designations | Filter, Employees, States, Designations | NOW |
| 25 | MR Wise Route Master | M | Territory or route assignment per employee | Employees (standard) | NOW |
| 26 | Unassigned_Customers_Division_Wise_Report | W | Customers with no employee assigned, by division | Divisions, States (standard) | NOW |
| 27 | Unassigned_MR_Customer_Wise_Report | W | Employees with no customers assigned | (standard) | NOW |
| 28 | Unassigned_MR_Division_Wise_Report | W | Employees not mapped to a division | (standard) | NOW |


### Plans, leave and expense

| No | Report (name as seen) | Seen in | Probable output | Filters | Status |
|---|---|---|---|---|---|
| 29 | Tour Plan Report | D | Tour plans per employee | From-To date*, Employees | NOW |
| 30 | Tour Plan Status Report | U | Submitted, approved, pending tour plans per employee for a month | Month*, FY*, States, Designations, Filter (Active) | NOW |
| 31 | MR_Wise_Leave_Report | W | Leaves per employee with balances | Date range, Employees (standard) | NOW |
| 32 | MR_Wise_Monthly_Expense_Report | W | Expense per employee for a month | Month, Employees (standard) | NOW |
| 33 | Monthly Expense Reimbursement Statement | U | Printable monthly statement for one employee (PDF with signature block) | Month*, Year*, Employee | NOW |


### Stock, orders, sales and finance

| No | Report (name as seen) | Seen in | Probable output | Filters | Status |
|---|---|---|---|---|---|
| 34 | Order_Register / Order Register | W, M | Orders (chemist and doctor) with estimated date | Date range, Employees (standard) | P8 |
| 35 | Sample Balance Report / MR Wise Sample Balance | D, M | Sample stock balance per employee | From-To date*, Employees, Divisions, Product types, Products | P8 |
| 36 | Product Comparison Report | D | Product wise comparison (probably sales or visits) | From-To date*, Employees, Divisions, Product types, Products | P8 |
| 37 | Chemist Wise Sales Report / MR Wise Chemist Wise Sales | D, M | Secondary sales by chemist | Month*, FY*, Chemists, Stockists | SALES |
| 38 | Stockist Wise Sales Report / MR Wise Stockist Wise Sales | D, M | Sales by stockist | Month*, FY*, Stockists, Chemists | SALES |
| 39 | Primary Sales Report | D | Primary sales per stockist, detail or summary | From-To date*, Report type*, Filter, Employee, Stockists, Detail or Summary | SALES |
| 40 | Monthly Business Report / MR Wise Monthly Business | D, M | Monthly business per employee | From-To date*, Employees*, Specialities, States | SALES |
| 41 | Target VS Primary and Secondary Achievement | D | Target against primary and secondary sales (value, quantity) | Territory*, FY*, From-To*, Prev FY*, Report type*, Value, Qty, Primary, Secondary, Cities, States | SALES |
| 42 | Collection Report | D, M | Payments collected | not seen | SALES |
| 43 | Credit Note Report | M | Credit notes | not seen | SALES |
| 44 | Out Standing Report / OutStanding Report | D, M | Outstanding receivables with a 'data as of' note | Date*, Report type*, Division, Stockists, Areas, Cities, States, Outstanding type* | SALES |


### Unclear or company specific

| No | Report (name as seen) | Seen in | Probable output | Filters | Status |
|---|---|---|---|---|---|
| 45 | PP and Ivset Report | D | Unknown, looks product or company specific | not seen | ASK |
| 46 | Steriport And FFS Report | D | Unknown, looks product or company specific | not seen | ASK |
| 47 | Induction Report | M | Unknown (induction or training) | not seen | ASK |
| 48 | Visit Analysis (employee tracker) | U | Per employee visit analysis | From-To date*, Filters (Active), Employees | NOW |


## 5. Summary and the status of data

| Status | Count | What it means |
|---|---|---|
| NOW | 32 | Can be built now from existing data |
| P8 | 3 | Wait for products, stock and orders (Phase 8) |
| SALES | 8 | Wait for sales, collection, credit note, outstanding data (D4) |
| DECISION | 1 | Track report: tracking decision D3 |
| ASK | 4 | Meaning unknown: need output screenshots |
| Total | 48 |  |


### Definitions to confirm (assumptions used in the prompts)

| Report | Assumption | Confirm with |
|---|---|---|
| Management Summary | Summary numbers per territory for a date range: employees, working days, calls, doctor coverage, pending DCR | Output screenshot |
| MR Wise Details | Not built until the output is seen | Output screenshot |
| Not Login WEB | Active employees with no web login in the date range; needs login events with a channel (web or mobile) | Owner |
| K.M. Report | Distance between consecutive visit points of a day (check-in, visits, check-out) using the haversine formula; standard route chart km later | Decision D6 |
| Unassigned reports | Customers without an assigned employee; employees without customers; employees without a division | Output screenshot |
| Track Report View | Waits for decision D3 (tracking) | Owner |
| Orders | Orders also exist for doctors | Already noted |


## 6. Backend design


### 6.1 Tables and seed

| Item | Detail |
|---|---|
| report_definitions | key (unique), name, group, description, sort_order, status (AVAILABLE, COMING_SOON), unavailable_reason, formats (screen, xlsx, pdf), filter_schema (JSON), allowed_roles, data_as_of_source, is_active |
| Seed | seed/seed_report_definitions.py reads seed/data/report_definitions.json (all 48 reports, names as in the catalog, filter schemas, roles). Config data only. Idempotent, upsert by key |
| Code | One file per report: app/modules/reports/definitions/.py with the query, columns and summary. A definition row without code is listed as COMING_SOON. Code without a row is not listed |
| Engine | app/modules/reports/engine/: registry, filter parsing and validation, scope, xlsx export, pdf export, fonts |


### 6.2 Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | /api/v1/reports | Catalog for the caller (search, group, status, page, page_size). Drives the Reports page and the menu tags |
| GET | /api/v1/reports/{key} | Definition: name, group, filter schema with defaults, status, formats, data_as_of |
| GET | /api/v1/reports/options/{source} | Options for filters (employees, divisions, designations, states, cities, areas, territories, specialities, product types, products, stockists, chemists, financial years); search, parent ids, paging; scoped by role |
| POST | /api/v1/reports/{key}/run | View: body { filters, page, page_size, sort } returns { meta, summary, columns, rows, total } |
| POST | /api/v1/reports/{key}/export?format=xlsx/pdf | Download with the same filters (POST because multi-select lists are long); audit log |

Errors: REPORT_NOT_FOUND, REPORT_NOT_AVAILABLE (with the reason), REPORT_FILTER_REQUIRED, REPORT_SCOPE_DENIED, EXPORT_TOO_LARGE, INVALID_FILTER.


### 6.3 Output rules

- Excel and PDF follow docs/reports-spec.md sections 6 to 8 (deep green header band, filters block, summary strip, repeated header row, page numbers, Unicode font, styled Excel with frozen header and real types).
- Company logo, name and signature come from Application Setting (dynamic), not from files in the code.
- Layouts: attendance and yearly summaries as matrices in landscape; visit reports grouped by date with day subtotals; expense statement as a printable page with a signature block.
- meta.data_as_of shown for data that is synced (for example outstanding).
- Row-level export limit 50,000; aggregated SQL; no N+1; indexes on visit date, employee, customer.
