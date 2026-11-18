"""Script to generate seed/data/report_definitions.json containing all 48 catalog reports."""

import json
from pathlib import Path

REPORTS = [
    # -------------------------------------------------------------
    # 1. FIELD ACTIVITY (15 reports: 13 NOW, 1 DECISION, 1 ASK)
    # -------------------------------------------------------------
    {
        "key": "daily_call_report",
        "name": "Daily Call Report (MR Wise Call Summary) / Daily Work Report",
        "group": "Field Activity",
        "description": "Per employee per day: doctor, chemist, stockist calls, new customers, first and last call time, hours.",
        "sort_order": 1,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "month", "label": "Month", "type": "month", "required": True},
                {"name": "year", "label": "Year", "type": "year", "required": True},
                {"name": "status", "label": "Status", "type": "select", "options": ["ALL", "SUBMITTED", "APPROVED", "REJECTED"], "default": "ALL"},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"},
                {"name": "divisions", "label": "Divisions", "type": "multi_select", "source": "divisions", "helper_text": "By default all are considered as selected"},
                {"name": "designations", "label": "Designations", "type": "multi_select", "source": "designations", "helper_text": "By default all are considered as selected"},
                {"name": "states", "label": "States", "type": "multi_select", "source": "states", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "mr_wise_visit_detail",
        "name": "MR Wise Visit Detail / MR Wise Visits",
        "group": "Field Activity",
        "description": "Every visit with its details, grouped by employee and date.",
        "sort_order": 2,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "month", "label": "Month", "type": "month", "required": True},
                {"name": "financial_year", "label": "Financial Year", "type": "financial_year", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "at_least_one": True, "required": True}
            ]
        }
    },
    {
        "key": "mr_daily_punching",
        "name": "MR_DailyPunching",
        "group": "Field Activity",
        "description": "Punch in and punch out time and place per day.",
        "sort_order": 3,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "mr_attendance",
        "name": "MR_Wise_Attendence_Report",
        "group": "Field Activity",
        "description": "Month matrix P, A, L, W with totals.",
        "sort_order": 4,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "month", "label": "Month", "type": "month", "required": True},
                {"name": "year", "label": "Year", "type": "year", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "mr_visits_analysis",
        "name": "MR_Wise_Visits_Analysis",
        "group": "Field Activity",
        "description": "Visits split by customer type, averages, verified %.",
        "sort_order": 5,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "designation_visits_analysis",
        "name": "MR_Designation_Wise_Visits_Analysis",
        "group": "Field Activity",
        "description": "Visits grouped by designation.",
        "sort_order": 6,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "designations", "label": "Designations", "type": "multi_select", "source": "designations", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "doctor_chemist_call",
        "name": "MR_Wise_Doctor_Chemist_Call",
        "group": "Field Activity",
        "description": "Doctor, chemist and stockist calls per employee.",
        "sort_order": 7,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "promotional_call",
        "name": "MR Wise PromotionalCall",
        "group": "Field Activity",
        "description": "Calls of the promotional call type.",
        "sort_order": 8,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"},
                {"name": "visit_type", "label": "Visit Type", "type": "select", "options": ["ALL", "REGULAR SAMPLE CALL", "GROUP PROMOTIONAL CALL", "REMINDER"], "default": "ALL"}
            ]
        }
    },
    {
        "key": "deviation_report",
        "name": "MR_Deviation_Report",
        "group": "Field Activity",
        "description": "Planned versus actual (outside tour plan, unplanned, missed).",
        "sort_order": 9,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "pending_dcr",
        "name": "Pending DCR Details",
        "group": "Field Activity",
        "description": "Days with check-in but missing or late visit reports.",
        "sort_order": 10,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "mr_wise_details",
        "name": "MR_Wise_Details",
        "group": "Field Activity",
        "description": "Unclear (employee wise details).",
        "sort_order": 11,
        "status": "COMING_SOON",
        "unavailable_reason": "Awaiting definition and sample output screenshot from stakeholder",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employee", "label": "Employee", "type": "select", "source": "employees", "required": True}
            ]
        }
    },
    {
        "key": "management_summary",
        "name": "Management_Summary_Report",
        "group": "Field Activity",
        "description": "Summary numbers per territory or employee for a period.",
        "sort_order": 12,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "territories", "label": "Territories", "type": "multi_select", "source": "territories", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "not_login_web",
        "name": "MR_Wise_Not_Login_WEB",
        "group": "Field Activity",
        "description": "Active employees who did not log in on the web in the period.",
        "sort_order": 13,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True}
            ]
        }
    },
    {
        "key": "track_report",
        "name": "Track Report View",
        "group": "Field Activity",
        "description": "Movement points of one employee between start and end time.",
        "sort_order": 14,
        "status": "COMING_SOON",
        "unavailable_reason": "Awaiting live tracking architecture decision D3 (GPS breadcrumbs)",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date", "label": "Date", "type": "date", "required": True},
                {"name": "start_time", "label": "Start Time", "type": "time", "required": True},
                {"name": "end_time", "label": "End Time", "type": "time", "required": True},
                {"name": "employee", "label": "Employee", "type": "select", "source": "employees", "required": True}
            ]
        }
    },
    {
        "key": "km_report",
        "name": "K.M. Report",
        "group": "Field Activity",
        "description": "Kilometres travelled per day using haversine distance between consecutive visit locations.",
        "sort_order": 15,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employee", "label": "Employee", "type": "select", "source": "employees", "required": True}
            ]
        }
    },

    # -------------------------------------------------------------
    # 2. DOCTOR AND CUSTOMER ANALYSIS (13 reports: 13 NOW)
    # -------------------------------------------------------------
    {
        "key": "doctor_monthly_summary",
        "name": "MR_Doctor_Wise_Monthly_Summary",
        "group": "Doctor & Customer",
        "description": "Doctor x day visit counts for a month.",
        "sort_order": 16,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "month", "label": "Month", "type": "month", "required": True},
                {"name": "year", "label": "Year", "type": "year", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "doctor_yearly_summary",
        "name": "MR_DoctorWise_Yearly_Summary",
        "group": "Doctor & Customer",
        "description": "Doctor x month visit counts for a financial year.",
        "sort_order": 17,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "financial_year", "label": "Financial Year", "type": "financial_year", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "not_seen_doctor",
        "name": "MR_Wise_Not_Seen_Doctor",
        "group": "Doctor & Customer",
        "description": "Doctors not visited in the selected period.",
        "sort_order": 18,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "docsp_stats",
        "name": "MR Wise DocSp Wise Stats",
        "group": "Doctor & Customer",
        "description": "Specialization wise doctors, visits, coverage.",
        "sort_order": 19,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"},
                {"name": "specialities", "label": "Specialities", "type": "multi_select", "source": "specialities", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "doctor_category_wise",
        "name": "MR Wise Doctor Category Wise Report",
        "group": "Doctor & Customer",
        "description": "Category wise assigned, visited, coverage.",
        "sort_order": 20,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "doctor_type_wise",
        "name": "Doctor Type Wise Report / MR Wise Doctor Type Wise",
        "group": "Doctor & Customer",
        "description": "Visits and coverage by doctor meeting type.",
        "sort_order": 21,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "doctor_list",
        "name": "Doctor List",
        "group": "Doctor & Customer",
        "description": "Doctor master listing with contact details, specialities, and territories.",
        "sort_order": 22,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "states", "label": "States", "type": "multi_select", "source": "states"},
                {"name": "cities", "label": "Cities", "type": "multi_select", "source": "cities", "parent_field": "states"},
                {"name": "territories", "label": "Territories", "type": "multi_select", "source": "territories"},
                {"name": "specialities", "label": "Specialities", "type": "multi_select", "source": "specialities"},
                {"name": "status", "label": "Status", "type": "select", "options": ["ALL", "ACTIVE", "INACTIVE"], "default": "ALL"}
            ]
        }
    },
    {
        "key": "chemist_list",
        "name": "Chemist List",
        "group": "Doctor & Customer",
        "description": "Chemist master listing with drug license, phone, and territory info.",
        "sort_order": 23,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "states", "label": "States", "type": "multi_select", "source": "states"},
                {"name": "cities", "label": "Cities", "type": "multi_select", "source": "cities", "parent_field": "states"},
                {"name": "territories", "label": "Territories", "type": "multi_select", "source": "territories"},
                {"name": "status", "label": "Status", "type": "select", "options": ["ALL", "ACTIVE", "INACTIVE"], "default": "ALL"}
            ]
        }
    },
    {
        "key": "territory_hierarchy_report",
        "name": "Territory Hierarchy Report",
        "group": "Doctor & Customer",
        "description": "Territory tree with employees and designations.",
        "sort_order": 24,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "filter", "label": "Filter", "type": "select", "options": ["ALL", "ACTIVE", "INACTIVE"], "default": "ACTIVE"},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees"},
                {"name": "states", "label": "States", "type": "multi_select", "source": "states"},
                {"name": "designations", "label": "Designations", "type": "multi_select", "source": "designations"}
            ]
        }
    },
    {
        "key": "route_master",
        "name": "MR Wise Route Master",
        "group": "Doctor & Customer",
        "description": "Territory or route assignment per employee.",
        "sort_order": 25,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "unassigned_customers_division",
        "name": "Unassigned_Customers_Division_Wise_Report",
        "group": "Doctor & Customer",
        "description": "Customers with no employee assigned, by division.",
        "sort_order": 26,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "divisions", "label": "Divisions", "type": "multi_select", "source": "divisions"},
                {"name": "states", "label": "States", "type": "multi_select", "source": "states"}
            ]
        }
    },
    {
        "key": "unassigned_mr_customer",
        "name": "Unassigned_MR_Customer_Wise_Report",
        "group": "Doctor & Customer",
        "description": "Employees with no customers assigned.",
        "sort_order": 27,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "unassigned_mr_division",
        "name": "Unassigned_MR_Division_Wise_Report",
        "group": "Doctor & Customer",
        "description": "Employees not mapped to a division.",
        "sort_order": 28,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },

    # -------------------------------------------------------------
    # 3. PLANS, LEAVE AND EXPENSE (5 reports: 5 NOW)
    # -------------------------------------------------------------
    {
        "key": "tour_plan_report",
        "name": "Tour Plan Report",
        "group": "Plans & HR",
        "description": "Tour plans per employee with routes, dates, and approval status.",
        "sort_order": 29,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "tour_plan_status",
        "name": "Tour Plan Status Report",
        "group": "Plans & HR",
        "description": "Submitted, approved, pending tour plans per employee for a month.",
        "sort_order": 30,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "month", "label": "Month", "type": "month", "required": True},
                {"name": "financial_year", "label": "Financial Year", "type": "financial_year", "required": True},
                {"name": "states", "label": "States", "type": "multi_select", "source": "states"},
                {"name": "designations", "label": "Designations", "type": "multi_select", "source": "designations"},
                {"name": "filter", "label": "Filter", "type": "select", "options": ["ALL", "ACTIVE", "INACTIVE"], "default": "ACTIVE"}
            ]
        }
    },
    {
        "key": "leave_report",
        "name": "MR_Wise_Leave_Report",
        "group": "Plans & HR",
        "description": "Leaves per employee with balances and approval trail.",
        "sort_order": 31,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "expense_report",
        "name": "MR_Wise_Monthly_Expense_Report",
        "group": "Plans & HR",
        "description": "Expense per employee for a month.",
        "sort_order": 32,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "month", "label": "Month", "type": "month", "required": True},
                {"name": "year", "label": "Year", "type": "year", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    },
    {
        "key": "expense_statement",
        "name": "Monthly Expense Reimbursement Statement",
        "group": "Plans & HR",
        "description": "Printable monthly statement for one employee (PDF with signature block).",
        "sort_order": 33,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "month", "label": "Month", "type": "month", "required": True},
                {"name": "year", "label": "Year", "type": "year", "required": True},
                {"name": "employee", "label": "Employee", "type": "select", "source": "employees", "required": True}
            ]
        }
    },

    # -------------------------------------------------------------
    # 4. STOCK, ORDERS, SALES AND FINANCE (11 reports: 3 P8, 8 SALES)
    # -------------------------------------------------------------
    {
        "key": "order_register",
        "name": "Order_Register / Order Register",
        "group": "Stock & Orders",
        "description": "Orders (chemist and doctor) with estimated delivery date.",
        "sort_order": 34,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for Phase 8 Order Management & SKU distribution",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees"}
            ]
        }
    },
    {
        "key": "sample_balance",
        "name": "Sample Balance Report / MR Wise Sample Balance",
        "group": "Stock & Orders",
        "description": "Sample stock balance per employee.",
        "sort_order": 35,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for Phase 8 Sample Stock Ledger",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees"},
                {"name": "divisions", "label": "Divisions", "type": "multi_select", "source": "divisions"},
                {"name": "products", "label": "Products", "type": "multi_select", "source": "products"}
            ]
        }
    },
    {
        "key": "product_comparison",
        "name": "Product Comparison Report",
        "group": "Stock & Orders",
        "description": "Product wise comparison across divisions and territories.",
        "sort_order": 36,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for Phase 8 Multi-SKU sales analytics",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees"},
                {"name": "divisions", "label": "Divisions", "type": "multi_select", "source": "divisions"},
                {"name": "products", "label": "Products", "type": "multi_select", "source": "products"}
            ]
        }
    },
    {
        "key": "chemist_wise_sales",
        "name": "Chemist Wise Sales Report / MR Wise Chemist Wise Sales",
        "group": "Sales & Finance",
        "description": "Secondary sales by chemist.",
        "sort_order": 37,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for ERP Secondary Sales integration (Decision D4)",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "month", "label": "Month", "type": "month", "required": True},
                {"name": "financial_year", "label": "Financial Year", "type": "financial_year", "required": True},
                {"name": "chemists", "label": "Chemists", "type": "multi_select", "source": "chemists"},
                {"name": "stockists", "label": "Stockists", "type": "multi_select", "source": "stockists"}
            ]
        }
    },
    {
        "key": "stockist_wise_sales",
        "name": "Stockist Wise Sales Report / MR Wise Stockist Wise Sales",
        "group": "Sales & Finance",
        "description": "Sales by stockist.",
        "sort_order": 38,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for ERP Stockist Invoicing data (Decision D4)",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "month", "label": "Month", "type": "month", "required": True},
                {"name": "financial_year", "label": "Financial Year", "type": "financial_year", "required": True},
                {"name": "stockists", "label": "Stockists", "type": "multi_select", "source": "stockists"},
                {"name": "chemists", "label": "Chemists", "type": "multi_select", "source": "chemists"}
            ]
        }
    },
    {
        "key": "primary_sales",
        "name": "Primary Sales Report",
        "group": "Sales & Finance",
        "description": "Primary sales per stockist, detail or summary.",
        "sort_order": 39,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for ERP Primary Sales data (Decision D4)",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "report_type", "label": "Report Type", "type": "select", "options": ["DETAIL", "SUMMARY"], "default": "SUMMARY", "required": True},
                {"name": "stockists", "label": "Stockists", "type": "multi_select", "source": "stockists"}
            ]
        }
    },
    {
        "key": "monthly_business",
        "name": "Monthly Business Report / MR Wise Monthly Business",
        "group": "Sales & Finance",
        "description": "Monthly business per employee.",
        "sort_order": 40,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for ERP Monthly Business data (Decision D4)",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "at_least_one": True, "required": True},
                {"name": "specialities", "label": "Specialities", "type": "multi_select", "source": "specialities"},
                {"name": "states", "label": "States", "type": "multi_select", "source": "states"}
            ]
        }
    },
    {
        "key": "target_vs_achievement",
        "name": "Target VS Primary and Secondary Achievement",
        "group": "Sales & Finance",
        "description": "Target against primary and secondary sales (value, quantity).",
        "sort_order": 41,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for ERP Target vs Sales integration (Decision D4)",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "territory", "label": "Territory", "type": "select", "source": "territories", "required": True},
                {"name": "financial_year", "label": "Financial Year", "type": "financial_year", "required": True},
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "value", "label": "Value", "type": "toggle", "default": True},
                {"name": "qty", "label": "Quantity", "type": "toggle", "default": False},
                {"name": "primary", "label": "Primary", "type": "toggle", "default": True},
                {"name": "secondary", "label": "Secondary", "type": "toggle", "default": True}
            ]
        }
    },
    {
        "key": "collection_report",
        "name": "Collection Report",
        "group": "Sales & Finance",
        "description": "Payments collected against outstanding bills.",
        "sort_order": 42,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for ERP Collection & Bank reconciliation data (Decision D4)",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "stockists", "label": "Stockists", "type": "multi_select", "source": "stockists"}
            ]
        }
    },
    {
        "key": "credit_note_report",
        "name": "Credit Note Report",
        "group": "Sales & Finance",
        "description": "Credit notes issued for expiry, breakage, and returns.",
        "sort_order": 43,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for ERP Credit Note ledger data (Decision D4)",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "stockists", "label": "Stockists", "type": "multi_select", "source": "stockists"}
            ]
        }
    },
    {
        "key": "outstanding_report",
        "name": "Out Standing Report / OutStanding Report",
        "group": "Sales & Finance",
        "description": "Outstanding receivables with ageing analysis.",
        "sort_order": 44,
        "status": "COMING_SOON",
        "unavailable_reason": "Wait for ERP Outstanding sync (Decision D4)",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": "ERP Financial Sync",
        "filter_schema": {
            "fields": [
                {"name": "date", "label": "Date", "type": "date", "required": True},
                {"name": "outstanding_type", "label": "Outstanding Type", "type": "select", "options": ["ALL", "DUE", "OVERDUE"], "default": "ALL", "required": True},
                {"name": "stockists", "label": "Stockists", "type": "multi_select", "source": "stockists"},
                {"name": "divisions", "label": "Divisions", "type": "multi_select", "source": "divisions"}
            ]
        }
    },

    # -------------------------------------------------------------
    # 5. UNCLEAR OR COMPANY SPECIFIC (4 reports: 1 NOW, 3 ASK)
    # -------------------------------------------------------------
    {
        "key": "pp_and_ivset",
        "name": "PP and Ivset Report",
        "group": "Specialty & Corporate",
        "description": "Product-specific infusion & medical sets report.",
        "sort_order": 45,
        "status": "COMING_SOON",
        "unavailable_reason": "Product-specific formulation, awaiting specification from stakeholder",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True}
            ]
        }
    },
    {
        "key": "steriport_and_ffs",
        "name": "Steriport And FFS Report",
        "group": "Specialty & Corporate",
        "description": "Product-specific surgical port and form-fill-seal packaging tracking.",
        "sort_order": 46,
        "status": "COMING_SOON",
        "unavailable_reason": "Product-specific formulation, awaiting specification from stakeholder",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True}
            ]
        }
    },
    {
        "key": "induction_report",
        "name": "Induction Report",
        "group": "Specialty & Corporate",
        "description": "Employee onboarding, territory orientation and field induction.",
        "sort_order": 47,
        "status": "COMING_SOON",
        "unavailable_reason": "Training/HR module, awaiting specification from stakeholder",
        "formats": [],
        "allowed_roles": ["ADMIN", "MANAGER"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True}
            ]
        }
    },
    {
        "key": "visit_analysis",
        "name": "Visit Analysis (employee tracker)",
        "group": "Specialty & Corporate",
        "description": "Per employee visit analysis and field engagement tracker.",
        "sort_order": 48,
        "status": "AVAILABLE",
        "unavailable_reason": None,
        "formats": ["screen", "xlsx", "pdf"],
        "allowed_roles": ["ADMIN", "MANAGER", "MR"],
        "data_as_of_source": None,
        "filter_schema": {
            "fields": [
                {"name": "date_range", "label": "From-To Date", "type": "date_range", "required": True},
                {"name": "filter", "label": "Filter", "type": "select", "options": ["ALL", "ACTIVE", "INACTIVE"], "default": "ACTIVE"},
                {"name": "employees", "label": "Employees", "type": "multi_select", "source": "employees", "helper_text": "By default all are considered as selected"}
            ]
        }
    }
]

if __name__ == "__main__":
    out_path = Path("E:/Mediate/Mediateappbackend-api/seed/data/report_definitions.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(REPORTS, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(REPORTS)} report definitions at {out_path}")
