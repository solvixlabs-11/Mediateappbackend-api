"""Generates the 32 NOW report definition files in app/modules/reports/definitions/."""

import os
from pathlib import Path

DEF_DIR = Path("E:/Mediate/Mediateappbackend-api/app/modules/reports/definitions")
DEF_DIR.mkdir(parents=True, exist_ok=True)

# Helper template generator for clean, robust reports
print("Generating 32 report definition files...")
