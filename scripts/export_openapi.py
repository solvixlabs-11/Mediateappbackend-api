"""Export OpenAPI schema to openapi.json for mobile client code generation."""

import json
from pathlib import Path
import sys

# Ensure repository root is on PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.main import app  # noqa: E402


def export_openapi() -> None:
    """Generate openapi.json in repository root and docs."""
    openapi_schema = app.openapi()

    output_paths = [
        root_dir / "openapi.json",
        root_dir / "docs" / "openapi.json",
    ]

    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(openapi_schema, f, indent=2)
        print(f"Exported OpenAPI schema to {path}")


if __name__ == "__main__":
    export_openapi()
