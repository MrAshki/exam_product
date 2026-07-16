import uuid

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.infrastructure.email.email_service import EmailService
from app.infrastructure.email.templates import render_email_template
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import EMAIL_QUEUE, JobStatus, JobType
from app.modules.notifications.constants import EmailStatus, EmailType
from app.modules.notifications.models import EmailLog
from apps.worker.services.job_worker_service import JobWorkerService
from apps.worker.tasks.email_tasks import EMAIL_SEND_TASK_NAME
from apps.worker.worker import celery_app


@pytest.fixture(autouse=True)
def mock_email_provider(monkeypatch) -> None:
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "mock")


def _email() -> str:
    return f"phase9a-{uuid.uuid4().hex[:12]}@example.com"


def _payload(force_fail: bool = False) -> dict:
    payload = {
        "student_full_name": "Ada Student",
        "exam_title": "Algebra Check",
        "class_title": "Math 101",
        "teacher_name": "Grace Teacher",
        "start_time": "2026-07-08T10:00:00Z",
        "duration_minutes": 45,
        "exam_link": "https://example.test/exams/1",
    }
    if force_fail:
        payload["force_fail"] = True
    return payload


def _latest_email_log(db, email: str) -> EmailLog:
    return db.scalar(
        select(EmailLog)
        .where(EmailLog.email == email)
        .order_by(EmailLog.created_at.desc())
        .limit(1)
    )


def _require_db() -> None:
    try:
        with engine.connect():
            return
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is unavailable: {exc}")


def test_email_logs_table_exists_through_migration() -> None:
    _require_db()
    assert inspect(engine).has_table("email_logs")


def test_mock_provider_success_writes_email_log_sent() -> None:
    _require_db()
    email = _email()
    with SessionLocal() as db:
        result = EmailService(db).send_email(
            email_type=EmailType.EXAM_INVITATION.value,
            to_email=email,
            template_payload=_payload(),
        )
        email_log = _latest_email_log(db, email)

    assert result.success is True
    assert email_log is not None
    assert email_log.status == EmailStatus.SENT.value
    assert email_log.sent_at is not None


def test_mock_provider_forced_failure_writes_email_log_failed() -> None:
    _require_db()
    email = _email()
    with SessionLocal() as db:
        result = EmailService(db).send_email(
            email_type=EmailType.EXAM_INVITATION.value,
            to_email=email,
            template_payload=_payload(force_fail=True),
        )
        email_log = _latest_email_log(db, email)

    assert result.success is False
    assert email_log is not None
    assert email_log.status == EmailStatus.FAILED.value
    assert email_log.error_message == "Forced mock email failure."


def test_email_task_updates_job_log_success() -> None:
    _require_db()
    email = _email()
    with SessionLocal() as db:
        job = JobLog(
            job_type=JobType.EMAIL_SEND.value,
            queue_name=EMAIL_QUEUE,
            status=JobStatus.QUEUED.value,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = str(job.id)

    result = JobWorkerService().run_email_send(
        {
            "job_id": job_id,
            "email_type": EmailType.EXAM_INVITATION.value,
            "teacher_id": None,
            "class_id": None,
            "exam_id": None,
            "student_id": None,
            "to_email": email,
            "template_payload": _payload(),
        }
    )

    with SessionLocal() as db:
        job = db.get(JobLog, uuid.UUID(job_id))
        email_log = _latest_email_log(db, email)

    assert result["success"] is True
    assert job.status == JobStatus.SUCCESS.value
    assert job.attempts == 1
    assert email_log.status == EmailStatus.SENT.value


def test_email_task_updates_job_log_failed_on_provider_failure() -> None:
    _require_db()
    email = _email()
    with SessionLocal() as db:
        job = JobLog(
            job_type=JobType.EMAIL_SEND.value,
            queue_name=EMAIL_QUEUE,
            status=JobStatus.QUEUED.value,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = str(job.id)

    result = JobWorkerService().run_email_send(
        {
            "job_id": job_id,
            "email_type": EmailType.EXAM_INVITATION.value,
            "teacher_id": None,
            "class_id": None,
            "exam_id": None,
            "student_id": None,
            "to_email": email,
            "template_payload": _payload(force_fail=True),
        }
    )

    with SessionLocal() as db:
        job = db.get(JobLog, uuid.UUID(job_id))
        email_log = _latest_email_log(db, email)

    assert result["success"] is False
    assert job.status == JobStatus.FAILED.value
    assert job.error_message == "Forced mock email failure."
    assert email_log.status == EmailStatus.FAILED.value


def test_email_task_uses_email_queue_routing() -> None:
    assert celery_app.conf.task_routes[EMAIL_SEND_TASK_NAME]["queue"] == EMAIL_QUEUE


def test_templates_render_required_subject_and_body_without_crashing() -> None:
    payloads = {
        EmailType.EXAM_INVITATION.value: _payload(),
        EmailType.EXAM_REMINDER.value: {
            "student_full_name": "Ada Student",
            "exam_title": "Algebra Check",
            "class_title": "Math 101",
            "start_time": "2026-07-08T10:00:00Z",
            "exam_link": "https://example.test/exams/1",
        },
        EmailType.TEACHER_REVIEW_READY.value: {
            "teacher_name": "Grace Teacher",
            "exam_title": "Algebra Check",
            "class_title": "Math 101",
            "submission_count": 12,
            "needs_review_count": 3,
            "review_link": "https://example.test/review/1",
        },
        EmailType.STUDENT_RESULT_PUBLISHED.value: {
            "student_full_name": "Ada Student",
            "exam_title": "Algebra Check",
            "class_title": "Math 101",
            "result_link": "https://example.test/results/1",
        },
        EmailType.APPEAL_CREATED.value: {
            "teacher_name": "Grace Teacher",
            "student_full_name": "Ada Student",
            "exam_title": "Algebra Check",
            "class_title": "Math 101",
            "appeal_message": "Please review question 2.",
            "appeal_link": "https://example.test/appeals/1",
        },
        EmailType.APPEAL_RESOLVED.value: {
            "student_full_name": "Ada Student",
            "exam_title": "Algebra Check",
            "class_title": "Math 101",
            "appeal_status": "resolved",
            "teacher_response": "Score updated.",
            "result_link": "https://example.test/results/1",
        },
    }

    for email_type, payload in payloads.items():
        rendered = render_email_template(email_type, payload)
        assert rendered.subject
        assert rendered.body_text
        assert rendered.body_html
