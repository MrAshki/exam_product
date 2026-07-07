from apps.worker.shared.worker_context import ensure_api_path


ensure_api_path()

from app.core.config import settings  # noqa: E402


CELERY_BROKER_URL = settings.CELERY_BROKER_URL
CELERY_RESULT_BACKEND = settings.CELERY_RESULT_BACKEND

