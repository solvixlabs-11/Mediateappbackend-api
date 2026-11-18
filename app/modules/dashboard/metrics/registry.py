"""Registry for Visits Summary metric handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.dashboard.metrics.base import BaseMetricHandler


class MetricRegistry:
    """Registry managing all 16 Visits Summary metric handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, BaseMetricHandler] = {}

    def register(self, handler: BaseMetricHandler) -> None:
        """Register a metric handler under its key."""
        self._handlers[handler.key] = handler

    def get(self, key: str) -> BaseMetricHandler | None:
        """Retrieve handler for key."""
        return self._handlers.get(key)

    def list_handlers(self) -> list[BaseMetricHandler]:
        """Return all registered handlers in canonical order."""
        return list(self._handlers.values())

    def get_keys(self) -> list[str]:
        """Return all registered metric keys."""
        return list(self._handlers.keys())


metric_registry = MetricRegistry()
