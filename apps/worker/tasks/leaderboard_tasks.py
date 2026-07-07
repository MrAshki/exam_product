from apps.worker.worker import celery_app


@celery_app.task(name="apps.worker.tasks.leaderboard_tasks.placeholder")
def leaderboard_placeholder() -> None:
    return None

