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
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import EMAIL_QUEUE, LEADERBOARD_QUEUE, JobStatus, JobType
from app.modules.notifications.constants import EmailType
from app.modules.questions.models import Question
from app.modules.results.models import LeaderboardToken, ResultToken
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus
from apps.worker.services.leaderboard_worker_service import LeaderboardWorkerService
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


def _publish_url(context: dict) -> str:
    return f"/api/v1/classes/{context['class_id']}/exams/{context['exam_id']}/publish-results"


def _create_publish_context(
    db,
    *,
    exam_status: str = ExamStatus.APPROVED.value,
    show_leaderboard: bool = True,
    show_correct_answers: bool = True,
    show_feedback: bool = True,
    allow_appeals: bool = True,
    submission_count: int = 2,
    create_answers: bool = True,
    submission_status: str = SubmissionStatus.APPROVED.value,
) -> dict:
    teacher = User(
        full_name="Publish Teacher",
        email=_email("phase13-teacher"),
        password_hash="not-used",
    )
    db.add(teacher)
    db.flush()

    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"Phase 13 Class {uuid.uuid4().hex[:8]}",
        subject="Math",
    )
    db.add(classroom)
    db.flush()

    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Phase 13 Exam {uuid.uuid4().hex[:8]}",
        status=exam_status,
        start_time=_now() - timedelta(hours=2),
        end_time=_now() - timedelta(hours=1),
        duration_minutes=60,
        total_points=10,
        show_leaderboard=show_leaderboard,
        show_correct_answers=show_correct_answers,
        show_feedback=show_feedback,
        allow_appeals=allow_appeals,
    )
    db.add(exam)
    db.flush()

    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        multiple_choice_count=1,
        short_answer_count=1,
        total_question_count=2,
    )
    question_one = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.MULTIPLE_CHOICE.value,
        status=QuestionStatus.CONFIRMED.value,
        text="What is 2 + 2?",
        correct_answer="B",
        correct_answer_data={"selected_option": "B"},
        points=4,
        order_index=1,
        teacher_confirmed=True,
    )
    question_two = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.SHORT_ANSWER.value,
        status=QuestionStatus.CONFIRMED.value,
        text="Explain addition.",
        expected_answer="Combining quantities.",
        points=6,
        order_index=2,
        teacher_confirmed=True,
    )
    db.add_all([blueprint, question_one, question_two])
    db.flush()

    submissions = []
    students = []
    for index in range(submission_count):
        student = Student(
            teacher_id=teacher.id,
            full_name=f"Student {index + 1}",
            email=_email(f"phase13-student-{index}"),
        )
        db.add(student)
        db.flush()
        db.add(ClassStudent(class_id=classroom.id, student_id=student.id))
        token = ExamToken(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            student_id=student.id,
            token=f"phase13-exam-{uuid.uuid4().hex}",
        )
        db.add(token)
        db.flush()
        total = Decimal("10.00") - Decimal(index)
        submission = Submission(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            student_id=student.id,
            token_id=token.id,
            started_at=_now() - timedelta(minutes=30),
            submitted_at=_now() - timedelta(minutes=20 - index),
            status=submission_status,
            total_score=total,
            max_score=Decimal("10.00"),
            needs_review_count=0,
            teacher_approved_at=_now() - timedelta(minutes=5),
        )
        db.add(submission)
        db.flush()
        if create_answers:
            db.add_all(
                [
                    Answer(
                        teacher_id=teacher.id,
                        class_id=classroom.id,
                        exam_id=exam.id,
                        student_id=student.id,
                        submission_id=submission.id,
                        question_id=question_one.id,
                        student_answer="B",
                        answer_data={"selected_option": "B"},
                        auto_score=Decimal("4.00"),
                        final_score=Decimal("4.00"),
                        max_score=Decimal("4.00"),
                        needs_review=False,
                    ),
                    Answer(
                        teacher_id=teacher.id,
                        class_id=classroom.id,
                        exam_id=exam.id,
                        student_id=student.id,
                        submission_id=submission.id,
                        question_id=question_two.id,
                        student_answer="Addition combines numbers.",
                        answer_data={"text": "Addition combines numbers."},
                        ai_feedback="Clear answer.",
                        auto_score=Decimal("6.00") - Decimal(index),
                        final_score=Decimal("6.00") - Decimal(index),
                        max_score=Decimal("6.00"),
                        needs_review=False,
                    ),
                ]
            )
        submissions.append(submission)
        students.append(student)

    db.commit()
    return {
        "teacher_id": teacher.id,
        "class_id": classroom.id,
        "exam_id": exam.id,
        "question_ids": [question_one.id, question_two.id],
        "submission_ids": [submission.id for submission in submissions],
        "student_ids": [student.id for student in students],
        "cookies": _auth_cookies(teacher.id),
    }


