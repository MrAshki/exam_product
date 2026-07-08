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


SUBMITTED_OR_LATER_STATUSES = {
    SubmissionStatus.SUBMITTED.value,
    SubmissionStatus.AUTO_GRADED.value,
    SubmissionStatus.NEEDS_REVIEW.value,
    SubmissionStatus.TEACHER_REVIEWED.value,
    SubmissionStatus.APPROVED.value,
    SubmissionStatus.PUBLISHED.value,
}


class ExamAccessStatus(StrEnum):
    WAITING = "waiting"
    READY = "ready"
