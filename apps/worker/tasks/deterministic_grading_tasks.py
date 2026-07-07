from apps.worker.worker import celery_app


@celery_app.task(name="apps.worker.tasks.deterministic_grading_tasks.placeholder")
def deterministic_grading_placeholder() -> None:
    return None

