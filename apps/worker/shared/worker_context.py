from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
import sys

from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = PROJECT_ROOT / "apps" / "api"


def ensure_api_path() -> None:
    api_root = str(API_ROOT)
    if api_root not in sys.path:
        sys.path.insert(0, api_root)


ensure_api_path()

from app.db.session import SessionLocal  # noqa: E402
from app.modules.ai import logs as ai_logs  # noqa: E402,F401
from app.modules.auth import models as auth_models  # noqa: E402,F401
from app.modules.classrooms import models as classroom_models  # noqa: E402,F401
from app.modules.exams import models as exam_models  # noqa: E402,F401
from app.modules.notifications import models as notification_models  # noqa: E402,F401
from app.modules.questions import models as question_models  # noqa: E402,F401
from app.modules.results import models as result_models  # noqa: E402,F401
from app.modules.students import models as student_models  # noqa: E402,F401
from app.modules.submissions import models as submission_models  # noqa: E402,F401


@contextmanager
def worker_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
