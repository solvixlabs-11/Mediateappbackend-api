"""Pydantic schemas for Unified Calendar Month View."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CalendarDayCounts(BaseModel):
    """Daily operational metric counts for calendar cells."""

    doctor: int = 0
    chemist: int = 0
    stockist: int = 0
    new_doctor: int = 0
    new_chemist: int = 0
    new_stockist: int = 0
    total_pob: float | None = None


class CalendarDayEvent(BaseModel):
    """Individual event scheduled on a day."""

    id: str
    title: str
    event_type: str  # HOLIDAY, LEAVE, TOUR_PLAN, MEETING
    status: str | None = None
    time: str | None = None
    description: str | None = None


class CalendarDayData(BaseModel):
    """Single calendar day grid cell containing counts and events."""

    date: str  # YYYY-MM-DD
    day: int
    weekday: int  # 0=Monday, 6=Sunday
    is_today: bool = False
    counts: CalendarDayCounts
    events: list[CalendarDayEvent] = []


class CalendarMonthResponse(BaseModel):
    """Monthly calendar data with daily operational cells and month totals."""

    employee_id: int
    employee_name: str
    year: int
    month: int
    days: list[CalendarDayData]
    monthly_totals: CalendarDayCounts
