from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import OperationalError

from app.core.exceptions import AppException
from app.db.session import SessionLocal, engine
from app.main import app
from app.modules.auth.models import User
from app.modules.exams.errors import ExamErrorCode
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.routes import get_exam_service
from app.modules.exams.schemas import ExamInvitationRequest, ExamScheduleRequest
from app.modules.exams.permissions import get_current_teacher
from app.modules.exams.service import ExamService
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import EMAIL_QUEUE
from app.modules.notifications.constants import EmailType
from app.modules.questions.models import Question, QuestionOption
from app.modules.classrooms.models import Classroom
from app.modules.students.models import ClassStudent, Student
from apps.worker.tasks.email_tasks import EMAIL_SEND_TASK_NAME
from apps.worker.worker import celery_app


START_TIME = datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc)
END_TIME = datetime(2026, 7, 10, 11, 30, tzinfo=timezone.utc)


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def _require_db() -> None:
    try:
        with engine.connect():
            return
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is unavailable: {exc}")


def _schedule_payload() -> ExamScheduleRequest:
    return ExamScheduleRequest(
        start_time=START_TIME,
        end_time=END_TIME,
        duration_minutes=60,
    )


def _create_teacher(db) -> User:
    teacher = User(
        full_name="Grace Teacher",
        email=_email("phase9b-teacher"),
        password_hash="not-used-in-tests",
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def _create_classroom(db, teacher: User) -> Classroom:
    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"Math {uuid.uuid4().hex[:8]}",
        subject="Math",
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def _create_student(db, teacher: User, classroom: Classroom, *, is_active: bool = True) -> Student:
    student = Student(
        teacher_id=teacher.id,
        full_name=f"Ada Student {uuid.uuid4().hex[:6]}",
        email=_email("phase9b-student"),
        is_active=is_active,
    )
    db.add(student)
    db.flush()
    db.add(ClassStudent(class_id=classroom.id, student_id=student.id))
    db.commit()
    db.refresh(student)
    return student


def _create_exam(db, teacher: User, classroom: Classroom, *, total_points: int = 10) -> Exam:
    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Ready Exam {uuid.uuid4().hex[:8]}",
        total_points=total_points,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def _add_true_false_blueprint_and_question(
    db,
    teacher: User,
    classroom: Classroom,
    exam: Exam,
    *,
    points: int = 10,
    confirmed: bool = True,
) -> Question:
    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        true_false_count=1,
        total_question_count=1,
    )
    question = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.TRUE_FALSE.value,
        status=QuestionStatus.CONFIRMED.value if confirmed else QuestionStatus.DRAFT.value,
        text="The derivative of x^2 is 2x.",
        correct_answer="true",
        points=points,
        order_index=1,
        teacher_confirmed=confirmed,
    )
    db.add_all([blueprint, question])
    db.commit()
    db.refresh(question)
    return question


def _finalize_ready_exam(db, teacher: User, classroom: Classroom, exam: Exam) -> None:
    ExamService(db).finalize(classroom.id, exam.id, teacher)


def test_exam_tokens_table_exists_after_migration() -> None:
    _require_db()
    assert inspect(engine).has_table("exam_tokens")


def test_cannot_schedule_exam_without_active_class_student() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        exam = _create_exam(db, teacher, classroom)
        _add_true_false_blueprint_and_question(db, teacher, classroom, exam)
        _finalize_ready_exam(db, teacher, classroom, exam)

        with pytest.raises(AppException) as exc_info:
            ExamService(db).schedule(classroom.id, exam.id, _schedule_payload(), teacher)

    assert exc_info.value.code == ExamErrorCode.EXAM_NOT_READY
    assert "students" in exc_info.value.details


def test_cannot_schedule_exam_with_incomplete_unconfirmed_questions() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        _create_student(db, teacher, classroom)
        exam = _create_exam(db, teacher, classroom)
        question = _add_true_false_blueprint_and_question(db, teacher, classroom, exam, confirmed=False)
        question.text = None
        db.add(question)
        db.commit()

        with pytest.raises(AppException) as exc_info:
            ExamService(db).finalize(classroom.id, exam.id, teacher)

    assert exc_info.value.code == ExamErrorCode.EXAM_NOT_READY
    assert exc_info.value.details["readiness"]["failures"]


def test_cannot_schedule_exam_if_question_points_do_not_match_exam_total() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        _create_student(db, teacher, classroom)
        exam = _create_exam(db, teacher, classroom, total_points=20)
        _add_true_false_blueprint_and_question(db, teacher, classroom, exam, points=10)

        with pytest.raises(AppException) as exc_info:
            ExamService(db).finalize(classroom.id, exam.id, teacher)

    assert exc_info.value.code == ExamErrorCode.EXAM_NOT_READY
    assert exc_info.value.details["readiness"]["points_match"] is False


