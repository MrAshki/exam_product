from apps.worker.services.leaderboard_worker_service import LeaderboardWorkerService
from apps.worker.worker import celery_app


LEADERBOARD_UPDATE_TASK_NAME = "apps.worker.tasks.leaderboard_tasks.update_leaderboard"


@celery_app.task(name=LEADERBOARD_UPDATE_TASK_NAME)
def update_leaderboard(payload: dict) -> dict:
    return LeaderboardWorkerService().run(payload)