def test_result_and_leaderboard_token_tables_and_indexes_exist() -> None:
    inspector = inspect(engine)
    assert inspector.has_table("result_tokens")
    assert inspector.has_table("leaderboard_tokens")
    result_indexes = {index["name"] for index in inspector.get_indexes("result_tokens")}
    leaderboard_indexes = {index["name"] for index in inspector.get_indexes("leaderboard_tokens")}
    assert {
        "idx_result_tokens_token",
        "idx_result_tokens_submission_id",
        "idx_result_tokens_exam_student",
        "idx_result_tokens_deleted_at",
        "uq_result_tokens_submission_active",
    }.issubset(result_indexes)
    assert {
        "idx_leaderboard_tokens_token",
        "idx_leaderboard_tokens_class_exam",
        "idx_leaderboard_tokens_deleted_at",
        "uq_leaderboard_tokens_class_exam_active",
    }.issubset(leaderboard_indexes)


def test_publish_results_requires_teacher_auth() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db)

    response = client.post(_publish_url(context))

    assert response.status_code == 401


def test_publish_results_enforces_teacher_ownership_and_exam_class_match() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db)
        other_context = _create_publish_context(db)
        second_class = Classroom(
            teacher_id=context["teacher_id"],
            title=f"Wrong Class {uuid.uuid4().hex[:8]}",
            subject="Math",
        )
        db.add(second_class)
        db.commit()
        wrong_class_id = second_class.id

    wrong_teacher = client.post(_publish_url(context), cookies=other_context["cookies"])
    wrong_class = client.post(
        f"/api/v1/classes/{wrong_class_id}/exams/{context['exam_id']}/publish-results",
        cookies=context["cookies"],
    )

    assert wrong_teacher.status_code == 404
    assert wrong_teacher.json()["error"]["code"] == "CLASS_NOT_FOUND"
    assert wrong_class.status_code == 404
    assert wrong_class.json()["error"]["code"] == "EXAM_NOT_FOUND"


def test_publish_results_blocks_not_approved_no_submissions_and_incomplete_results() -> None:
    with SessionLocal() as db:
        draft_context = _create_publish_context(db, exam_status=ExamStatus.REVIEW_REQUIRED.value)
        empty_context = _create_publish_context(db, submission_count=0)
        incomplete_context = _create_publish_context(db, create_answers=False)

    draft_response = client.post(_publish_url(draft_context), cookies=draft_context["cookies"])
    empty_response = client.post(_publish_url(empty_context), cookies=empty_context["cookies"])
    incomplete_response = client.post(_publish_url(incomplete_context), cookies=incomplete_context["cookies"])

    assert draft_response.status_code == 409
    assert draft_response.json()["error"]["code"] == "EXAM_NOT_APPROVED"
    assert empty_response.status_code == 409
    assert empty_response.json()["error"]["code"] == "NO_APPROVED_SUBMISSIONS"
    assert incomplete_response.status_code == 409
    assert incomplete_response.json()["error"]["code"] == "RESULTS_INCOMPLETE"


