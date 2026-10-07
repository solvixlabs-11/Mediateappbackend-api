"""Timezone, date range, and formatting helpers for Reports."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException

IST = ZoneInfo("Asia/Kolkata")


def parse_date_string(date_str: str) -> date:
    """Parse date string flexibly supporting YYYY-MM-DD, YYYY-M-D, DD-MM-YYYY, etc."""
    s = date_str.strip()
    if "-" in s:
        parts = s.split("-")
        if len(parts) == 3:
            if len(parts[0]) == 4:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            elif len(parts[2]) == 4:
                return date(int(parts[2]), int(parts[1]), int(parts[0]))
    elif "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            if len(parts[0]) == 4:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            elif len(parts[2]) == 4:
                return date(int(parts[2]), int(parts[1]), int(parts[0]))
    return date.fromisoformat(s)


def resolve_date_range(
    from_date_str: str | None,
    to_date_str: str | None,
    max_days: int = 92,
) -> tuple[datetime, datetime, date, date]:
    """Parse date strings, validate range <= 92 days, and return UTC bounding datetimes."""
    now_ist = datetime.now(IST)

    try:
        to_date = parse_date_string(to_date_str) if to_date_str else now_ist.date()
    except Exception as err:
        raise HTTPException(
            status_code=400,
            detail="Invalid to_date format, expected YYYY-MM-DD",
            headers={"X-Error-Code": "INVALID_FILTER"},
        ) from err

    try:
        from_date = (
            parse_date_string(from_date_str) if from_date_str else (to_date - timedelta(days=30))
        )
    except Exception as err:
        raise HTTPException(
            status_code=400,
            detail="Invalid from_date format, expected YYYY-MM-DD",
            headers={"X-Error-Code": "INVALID_FILTER"},
        ) from err

    if from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date",
            headers={"X-Error-Code": "INVALID_FILTER"},
        )

    if (to_date - from_date).days > max_days:
        raise HTTPException(
            status_code=400,
            detail=f"Date range exceeds maximum allowed {max_days} days",
            headers={"X-Error-Code": "REPORT_RANGE_TOO_LARGE"},
        )

    # 00:00:00.000000 IST converted to UTC
    start_dt_ist = datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0, tzinfo=IST)
    start_utc = start_dt_ist.astimezone(UTC).replace(tzinfo=None)

    # 23:59:59.999999 IST converted to UTC
    end_dt_ist = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, 999999, tzinfo=IST)
    end_utc = end_dt_ist.astimezone(UTC).replace(tzinfo=None)

    return start_utc, end_utc, from_date, to_date


def utc_to_ist_str(dt: datetime | None, fmt: str = "%Y-%m-%d %I:%M %p") -> str:
    """Format UTC datetime into Asia/Kolkata localized string."""
    if not dt:
        return "-"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    ist_dt = dt.astimezone(IST)
    return ist_dt.strftime(fmt)


def utc_to_ist_date(dt: datetime | None) -> str:
    """Format UTC datetime into YYYY-MM-DD in Asia/Kolkata."""
    return utc_to_ist_str(dt, fmt="%Y-%m-%d")


def utc_to_ist_time(dt: datetime | None) -> str:
    """Format UTC datetime into 12-hour hh:mm AM/PM in Asia/Kolkata."""
    return utc_to_ist_str(dt, fmt="%I:%M %p")
