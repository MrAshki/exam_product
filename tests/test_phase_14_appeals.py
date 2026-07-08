from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import SessionLocal, engine
from app.main import app
from app.modules.appeals.models import Appeal
from app.modules.appeals.status import AppealStatus
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.grading.models import GradeChangeLog
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import EMAIL_QUEUE, LEADERBOARD_QUEUE, JobType
from app.modules.notifications.constants import EmailType
from app.modules.questions.models import Question
from app.modules.results.models import LeaderboardToken, ResultToken
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus
from apps.worker.tasks.leaderboard_tasks import LEADERBOARD_UPDATE_TASK_NAME
from apps.worker.worker import celery_app


client = TestClient(app)


@pytest.fixture(autouse=True)
def require_db() -> None:
    try:
        with engine.connect():
            return
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is unavailable: {exc}")


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def _auth_cookies(teacher_id: uuid.UUID) -> dict[str, str]:
    return {settings.COOKIE_NAME: create_access_token(str(teacher_id))}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _create_context(
    db,
    *,
    published: bool = True,
    allow_appeals: bool = True,
    show_leaderboard: bool = True,
) -> dict:
    teacher = User(full_name="Appeal Teacher", email=_email("phase14-teacher"), password_hash="not-used")
    db.add(teacher)
    db.flush()
    classroom = Classroom(teacher_id=teacher.id, title=f"Appeal Class {uuid.uuid4().hex[:8]}", subject="Math")
    db.add(classroom)
    db.flush()
    student = Student(teacher_id=teacher.id, full_name="Ali Ahmadi", email=_email("phase14-student"))
    db.add(student)
    db.flush()
    db.add(ClassStudent(class_id=classroom.id, student_id=student.id))

    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Appeal Exam {uuid.uuid4().hex[:8]}",
        status=ExamStatus.PUBLISHED.value if published else ExamStatus.APPROVED.value,
        start_time=_now() - timedelta(hours=2),
        end_time=_now() - timedelta(hours=1),
        duration_minutes=60,
        total_points=10,
        allow_appeals=allow_appeals,
        show_leaderboard=show_leaderboard,
    )
    db.add(exam)
    db.flush()
    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        short_answer_count=1,
        multiple_choice_count=1,
        total_question_count=2,
    )
    question_one = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.SHORT_ANSWER.value,
        status=QuestionStatus.CONFIRMED.value,
        text="Explain variables.",
        expected_answer="Variables represent values.",
        correct_answer="Variables represent values.",
        correct_answer_data={"text": "Variables represent values."},
        points=4,
        order_index=1,
        teacher_confirmed=True,
    )
    question_two = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.MULTIPLE_CHOICE.value,
        status=QuestionStatus.CONFIRMED.value,
        text="What is 2 + 2?",
        correct_answer="B",
        correct_answer_data={"selected_option": "B"},
        points=6,
        order_index=2,
        teacher_confirmed=True,
    )
    token = ExamToken(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        token=f"phase14-exam-{uuid.uuid4().hex}",
    )
    db.add_all([blueprint, question_one, question_two, token])
    db.flush()

    submission = Submission(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        token_id=token.id,
        started_at=_now() - timedelta(minutes=40),
        submitted_at=_now() - timedelta(minutes=30),
        status=SubmissionStatus.PUBLISHED.value if published else SubmissionStatus.APPROVED.value,
        total_score=Decimal("8.00"),
        max_score=Decimal("10.00"),
        needs_review_count=0,
        teacher_approved_at=_now() - timedelta(minutes=20),
        published_at=_now() - timedelta(minutes=10) if published else None,
    )
    db.add(submission)
    db.flush()
    answer = Answer(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        submission_id=submission.id,
        question_id=question_one.id,
        student_answer="Variables are symbols.",
        answer_data={"text": "Variables are symbols."},
        auto_score=Decimal("2.00"),
        final_score=Decimal("2.00"),
        max_score=Decimal("4.00"),
        ai_feedback="Partially correct.",
        ai_confidence=Decimal("0.670"),
        needs_review=False,
    )
    answer_two = Answer(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        submission_id=submission.id,
        question_id=question_two.id,
        student_answer="B",
        answer_data={"selected_option": "B"},
        auto_score=Decimal("6.00"),
        final_score=Decimal("6.00"),
        max_score=Decimal("6.00"),
        needs_review=False,
    )
    result_token = ResultToken(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        submission_id=submission.id,
        token=f"phase14-result-{uuid.uuid4().hex}",
    )
    db.add_all([answer, answer_two, result_token])
    leaderboard_token = None
    if show_leaderboard:
        leaderboard_token = LeaderboardToken(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            token=f"phase14-leaderboard-{uuid.uuid4().hex}",
        )
        db.add(leaderboard_token)
    db.commit()
    return {
        "teacher_id": teacher.id,
        "class_id": classroom.id,
        "exam_id": exam.id,
        "student_id": student.id,
        "submission_id": submission.id,
        "answer_id": answer.id,
        "answer_two_id": answer_two.id,
        "result_token": result_token.token,
        "leaderboard_token_id": leaderboard_token.id if leaderboard_token else None,
        "cookies": _auth_cookies(teacher.id),
    }


