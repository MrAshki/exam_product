import json
from decimal import Decimal, InvalidOperation
from typing import Any

from app.modules.ai.errors import ai_response_invalid


def _decimal_from_value(value: Any) -> Decimal | None:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not decimal_value.is_finite():
        return None
    return decimal_value


def parse_rubric_response(raw_text: str, expected_total_points: Decimal) -> dict[str, Any]:
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

    expected_total = Decimal(str(expected_total_points))
    total = Decimal("0")
    if isinstance(criteria, list):
        for index, criterion in enumerate(criteria):
            field = f"criteria[{index}]"
            if not isinstance(criterion, dict):
                errors.setdefault(field, []).append("Criterion must be an object.")
                continue
            if not criterion.get("name"):
                errors.setdefault(f"{field}.name", []).append("Name is required.")
            description = criterion.get("description")
            if not isinstance(description, str):
                errors.setdefault(f"{field}.description", []).append("Description must be a string.")
            points = criterion.get("points")
            criterion_points = _decimal_from_value(points)
            if criterion_points is None:
                errors.setdefault(f"{field}.points", []).append("Points must be numeric.")
                continue
            if criterion_points <= 0:
                errors.setdefault(f"{field}.points", []).append("Points must be positive.")
            else:
                total += criterion_points

    response_total = parsed.get("total_points") if isinstance(parsed, dict) else None
    response_total_decimal = _decimal_from_value(response_total)
    if response_total_decimal is None:
        errors.setdefault("total_points", []).append("Total points must be numeric.")
    elif response_total_decimal != expected_total:
        errors.setdefault("total_points", []).append("Total points must equal the question points.")

    if total and total != expected_total:
        errors.setdefault("criteria", []).append("Criteria points must sum to the question points.")

    if errors:
        raise ai_response_invalid(errors)
    return parsed


def parse_grading_response(raw_text: str, max_score: Decimal) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        raise ai_response_invalid({"response": ["Response must be valid JSON."]}) from None

    errors: dict[str, list[str]] = {}
    if not isinstance(parsed, dict):
        raise ai_response_invalid({"response": ["Response must be a JSON object."]})

    try:
        score = Decimal(str(parsed.get("score")))
    except (InvalidOperation, TypeError):
        errors.setdefault("score", []).append("Score must be numeric.")
        score = Decimal("0")
    if score < 0 or score > max_score:
        errors.setdefault("score", []).append("Score must be between 0 and max_score.")

    feedback = parsed.get("feedback")
    if not isinstance(feedback, str):
        errors.setdefault("feedback", []).append("Feedback must be a string.")

    confidence = parsed.get("confidence")
    if confidence is None:
        normalized_confidence = None
    else:
        try:
            normalized_confidence = Decimal(str(confidence))
        except (InvalidOperation, TypeError):
            errors.setdefault("confidence", []).append("Confidence must be numeric.")
            normalized_confidence = None
        if normalized_confidence is not None and (
            normalized_confidence < Decimal("0") or normalized_confidence > Decimal("1")
        ):
            errors.setdefault("confidence", []).append("Confidence must be between 0 and 1.")

    needs_review = parsed.get("needs_review", False)
    if not isinstance(needs_review, bool):
        errors.setdefault("needs_review", []).append("Needs review must be a boolean.")

    if errors:
        raise ai_response_invalid(errors)

    return {
        "score": score,
        "feedback": feedback,
        "confidence": normalized_confidence,
        "needs_review": needs_review,
    }
