# Reports Spec - Mediate MR App (view + PDF + Excel export)

Place this file at `docs/reports-spec.md` in BOTH repos (mr-backend and mr-mobile). It covers features 27 (Reports and Analytics) and 28 (Export). Backend builds the report engine first; mobile builds the screens after the backend openapi.json is exported.

## 0. Scope and phase note
- This is Phase 7 work (reports, export). 14 reports can be built now because their data already exists (Phases 1 to 5). 7 reports are added later when their data exists (Phase 6 and Phase 8). The report engine is a registry, so later reports plug in without changes to the engine.
- If Phase 6 is still pending, building reports now is an owner decision. Record it in memory.md before starting.
- Same rules as rules.md: no business logic in routers or screens, scope only through core/scope.py, every report test includes scope checks.

## 1. Who sees what (server enforced)
| Role | Scope | Filters offered |
|---|---|---|
| MR | Only own data. mr_id is always forced to the caller | Date, status, customer type |
| MANAGER | Only MRs assigned to the manager (own team) | Date, MR (All my MRs or one MR), territory, status, customer type |
| ADMIN | All MRs | Date, manager, MR, territory, status, customer type |
Rules:
- The export uses exactly the same query, filters and scope as the on-screen report.
- A requested mr_id outside the caller's scope returns 403 with code REPORT_SCOPE_DENIED. Never return partial data silently.
- Every export writes an audit log row: user, report key, filters, format, row count, time.

## 2. Report catalog
Data sources use the table names from the project guide. "Now" means data exists after Phase 5.
| No | Report | What it shows | Data source | Build |
|---|---|---|---|---|
| R01 | DCR Detailed (date wise) | Every visit report, grouped by date, with products, samples, gifts, outcome, verification | dcr_visits, dcr_*_lines, post_call_analysis, customers | Now |
| R02 | Daily Activity Summary | One row per MR per day: check-in/out, hours, calls by type, planned vs done | attendance, dcr_visits, planned_visits | Now |
| R03 | Customer-wise Visits | Per doctor/chemist/stockist/hospital: total visits, last visit, days since, next due | dcr_visits, customers, customer_coverage | Now |
| R04 | Coverage | Assigned customers vs visited, by category A/B/C and MR | customer_coverage, dcr_visits, categories | Now |
| R05 | MR Performance | Working days, calls, call average, coverage %, verified %, target achievement | dcr_visits, attendance, leave_requests, targets | Now (targets added here) |
| R06 | Pending / Late DCR | Days with check-in but missing or late DCRs | attendance, dcr_visits | Now |
| R07 | Geo-Verification | Distance, radius, accuracy, verified or not, mock-location flag | dcr_visits, attendance | Now |
| R08 | Planned vs Actual | Planned, completed, missed, cancelled, unplanned visits, adherence % | planned_visits, dcr_visits | Now |
| R09 | Attendance | Check-in/out time and place, hours, late, absent, leave | attendance, leave_requests | Now |
| R10 | Leave | Requests, type, dates, days, status, approver, balances | leave_requests, leave_balances, approval_actions | Now |
| R11 | Expense | Claims by date, type, amount, receipt, status, approver; totals | expenses, expense_types, approval_actions | Now |
| R12 | Tour Plan | Plans, dates, places, customers, status, deviation days | tour_plans, tour_plan_days, dcr_visits | Now |
| R13 | Follow-up | Pending, overdue, done follow-ups with days overdue | follow_ups, customers | Now |
| R14 | Approval Turnaround | Time taken per approval, pending ageing, average hours | approval_requests, approval_actions | Now |
| R15 | Task | Assigned, completed, pending, overdue tasks | tasks | Later (Phase 6) |
| R16 | Joint Working | Manager visits, observations, feedback | joint_working_visits | Later (Phase 6) |
| R17 | Product Promotion | Products promoted per MR and doctor | dcr_product_lines, products | Later (Phase 8) |
| R18 | Sample and Gift Distribution | Items given, quantities, by MR and customer | dcr_sample_lines, dcr_gift_lines, promo_items | Later (Phase 8) |
| R19 | Stock Balance | MR stock, ledger history | mr_stock_balances, inventory_ledger | Later (Phase 8) |
| R20 | Orders | Chemist and stockist orders, items, status | orders, order_items | Later (Phase 8) |
| R21 | Sales vs Target | Sales against monthly target | orders, targets | Later (Phase 8) |

## 3. Standard filters
| Filter | Notes |
|---|---|
| Date range | Presets: Today, Yesterday, This week, This month, Last month, Custom. Maximum range 92 days for row-level reports (setting). Dates are in Asia/Kolkata and converted to UTC for queries |
| MR, manager | By role (section 1) |
| Territory | Optional |
| Customer type | Doctor, Hospital, Chemist, Stockist |
| Status | Depends on report (Verified / Not verified, Pending / Approved / Rejected, etc.) |
| Sort and page | page, page_size (max 100) for screens; export ignores paging |