def _submit_url(context: dict) -> str:
    return f"/api/v1/result/{context['result_token']}/appeals"


def _list_url(context: dict) -> str:
    return f"/api/v1/classes/{context['class_id']}/appeals"


def _detail_url(context: dict, appeal_id: uuid.UUID) -> str:
    return f"/api/v1/classes/{context['class_id']}/appeals/{appeal_id}"


def _resolve_url(context: dict, appeal_id: uuid.UUID) -> str:
    return f"/api/v1/classes/{context['class_id']}/appeals/{appeal_id}/resolve"


def _submit_appeal(context: dict, answer_id=None, message: str = "Please review this answer.") -> uuid.UUID:
    response = client.post(
        _submit_url(context),
        json={"answer_id": str(answer_id) if answer_id is not None else None, "message": message},
    )
    assert response.status_code == 200
    return uuid.UUID(response.json()["data"]["appeal_id"])


def test_appeals_table_and_indexes_exist() -> None:
    inspector = inspect(engine)
    assert inspector.has_table("appeals")
    indexes = {index["name"] for index in inspector.get_indexes("appeals")}
    assert {
        "idx_appeals_teacher_id",
        "idx_appeals_class_id",
        "idx_appeals_exam_id",
        "idx_appeals_student_id",
        "idx_appeals_submission_id",
        "idx_appeals_status",
        "idx_appeals_deleted_at",
    }.issubset(indexes)


def test_submit_appeal_for_answer_and_full_exam_creates_pending_and_queues_email() -> None:
    with SessionLocal() as db:
        context = _create_context(db)

    answer_response = client.post(
        _submit_url(context),
        json={"answer_id": str(context["answer_id"]), "message": "Partial credit seems fair."},
    )
    full_exam_response = client.post(
        _submit_url(context),
        json={"answer_id": None, "message": "Please review the total score."},
    )

    with SessionLocal() as db:
        appeals = list(db.scalars(select(Appeal).where(Appeal.submission_id == context["submission_id"])).all())
        jobs = list(
            db.scalars(
                select(JobLog).where(
                    JobLog.exam_id == context["exam_id"],
                    JobLog.job_type == JobType.EMAIL_SEND.value,
                    JobLog.entity_type == "appeal",
                )
            ).all()
        )

    assert answer_response.status_code == 200
    assert full_exam_response.status_code == 200
    assert {appeal.status for appeal in appeals} == {AppealStatus.PENDING.value}
    assert any(appeal.answer_id is None for appeal in appeals)
    assert len(jobs) == 2
    assert {job.queue_name for job in jobs} == {EMAIL_QUEUE}
    assert {job.payload_json["email_type"] for job in jobs} == {EmailType.APPEAL_CREATED.value}


def test_submit_appeal_rejects_invalid_unpublished_disabled_wrong_answer_and_duplicate() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        unpublished = _create_context(db, published=False)
        disabled = _create_context(db, allow_appeals=False)
        other = _create_context(db)

    invalid_response = client.post("/api/v1/result/not-real/appeals", json={"message": "Please review."})
    unpublished_response = client.post(_submit_url(unpublished), json={"message": "Please review."})
    disabled_response = client.post(_submit_url(disabled), json={"message": "Please review."})
    wrong_answer_response = client.post(
        _submit_url(context),
        json={"answer_id": str(other["answer_id"]), "message": "Wrong answer id."},
    )
    first = client.post(_submit_url(context), json={"answer_id": str(context["answer_id"]), "message": "Review."})
    duplicate = client.post(_submit_url(context), json={"answer_id": str(context["answer_id"]), "message": "Again."})

    assert invalid_response.status_code == 404
    assert invalid_response.json()["error"]["code"] == "INVALID_RESULT_TOKEN"
    assert unpublished_response.status_code == 404
    assert unpublished_response.json()["error"]["code"] == "RESULT_NOT_PUBLISHED"
    assert disabled_response.status_code == 409
    assert disabled_response.json()["error"]["code"] == "APPEALS_NOT_ALLOWED"
    assert wrong_answer_response.status_code == 404
    assert wrong_answer_response.json()["error"]["code"] == "ANSWER_NOT_IN_SUBMISSION"
    assert first.status_code == 200
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "APPEAL_ALREADY_EXISTS"


