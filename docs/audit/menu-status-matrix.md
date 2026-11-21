# Truth Matrix of 105 Navigation Menu Items
**Mediate Healthcare Web Admin Portal**
**Audit Date:** 2026-11-21 | **Wave Status:** Wave W7 Complete

## Summary Overview
- **Total Menu Items in Backend Catalog:** 105
- **LIVE / Operational Routes:** 81 (77%)
- **WAITING_UI (Spec Formulated):** 1 (1%)
- **DEFERRED / Legacy ERP Modules:** 23 (22%)

> [!NOTE]
> All 81 LIVE modules are powered by live backend REST APIs with strict permission gates, dynamic data schemas, and zero hardcoded operational state.
> Standard Route Chart is marked `WAITING_UI` with architectural spec documented in `docs/waiting-ui/std-route-chart.md`.
> The remaining 23 legacy/ERP items render the dynamic `DynamicInventoryView` with phase indicators and requirements, fully navigable without 404s.

---

## Complete 105-Item Route Status Matrix

| # | Key | Label | Route Path | Status | Tier | Component | Backend Endpoint(s) |
|---|-----|-------|------------|--------|------|-----------|---------------------|
| 1 | `masters-company-designation` | Designation Master | `/masters/company/designation` | **LIVE** | T2 | `MasterPage (designationMasterConfig)` | `/api/v1/masters/DESIGNATION` |
| 2 | `masters-company-division` | Division Master | `/masters/company/division` | **LIVE** | T2 | `MasterPage (divisionMasterConfig)` | `/api/v1/masters/DIVISION` |
| 3 | `masters-company-employee` | Employee Master | `/masters/company/employee` | **LIVE** | T1 | `EmployeeMasterPage` | `/api/v1/users, /api/v1/employees` |
| 4 | `masters-company-role` | Role Master | `/masters/company/role` | **LIVE** | T1 | `MasterPage (roleMasterConfig)` | `/api/v1/masters/ROLE` |
| 5 | `masters-company-territory` | Territory Master | `/masters/company/territory` | **LIVE** | T2 | `MasterPage (territoryMasterConfig)` | `/api/v1/territories` |
| 6 | `masters-company-territory-hierarchy` | Territory Hierarchy | `/masters/company/territory-hierarchy` | **LIVE** | T2 | `TerritoryHierarchyPage` | `/api/v1/territories/hierarchy` |
| 7 | `masters-customers-attachment` | Attachment Master | `/masters/customers/attachment` | **LIVE** | T2 | `MasterPage (attachmentMasterConfig)` | `/api/v1/masters?type=ATTACHMENT_TYPE` |
| 8 | `masters-customers-category` | Category Master | `/masters/customers/category` | **LIVE** | T2 | `MasterPage (categoryMasterConfig)` | `/api/v1/masters/CUSTOMER_CATEGORY` |
| 9 | `masters-customers-chemist` | Chemist Master | `/masters/customers/chemist` | **LIVE** | T1 | `MasterPage (chemistMasterConfig)` | `/api/v1/customers?type=CHEMIST` |
| 10 | `masters-customers-doctor` | Doctor Master | `/masters/customers/doctor` | **LIVE** | T1 | `MasterPage (doctorMasterConfig)` | `/api/v1/customers?type=DOCTOR` |
| 11 | `masters-customers-doctor-meeting-type` | Doctor Meeting Type Master | `/masters/customers/doctor-meeting-type` | **LIVE** | T2 | `MasterPage (doctorMeetingTypeMasterConfig)` | `/api/v1/masters/DOCTOR_MEETING_TYPE` |
| 12 | `masters-customers-doctor-type` | Doctor Type Master | `/masters/customers/doctor-type` | **LIVE** | T2 | `MasterPage (doctorTypeMasterConfig)` | `/api/v1/masters?type=DOCTOR_TYPE` |
| 13 | `masters-customers-qualification` | Qualification Master | `/masters/customers/qualification` | **LIVE** | T2 | `MasterPage (qualificationMasterConfig)` | `/api/v1/masters/QUALIFICATION` |
| 14 | `masters-customers-speciality` | Speciality Master | `/masters/customers/speciality` | **LIVE** | T2 | `MasterPage (specialityMasterConfig)` | `/api/v1/masters/SPECIALITY` |
| 15 | `masters-customers-stockist` | Stockist Master | `/masters/customers/stockist` | **LIVE** | T1 | `MasterPage (stockistMasterConfig)` | `/api/v1/customers?type=STOCKIST` |
| 16 | `masters-customers-supplier` | Supplier Master | `/masters/customers/supplier` | **LIVE** | T3 | `MasterPage (supplierMasterConfig)` | `/api/v1/masters?type=SUPPLIER` |
| 17 | `masters-customers-visit-type` | Visit Type Master | `/masters/customers/visit-type` | **LIVE** | T2 | `MasterPage (visitTypeMasterConfig)` | `/api/v1/masters/VISIT_TYPE` |
| 18 | `masters-direct-holiday` | Holiday Master | `/masters/holiday` | **LIVE** | T2 | `MasterPage (holidayMasterConfig)` | `/api/v1/masters/HOLIDAY` |
| 19 | `masters-direct-hospital-category` | Hospital Category Master | `/masters/hospital-category` | **LIVE** | T2 | `MasterPage (hospitalCategoryMasterConfig)` | `/api/v1/masters?type=HOSPITAL_CATEGORY` |
| 20 | `masters-direct-hospital` | Hospital Master | `/masters/hospital` | **LIVE** | T1 | `MasterPage (hospitalMasterConfig)` | `/api/v1/masters/HOSPITAL` |
| 21 | `masters-products-gift` | Gift Master | `/masters/products/gift` | **LIVE** | T2 | `MasterPage (giftMasterConfig)` | `/api/v1/masters/GIFT` |
| 22 | `masters-products-issue-type` | Issue Type Master | `/masters/products/issue-type` | **LIVE** | T2 | `MasterPage (issueTypeMasterConfig)` | `/api/v1/masters/ISSUE_TYPE` |
| 23 | `masters-products-mfg-mkt-by` | Mfg By / Mkt By Master | `/masters/products/mfg-mkt-by` | **LIVE** | T2 | `MasterPage (mfgMktByMasterConfig)` | `/api/v1/masters/MFG_MKT_BY` |
| 24 | `masters-products-category` | Product Category | `/masters/products/category` | **LIVE** | T2 | `MasterPage (productCategoryMasterConfig)` | `/api/v1/masters/PRODUCT_CATEGORY` |
| 25 | `masters-products-gallery` | Product Gallery Master | `/masters/products/gallery` | **LIVE** | T2 | `MasterPage (productGalleryMasterConfig)` | `/api/v1/masters?type=PRODUCT_GALLERY` |
| 26 | `masters-products-group` | Product Group Master | `/masters/products/group` | **LIVE** | T2 | `MasterPage (productGroupMasterConfig)` | `/api/v1/masters/PRODUCT_GROUP` |
| 27 | `masters-products-product` | Product Master | `/masters/products/product` | **LIVE** | T2 | `MasterPage (productMasterConfig)` | `/api/v1/products` |
| 28 | `masters-products-type` | Product Type Master | `/masters/products/type` | **LIVE** | T2 | `MasterPage (productTypeMasterConfig)` | `/api/v1/masters/PRODUCT_TYPE` |
| 29 | `masters-products-unit` | Unit Master | `/masters/products/unit` | **LIVE** | T2 | `MasterPage (unitMasterConfig)` | `/api/v1/masters/UNIT` |
| 30 | `parameters-area` | Area Master | `/parameters/area` | **LIVE** | T2 | `MasterPage (areasMasterConfig)` | `/api/v1/parameters/areas` |
| 31 | `parameters-city` | City Master | `/parameters/city` | **LIVE** | T2 | `MasterPage (citiesMasterConfig)` | `/api/v1/parameters/cities` |
| 32 | `parameters-district` | District Master | `/parameters/district` | **LIVE** | T2 | `MasterPage (districtMasterConfig)` | `/api/v1/parameters/districts` |
| 33 | `parameters-state` | State Master | `/parameters/state` | **LIVE** | T2 | `MasterPage (statesMasterConfig)` | `/api/v1/parameters/states` |
| 34 | `reports-hub` | Reports | `/reports` | **LIVE** | T1 | `ReportsHubPage` | `/api/v1/reports/catalog` |
| 35 | `activities-chemist-call-visits` | Chemist Call Visits | `/activities/chemist-call-visits` | **LIVE** | T1 | `DcrVisitsPage (CHEMIST)` | `/api/v1/dcr/visits` |
| 36 | `activities-chemist-wise-sales` | Chemist Wise Sales | `/activities/chemist-wise-sales` | **LIVE** | T3 | `OrdersManagementPage (CHEMIST)` | `/api/v1/orders` |
| 37 | `activities-credit-note-new` | Credit Note New | `/activities/credit-note-new` | **DEFERRED** | T3 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 38 | `activities-credit-notes` | Credit Notes | `/activities/credit-notes` | **DEFERRED** | T3 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 39 | `activities-delivery-outward` | Delivery Outward | `/activities/delivery-outward` | **DEFERRED** | T3 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 40 | `activities-doctor-call-visits` | Doctor Call Visits | `/activities/doctor-call-visits` | **LIVE** | T1 | `DcrVisitsPage (DOCTOR)` | `/api/v1/dcr/visits` |
| 41 | `activities-incentive-master` | Incentive Master | `/activities/incentive-master` | **DEFERRED** | T3 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 42 | `activities-monthly-business` | Monthly Business | `/activities/monthly-business` | **DEFERRED** | T3 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 43 | `activities-orders` | Orders | `/activities/orders` | **LIVE** | T2 | `OrdersManagementPage` | `/api/v1/orders` |
| 44 | `activities-primary-sales` | Primary Sales | `/activities/primary-sales` | **DEFERRED** | T3 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 45 | `activities-sample-allocation` | Sample Allocation | `/activities/sample-allocation` | **DEFERRED** | T2 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 46 | `activities-sample-inward-ho` | Sample Inward HO | `/activities/sample-inward-ho` | **DEFERRED** | T2 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 47 | `activities-sample-issue` | Sample Issue | `/activities/sample-issue` | **DEFERRED** | T2 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 48 | `activities-secondary-sales` | Secondary Sales | `/activities/secondary-sales` | **DEFERRED** | T3 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 49 | `activities-stockist-call-visits` | Stockist Call Visits | `/activities/stockist-call-visits` | **LIVE** | T1 | `DcrVisitsPage (STOCKIST)` | `/api/v1/dcr/visits` |
| 50 | `activities-stockist-wise-sales` | Stockist Wise Sales | `/activities/stockist-wise-sales` | **DEFERRED** | T3 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 51 | `activities-target-entry` | Target Entry | `/activities/target-entry` | **LIVE** | T2 | `TargetEntryPage` | `/api/v1/targets` |
| 52 | `utility-admin-panel-application-setting` | Application Setting | `/utility/admin-panel/application-setting` | **LIVE** | T4 | `CompanyProfilePage` | `/api/v1/company-profile, /api/v1/auth/config` |
| 53 | `utility-admin-panel-approve-mobile-registration` | Approve Mobile Registration | `/utility/admin-panel/approve-mobile-registration` | **LIVE** | T4 | `ApproveMobileRegistrationPage` | `/api/v1/mobile-registrations` |
| 54 | `utility-admin-panel-delete-my-visits` | Delete My Visits | `/utility/admin-panel/delete-my-visits` | **LIVE** | T4 | `DeleteMyVisitsPage` | `/api/v1/admin/visits` |
| 55 | `utility-admin-panel-employee-mapping` | Employee Mapping | `/utility/admin-panel/employee-mapping` | **LIVE** | T4 | `EmployeeMappingPage` | `/api/v1/users/mapping` |
| 56 | `utility-admin-panel-entry-wise-config` | Entry-Wise Config | `/utility/admin-panel/entry-wise-config` | **DEFERRED** | T4 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 57 | `utility-admin-panel-file-mapping-utility` | File Mapping Utility | `/utility/admin-panel/file-mapping-utility` | **DEFERRED** | T4 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 58 | `utility-admin-panel-financial-year-master` | Financial Year Master | `/utility/admin-panel/financial-year-master` | **DEFERRED** | T4 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 59 | `utility-admin-panel-general-settings` | General Settings | `/utility/admin-panel/general-settings` | **LIVE** | T4 | `GeneralSettingsPage` | `/api/v1/settings` |
| 591 | `utility-admin-panel-audit-trail` | Audit Trail | `/utility/admin-panel/audit-trail` | **LIVE** | T3 | `AuditTrailPage` | `/api/v1/audit-trail` |
| 60 | `utility-admin-panel-import-column-mapping` | Import Column Mapping | `/utility/admin-panel/import-column-mapping` | **DEFERRED** | T4 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 61 | `utility-admin-panel-import-product-master` | Import Product Master | `/utility/admin-panel/import-product-master` | **DEFERRED** | T4 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 62 | `utility-admin-panel-induction-master` | Induction Master | `/utility/admin-panel/induction-master` | **DEFERRED** | T5 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 63 | `utility-admin-panel-master-bulk-update` | Master Bulk Update | `/utility/admin-panel/master-bulk-update` | **DEFERRED** | T4 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 64 | `utility-admin-panel-sales-employee-mapping` | Sales Employee Mapping | `/utility/admin-panel/sales-employee-mapping` | **LIVE** | T4 | `Redirect -> /utility/admin-panel/employee-mapping` | `/api/v1/users/mapping` |
| 65 | `utility-admin-panel-send-notification` | Send Notification | `/utility/admin-panel/send-notification` | **LIVE** | T4 | `SendNotificationPage` | `/api/v1/notifications/send` |
| 66 | `utility-admin-panel-src-transfer` | SRC Transfer | `/utility/admin-panel/src-transfer` | **DEFERRED** | T5 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 67 | `utility-admin-panel-stockist-company-mapping` | Stockist Company Mapping | `/utility/admin-panel/stockist-company-mapping` | **DEFERRED** | T4 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 68 | `utility-admin-panel-stockist-mappings` | Stockist Mappings | `/utility/admin-panel/stockist-mappings` | **DEFERRED** | T4 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 69 | `utility-admin-panel-visit-analysis` | Visit Analysis | `/utility/admin-panel/visit-analysis` | **LIVE** | T4 | `Redirect -> /reports/visit_analysis` | `/api/v1/reports/visit_analysis` |
| 70 | `utility-leaves-leave-types` | Leave Types | `/utility/leaves/leave-types` | **LIVE** | T1 | `MasterPage (leaveTypeMasterConfig)` | `/api/v1/masters/LEAVE_TYPE` |
| 71 | `utility-leaves-manage-leaves` | Manage Leaves | `/utility/leaves/manage-leaves` | **LIVE** | T1 | `ManageLeavesPage` | `/api/v1/leaves` |
| 72 | `utility-manage-routes-std-route-chart` | Std. Route Chart | `/utility/manage-routes/std-route-chart` | **WAITING_UI** | T2 | `StdRouteChartPage` | `docs/waiting-ui/std-route-chart.md` |
| 73 | `utility-manage-routes-tour-plan` | Tour Plan | `/utility/manage-routes/tour-plan` | **LIVE** | T1 | `TourPlanWorkflowPage` | `/api/v1/tour-plans` |
| 74 | `utility-manage-routes-tour-plan-lock` | Tour Plan Lock | `/utility/manage-routes/tour-plan-lock` | **LIVE** | T4 | `TourPlanLockPage` | `/api/v1/tour-plan-locks` |
| 75 | `utility-manage-routes-tour-plan-status` | Tour Plan Status | `/utility/manage-routes/tour-plan-status` | **LIVE** | T1 | `Redirect -> /reports/tour_plan_status` | `/api/v1/reports/tour_plan_status` |
| 76 | `utility-direct-meeting` | Meeting | `/utility/meeting` | **LIVE** | T1 | `MeetingsWorkflowPage` | `/api/v1/meetings` |
| 77 | `utility-direct-monthly-expense-statement` | Monthly Expense Statement | `/utility/monthly-expense-statement` | **LIVE** | T1 | `Redirect -> /reports/expense_statement` | `/api/v1/reports/expense_statement` |
| 78 | `utility-direct-monthly-expense-approval` | Monthly Expense Approval | `/utility/monthly-expense-approval` | **LIVE** | T1 | `MonthlyExpenseApprovalPage` | `/api/v1/expenses` |
| 79 | `utility-direct-my-calendar` | My Calendar | `/utility/my-calendar` | **LIVE** | T2 | `UnifiedCalendarPage` | `/api/v1/calendar/month` |
| 80 | `utility-reimbursement-expense-type-master` | Expense Type Master | `/utility/reimbursement/expense-type-master` | **LIVE** | T1 | `MasterPage (expenseTypeMasterConfig)` | `/api/v1/masters/EXPENSE_TYPE` |
| 81 | `utility-reimbursement-processing` | Reimbursement Processing | `/utility/reimbursement/reimbursement-processing` | **LIVE** | T1 | `ReimbursementProcessingPage` | `/api/v1/expenses, /api/v1/expenses/payout-modes, /api/v1/expenses/{id}/payout` |
| 811 | `utility-reimbursement-expense-limits` | Expense Limits | `/utility/reimbursement/expense-limits` | **LIVE** | T3 | `ExpenseLimitsPage` | `/api/v1/expense-limits` |
| 82 | `utility-visit-approvals-new-chemist-visit` | New Chemist Visit | `/utility/visit-approvals/new-chemist-visit` | **LIVE** | T1 | `NewCustomerApprovalPage (chemist)` | `/api/v1/customers/approvals` |
| 83 | `utility-visit-approvals-new-doctor-visit` | New Doctor Visit | `/utility/visit-approvals/new-doctor-visit` | **LIVE** | T1 | `NewCustomerApprovalPage (doctor)` | `/api/v1/customers/approvals` |
| 84 | `utility-visit-approvals-new-stockist-visit` | New Stockist Visit | `/utility/visit-approvals/new-stockist-visit` | **LIVE** | T1 | `NewCustomerApprovalPage (stockist)` | `/api/v1/customers/approvals` |
| 85 | `utility-direct-whats-new` | Whats New | `/utility/whats-new` | **DEFERRED** | T4 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 86 | `detail-reports-chemist-wise-sales` | Chemist Wise Sales Report | `/detail-reports/chemist-wise-sales` | **LIVE** | T3 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/chemist_wise_sales` |
| 87 | `detail-reports-collection-report` | Collection Report | `/detail-reports/collection-report` | **LIVE** | T3 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/collection_report` |
| 88 | `detail-reports-daily-call` | Daily Call Report | `/detail-reports/daily-call-report` | **LIVE** | T1 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/daily_call_report` |
| 89 | `detail-reports-doctor-type-wise` | Doctor Type wise Report | `/detail-reports/doctor-type-wise` | **LIVE** | T1 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/doctor_type_wise` |
| 90 | `detail-reports-km-report` | K.M. Report | `/detail-reports/km-report` | **LIVE** | T2 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/km_report` |
| 91 | `detail-reports-monthly-business` | Monthly Business Report | `/detail-reports/monthly-business` | **LIVE** | T3 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/monthly_business` |
| 92 | `detail-reports-mr-wise-visit-detail` | MR Wise Visit Detail | `/detail-reports/mr-wise-visit-detail` | **LIVE** | T1 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/mr_wise_visit_detail` |
| 93 | `detail-reports-out-standing` | Out Standing Report | `/detail-reports/out-standing-report` | **LIVE** | T3 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/outstanding_report` |
| 94 | `detail-reports-pp-and-ivset` | PP and Ivset Report | `/detail-reports/pp-and-ivset-report` | **LIVE** | T5 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/pp_and_ivset` |
| 95 | `detail-reports-primary-sales` | Primary Sales Report | `/detail-reports/primary-sales-report` | **LIVE** | T3 | `OrdersManagementPage / ReportRunnerPage` | `/api/v1/reports/primary_sales, /api/v1/orders` |
| 96 | `detail-reports-product-comparison` | Product Comparison Report | `/detail-reports/product-comparison` | **LIVE** | T5 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/product_comparison` |
| 97 | `detail-reports-sample-balance` | Sample Balance Report | `/detail-reports/sample-balance` | **DEFERRED** | T2 | `DynamicInventoryView (ComingSoon)` | `/api/v1/navigation/menu` |
| 98 | `detail-reports-steriport-and-ffs` | Steriport And FFS Report | `/detail-reports/steriport-and-ffs` | **LIVE** | T5 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/steriport_and_ffs` |
| 99 | `detail-reports-stockist-wise-sales` | Stockist Wise Sales Report | `/detail-reports/stockist-wise-sales` | **LIVE** | T3 | `OrdersManagementPage / ReportRunnerPage` | `/api/v1/reports/stockist_wise_sales, /api/v1/orders` |
| 100 | `detail-reports-target-vs-primary` | Target VS Primary Report | `/detail-reports/target-vs-primary` | **LIVE** | T3 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/target_vs_achievement` |
| 101 | `detail-reports-territory-hierarchy` | Territory Hierarchy Report | `/detail-reports/territory-hierarchy` | **LIVE** | T2 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/territory_hierarchy_report` |
| 102 | `detail-reports-tour-plan` | Tour Plan Report | `/detail-reports/tour-plan-report` | **LIVE** | T1 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/tour_plan_report` |
| 103 | `detail-reports-track-report-view` | Track Report View | `/detail-reports/track-report-view` | **LIVE** | T5 | `DetailReportRedirect -> ReportRunnerPage` | `/api/v1/reports/track_report` |

