from apps.worker.worker import celery_app


@celery_app.task(name="apps.worker.tasks.email_tasks.placeholder")
def email_placeholder() -> None:
    return None

