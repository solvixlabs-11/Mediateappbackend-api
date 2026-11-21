# Backend Endpoint Coverage Matrix (Wave W6)

This document tracks all 105 web admin inventory routes against their backing FastAPI REST endpoints and test coverage.

## Summary
- **Total Menu Items**: 105
- **Endpoints Crawled in Smoke Matrix**: 320 checks across ADMIN, MANAGER, MR
- **Smoke Failures**: 0
- **Pytest Suite**: 76 tests passing (100% green)

---

## 1. Masters (29 Items)

| Route | Label | Backing API Endpoint(s) | Covering Tests | Status |
|---|---|---|---|---|
| `/masters/company/designation` | Designation Master | `GET/POST/PUT/DELETE /api/v1/masters?type=DESIGNATION` | `test_masters.py`, `test_navigation.py` | LIVE |
| `/masters/company/division` | Division Master | `GET/POST/PUT/DELETE /api/v1/masters?type=DIVISION` | `test_masters.py` | LIVE |
| `/masters/company/employee` | Employee Master | `GET/POST/PUT/DELETE /api/v1/users` | `test_users.py`, `test_navigation.py` | LIVE |
| `/masters/company/role` | Role Master | `GET/POST/PUT/DELETE /api/v1/masters?type=ROLE` | `test_masters.py` | LIVE |
| `/masters/company/territory` | Territory Master | `GET/POST/PUT /api/v1/territories` | `test_territories.py` | LIVE |
| `/masters/company/territory-hierarchy` | Territory Hierarchy | `GET /api/v1/territories/tree` | `test_territories.py` | LIVE |
| `/masters/customers/category` | Category Master | `GET/POST/PUT/DELETE /api/v1/masters?type=CUSTOMER_CATEGORY` | `test_masters.py` | LIVE |
| `/masters/customers/chemist` | Chemist Master | `GET/POST/PUT/DELETE /api/v1/customers/chemists` | `test_customers.py` | LIVE |
| `/masters/customers/doctor` | Doctor Master | `GET/POST/PUT/DELETE /api/v1/customers/doctors` | `test_customers.py` | LIVE |
| `/masters/customers/doctor-meeting-type` | Doctor Meeting Type Master | `GET/POST/PUT/DELETE /api/v1/masters?type=DOCTOR_MEETING_TYPE` | `test_masters.py` | LIVE |
| `/masters/customers/qualification` | Qualification Master | `GET/POST/PUT/DELETE /api/v1/masters?type=QUALIFICATION` | `test_masters.py` | LIVE |
| `/masters/customers/speciality` | Speciality Master | `GET/POST/PUT/DELETE /api/v1/masters?type=SPECIALIZATION` | `test_masters.py` | LIVE |
| `/masters/customers/stockist` | Stockist Master | `GET/POST/PUT/DELETE /api/v1/customers/stockists` | `test_customers.py` | LIVE |
| `/masters/customers/visit-type` | Visit Type Master | `GET/POST/PUT/DELETE /api/v1/masters?type=VISIT_TYPE` | `test_masters.py` | LIVE |
| `/masters/customers/attachment` | Attachment Master | `GET/POST/PUT/DELETE /api/v1/masters?type=ATTACHMENT_TYPE` + `confirm` | `test_w6_features.py` | PROVISIONAL |
| `/masters/customers/doctor-type` | Doctor Type Master | `GET/POST/PUT/DELETE /api/v1/masters?type=DOCTOR_TYPE` + `confirm` | `test_w6_features.py` | PROVISIONAL |
| `/masters/customers/supplier` | Supplier Master | `GET/POST/PUT/DELETE /api/v1/masters?type=SUPPLIER` + `confirm` | `test_w6_features.py` | PROVISIONAL |
| `/masters/hospital` | Hospital Master | `GET/POST/PUT/DELETE /api/v1/customers/hospitals` | `test_customers.py` | LIVE |
| `/masters/hospital-category` | Hospital Category Master | `GET/POST/PUT/DELETE /api/v1/masters?type=HOSPITAL_CATEGORY` + `confirm` | `test_w6_features.py` | PROVISIONAL |
| `/masters/products/product` | Product Master | `GET/POST/PUT/DELETE /api/v1/products` | `test_reports_products_orders.py` | LIVE |
| `/masters/products/category` | Product Category Master | `GET/POST/PUT/DELETE /api/v1/masters?type=PRODUCT_CATEGORY` | `test_masters.py` | LIVE |
| `/masters/products/unit` | Unit Master | `GET/POST/PUT/DELETE /api/v1/masters?type=UNIT` | `test_masters.py` | LIVE |
| `/masters/products/issue-type` | Issue Type Master | `GET/POST/PUT/DELETE /api/v1/masters?type=ISSUE_TYPE` | `test_masters.py` | LIVE |
| `/masters/products/gift` | Gift Master | `GET/POST/PUT/DELETE /api/v1/masters?type=GIFT` | `test_masters.py` | LIVE |
| `/masters/products/group` | Product Group Master | `GET/POST/PUT/DELETE /api/v1/masters?type=PRODUCT_GROUP` | `test_masters.py` | LIVE |
| `/masters/products/type` | Product Type Master | `GET/POST/PUT/DELETE /api/v1/masters?type=PRODUCT_TYPE` | `test_masters.py` | LIVE |
| `/masters/products/mfg-mkt-by` | Mfg / Mkt By Master | `GET/POST/PUT/DELETE /api/v1/masters?type=MFG_MKT_BY` | `test_masters.py` | LIVE |
| `/masters/products/gallery` | Product Gallery Master | `GET/POST/PUT/DELETE /api/v1/masters?type=PRODUCT_GALLERY` + `confirm` | `test_w6_features.py` | PROVISIONAL |
| `/masters/holiday` | Holiday Master | `GET/POST/PUT/DELETE /api/v1/masters?type=HOLIDAY` | `test_masters.py` | LIVE |

