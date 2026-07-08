from apps.worker.services.grading_worker_service import DeterministicGradingWorkerService
from apps.worker.worker import celery_app


DETERMINISTIC_GRADING_TASK_NAME = "apps.worker.tasks.deterministic_grading_tasks.grade_submission"


@celery_app.task(name=DETERMINISTIC_GRADING_TASK_NAME)
def grade_submission(payload: dict) -> dict:
    return DeterministicGradingWorkerService().run(payload)
