import json
from typing import Any

from app.modules.ai.errors import ai_response_invalid


def parse_rubric_response(raw_text: str, expected_total_points: int) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        raise ai_response_invalid({"response": ["Response must be valid JSON."]}) from None

    errors: dict[str, list[str]] = {}
    if not isinstance(parsed, dict):
        errors.setdefault("response", []).append("Response must be a JSON object.")
    criteria = parsed.get("criteria") if isinstance(parsed, dict) else None
    if not isinstance(criteria, list) or not criteria:
        errors.setdefault("criteria", []).append("Criteria must be a non-empty list.")

    total = 0
    if isinstance(criteria, list):
        for index, criterion in enumerate(criteria):
            field = f"criteria[{index}]"
            if not isinstance(criterion, dict):
                errors.setdefault(field, []).append("Criterion must be an object.")
                continue
            if not criterion.get("name"):
                errors.setdefault(f"{field}.name", []).append("Name is required.")
            points = criterion.get("points")
            if not isinstance(points, int) or points <= 0:
                errors.setdefault(f"{field}.points", []).append("Points must be a positive integer.")
            else:
                total += points

    response_total = parsed.get("total_points") if isinstance(parsed, dict) else None
    if not isinstance(response_total, int):
        errors.setdefault("total_points", []).append("Total points must be an integer.")
    elif response_total != expected_total_points:
        errors.setdefault("total_points", []).append("Total points must match the question points.")

    if total and total != expected_total_points:
        errors.setdefault("criteria", []).append("Criteria points must sum to the question points.")

    if errors:
        raise ai_response_invalid(errors)
    return parsed
