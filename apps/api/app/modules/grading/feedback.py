from __future__ import annotations

from typing import TYPE_CHECKING

from app.modules.submissions.status import ReviewReasonCode

if TYPE_CHECKING:
    from app.modules.submissions.models import Answer


LEGACY_AI_FAILURE_FEEDBACK = "AI grading failed. Teacher review required."


def normalize_feedback(feedback: str | None) -> str | None:
    if feedback is None:
        return None
    normalized = feedback.strip()
    return normalized or None


def safe_ai_feedback(feedback: str | None) -> str | None:
    normalized = normalize_feedback(feedback)
    if normalized is None or normalized == LEGACY_AI_FAILURE_FEEDBACK:
        return None
    return normalized


def student_visible_feedback(answer: Answer) -> str | None:
    teacher_feedback = safe_ai_feedback(answer.teacher_feedback)
    if teacher_feedback:
        return teacher_feedback
    if answer.review_reason_code == ReviewReasonCode.AI_UNAVAILABLE.value:
        return None
    return safe_ai_feedback(answer.ai_feedback)
