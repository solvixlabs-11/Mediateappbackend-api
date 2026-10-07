"""Base report definition and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.modules.reports.schemas import (
    ReportCatalogItem,
    ReportColumn,
    ReportFilterParams,
    ReportFilterSchema,
)


class BaseReport(ABC):
    """Abstract base class for all report definitions."""

    key: str
    title: str
    group: str
    description: str
    landscape: bool = False
    allowed_roles: list[str] = ["ADMIN", "MANAGER", "MR"]
    filter_schema: ReportFilterSchema = ReportFilterSchema()
    status: str = "NOW"  # "NOW", "P8", "SALES", "ASK"
    is_ready: bool = True
    coming_soon_reason: str | None = None
    report_number: int | None = None

    @abstractmethod
    def get_columns(self) -> list[ReportColumn]:
        """Return table columns specification."""
        pass

    @abstractmethod
    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        """Execute database query and return formatted row dictionaries."""
        pass

    @abstractmethod
    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Compute aggregate summary KPIs for the report results."""
        pass

    def get_layout_hints(self) -> dict[str, Any]:
        """Return visual hints for PDF and Excel rendering."""
        return {
            "landscape": self.landscape,
            "group_by_date": self.key in ["dcr_detailed", "mr_wise_visits"],
        }


class ReportRegistry:
    """Registry maintaining active report definitions."""

    _registry: dict[str, type[BaseReport]] = {}

    @classmethod
    def register(cls, report_cls: type[BaseReport]) -> None:
        """Register a report definition class."""
        cls._registry[report_cls.key] = report_cls

    @classmethod
    def get(cls, key: str) -> BaseReport | None:
        """Retrieve instantiated report by key."""
        cls_ = cls._registry.get(key)
        return cls_() if cls_ else None

    @classmethod
    def list_for_role(cls, role: str) -> list[ReportCatalogItem]:
        """Return catalog items accessible to the specified user role."""
        catalog: list[ReportCatalogItem] = []
        for report_cls in cls._registry.values():
            if role in report_cls.allowed_roles:
                catalog.append(
                    ReportCatalogItem(
                        key=report_cls.key,
                        title=report_cls.title,
                        group=report_cls.group,
                        description=report_cls.description,
                        filter_schema=report_cls.filter_schema,
                        available_formats=["json", "xlsx", "pdf"] if report_cls.is_ready else [],
                        status=report_cls.status,
                        is_ready=report_cls.is_ready,
                        coming_soon_reason=report_cls.coming_soon_reason,
                        report_number=report_cls.report_number,
                    )
                )
        # Order by report_number (1 to 26)
        catalog.sort(key=lambda r: (r.report_number or 999, r.title))
        return catalog

    @classmethod
    def get_all(cls) -> list[type[BaseReport]]:
        """Return list of all registered report classes."""
        return list(cls._registry.values())

    @classmethod
    def list_keys(cls) -> list[str]:
        """Return list of all registered report keys."""
        return list(cls._registry.keys())
