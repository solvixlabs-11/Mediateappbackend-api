"""Report definitions loader and registry initializer."""

from app.modules.reports.definitions.r01_dcr_detailed import DcrDetailedReport
from app.modules.reports.definitions.r02_daily_activity import DailyActivityReport
from app.modules.reports.definitions.r03_customer_visits import CustomerVisitsReport
from app.modules.reports.definitions.r04_coverage import CustomerCoverageReport
from app.modules.reports.definitions.r05_mr_performance import MrPerformanceReport
from app.modules.reports.definitions.r06_pending_late_dcr import PendingLateDcrReport
from app.modules.reports.definitions.r07_geo_verification import GeoVerificationReport
from app.modules.reports.definitions.r08_planned_vs_actual import PlannedVsActualReport
from app.modules.reports.definitions.r09_attendance import AttendanceReport
from app.modules.reports.definitions.r10_leave import LeaveReport
from app.modules.reports.definitions.r11_expense import ExpenseReport
from app.modules.reports.definitions.r12_tour_plan import TourPlanReport
from app.modules.reports.definitions.r13_followup import FollowUpReport
from app.modules.reports.definitions.r14_approval_turnaround import ApprovalTurnaroundReport

__all__ = [
    "DcrDetailedReport",
    "DailyActivityReport",
    "CustomerVisitsReport",
    "CustomerCoverageReport",
    "MrPerformanceReport",
    "PendingLateDcrReport",
    "GeoVerificationReport",
    "PlannedVsActualReport",
    "AttendanceReport",
    "LeaveReport",
    "ExpenseReport",
    "TourPlanReport",
    "FollowUpReport",
    "ApprovalTurnaroundReport",
]
