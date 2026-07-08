from celery import Celery
from kombu import Queue

from apps.worker.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from apps.worker.queues import (
    AI_GRADING_QUEUE,
    ALL_QUEUES,
    DEFAULT_QUEUE,
    DETERMINISTIC_GRADING_QUEUE,
    EMAIL_QUEUE,
    LEADERBOARD_QUEUE,
)


celery_app = Celery(
    "class_centric_exam_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "apps.worker.tasks.test_tasks",
        "apps.worker.tasks.deterministic_grading_tasks",
        "apps.worker.tasks.ai_grading_tasks",
        "apps.worker.tasks.email_tasks",
        "apps.worker.tasks.leaderboard_tasks",
    ],
)

celery_app.conf.update(
    task_default_queue=DEFAULT_QUEUE,
    task_queues=tuple(Queue(queue_name) for queue_name in ALL_QUEUES),
    task_routes={
        "apps.worker.tasks.test_tasks.test_ping": {"queue": DEFAULT_QUEUE},
        "apps.worker.tasks.deterministic_grading_tasks.grade_submission": {
            "queue": DETERMINISTIC_GRADING_QUEUE
        },
        "apps.worker.tasks.ai_grading_tasks.grade_subjective_submission": {"queue": AI_GRADING_QUEUE},
        "apps.worker.tasks.email_tasks.send_email": {"queue": EMAIL_QUEUE},
        "apps.worker.tasks.leaderboard_tasks.update_leaderboard": {"queue": LEADERBOARD_QUEUE},
    },
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
