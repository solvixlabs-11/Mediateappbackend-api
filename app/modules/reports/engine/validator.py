"""Filter schema validator and parser for dynamic reports."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def validate_filter_schema(
    schema: dict[str, Any],
    filters: dict[str, Any],
) -> dict[str, Any]:
    """Validate incoming filter dictionary against the report's filter_schema.

    Raises:
        HTTPException(400, detail, headers={"X-Error-Code": "REPORT_FILTER_REQUIRED"})
        HTTPException(400, detail, headers={"X-Error-Code": "INVALID_FILTER"})
    Returns:
        Sanitized and validated filter dictionary.
    """
    fields = schema.get("fields", [])
    validated: dict[str, Any] = {}

    for field in fields:
        name = field.get("name")
        label = field.get("label", name)
        required = field.get("required", False)
        at_least_one = field.get("at_least_one", False)

        val = filters.get(name)

        # Check required fields
        if required:
            if val is None or (isinstance(val, str) and not val.strip()):
                raise HTTPException(
                    status_code=400,
                    detail=f"Filter '{label}' is mandatory",
                    headers={"X-Error-Code": "REPORT_FILTER_REQUIRED", "X-Field-Name": name},
                )
            if isinstance(val, list) and len(val) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Filter '{label}' is mandatory",
                    headers={"X-Error-Code": "REPORT_FILTER_REQUIRED", "X-Field-Name": name},
                )

        # Check at_least_one
        if at_least_one:
            if not val or not isinstance(val, list) or len(val) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"At least one '{label}' must be selected",
                    headers={"X-Error-Code": "REPORT_FILTER_REQUIRED", "X-Field-Name": name},
                )

        # Handle defaults if omitted
        if val is None and "default" in field:
            val = field["default"]

        validated[name] = val

    return validated
