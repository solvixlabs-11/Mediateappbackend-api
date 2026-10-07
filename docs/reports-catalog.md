# Reports Catalog (v2) - target: feature parity with the reference MR app

Place at `docs/reports-catalog.md` in BOTH repos. This file REPLACES sections 2 (Report catalog) and 5 (Report definitions) of docs/reports-spec.md. All other sections of reports-spec.md (roles and scope, filters, API contract, PDF design, Excel design, export rules, mobile UX, tests) still apply.

Decision: first build the same set of reports as the reference app (26 seen so far; the list may continue below "Outstanding Report", the owner will send the rest). The owner's own extra features come after this is complete. The UI is our own design, not a copy.

## 1. Build status groups
| Group | Meaning | Count |
|---|---|---|
| NOW | Data exists after Phases 1 to 5 | 16 |
| P8 | Needs Phase 8 data (products, samples, orders) | 3 |
| SALES | Needs new sales and finance data (see section 4) | 6 |
| ASK | Meaning unknown, owner must explain | 1 |
Admin sees ALL 26 in the catalog. Reports that cannot run yet show a "Coming soon" tag and open a named ComingSoon screen with the reason. They never crash and are never hidden.

## 2. Catalog and definitions
Names follow the reference app (spelling fixed). Common filters for every report: date range, MR (by role), territory, plus the extra filters listed. Common export: PDF and Excel.
Role rule: MR = own data. MANAGER = own team. ADMIN = all. Exceptions: "MR Designation Wise Visits Analysis" is Manager and Admin only; "Induction Report" is Admin only.

### Group A: Master lists
| No | Report | Columns | Extra filters | Source | Status |
|---|---|---|---|---|---|
| 1 | Doctor List | Name, Code, Specialization, Category, Priority, Qualification, Hospital or clinic, Area, City, Territory, Phone, Assigned MR, Active | Specialization, category, active | doctors, hospital_doctors, customer_coverage | NOW |
| 2 | Chemist List | Name, Code, Owner, Phone, Address, Area, Territory, Assigned MR, Active | Active | chemists, customer_coverage | NOW |
| 3 | MR Wise Route Master | MR, Territory or route, Area, City, Assigned from, Doctors count, Chemists count, Stockists count | - | territory_assignments, territories, areas | NOW (confirm if the reference app has a separate "route" master) |

### Group B: Attendance and daily work
| No | Report | Columns | Extra filters | Source | Status |
|---|---|---|---|---|---|
| 4 | MR Daily Punching | Date, MR, Punch-in time and place, Punch-out time and place, Hours, Late, Work type | Work type | attendance | NOW |
| 5 | MR Wise Attendance Report | Month matrix: MR rows, day columns with P (present), A (absent), L (leave), W (weekly off); totals present, absent, leave, late | Month | attendance, leave_requests | NOW |
| 6 | Daily Work Report | Date, MR, Work type, Planned visits, Doctor calls, Chemist calls, Stockist calls, Hospital calls, Total calls, DCR submitted, Hours, Remarks | - | attendance, dcr_visits, planned_visits | NOW |

### Group C: Visits
| No | Report | Columns | Extra filters | Source | Status |
|---|---|---|---|---|---|
| 7 | MR Wise Visits | Grouped by MR then date: Time, Visit type, Customer, Specialization or type, Category, Verified, Distance, Outcome, Remarks, Next visit. PDF grouped date wise with day subtotals | Visit type, verified | dcr_visits, post_call_analysis | NOW |
| 8 | MR Wise Visits Analysis | MR, Total visits, Doctor, Hospital, Chemist, Stockist split, Unique customers, Days worked, Average per day, Verified %, Planned vs actual % | Visit type | dcr_visits, attendance, planned_visits | NOW |
| 9 | MR Designation Wise Visits Analysis | Designation, MR count, Total visits, Average visits per MR, Average per day, Verified % | Designation | dcr_visits, users.designation | NOW |
| 10 | MR Wise Doctor Chemist Call | MR, Doctor calls, Chemist calls, Stockist calls, Doctor to chemist ratio (optional day-wise view) | - | dcr_visits | NOW |
| 11 | MR Wise Promotional Call | MR, Date, Customer, Products promoted, Samples, Gifts | Product | dcr_visits, dcr_product_lines, products | P8 |
| 12 | MR Deviation Report | Date, MR, Planned territory and customers, Actual territory and visits, Deviation type (other territory, unplanned, missed), Remarks | Deviation type | tour_plans, tour_plan_days, planned_visits, dcr_visits | NOW |

