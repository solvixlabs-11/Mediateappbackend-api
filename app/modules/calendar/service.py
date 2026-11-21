"""Unified Calendar Month business logic service."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import cast, Date, func, or_, select
from sqlalchemy.orm import Session

from app.modules.calendar.schemas import (
    CalendarDayCounts,
    CalendarDayData,
    CalendarDayEvent,
    CalendarMonthResponse,
)
from app.modules.customers.models import Chemist, Doctor, Stockist
from app.modules.dcr.models import DcrVisit
from app.modules.leaves.models import LeaveRequest
from app.modules.masters.models import MasterItem
from app.modules.meetings.models import Meeting
from app.modules.orders.models import Order
from app.modules.tours.models import TourProgram
from app.modules.users.models import User


class CalendarService:
    """Service providing aggregated daily counts and operational events for calendar."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_month_calendar(
        self,
        employee_id: int | None,
        year: int | None,
        month: int | None,
        current_user: User,
    ) -> CalendarMonthResponse:
        today = date.today()
        target_year = year or today.year
        target_month = month or today.month
        target_emp_id = employee_id or current_user.id

        # Role permission check
        is_admin = bool(current_user.role and current_user.role.code in ["ADMIN", "ERP ADMIN"])
        is_manager = bool(current_user.role and current_user.role.code in ["MANAGER", "RM", "ABM"])

        if target_emp_id != current_user.id and not (is_admin or is_manager):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own operational calendar.",
            )

        emp = self.db.query(User).filter(User.id == target_emp_id).first()
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {target_emp_id} not found.",
            )

        num_days = calendar.monthrange(target_year, target_month)[1]
        start_date = date(target_year, target_month, 1)
        end_date = date(target_year, target_month, num_days)

        # 1. Fetch DCR Visits for the month
        visits = (
            self.db.query(DcrVisit)
            .filter(
                DcrVisit.user_id == target_emp_id,
                DcrVisit.dcr_date >= start_date,
                DcrVisit.dcr_date <= end_date,
            )
            .all()
        )
        visits_by_day: dict[int, list[DcrVisit]] = {d: [] for d in range(1, num_days + 1)}
        for v in visits:
            visits_by_day[v.dcr_date.day].append(v)

        # 2. Fetch new customers created in the month
        new_docs = (
            self.db.query(Doctor)
            .filter(
                Doctor.created_by == target_emp_id,
                cast(Doctor.created_at, Date) >= start_date,
                cast(Doctor.created_at, Date) <= end_date,
            )
            .all()
        )
        new_docs_by_day: dict[int, int] = {d: 0 for d in range(1, num_days + 1)}
        for d in new_docs:
            if d.created_at:
                new_docs_by_day[d.created_at.day] += 1

        new_chemists = (
            self.db.query(Chemist)
            .filter(
                Chemist.created_by == target_emp_id,
                cast(Chemist.created_at, Date) >= start_date,
                cast(Chemist.created_at, Date) <= end_date,
            )
            .all()
        )
        new_chemists_by_day: dict[int, int] = {d: 0 for d in range(1, num_days + 1)}
        for c in new_chemists:
            if c.created_at:
                new_chemists_by_day[c.created_at.day] += 1

        new_stockists = (
            self.db.query(Stockist)
            .filter(
                Stockist.created_by == target_emp_id,
                cast(Stockist.created_at, Date) >= start_date,
                cast(Stockist.created_at, Date) <= end_date,
            )
            .all()
        )
        new_stockists_by_day: dict[int, int] = {d: 0 for d in range(1, num_days + 1)}
        for s in new_stockists:
            if s.created_at:
                new_stockists_by_day[s.created_at.day] += 1

        # 3. Fetch Orders / POB for the month
        orders = (
            self.db.query(Order)
            .filter(
                Order.user_id == target_emp_id,
                cast(Order.created_at, Date) >= start_date,
                cast(Order.created_at, Date) <= end_date,
            )
            .all()
        )
        pob_by_day: dict[int, float] = {d: 0.0 for d in range(1, num_days + 1)}
        order_count_by_day: dict[int, int] = {d: 0 for d in range(1, num_days + 1)}
        for o in orders:
            if o.created_at:
                pob_by_day[o.created_at.day] += float(o.total_amount or 0.0)
                order_count_by_day[o.created_at.day] += 1

        # 4. Fetch Leaves for the month
        leaves = (
            self.db.query(LeaveRequest)
            .filter(
                LeaveRequest.user_id == target_emp_id,
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
                LeaveRequest.status.in_(["APPROVED", "SUBMITTED"]),
            )
            .all()
        )

        # 5. Fetch Tour Plans for the month
        tours = (
            self.db.query(TourProgram)
            .filter(
                TourProgram.user_id == target_emp_id,
                TourProgram.start_date <= end_date,
                TourProgram.end_date >= start_date,
            )
            .all()
        )

        # 6. Fetch Meetings for the month
        meetings = (
            self.db.query(Meeting)
            .filter(
                or_(
                    Meeting.created_by_id == target_emp_id,
                    Meeting.organiser_id == target_emp_id,
                ),
                Meeting.start_date <= datetime.combine(end_date, datetime.max.time()),
                Meeting.end_date >= datetime.combine(start_date, datetime.min.time()),
                Meeting.is_active == True,
            )
            .all()
        )

        # Build day-by-day response
        days_response: list[CalendarDayData] = []
        tot_doc = 0
        tot_chem = 0
        tot_stock = 0
        tot_new_doc = 0
        tot_new_chem = 0
        tot_new_stock = 0
        tot_pob = 0.0
        has_any_pob = False

        for day_num in range(1, num_days + 1):
            cur_date = date(target_year, target_month, day_num)
            day_visits = visits_by_day[day_num]

            d_count = sum(1 for v in day_visits if v.customer_type == "DOCTOR")
            c_count = sum(1 for v in day_visits if v.customer_type == "CHEMIST")
            s_count = sum(1 for v in day_visits if v.customer_type == "STOCKIST")
            nd_count = new_docs_by_day[day_num]
            nc_count = new_chemists_by_day[day_num]
            ns_count = new_stockists_by_day[day_num]
            day_pob = pob_by_day[day_num] if order_count_by_day[day_num] > 0 else None

            tot_doc += d_count
            tot_chem += c_count
            tot_stock += s_count
            tot_new_doc += nd_count
            tot_new_chem += nc_count
            tot_new_stock += ns_count
            if day_pob is not None:
                tot_pob += day_pob
                has_any_pob = True

            day_counts = CalendarDayCounts(
                doctor=d_count,
                chemist=c_count,
                stockist=s_count,
                new_doctor=nd_count,
                new_chemist=nc_count,
                new_stockist=ns_count,
                total_pob=day_pob,
            )

            # Events on this day
            events: list[CalendarDayEvent] = []

            # Check Sunday weekly off
            if cur_date.weekday() == 6:
                events.append(
                    CalendarDayEvent(
                        id=f"off-{cur_date}",
                        title="Weekly Off (Sunday)",
                        event_type="HOLIDAY",
                        status="CONFIRMED",
                    )
                )

            # Check Leaves
            for l in leaves:
                if l.start_date <= cur_date <= l.end_date:
                    events.append(
                        CalendarDayEvent(
                            id=f"leave-{l.id}",
                            title=f"Leave: {l.leave_type}",
                            event_type="LEAVE",
                            status=l.status,
                            description=l.reason,
                        )
                    )

            # Check Tour Plans
            for t in tours:
                if t.start_date <= cur_date <= t.end_date:
                    events.append(
                        CalendarDayEvent(
                            id=f"tp-{t.id}",
                            title=f"Tour: {t.title}",
                            event_type="TOUR_PLAN",
                            status=t.status,
                            description=t.route_details,
                        )
                    )

            # Check Meetings
            for m in meetings:
                if m.start_date.date() <= cur_date <= m.end_date.date():
                    events.append(
                        CalendarDayEvent(
                            id=f"meet-{m.id}",
                            title=f"Meeting: {m.agenda}",
                            event_type="MEETING",
                            status=m.status,
                            time=m.start_date.strftime("%H:%M"),
                            description=m.location,
                        )
                    )

            days_response.append(
                CalendarDayData(
                    date=cur_date.isoformat(),
                    day=day_num,
                    weekday=cur_date.weekday(),
                    is_today=(cur_date == today),
                    counts=day_counts,
                    events=events,
                )
            )

        monthly_totals = CalendarDayCounts(
            doctor=tot_doc,
            chemist=tot_chem,
            stockist=tot_stock,
            new_doctor=tot_new_doc,
            new_chemist=tot_new_chem,
            new_stockist=tot_new_stock,
            total_pob=tot_pob if has_any_pob else None,
        )

        return CalendarMonthResponse(
            employee_id=emp.id,
            employee_name=emp.full_name,
            year=target_year,
            month=target_month,
            days=days_response,
            monthly_totals=monthly_totals,
        )