## 4. Backend contract (new endpoints)
| Method | Path | Purpose |
|---|---|---|
| GET | /api/v1/reports | Catalog for the caller: key, title, group, description, filter schema, available formats |
| GET | /api/v1/reports/{key} | Paged JSON result |
| GET | /api/v1/reports/{key}/export?format=xlsx or pdf | File download with the same filters |
| GET, PUT | /api/v1/targets | Monthly targets (ADMIN and MANAGER), needed by R05 |
JSON result shape:
```
{
  "meta": { "key": "dcr_detailed", "title": "DCR Detailed Report",
            "filters": { ... applied filters ... }, "scope_label": "Your team (8 MRs)",
            "generated_at": "2026-10-03T10:11:00Z", "columns": [ {"key","label","type","align"} ] },
  "summary": { "total_calls": 214, "verified_pct": 82.5, ... },
  "items": [ ... ], "total": 214, "page": 1, "page_size": 20
}
```
Errors use the standard format. Codes: REPORT_NOT_FOUND, REPORT_SCOPE_DENIED, REPORT_RANGE_TOO_LARGE, EXPORT_TOO_LARGE, INVALID_FILTER.

## 5. Report definitions (columns and summary)
### R01 DCR Detailed
Columns: Date, MR, Emp code, Time, Visit type, Customer, Specialization or type, Category, Territory, Verified, Distance (m), Accuracy (m), Products promoted, Samples, Gifts, Outcome, Remarks, Next visit date.
Summary: total calls, by visit type, verified %, unique customers, total samples, total gifts.
PDF layout: grouped by date, then by MR (manager and admin). Each date has a heading and a day subtotal line (Calls, Doctors, Chemists, Stockists, Verified).
### R02 Daily Activity Summary
Date, MR, Work type, Check-in, Check-out, Hours, Calls total, Doctors, Hospitals, Chemists, Stockists, Planned, Missed, DCR submitted (Yes/No). Summary: days worked, total calls, average calls per day, average hours.
### R03 Customer-wise Visits
Customer, Type, Category, Territory, MR, Total visits in range, Last visit date, Days since last visit, Next visit due, Status (On track / Due / Overdue). Summary: customers, never visited, overdue.
### R04 Coverage
MR, Territory, Assigned customers (A, B, C counts), Visited, Not visited, Coverage %, Frequency met %. Summary: overall coverage %.
### R05 MR Performance
MR, Working days, Calls, Call average, Visit target, Achievement %, Coverage %, Verified %, Attendance days, Leave days. Targets come from the targets table; if no target is set, show "-" and compute the rest.
### R06 Pending / Late DCR
Date, MR, Check-in time, Planned visits, DCRs submitted, Gap, Late submissions (submitted next day or later). Summary: days with gaps.
### R07 Geo-Verification
Date, Time, MR, Customer, Distance (m), Radius (m), Accuracy (m), Verified, Mock location flag, Reason. Summary: verified %, not verified count, mock count.
### R08 Planned vs Actual
Date, MR, Planned, Completed, Missed, Cancelled, Unplanned visits, Adherence %. Summary: overall adherence %.
### R09 Attendance
Date, MR, Work type, Check-in time, Check-in place, Check-out time, Check-out place, Hours, Late (after the configurable late time, default 09:30), Status (Present, Absent, Leave, Weekly off). Absent = no check-in, no approved leave, not a weekly off (Sunday by default). Use the holiday list only if that table exists. Summary: present, absent, leave, late counts.
### R10 Leave
MR, Leave type, From, To, Days, Half day, Reason, Status, Approver, Applied on, Balance after. Summary: total days by type, by status.
### R11 Expense
Date, MR, Type, Amount, Description, Receipt (Yes/No), Status, Approver, Approved on. Summary: total claimed, approved, pending, rejected, by type. Amounts are decimals with 2 places.
### R12 Tour Plan
MR, From, To, Places (territories, cities), Planned customers, Status, Approver, Deviation days (days where visits happened outside the planned territory). Summary: plans by status.
### R13 Follow-up
Customer, Type, MR, Source visit date, Due date, Status, Days overdue. Summary: pending, overdue, done.
### R14 Approval Turnaround
Request type, Requester, Submitted on, Current step, Approver, Action, Action time, Hours taken, Status. Summary: average hours, pending older than 24 hours.

