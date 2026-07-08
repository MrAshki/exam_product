from apps.worker.services.grading_worker_service import AIGradingWorkerService
from apps.worker.worker import celery_app


AI_GRADING_TASK_NAME = "apps.worker.tasks.ai_grading_tasks.grade_subjective_submission"


@celery_app.task(name=AI_GRADING_TASK_NAME)
def grade_subjective_submission(payload: dict) -> dict:
    return AIGradingWorkerService().run(payload)