---

## 2. Parameters (4 Items)
| Route | Label | Backing API Endpoint(s) | Covering Tests | Status |
|---|---|---|---|---|
| `/parameters/state` | State Master | `GET/POST/PUT/DELETE /api/v1/masters/states` | `test_masters.py` | LIVE |
| `/parameters/district` | District Master | `GET/POST/PUT/DELETE /api/v1/masters/districts` | `test_masters.py` | LIVE |
| `/parameters/city` | City Master | `GET/POST/PUT/DELETE /api/v1/masters/cities` | `test_masters.py` | LIVE |
| `/parameters/area` | Area Master | `GET/POST/PUT/DELETE /api/v1/masters/areas` | `test_masters.py` | LIVE |

---

## 3. Reports & Detail Reports (20 Items)
- Backed by `/api/v1/reports` and `/api/v1/reports/{key}/export`
- Covered in `test_reports_catalog_v3.py` and `test_w6_regressions.py` (ALL LIVE).

---

## 4. Activities & Operations (17 Items)
| Route | Label | Backing API Endpoint(s) | Covering Tests | Status |
|---|---|---|---|---|
| `/activities/live-tracking` | Live Tracking | `GET /api/v1/dcr/locations/live` | `test_dcr.py` | LIVE |
| `/activities/attendance` | Attendance Management | `GET /api/v1/attendance/history`, `POST /punch-in` | `test_dcr.py` | LIVE |
| `/activities/doctor-call-visits` | Doctor Call Visits | `GET /api/v1/dcr/visits?customer_type=DOCTOR` | `test_dcr.py` | LIVE |
| `/activities/chemist-call-visits` | Chemist Call Visits | `GET /api/v1/dcr/visits?customer_type=CHEMIST` | `test_dcr.py` | LIVE |
| `/activities/stockist-call-visits` | Stockist Call Visits | `GET /api/v1/dcr/visits?customer_type=STOCKIST` | `test_dcr.py` | LIVE |
| `/activities/dcr` | Daily Call Report | `GET /api/v1/dcr/visits`, `POST /submit` | `test_dcr.py` | LIVE |
| `/activities/orders` | Orders Management | `GET/POST /api/v1/orders` | `test_reports_products_orders.py` | LIVE |
| `/activities/order-booking` | Order Booking | `GET/POST /api/v1/orders` | `test_reports_products_orders.py` | LIVE |
| `/activities/chemist-wise-sales` | Chemist Wise Sales | `GET /api/v1/orders` | `test_reports_products_orders.py` | LIVE |
| `/activities/target-entry` | Target Entry | `GET/POST/PUT /api/v1/targets` | `test_targets.py` | LIVE |