def test_list_appeals_requires_auth_enforces_class_and_supports_filters() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        other = _create_context(db)
    appeal_id = _submit_appeal(context, context["answer_id"])
    _submit_appeal(other, other["answer_id"])

    no_auth = client.get(_list_url(context))
    wrong_teacher = client.get(_list_url(context), cookies=other["cookies"])
    status_filtered = client.get(_list_url(context), cookies=context["cookies"], params={"status": "pending"})
    exam_filtered = client.get(_list_url(context), cookies=context["cookies"], params={"exam_id": str(context["exam_id"])})
    student_filtered = client.get(
        _list_url(context),
        cookies=context["cookies"],
        params={"student_id": str(context["student_id"])},
    )
    other_exam_filtered = client.get(_list_url(context), cookies=context["cookies"], params={"exam_id": str(other["exam_id"])})

    assert no_auth.status_code == 401
    assert wrong_teacher.status_code == 404
    assert wrong_teacher.json()["error"]["code"] == "CLASS_NOT_FOUND"
    for response in [status_filtered, exam_filtered, student_filtered]:
        assert response.status_code == 200
        assert response.json()["data"]["total"] == 1
        assert response.json()["data"]["items"][0]["id"] == str(appeal_id)
    assert other_exam_filtered.status_code == 200
    assert other_exam_filtered.json()["data"]["total"] == 0


def test_get_appeal_returns_answer_context_and_full_exam_summary_and_rejects_other_class() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        other = _create_context(db)
    answer_appeal_id = _submit_appeal(context, context["answer_id"])
    full_appeal_id = _submit_appeal(context, None, "Review the whole exam.")

    answer_response = client.get(_detail_url(context, answer_appeal_id), cookies=context["cookies"])
    full_response = client.get(_detail_url(context, full_appeal_id), cookies=context["cookies"])
    wrong_class_response = client.get(_detail_url(other, answer_appeal_id), cookies=other["cookies"])

    assert answer_response.status_code == 200
    data = answer_response.json()["data"]
    assert data["student_email"].endswith("@example.com")
    assert data["answer"]["answer_id"] == str(context["answer_id"])
    assert data["answer"]["expected_answer"] == "Variables represent values."
    assert data["answer"]["ai_confidence"] == "0.670"
    assert full_response.status_code == 200
    assert full_response.json()["data"]["answer"] is None
    assert full_response.json()["data"]["total_score"] == "8.00"
    assert full_response.json()["data"]["max_score"] == "10.00"
    assert wrong_class_response.status_code == 404
    assert wrong_class_response.json()["error"]["code"] == "APPEAL_NOT_FOUND"


def test_resolve_rejected_marks_resolved_and_queues_resolved_email() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
    appeal_id = _submit_appeal(context, context["answer_id"])

    response = client.post(
        _resolve_url(context, appeal_id),
        cookies=context["cookies"],
        json={"status": "rejected", "teacher_response": "The original score is correct."},
    )

    with SessionLocal() as db:
        appeal = db.get(Appeal, appeal_id)
        jobs = list(
            db.scalars(
                select(JobLog).where(
                    JobLog.entity_type == "appeal",
                    JobLog.entity_id == appeal_id,
                    JobLog.job_type == JobType.EMAIL_SEND.value,
                )
            ).all()
        )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == AppealStatus.RESOLVED.value
    assert response.json()["data"]["final_decision"] == AppealStatus.REJECTED.value
    assert response.json()["data"]["score_changed"] is False
    assert appeal.status == AppealStatus.RESOLVED.value
    assert appeal.resolved_at is not None
    assert any(job.payload_json["email_type"] == EmailType.APPEAL_RESOLVED.value for job in jobs)
    assert {job.queue_name for job in jobs} == {EMAIL_QUEUE}