def test_publish_results_creates_tokens_sets_published_and_queues_jobs() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db)

    response = client.post(_publish_url(context), cookies=context["cookies"])

    with SessionLocal() as db:
        exam = db.get(Exam, context["exam_id"])
        submissions = list(db.scalars(select(Submission).where(Submission.exam_id == context["exam_id"])).all())
        result_tokens = list(db.scalars(select(ResultToken).where(ResultToken.exam_id == context["exam_id"])).all())
        leaderboard_tokens = list(db.scalars(select(LeaderboardToken).where(LeaderboardToken.exam_id == context["exam_id"])).all())
        jobs = list(db.scalars(select(JobLog).where(JobLog.exam_id == context["exam_id"])).all())

    assert response.status_code == 200
    assert response.json()["data"]["status"] == ExamStatus.PUBLISHED.value
    assert response.json()["data"]["created_result_tokens"] == 2
    assert response.json()["data"]["queued_result_emails"] == 2
    assert exam.status == ExamStatus.PUBLISHED.value
    assert {submission.status for submission in submissions} == {SubmissionStatus.PUBLISHED.value}
    assert all(submission.published_at is not None for submission in submissions)
    assert len(result_tokens) == 2
    assert len({token.token for token in result_tokens}) == 2
    assert len(leaderboard_tokens) == 1
    email_jobs = [job for job in jobs if job.job_type == JobType.EMAIL_SEND.value]
    leaderboard_jobs = [job for job in jobs if job.job_type == JobType.LEADERBOARD_UPDATE.value]
    assert len(email_jobs) == 2
    assert {job.queue_name for job in email_jobs} == {EMAIL_QUEUE}
    assert {job.entity_type for job in email_jobs} == {"result_token"}
    assert {job.payload_json["email_type"] for job in email_jobs} == {EmailType.STUDENT_RESULT_PUBLISHED.value}
    assert all("/result/" in job.payload_json["template_payload"]["result_link"] for job in email_jobs)
    assert len(leaderboard_jobs) == 1
    assert leaderboard_jobs[0].queue_name == LEADERBOARD_QUEUE


def test_publish_results_does_not_create_leaderboard_token_when_disabled() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db, show_leaderboard=False)

    response = client.post(_publish_url(context), cookies=context["cookies"])

    with SessionLocal() as db:
        leaderboard_count = len(list(db.scalars(select(LeaderboardToken).where(LeaderboardToken.exam_id == context["exam_id"])).all()))
        leaderboard_jobs = list(
            db.scalars(
                select(JobLog).where(
                    JobLog.exam_id == context["exam_id"],
                    JobLog.job_type == JobType.LEADERBOARD_UPDATE.value,
                )
            ).all()
        )

    assert response.status_code == 200
    assert response.json()["data"]["leaderboard_enabled"] is False
    assert leaderboard_count == 0
    assert leaderboard_jobs == []


