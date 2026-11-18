"""Central dynamic registry mapping report keys to implementation classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.reports.base import BaseReport


class ReportEngineRegistry:
    """Registry maintaining active report definition classes."""

    _registry: dict[str, type[BaseReport]] = {}

    @classmethod
    def register(cls, report_cls: type[BaseReport]) -> None:
        """Register a report definition class by its unique key."""
        cls._registry[report_cls.key] = report_cls

    @classmethod
    def get(cls, key: str) -> BaseReport | None:
        """Retrieve instantiated report by key."""
        cls_ = cls._registry.get(key)
        return cls_() if cls_ else None

    @classmethod
    def has_code(cls, key: str) -> bool:
        """Check if an executable report code class is registered for key."""
        return key in cls._registry

    @classmethod
    def list_keys(cls) -> list[str]:
        """Return list of all registered report keys."""
        return list(cls._registry.keys())

    @classmethod
    def get_all(cls) -> list[type[BaseReport]]:
        """Return all registered report classes."""
        return list(cls._registry.values())
