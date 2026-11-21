import json
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from app.main import app

schema = app.openapi()

targets = [
    "openapi.json",
    "docs/openapi.json",
    "../openapi.json",
    "../Mediateappfrontent/openapi.json",
    "../Mediateappfrontent/docs/openapi.json",
    "../Mediateappweb/openapi.json",
]

for t in targets:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(t)), exist_ok=True)
        with open(t, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)
        print(f"Exported openapi to {t}")
    except Exception as e:
        print(f"Failed to write {t}: {e}")