def test_publish_results_is_idempotent_for_tokens_and_jobs() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db)

    first = client.post(_publish_url(context), cookies=context["cookies"])
    second = client.post(_publish_url(context), cookies=context["cookies"])

    with SessionLocal() as db:
        result_tokens = list(db.scalars(select(ResultToken).where(ResultToken.exam_id == context["exam_id"])).all())
        leaderboard_tokens = list(db.scalars(select(LeaderboardToken).where(LeaderboardToken.exam_id == context["exam_id"])).all())
        email_jobs = list(
            db.scalars(
                select(JobLog).where(
                    JobLog.exam_id == context["exam_id"],
                    JobLog.job_type == JobType.EMAIL_SEND.value,
                )
            ).all()
        )
        leaderboard_jobs = list(
            db.scalars(
                select(JobLog).where(
                    JobLog.exam_id == context["exam_id"],
                    JobLog.job_type == JobType.LEADERBOARD_UPDATE.value,
                )
            ).all()
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"]["created_result_tokens"] == 0
    assert len(result_tokens) == 2
    assert len(leaderboard_tokens) == 1
    assert len(email_jobs) == 2
    assert len(leaderboard_jobs) == 1


def test_get_result_returns_one_student_and_respects_visibility_flags() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(
            db,
            show_correct_answers=False,
            show_feedback=False,
            allow_appeals=False,
        )
    client.post(_publish_url(context), cookies=context["cookies"])

    with SessionLocal() as db:
        tokens = list(db.scalars(select(ResultToken).where(ResultToken.exam_id == context["exam_id"])).all())

    response = client.get(f"/api/v1/result/{tokens[0].token}")
    data = response.json()["data"]

    assert response.status_code == 200
    assert data["student_full_name"] in {"Student 1", "Student 2"}
    assert data["can_appeal"] is False
    assert len(data["answers"]) == 2
    assert all(answer["correct_answer"] is None for answer in data["answers"])
    assert all(answer["correct_answer_data"] is None for answer in data["answers"])
    assert all(answer["feedback"] is None for answer in data["answers"])
    assert "student_email" not in data
    assert "teacher_id" not in data


def test_get_result_rejects_invalid_soft_deleted_and_unpublished_tokens() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db)
    client.post(_publish_url(context), cookies=context["cookies"])

    with SessionLocal() as db:
        token = db.scalar(select(ResultToken).where(ResultToken.exam_id == context["exam_id"]))
        token.soft_delete()
        db.add(token)
        unpublished_context = _create_publish_context(db, exam_status=ExamStatus.APPROVED.value)
        unpublished_token = ResultToken(
            teacher_id=unpublished_context["teacher_id"],
            class_id=unpublished_context["class_id"],
            exam_id=unpublished_context["exam_id"],
            student_id=unpublished_context["student_ids"][0],
            submission_id=unpublished_context["submission_ids"][0],
            token=f"manual-result-{uuid.uuid4().hex}",
        )
        db.add(unpublished_token)
        db.commit()
        soft_deleted = token.token
        unpublished = unpublished_token.token

    invalid_response = client.get("/api/v1/result/not-a-real-token")
    deleted_response = client.get(f"/api/v1/result/{soft_deleted}")
    unpublished_response = client.get(f"/api/v1/result/{unpublished}")

    assert invalid_response.status_code == 404
    assert invalid_response.json()["error"]["code"] == "INVALID_RESULT_TOKEN"
    assert deleted_response.status_code == 404
    assert deleted_response.json()["error"]["code"] == "INVALID_RESULT_TOKEN"
    assert unpublished_response.status_code == 404
    assert unpublished_response.json()["error"]["code"] == "RESULT_NOT_PUBLISHED"


def test_get_result_can_appeal_true_when_published_and_allowed() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db, allow_appeals=True)
    client.post(_publish_url(context), cookies=context["cookies"])

    with SessionLocal() as db:
        token = db.scalar(select(ResultToken).where(ResultToken.exam_id == context["exam_id"]))

    response = client.get(f"/api/v1/result/{token.token}")

    assert response.status_code == 200
    assert response.json()["data"]["can_appeal"] is True


def test_get_leaderboard_returns_class_scoped_ranking_without_private_details() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db)
        other_context = _create_publish_context(db)
    client.post(_publish_url(context), cookies=context["cookies"])
    client.post(_publish_url(other_context), cookies=other_context["cookies"])

    with SessionLocal() as db:
        token = db.scalar(select(LeaderboardToken).where(LeaderboardToken.exam_id == context["exam_id"]))

    response = client.get(f"/api/v1/leaderboard/{token.token}")
    data = response.json()["data"]

    assert response.status_code == 200
    assert [item["student_full_name"] for item in data["items"]] == ["Student 1", "Student 2"]
    assert data["items"][0]["rank"] == 1
    assert data["items"][0]["percentage"] == 100.0
    assert "result_token" not in data["items"][0]
    assert "answers" not in data["items"][0]
    assert "email" not in data["items"][0]
    assert len(data["items"]) == 2