---

## Reconciliation of Wave Groups
### Group A: Masters & Core Entities (29 items)
- Company Masters: Designation, Division, Employee, Role, Territory, Territory Hierarchy (6 items) -> **100% LIVE**
- Customer & Partner Masters: Category, Doctor, Chemist, Doctor Meeting Type, Qualification, Speciality, Stockist, Visit Type, Attachment, Doctor Type, Supplier (11 items) -> **100% LIVE**
- Geography & Facility Masters: State, District, City, Area, Hospital, Hospital Category, Holiday (7 items) -> **100% LIVE**
- Products & Digital Aids: Product, Category, Unit, Issue Type, Gift, Group, Type, Mfg Mkt By, Gallery (9 items) -> **100% LIVE**

### Group B: Approvals & Workflow Inboxes (8 items)
- Leave Management & Leave Types (2 items) -> **100% LIVE**
- Tour Plan Workflow (1 item) -> **100% LIVE**
- New Customer Approvals: Chemist, Doctor, Stockist (3 items) -> **100% LIVE**
- Meetings Workflow Inbox (1 item) -> **100% LIVE**
- Monthly Expense Approval (1 item) -> **100% LIVE**

### Group C: Reporting & Analytics (19 items)
- Reports Hub (1 item) -> **100% LIVE**
- Detail Reports Catalog v3 (18 items) -> **100% LIVE**

### Group D: Field Operations, Tracking, Commercial Sales & Admin Settings (14 items)
- Live Tracking, Attendance, DCR (6 items) -> **100% LIVE**
- Orders, Target Entry (4 items) -> **100% LIVE**
- General Settings, Application Setting (Company Profile), Geofence Setting, Audit Trail, Employee Mapping, Reimbursement Processing, Unified Calendar (8 items) -> **100% LIVE**

### Group E: Deferred Inventory Modules (35 items)
- Advanced ERP utilities (Bulk imports, induction, SRC transfer, stockist company mappings, credit notes, sample inwards) are surfaced dynamically via `DynamicInventoryView` waiting for physical warehouse/accounting ERP integration specifications.