## 6. PDF design
- A4. Landscape for wide tables (R01, R02, R07, R09, R11), portrait for others.
- Header band in deep green (#0C5D46) with white text: company name "Mediate Healthcare", report title, logo placeholder (configurable image in settings).
- Info block under the band: date range, MR or team, territory, other filters, "Generated by <name> (<role>)", generated at (Asia/Kolkata, DD-MMM-YYYY hh:mm A).
- Summary strip: 4 to 6 KPI boxes (light green #DCFCE7 background).
- Table: header row deep green with white bold text, zebra rows (#F3F7FA), thin borders (#EDEEF6), repeated header on every page, right-aligned numbers, wrapped long text (remarks), never cut text.
- Status text colours: Verified or Approved green (#19A14D), Pending amber (#F2A900), Rejected or Not verified or Overdue red (#E22122).
- Footer: "Confidential", "Page x of y", report key.
- Fonts: embed a Unicode TTF (Noto Sans or DejaVu Sans) because the default PDF fonts cannot draw the rupee sign or non-English names. Package the font file in the repo.
- Empty result: a one-page PDF with the header, filters and the line "No records for the selected filters".

## 7. Excel design
- Library: openpyxl.
- Sheets: "Summary" (title, filters, generated info, KPIs) and "Data" (the table). R01 may add a "By Date" sheet with daily subtotals.
- Data sheet: header row deep green fill with white bold font, freeze the header, auto filter on, column widths set per column, wrapped text for remarks, real Excel types (dates as dates, numbers as numbers), number format for amounts with 2 decimals, percent columns formatted as percent.
- Totals row with SUM formulas where meaningful (counts, amounts).
- File name: `<report-key>_<from>_to_<to>_<scope>.xlsx`, PDF the same with .pdf. Example: dcr_detailed_2026-10-01_to_2026-10-31_team.xlsx.

## 8. Export rules
- Row limit for export: 50,000 rows (setting). Above it return EXPORT_TOO_LARGE with a friendly message to narrow the dates.
- Stream the file; do not build huge files in memory when avoidable.
- Content types: application/pdf and application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; set Content-Disposition with the file name.
- Counts in JSON and in the file must match for the same filters.
- All times shown in Asia/Kolkata; stored as UTC.
- Never include data outside the caller's scope, including in the Summary sheet.

## 9. Mobile UX (routes registered in navigation/routes.ts)
| Route | Screen | Behaviour |
|---|---|---|
| Reports | Reports catalog | Grouped cards (Activity, Customers, HR and Expense, Approvals). Search. Only reports the role may open (from /reports). Scope chip: "Showing: Your team (8 MRs)" |
| ReportFilters | Filters | Date presets and custom range, MR picker for manager and admin (EntityPicker pattern), territory, status, customer type. Run report button |
| ReportResult | Result | Summary cards on top, then cards list (not a wide table) with infinite scroll, pull-to-refresh, filter chip row to edit filters, Export button in the app bar |
| (bottom sheet) | Export | Choose PDF or Excel, shows file name, Download button, progress and cancel |
After download: save to the app cache and open the system share sheet (Save to files, WhatsApp, Gmail, Drive). Show a success toast and keep a "Recent exports" list on the Reports screen (local, last 10).
States: loading skeleton, empty ("No records for these filters"), error with Retry, offline ("Reports need internet. Showing last saved result" with a saved copy of the last viewed result; export disabled offline).
Design: same tokens as the app (deep green primary). No design change to existing shared components.

## 10. Tests
Backend:
- Scope: MR cannot request another MR (403), manager cannot request an MR outside the team (403), admin can request anyone; export honours the same scope.
- Each report: correct columns, correct summary on a small seed data set, filters work, paging works.
- Export: PDF starts with %PDF and opens with a PDF reader library; XLSX loads with openpyxl, has the Summary and Data sheets, row count equals JSON total.
- Empty result, range too large, export too large, invalid filter.
- Time zone: a visit at 23:30 IST appears on the correct IST date.
Mobile:
- Hook tests for filters and result; export flow test with a mocked download; role-based catalog and MR picker visibility.

## 11. Acceptance checklist
- [ ] MR sees only own data in every report and export
- [ ] Manager sees only the team and can pick one MR from the team
- [ ] Admin sees all and can filter by manager, MR, territory
- [ ] Each of the 14 reports opens, filters, pages and exports to PDF and Excel
- [ ] PDF has header band, filters block, summary, repeated table header, page numbers, rupee sign renders
- [ ] Excel opens with frozen header, filters and correct types
- [ ] DCR PDF is grouped date wise with day subtotals
- [ ] Mobile downloads the file and opens the share sheet on a real phone
- [ ] Offline shows the saved copy and disables export
- [ ] Later reports (R15 to R21) can be added by registering a report class only