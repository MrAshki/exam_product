from enum import StrEnum


class EmailType(StrEnum):
    EXAM_INVITATION = "exam_invitation"
    EXAM_REMINDER = "exam_reminder"
    TEACHER_REVIEW_READY = "teacher_review_ready"
    STUDENT_RESULT_PUBLISHED = "student_result_published"
    APPEAL_CREATED = "appeal_created"
    APPEAL_RESOLVED = "appeal_resolved"


class EmailStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


VALID_EMAIL_TYPES = {email_type.value for email_type in EmailType}

