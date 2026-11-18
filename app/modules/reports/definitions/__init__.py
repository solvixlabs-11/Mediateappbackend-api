"""Report definitions loader importing all 32 NOW report definitions."""

from app.modules.reports.definitions.chemist_list import ChemistListReport
from app.modules.reports.definitions.daily_call_report import DailyCallReport
from app.modules.reports.definitions.designation_visits_analysis import (
    MrDesignationWiseVisitsAnalysisReport,
)
from app.modules.reports.definitions.deviation_report import MrDeviationReport
from app.modules.reports.definitions.docsp_stats import MrWiseDocSpWiseStatsReport
from app.modules.reports.definitions.doctor_category_wise import MrWiseDoctorCategoryWiseReport
from app.modules.reports.definitions.doctor_chemist_call import MrWiseDoctorChemistCallReport
from app.modules.reports.definitions.doctor_list import DoctorListReport
from app.modules.reports.definitions.doctor_monthly_summary import MrDoctorWiseMonthlySummaryReport
from app.modules.reports.definitions.doctor_type_wise import DoctorTypeWiseReport
from app.modules.reports.definitions.doctor_yearly_summary import MrDoctorWiseYearlySummaryReport
from app.modules.reports.definitions.expense_report import ExpenseReport
from app.modules.reports.definitions.expense_statement import ExpenseStatementReport
from app.modules.reports.definitions.km_report import KmReport
from app.modules.reports.definitions.leave_report import LeaveReport
from app.modules.reports.definitions.management_summary import ManagementSummaryReport
from app.modules.reports.definitions.mr_attendance import MrWiseAttendanceReport
from app.modules.reports.definitions.mr_daily_punching import MrDailyPunchingReport
from app.modules.reports.definitions.mr_visits_analysis import MrWiseVisitsAnalysisReport
from app.modules.reports.definitions.mr_wise_visit_detail import MrWiseVisitDetailReport
from app.modules.reports.definitions.not_login_web import MrWiseNotLoginWebReport
from app.modules.reports.definitions.not_seen_doctor import MrWiseNotSeenDoctorReport
from app.modules.reports.definitions.pending_dcr import PendingDcrReport
from app.modules.reports.definitions.promotional_call import MrWisePromotionalCallReport
from app.modules.reports.definitions.route_master import RouteMasterReport
from app.modules.reports.definitions.territory_hierarchy_report import TerritoryHierarchyReport
from app.modules.reports.definitions.tour_plan_report import TourPlanReport
from app.modules.reports.definitions.tour_plan_status import TourPlanStatusReport
from app.modules.reports.definitions.unassigned_customers_division import (
    UnassignedCustomersDivisionReport,
)
from app.modules.reports.definitions.unassigned_mr_customer import UnassignedMrCustomerReport
from app.modules.reports.definitions.unassigned_mr_division import UnassignedMrDivisionReport
from app.modules.reports.definitions.visit_analysis import VisitAnalysisReport

__all__ = [
    "DailyCallReport",
    "MrWiseVisitDetailReport",
    "MrDailyPunchingReport",
    "MrWiseAttendanceReport",
    "MrWiseVisitsAnalysisReport",
    "MrDesignationWiseVisitsAnalysisReport",
    "MrWiseDoctorChemistCallReport",
    "MrWisePromotionalCallReport",
    "MrDeviationReport",
    "PendingDcrReport",
    "ManagementSummaryReport",
    "MrWiseNotLoginWebReport",
    "KmReport",
    "MrDoctorWiseMonthlySummaryReport",
    "MrDoctorWiseYearlySummaryReport",
    "MrWiseNotSeenDoctorReport",
    "MrWiseDocSpWiseStatsReport",
    "MrWiseDoctorCategoryWiseReport",
    "DoctorTypeWiseReport",
    "DoctorListReport",
    "ChemistListReport",
    "TerritoryHierarchyReport",
    "RouteMasterReport",
    "UnassignedCustomersDivisionReport",
    "UnassignedMrCustomerReport",
    "UnassignedMrDivisionReport",
    "TourPlanReport",
    "TourPlanStatusReport",
    "LeaveReport",
    "ExpenseReport",
    "ExpenseStatementReport",
    "VisitAnalysisReport",
]
