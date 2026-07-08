from apps.worker.worker import celery_app
from apps.worker.services.job_worker_service import JobWorkerService


EMAIL_SEND_TASK_NAME = "apps.worker.tasks.email_tasks.send_email"


@celery_app.task(name=EMAIL_SEND_TASK_NAME)
def send_email(payload: dict) -> dict:
    return JobWorkerService().run_email_send(payload)
