#!/usr/bin/env python3
"""Export OpenAPI schema from Django REST Framework to stdout.

Uses DRF's built-in SchemaGenerator (no extra dependencies).
Output is sorted for determinism.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure the service directory is on sys.path so `cabulous` is importable
_SERVICE_DIR = Path(__file__).resolve().parent.parent
if str(_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICE_DIR))


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cabulous.settings")

    import django

    django.setup()

    from rest_framework.schemas.openapi import SchemaGenerator

    generator = SchemaGenerator(title="Cabulous API", version="1.0.0")
    # public=True skips authentication requirements during generation
    schema = generator.get_schema(request=None, public=True)  # type: ignore[arg-type]

    if schema is None:
        print("ERROR: SchemaGenerator returned None", file=sys.stderr)
        return 1

    print(json.dumps(schema, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
