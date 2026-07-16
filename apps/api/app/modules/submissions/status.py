from enum import StrEnum


class SubmissionStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    AUTO_GRADED = "auto_graded"
    NEEDS_REVIEW = "needs_review"
    TEACHER_REVIEWED = "teacher_reviewed"
    APPROVED = "approved"
    PUBLISHED = "published"


class ReviewReasonCode(StrEnum):
    AI_UNAVAILABLE = "AI_UNAVAILABLE"
    AI_LOW_CONFIDENCE = "AI_LOW_CONFIDENCE"
    POLICY_REQUIRES_TEACHER = "POLICY_REQUIRES_TEACHER"
    MISSING_GRADING_DATA = "MISSING_GRADING_DATA"
    AUTOMATIC_GRADING_CONFLICT = "AUTOMATIC_GRADING_CONFLICT"


SUBMITTED_OR_LATER_STATUSES = {
    SubmissionStatus.SUBMITTED.value,
    SubmissionStatus.AUTO_GRADED.value,
    SubmissionStatus.NEEDS_REVIEW.value,
    SubmissionStatus.TEACHER_REVIEWED.value,
    SubmissionStatus.APPROVED.value,
    SubmissionStatus.PUBLISHED.value,
}

TEACHER_CONTROLLED_SUBMISSION_STATUSES = {
    SubmissionStatus.TEACHER_REVIEWED.value,
    SubmissionStatus.APPROVED.value,
    SubmissionStatus.PUBLISHED.value,
}


def apply_grading_status_transition(current_status: str, candidate_status: SubmissionStatus | str) -> str:
    if current_status in TEACHER_CONTROLLED_SUBMISSION_STATUSES:
        return current_status
    return candidate_status.value if isinstance(candidate_status, SubmissionStatus) else candidate_status


class ExamAccessStatus(StrEnum):
    WAITING = "waiting"
    READY = "ready"