def test_get_leaderboard_rejects_invalid_soft_deleted_unpublished_and_disabled_tokens() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db)
        disabled_context = _create_publish_context(db, show_leaderboard=False)
    client.post(_publish_url(context), cookies=context["cookies"])
    client.post(_publish_url(disabled_context), cookies=disabled_context["cookies"])

    with SessionLocal() as db:
        token = db.scalar(select(LeaderboardToken).where(LeaderboardToken.exam_id == context["exam_id"]))
        token.soft_delete()
        unpublished_context = _create_publish_context(db)
        unpublished_token = LeaderboardToken(
            teacher_id=unpublished_context["teacher_id"],
            class_id=unpublished_context["class_id"],
            exam_id=unpublished_context["exam_id"],
            token=f"manual-leaderboard-{uuid.uuid4().hex}",
        )
        disabled_token = LeaderboardToken(
            teacher_id=disabled_context["teacher_id"],
            class_id=disabled_context["class_id"],
            exam_id=disabled_context["exam_id"],
            token=f"disabled-leaderboard-{uuid.uuid4().hex}",
        )
        db.add_all([token, unpublished_token, disabled_token])
        db.commit()
        soft_deleted = token.token
        unpublished = unpublished_token.token
        disabled = disabled_token.token

    invalid_response = client.get("/api/v1/leaderboard/not-a-real-token")
    deleted_response = client.get(f"/api/v1/leaderboard/{soft_deleted}")
    unpublished_response = client.get(f"/api/v1/leaderboard/{unpublished}")
    disabled_response = client.get(f"/api/v1/leaderboard/{disabled}")

    assert invalid_response.status_code == 404
    assert invalid_response.json()["error"]["code"] == "INVALID_LEADERBOARD_TOKEN"
    assert deleted_response.status_code == 404
    assert deleted_response.json()["error"]["code"] == "INVALID_LEADERBOARD_TOKEN"
    assert unpublished_response.status_code == 404
    assert unpublished_response.json()["error"]["code"] == "LEADERBOARD_NOT_AVAILABLE"
    assert disabled_response.status_code == 404
    assert disabled_response.json()["error"]["code"] == "LEADERBOARD_NOT_AVAILABLE"


def test_leaderboard_task_routes_to_leaderboard_queue() -> None:
    assert celery_app.conf.task_routes[LEADERBOARD_UPDATE_TASK_NAME]["queue"] == LEADERBOARD_QUEUE


def test_leaderboard_worker_updates_job_log_success_and_failed() -> None:
    with SessionLocal() as db:
        context = _create_publish_context(db)
        other_context = _create_publish_context(db)
    client.post(_publish_url(context), cookies=context["cookies"])

    with SessionLocal() as db:
        success_job = JobLog(
            teacher_id=context["teacher_id"],
            class_id=context["class_id"],
            exam_id=context["exam_id"],
            job_type=JobType.LEADERBOARD_UPDATE.value,
            queue_name=LEADERBOARD_QUEUE,
            status=JobStatus.QUEUED.value,
            entity_type="exam",
            entity_id=context["exam_id"],
        )
        failed_job = JobLog(
            teacher_id=context["teacher_id"],
            class_id=context["class_id"],
            exam_id=other_context["exam_id"],
            job_type=JobType.LEADERBOARD_UPDATE.value,
            queue_name=LEADERBOARD_QUEUE,
            status=JobStatus.QUEUED.value,
            entity_type="exam",
            entity_id=other_context["exam_id"],
        )
        db.add_all([success_job, failed_job])
        db.commit()
        db.refresh(success_job)
        db.refresh(failed_job)
        success_id = success_job.id
        failed_id = failed_job.id

    success = LeaderboardWorkerService().run(
        {
            "job_id": str(success_id),
            "teacher_id": str(context["teacher_id"]),
            "class_id": str(context["class_id"]),
            "exam_id": str(context["exam_id"]),
        }
    )
    failed = LeaderboardWorkerService().run(
        {
            "job_id": str(failed_id),
            "teacher_id": str(context["teacher_id"]),
            "class_id": str(context["class_id"]),
            "exam_id": str(other_context["exam_id"]),
        }
    )

    with SessionLocal() as db:
        success_job = db.get(JobLog, success_id)
        failed_job = db.get(JobLog, failed_id)

    assert success["success"] is True
    assert success_job.status == JobStatus.SUCCESS.value
    assert failed["success"] is False
    assert failed_job.status == JobStatus.FAILED.value
    assert failed_job.error_message
