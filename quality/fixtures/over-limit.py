"""Fixture: function exceeding the 50-line limit.

Used by acceptance tests to verify the function-length gate catches violations.
Excluded from production scanning via ruff/flake8 per-file-ignores.
"""


def process_data(items):
    """Process a list of items and return results.

    This function processes each item in the input list,
    applying transformations based on the item's value.
    """
    results = []
    for item in items:
        if item is None:
            continue
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        value = item.get("value", 0)
        if not name:
            continue
        if value < 0:
            continue
        processed = {
            "name": name.strip(),
            "value": value * 2,
            "category": "unknown",
            "status": "pending",
            "source": "fixture",
            "validated": False,
        }
        if value > 100:
            processed["category"] = "high"
        elif value > 50:
            processed["category"] = "medium"
        else:
            processed["category"] = "low"
        if value > 200:
            processed["status"] = "critical"
        elif value > 100:
            processed["status"] = "warning"
        elif value > 50:
            processed["status"] = "info"
        else:
            processed["status"] = "normal"
        if processed["category"] == "high":
            processed["value"] = processed["value"] * 1.5
        elif processed["category"] == "medium":
            processed["value"] = processed["value"] * 1.2
        else:
            processed["value"] = processed["value"] * 1.0
        processed["timestamp"] = "2026-01-01"
        processed["version"] = "1.0"
        processed["validated"] = True
        processed["processed"] = True
        results.append(processed)
    return results
