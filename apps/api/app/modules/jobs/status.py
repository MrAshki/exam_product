from enum import StrEnum


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class JobType(StrEnum):
    DETERMINISTIC_GRADING = "deterministic_grading"
    AI_GRADING = "ai_grading"
    EMAIL_SEND = "email_send"
    LEADERBOARD_UPDATE = "leaderboard_update"


DETERMINISTIC_GRADING_QUEUE = "deterministic_grading_queue"
AI_GRADING_QUEUE = "ai_grading_queue"
EMAIL_QUEUE = "email_queue"
LEADERBOARD_QUEUE = "leaderboard_queue"