def test_can_schedule_ready_exam_and_create_tokens_idempotently() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        student_one = _create_student(db, teacher, classroom)
        _create_student(db, teacher, classroom)
        exam = _create_exam(db, teacher, classroom)
        _add_true_false_blueprint_and_question(db, teacher, classroom, exam)
        _finalize_ready_exam(db, teacher, classroom, exam)
        db.add(
            ExamToken(
                teacher_id=teacher.id,
                class_id=classroom.id,
                exam_id=exam.id,
                student_id=student_one.id,
                token=f"existing-{uuid.uuid4().hex}",
                expires_at=END_TIME,
            )
        )
        db.commit()

        result = ExamService(db).schedule(classroom.id, exam.id, _schedule_payload(), teacher)
        active_token_count = db.scalar(
            select(func.count())
            .select_from(ExamToken)
            .where(ExamToken.exam_id == exam.id, ExamToken.deleted_at.is_(None))
        )
        scheduled_exam = db.get(Exam, exam.id)

    assert result["status"] == ExamStatus.SCHEDULED.value
    assert result["created_exam_tokens"] == 1
    assert scheduled_exam.status == ExamStatus.SCHEDULED.value
    assert active_token_count == 2


def test_send_invitations_requires_scheduled_exam() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        _create_student(db, teacher, classroom)
        exam = _create_exam(db, teacher, classroom)

        with pytest.raises(AppException) as exc_info:
            ExamService(db).send_invitations(
                classroom.id,
                exam.id,
                ExamInvitationRequest(send_to_all=True),
                teacher,
            )

    assert exc_info.value.code == ExamErrorCode.EXAM_NOT_SCHEDULED


def test_send_invitations_queues_email_jobs_with_exam_links(monkeypatch) -> None:
    _require_db()

    sent_tasks: list[dict] = []

    class FakeAsyncResult:
        id = f"task-{uuid.uuid4().hex}"

    class FakeCelery:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def send_task(self, name, args=None, queue=None):
            sent_tasks.append({"name": name, "args": args, "queue": queue})
            return FakeAsyncResult()

    monkeypatch.setattr("app.modules.notifications.service.Celery", FakeCelery)

    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        _create_student(db, teacher, classroom)
        _create_student(db, teacher, classroom)
        exam = _create_exam(db, teacher, classroom)
        _add_true_false_blueprint_and_question(db, teacher, classroom, exam)
        _finalize_ready_exam(db, teacher, classroom, exam)
        ExamService(db).schedule(classroom.id, exam.id, _schedule_payload(), teacher)

        result = ExamService(db).send_invitations(
            classroom.id,
            exam.id,
            ExamInvitationRequest(send_to_all=True),
            teacher,
        )
        jobs = list(
            db.scalars(
                select(JobLog)
                .where(JobLog.exam_id == exam.id, JobLog.entity_type == EmailType.EXAM_INVITATION.value)
                .order_by(JobLog.created_at.asc())
            ).all()
        )

    assert result["queued_emails"] == 2
    assert len(jobs) == 2
    assert len(sent_tasks) == 2
    assert {task["queue"] for task in sent_tasks} == {EMAIL_QUEUE}
    assert {job.payload_json["email_type"] for job in jobs} == {EmailType.EXAM_INVITATION.value}
    for job in jobs:
        exam_link = job.payload_json["template_payload"]["exam_link"]
        assert "/exam/access/" in exam_link


def test_class_ownership_and_exam_class_mismatch_are_rejected() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        other_classroom = _create_classroom(db, teacher)
        _create_student(db, teacher, classroom)
        exam = _create_exam(db, teacher, other_classroom)

        with pytest.raises(AppException) as exc_info:
            ExamService(db).schedule(classroom.id, exam.id, _schedule_payload(), teacher)

    assert exc_info.value.code == ExamErrorCode.EXAM_NOT_FOUND


def test_schedule_and_send_invitation_routes_are_wired() -> None:
    teacher = User(
        id=uuid.uuid4(),
        full_name="Route Teacher",
        email="route-teacher@example.com",
        password_hash="not-used",
    )
    class_id = uuid.uuid4()
    exam_id = uuid.uuid4()

    class FakeExamService:
        def schedule(self, route_class_id, route_exam_id, payload, route_teacher):
            assert route_class_id == class_id
            assert route_exam_id == exam_id
            assert route_teacher.id == teacher.id
            return {
                "id": exam_id,
                "status": ExamStatus.SCHEDULED.value,
                "start_time": payload.start_time,
                "end_time": payload.end_time,
                "duration_minutes": payload.duration_minutes,
                "created_exam_tokens": 1,
            }

        def send_invitations(self, route_class_id, route_exam_id, payload, route_teacher):
            assert route_class_id == class_id
            assert route_exam_id == exam_id
            assert route_teacher.id == teacher.id
            return {"queued_emails": 1}

    app.dependency_overrides[get_current_teacher] = lambda: teacher
    app.dependency_overrides[get_exam_service] = lambda: FakeExamService()
    try:
        client = TestClient(app)
        schedule_response = client.post(
            f"/api/v1/classes/{class_id}/exams/{exam_id}/schedule",
            json={
                "start_time": "2026-07-10T10:00:00Z",
                "end_time": "2026-07-10T11:30:00Z",
                "duration_minutes": 60,
            },
        )
        invitation_response = client.post(
            f"/api/v1/classes/{class_id}/exams/{exam_id}/send-invitations",
            json={"send_to_all": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert schedule_response.status_code == 200
    assert schedule_response.json()["data"]["created_exam_tokens"] == 1
    assert invitation_response.status_code == 200
    assert invitation_response.json()["data"]["queued_emails"] == 1


def test_email_jobs_route_through_email_queue() -> None:
    assert celery_app.conf.task_routes[EMAIL_SEND_TASK_NAME]["queue"] == EMAIL_QUEUE
