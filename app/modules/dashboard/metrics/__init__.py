"""Visits Summary metric handlers initialization and canonical registry."""

from __future__ import annotations

from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.metrics.chemist_visits import ChemistVisitsMetric
from app.modules.dashboard.metrics.doctor_call_average import DoctorCallAverageMetric
from app.modules.dashboard.metrics.doctor_visits import DoctorVisitsMetric
from app.modules.dashboard.metrics.evening_calls import EveningCallsMetric
from app.modules.dashboard.metrics.first_call_time import FirstCallTimeMetric
from app.modules.dashboard.metrics.last_call_time import LastCallTimeMetric
from app.modules.dashboard.metrics.missing_doctor import MissingDoctorMetric
from app.modules.dashboard.metrics.morning_calls import MorningCallsMetric
from app.modules.dashboard.metrics.new_chemist_visits import NewChemistVisitsMetric
from app.modules.dashboard.metrics.new_doctor_visits import NewDoctorVisitsMetric
from app.modules.dashboard.metrics.new_stockist_visits import NewStockistVisitsMetric
from app.modules.dashboard.metrics.punch_in_time import PunchInTimeMetric
from app.modules.dashboard.metrics.punch_out_time import PunchOutTimeMetric
from app.modules.dashboard.metrics.registry import MetricRegistry, metric_registry
from app.modules.dashboard.metrics.stockist_visits import StockistVisitsMetric
from app.modules.dashboard.metrics.total_pob import TotalPobMetric
from app.modules.dashboard.metrics.work_duration import WorkDurationMetric

# Register all 16 metrics in exact canonical reference order
_handlers: list[BaseMetricHandler] = [
    ChemistVisitsMetric(),
    NewChemistVisitsMetric(),
    DoctorVisitsMetric(),
    NewDoctorVisitsMetric(),
    StockistVisitsMetric(),
    NewStockistVisitsMetric(),
    DoctorCallAverageMetric(),
    MissingDoctorMetric(),
    PunchInTimeMetric(),
    FirstCallTimeMetric(),
    LastCallTimeMetric(),
    PunchOutTimeMetric(),
    MorningCallsMetric(),
    EveningCallsMetric(),
    WorkDurationMetric(),
    TotalPobMetric(),
]

for _h in _handlers:
    metric_registry.register(_h)

__all__ = [
    "BaseMetricHandler",
    "MetricHandlerContext",
    "MetricRegistry",
    "metric_registry",
]