def test_resolve_accepted_score_change_updates_answer_submission_log_and_leaderboard() -> None:
    with SessionLocal() as db:
        context = _create_context(db, show_leaderboard=True)
    appeal_id = _submit_appeal(context, context["answer_id"])

    response = client.post(
        _resolve_url(context, appeal_id),
        cookies=context["cookies"],
        json={
            "status": "accepted",
            "new_score": "4.00",
            "teacher_response": "Partial credit added.",
        },
    )

    with SessionLocal() as db:
        answer = db.get(Answer, context["answer_id"])
        submission = db.get(Submission, context["submission_id"])
        appeal = db.get(Appeal, appeal_id)
        logs = list(db.scalars(select(GradeChangeLog).where(GradeChangeLog.answer_id == context["answer_id"])).all())
        leaderboard_jobs = list(
            db.scalars(
                select(JobLog).where(
                    JobLog.exam_id == context["exam_id"],
                    JobLog.job_type == JobType.LEADERBOARD_UPDATE.value,
                    JobLog.entity_type == "exam",
                )
            ).all()
        )

    assert response.status_code == 200
    assert response.json()["data"]["score_changed"] is True
    assert answer.teacher_score == Decimal("4.00")
    assert answer.final_score == Decimal("4.00")
    assert answer.reviewed_by_teacher is True
    assert answer.needs_review is False
    assert submission.total_score == Decimal("10.00")
    assert submission.max_score == Decimal("10.00")
    assert submission.needs_review_count == 0
    assert appeal.old_score == Decimal("2.00")
    assert appeal.new_score == Decimal("4.00")
    assert len(logs) == 1
    assert logs[0].reason.startswith("Appeal resolved")
    assert len(leaderboard_jobs) == 1
    assert leaderboard_jobs[0].queue_name == LEADERBOARD_QUEUE


def test_resolve_accepted_score_change_does_not_queue_leaderboard_when_disabled() -> None:
    with SessionLocal() as db:
        context = _create_context(db, show_leaderboard=False)
    appeal_id = _submit_appeal(context, context["answer_id"])

    response = client.post(
        _resolve_url(context, appeal_id),
        cookies=context["cookies"],
        json={"status": "accepted", "new_score": "3.00", "teacher_response": "One point added."},
    )

    with SessionLocal() as db:
        leaderboard_jobs = list(
            db.scalars(
                select(JobLog).where(
                    JobLog.exam_id == context["exam_id"],
                    JobLog.job_type == JobType.LEADERBOARD_UPDATE.value,
                )
            ).all()
        )

    assert response.status_code == 200
    assert leaderboard_jobs == []


def test_resolve_rejects_score_above_max_and_already_resolved() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
    appeal_id = _submit_appeal(context, context["answer_id"])

    too_high = client.post(
        _resolve_url(context, appeal_id),
        cookies=context["cookies"],
        json={"status": "accepted", "new_score": "9.00", "teacher_response": "Too high."},
    )
    ok = client.post(
        _resolve_url(context, appeal_id),
        cookies=context["cookies"],
        json={"status": "rejected", "teacher_response": "No change."},
    )
    again = client.post(
        _resolve_url(context, appeal_id),
        cookies=context["cookies"],
        json={"status": "rejected", "teacher_response": "No change again."},
    )

    assert too_high.status_code == 422
    assert too_high.json()["error"]["code"] == "INVALID_SCORE"
    assert ok.status_code == 200
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "APPEAL_ALREADY_RESOLVED"


def test_resolve_accepted_without_new_score_does_not_create_grade_change_log() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
    appeal_id = _submit_appeal(context, context["answer_id"])

    response = client.post(
        _resolve_url(context, appeal_id),
        cookies=context["cookies"],
        json={"status": "accepted", "teacher_response": "Accepted but no score change."},
    )

    with SessionLocal() as db:
        logs = list(db.scalars(select(GradeChangeLog).where(GradeChangeLog.answer_id == context["answer_id"])).all())

    assert response.status_code == 200
    assert response.json()["data"]["score_changed"] is False
    assert logs == []


def test_deleted_appeals_are_filtered_from_list_and_get() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
    appeal_id = _submit_appeal(context, context["answer_id"])
    with SessionLocal() as db:
        appeal = db.get(Appeal, appeal_id)
        appeal.soft_delete()
        db.add(appeal)
        db.commit()

    list_response = client.get(_list_url(context), cookies=context["cookies"])
    get_response = client.get(_detail_url(context, appeal_id), cookies=context["cookies"])

    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 0
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "APPEAL_NOT_FOUND"


def test_email_and_leaderboard_task_routes_remain_intact() -> None:
    assert celery_app.conf.task_routes["apps.worker.tasks.email_tasks.send_email"]["queue"] == EMAIL_QUEUE
    assert celery_app.conf.task_routes[LEADERBOARD_UPDATE_TASK_NAME]["queue"] == LEADERBOARD_QUEUE
