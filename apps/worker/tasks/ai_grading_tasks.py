from apps.worker.worker import celery_app


@celery_app.task(name="apps.worker.tasks.ai_grading_tasks.placeholder")
def ai_grading_placeholder() -> None:
    return None