### Group D: Doctor analysis
| No | Report | Columns | Extra filters | Source | Status |
|---|---|---|---|---|---|
| 13 | MR Doctor Wise Monthly Summary | MR, Doctor, Category, Specialization, visit count per day or week of the month, Month total, Last visit, Required frequency, Frequency met | Month, category | dcr_visits, customer_coverage | NOW |
| 14 | MR Wise Not Seen Doctor | MR, Doctor, Category, Specialization, Territory, Last visit date, Days since last visit, Required frequency | Category, days not seen | doctors, dcr_visits, customer_coverage | NOW |
| 15 | MR Wise Doctor Specialization Wise Stats | MR, Specialization, Doctors assigned, Doctors visited, Total visits, Coverage %, Average visits per doctor | Specialization | doctors, dcr_visits | NOW |
| 16 | MR Wise Doctor Category Wise Report | MR, Category (A, B, C), Assigned, Visited, Total visits, Coverage %, Frequency met % | Category | doctors, dcr_visits, customer_coverage | NOW |
| 17 | MR Wise Doctor Type Wise Report | Same as report 16 but grouped by doctor type | Doctor type | doctors, dropdown_items | NOW (confirm what "doctor type" means; use a doctor type dropdown master) |

### Group E: Stock and orders
| No | Report | Columns | Extra filters | Source | Status |
|---|---|---|---|---|---|
| 18 | MR Wise Sample Balance Report | MR, Item, Opening, Allocated, Distributed, Returned, Balance | Item type | inventory_ledger, mr_stock_balances | P8 |
| 19 | Order Register | Order no, Date, MR, Customer, Items count, Quantity, Status | Status, customer type | orders, order_items | P8 |

### Group F: Sales and finance (new data needed)
| No | Report | Columns | Extra filters | Status |
|---|---|---|---|---|
| 20 | MR Wise Chemist Wise Sales | MR, Chemist, Month, Quantity, Sales amount | Month | SALES |
| 21 | MR Wise Stockist Wise Sales | MR, Stockist, Month, Quantity, Sales amount | Month | SALES |
| 22 | MR Wise Monthly Business Report | MR, Month, Target, Sales achieved, Achievement %, Growth vs last month | Month | SALES |
| 23 | Collection Report | Date, Customer, Receipt no, Mode, Amount, MR | Mode | SALES |
| 24 | Credit Note Report | Credit note no, Date, Customer, Reason, Amount, MR | - | SALES |
| 25 | Outstanding Report | Customer, Invoice no, Invoice date, Amount, Paid, Outstanding, Days overdue, MR | Overdue days | SALES |

### Group G: Unknown
| No | Report | Status |
|---|---|---|
| 26 | Induction Report | ASK: the owner must open it in the reference app and send a screenshot of the output. Do not guess its columns |

Columns above are our design based on the report names. When the owner sends a sample output of any report from the reference app, adjust the columns to match what users expect.

## 3. Mapping to the first catalog (reports-spec.md R01 to R14)
Reports 4 to 17 cover R01 to R09 and R12 and R13 of the first catalog. Keep these extra reports from the first catalog as Phase 7 extras after parity: R06 Pending or Late DCR, R07 Geo-Verification, R10 Leave, R11 Expense, R13 Follow-up, R14 Approval Turnaround.

## 4. Sales and finance data (decision needed before reports 20 to 25)
The app does not capture invoices, sales, collections, credit notes or outstanding yet. Options:
| Option | How data arrives | Notes |
|---|---|---|
| A (recommended first) | Admin uploads Excel files (sales, collections, credit notes, outstanding) with row-wise error report | Simple, safe, fast to build |
| B | Integration with the company billing or ERP software through the integration interface (feature 34) | Later, depends on the software |
| C | MR enters secondary sales in the app | More work, more errors |
Proposed tables (only after the owner decides): sales_entries, collections, credit_notes, outstanding_invoices, each with customer type and id, MR id, date, amounts, import batch id. Build as a separate small module after reports 1 to 19 are done. Record the decision in memory.md.

## 5. Admin catalog screen (mobile)
- Title "Reports" with a search box and a count chip ("26 reports").
- Grouped sections (collapsible): Master Lists, Attendance and Daily Work, Visits, Doctor Analysis, Stock and Orders, Sales and Finance, Other.
- Each report is a row card: icon, name, one-line description, and a tag: none (ready), "Coming soon" (P8, SALES, ASK).
- Tapping a ready report opens ReportFilters then ReportResult then Export (PDF or Excel). Tapping a coming-soon report opens a short screen explaining what it needs.
- MR and Manager see the same screen with only the reports their role may open; unavailable ones are not listed for them.

## 6. Acceptance
- [ ] Catalog lists all 26 reports for ADMIN with correct groups and tags
- [ ] The 16 NOW reports open, filter, page and export to PDF and Excel
- [ ] MR sees only own data, Manager only the team, Admin all, in view and in export
- [ ] Report 5 (attendance matrix) fits in landscape PDF and Excel with frozen first column
- [ ] Report 7 PDF is grouped date wise with day subtotals
- [ ] Coming-soon reports open a named screen, never crash
- [ ] Adding a later report needs only a new registered report class