---

## 5. Utility & Admin Panel (35 Items)
| Route | Label | Backing API Endpoint(s) | Covering Tests | Status |
|---|---|---|---|---|
| `/utility/admin-panel/application-setting` | Application Setting | `GET/PUT /api/v1/company-profile`, `GET /auth/config` | `test_w6_features.py` | LIVE |
| `/utility/admin-panel/general-settings` | General Settings | `GET/PUT /api/v1/settings` | `test_w5_config_audit_mapping.py` | LIVE |
| `/utility/reimbursement/expense-limits` | Expense Limits | `GET/PUT /api/v1/expense-limits` | `test_w5_config_audit_mapping.py` | LIVE |
| `/utility/reimbursement/reimbursement-processing` | Reimbursement Processing | `POST /api/v1/expenses/{id}/payout`, `/payout-modes` | `test_expenses_payout.py` | LIVE |
| `/utility/my-calendar` | My Calendar | `GET /api/v1/calendar/month` | `test_w6_features.py` | LIVE |
| `/utility/meeting` | Meeting | `GET/POST/PUT /api/v1/meetings`, `/summary` | `test_w6_features.py` | LIVE |
| `/utility/leaves/manage-leaves` | Manage Leaves | `GET/POST /api/v1/leaves`, `/approvals` | `test_approvals_tour_expense_leave.py` | LIVE |
| `/utility/manage-routes/tour-plan` | Tour Plan | `GET/POST /api/v1/tours` | `test_approvals_tour_expense_leave.py` | LIVE |
| `/utility/monthly-expense-approval` | Monthly Expense Approval | `GET /api/v1/approvals/inbox` | `test_approvals_tour_expense_leave.py` | LIVE |
| `/utility/admin-panel/audit-trail` | Audit Trail | `GET /api/v1/audit/logs` | `test_w5_config_audit_mapping.py` | LIVE |
| `/utility/admin-panel/employee-mapping` | Employee Mapping | `GET/POST /api/v1/mappings` | `test_w5_config_audit_mapping.py` | LIVE |
| `/utility/admin-panel/send-notification` | Send Notification | `POST /api/v1/notifications` | `test_tasks_and_notifications.py` | LIVE |
| `/utility/admin-panel/approve-mobile-registration` | Approve Mobile Registration | Scheduled for Wave W7 | `W7 BUILD` | PENDING W7 |
| `/utility/admin-panel/delete-my-visits` | Delete My Visits | Scheduled for Wave W7 | `W7 BUILD` | PENDING W7 |
| `/utility/manage-routes/tour-plan-lock` | Tour Plan Lock | Scheduled for Wave W7 | `W7 BUILD` | PENDING W7 |
| `/utility/manage-routes/std-route-chart` | Std Route Chart | Documentation spec | `WAITING_UI` | WAITING_UI |
| Sample Inward / Allocation / Issue | Sample Stock Management | Scheduled for Wave W8 | `W8 BUILD` | PENDING W8 |
| Credit Notes / Delivery Outward / Monthly Business / Secondary Sales | Legacy Sales & ERP | Client data source decisions | `DEFERRED` | DEFERRED |
| File Mapping / Product Mappings / Bulk Update | Sales Importers | Mappings specification | `DEFERRED` | DEFERRED |
