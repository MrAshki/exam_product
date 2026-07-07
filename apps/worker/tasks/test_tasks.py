from apps.worker.services.job_worker_service import JobWorkerService
from apps.worker.worker import celery_app


TEST_PING_TASK_NAME = "apps.worker.tasks.test_tasks.test_ping"


@celery_app.task(name=TEST_PING_TASK_NAME)
def test_ping(job_id: str, payload: dict | None = None) -> dict:
    return JobWorkerService().run_test_ping(job_id, payload or {})

