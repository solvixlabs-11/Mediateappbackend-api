"""Report definitions loader and registry initializer for all 26 reports."""

from app.modules.reports.definitions.group_a_masters import (
    ChemistListReport,
    DoctorListReport,
    MrWiseRouteMasterReport,
)
from app.modules.reports.definitions.group_b_attendance import (
    DailyWorkReport,
    MrDailyPunchingReport,
    MrWiseAttendanceReport,
)
from app.modules.reports.definitions.group_c_visits import (
    MrDesignationWiseVisitsAnalysisReport,
    MrDeviationReport,
    MrWiseDoctorChemistCallReport,
    MrWisePromotionalCallReport,
    MrWiseVisitsAnalysisReport,
    MrWiseVisitsReport,
)
from app.modules.reports.definitions.group_d_doctor_analysis import (
    MrDoctorWiseMonthlySummaryReport,
    MrWiseDocSpWiseStatsReport,
    MrWiseDoctorCategoryWiseReport,
    MrWiseDoctorTypeWiseReport,
    MrWiseNotSeenDoctorReport,
)
from app.modules.reports.definitions.group_e_stock_orders import (
    MrWiseSampleBalanceReport,
    OrderRegisterReport,
)
from app.modules.reports.definitions.group_f_sales_finance import (
    CollectionReport,
    CreditNoteReport,
    MrWiseChemistWiseSalesReport,
    MrWiseMonthlyBusinessReport,
    MrWiseStockistWiseSalesReport,
    OutstandingReport,
)
from app.modules.reports.definitions.group_g_unknown import InductionReport

__all__ = [
    # Group A: Master lists (1 to 3)
    "DoctorListReport",
    "ChemistListReport",
    "MrWiseRouteMasterReport",
    # Group B: Attendance and daily work (4 to 6)
    "MrDailyPunchingReport",
    "MrWiseAttendanceReport",
    "DailyWorkReport",
    # Group C: Visits (7 to 12)
    "MrWiseVisitsReport",
    "MrWiseVisitsAnalysisReport",
    "MrDesignationWiseVisitsAnalysisReport",
    "MrWiseDoctorChemistCallReport",
    "MrWisePromotionalCallReport",
    "MrDeviationReport",
    # Group D: Doctor analysis (13 to 17)
    "MrDoctorWiseMonthlySummaryReport",
    "MrWiseNotSeenDoctorReport",
    "MrWiseDocSpWiseStatsReport",
    "MrWiseDoctorCategoryWiseReport",
    "MrWiseDoctorTypeWiseReport",
    # Group E: Stock and orders (18 to 19)
    "MrWiseSampleBalanceReport",
    "OrderRegisterReport",
    # Group F: Sales and finance (20 to 25)
    "MrWiseChemistWiseSalesReport",
    "MrWiseStockistWiseSalesReport",
    "MrWiseMonthlyBusinessReport",
    "CollectionReport",
    "CreditNoteReport",
    "OutstandingReport",
    # Group G: Other / Unknown (26)
    "InductionReport",
]
