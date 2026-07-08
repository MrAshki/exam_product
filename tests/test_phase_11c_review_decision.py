from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.db.session import SessionLocal, engine
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.grading.review_decision import ReviewDecisionService
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import EMAIL_QUEUE, JobStatus, JobType
from app.modules.notifications.constants import EmailType
from app.modules.questions.models import Question
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus
from apps.worker.services.grading_worker_service import AIGradingWorkerService, DeterministicGradingWorkerService
from tests.test_phase_10b_student_exam_access import _now
from tests.test_phase_11a_deterministic_grading import (
    _create_grading_context,
    _create_job,
    _create_submission_with_answers,
)
from tests.test_phase_11b_ai_grading import _create_submission_with_subjective_answer


@pytest.fixture(autouse=True)
def require_db() -> None:
    try:
        with engine.connect():
            return
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is unavailable: {exc}")


class _FakeAsyncResult:
    id = f"task-{uuid.uuid4().hex}"


class _FakeCelery:
    sent_tasks: list[dict] = []

    def __init__(self, *args, **kwargs) -> None:
        pass

    def send_task(self, name, args=None, queue=None):
        self.sent_tasks.append({"name": name, "args": args, "queue": queue})
        return _FakeAsyncResult()


@pytest.fixture
def fake_notification_celery(monkeypatch) -> list[dict]:
    _FakeCelery.sent_tasks = []
    monkeypatch.setattr("app.modules.notifications.service.Celery", _FakeCelery)
    return _FakeCelery.sent_tasks


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def _create_review_context(db, *, question_points: tuple[int, ...] = (4, 6)) -> dict:
    teacher = User(
        full_name="Review Teacher",
        email=_email("phase11c-teacher"),
        password_hash="not-used-in-tests",
    )
    db.add(teacher)
    db.flush()

    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"Review Class {uuid.uuid4().hex[:8]}",
        subject="Math",
    )
    db.add(classroom)
    db.flush()

    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Review Exam {uuid.uuid4().hex[:8]}",
        status=ExamStatus.SCHEDULED.value,
        start_time=_now() - timedelta(minutes=10),
        end_time=_now() + timedelta(hours=1),
        duration_minutes=60,
        total_points=sum(question_points),
    )
    db.add(exam)
    db.flush()

    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        short_answer_count=len(question_points),
        total_question_count=len(question_points),
    )
    db.add(blueprint)
    questions = []
    for index, points in enumerate(question_points, start=1):
        question = Question(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            type=QuestionType.SHORT_ANSWER.value,
            status=QuestionStatus.CONFIRMED.value,
            text=f"Question {index}",
            expected_answer="Expected answer",
            points=points,
            order_index=index,
            teacher_confirmed=True,
        )
        db.add(question)
        questions.append(question)

    db.commit()
    for instance in [teacher, classroom, exam, *questions]:
        db.refresh(instance)
    return {
        "teacher_id": teacher.id,
        "class_id": classroom.id,
        "exam_id": exam.id,
        "questions": questions,
    }


def _add_submission(
    db,
    context: dict,
    *,
    final_scores: list[Decimal | None] | None = None,
    needs_review: list[bool] | None = None,
    status: str = SubmissionStatus.SUBMITTED.value,
) -> uuid.UUID:
    student = Student(
        teacher_id=context["teacher_id"],
        full_name=f"Review Student {uuid.uuid4().hex[:6]}",
        email=_email("phase11c-student"),
    )
    db.add(student)
    db.flush()
    db.add(ClassStudent(class_id=context["class_id"], student_id=student.id))
    db.flush()
    token = ExamToken(
        teacher_id=context["teacher_id"],
        class_id=context["class_id"],
        exam_id=context["exam_id"],
        student_id=student.id,
        token=f"phase11c-{uuid.uuid4().hex}",
    )
    db.add(token)
    db.flush()
    submission = Submission(
        teacher_id=context["teacher_id"],
        class_id=context["class_id"],
        exam_id=context["exam_id"],
        student_id=student.id,
        token_id=token.id,
        status=status,
        started_at=_now() - timedelta(minutes=5),
        submitted_at=_now(),
    )
    db.add(submission)
    db.flush()

    final_scores = final_scores if final_scores is not None else [Decimal("4"), Decimal("6")]
    needs_review = needs_review if needs_review is not None else [False for _ in final_scores]
    for question, final_score, answer_needs_review in zip(context["questions"], final_scores, needs_review):
        db.add(
            Answer(
                teacher_id=context["teacher_id"],
                class_id=context["class_id"],
                exam_id=context["exam_id"],
                student_id=student.id,
                submission_id=submission.id,
                question_id=question.id,
                student_answer="Student answer",
                answer_data={"text": "Student answer"},
                final_score=final_score,
                max_score=Decimal(question.points),
                needs_review=answer_needs_review,
            )
        )
    db.commit()
    db.refresh(submission)
    return submission.id


def _evaluate(context: dict, submission_id: uuid.UUID) -> dict:
    with SessionLocal() as db:
        return ReviewDecisionService(db).evaluate_submission(
            teacher_id=context["teacher_id"],
            class_id=context["class_id"],
            exam_id=context["exam_id"],
            submission_id=submission_id,
        )


def test_review_decision_recalculates_submission_scores_and_auto_grades(fake_notification_celery) -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        submission_id = _add_submission(
            db,
            context,
            final_scores=[Decimal("3.50"), Decimal("5.25")],
            needs_review=[False, False],
        )

    _evaluate(context, submission_id)

    with SessionLocal() as db:
        submission = db.get(Submission, submission_id)

    assert submission.total_score == Decimal("8.75")
    assert submission.max_score == Decimal("10.00")
    assert submission.needs_review_count == 0
    assert submission.status == SubmissionStatus.AUTO_GRADED.value


def test_review_decision_marks_submission_needs_review_when_any_answer_needs_review(fake_notification_celery) -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        submission_id = _add_submission(
            db,
            context,
            final_scores=[Decimal("4"), Decimal("5")],
            needs_review=[False, True],
        )

    _evaluate(context, submission_id)

    with SessionLocal() as db:
        submission = db.get(Submission, submission_id)

    assert submission.needs_review_count == 1
    assert submission.status == SubmissionStatus.NEEDS_REVIEW.value


def test_review_decision_keeps_submission_submitted_when_not_all_answers_have_final_score(
    fake_notification_celery,
) -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        submission_id = _add_submission(
            db,
            context,
            final_scores=[Decimal("4"), None],
            needs_review=[False, False],
        )

    _evaluate(context, submission_id)

    with SessionLocal() as db:
        submission = db.get(Submission, submission_id)
        exam = db.get(Exam, context["exam_id"])

    assert submission.status == SubmissionStatus.SUBMITTED.value
    assert exam.status == ExamStatus.SCHEDULED.value


def test_exam_does_not_become_review_required_when_no_submitted_submissions(fake_notification_celery) -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        result = ReviewDecisionService(db).evaluate_exam(
            teacher_id=context["teacher_id"],
            class_id=context["class_id"],
            exam_id=context["exam_id"],
        )
        exam = db.get(Exam, context["exam_id"])

    assert result["submitted_count"] == 0
    assert exam.status == ExamStatus.SCHEDULED.value


def test_exam_does_not_become_review_required_while_one_submitted_submission_is_ungraded(
    fake_notification_celery,
) -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        _add_submission(
            db,
            context,
            final_scores=[Decimal("4"), Decimal("6")],
            status=SubmissionStatus.AUTO_GRADED.value,
        )
        _add_submission(
            db,
            context,
            final_scores=[Decimal("4"), None],
            status=SubmissionStatus.SUBMITTED.value,
        )
        result = ReviewDecisionService(db).evaluate_exam(
            teacher_id=context["teacher_id"],
            class_id=context["class_id"],
            exam_id=context["exam_id"],
        )
        exam = db.get(Exam, context["exam_id"])

    assert result["submitted_count"] == 2
    assert exam.status == ExamStatus.SCHEDULED.value


def test_exam_review_required_transition_queues_teacher_review_ready_email_once(
    fake_notification_celery,
) -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        _add_submission(
            db,
            context,
            final_scores=[Decimal("4"), Decimal("6")],
            needs_review=[False, False],
            status=SubmissionStatus.AUTO_GRADED.value,
        )
        _add_submission(
            db,
            context,
            final_scores=[Decimal("3"), Decimal("5")],
            needs_review=[False, True],
            status=SubmissionStatus.NEEDS_REVIEW.value,
        )

    with SessionLocal() as db:
        first = ReviewDecisionService(db).evaluate_exam(
            teacher_id=context["teacher_id"],
            class_id=context["class_id"],
            exam_id=context["exam_id"],
        )
        second = ReviewDecisionService(db).evaluate_exam(
            teacher_id=context["teacher_id"],
            class_id=context["class_id"],
            exam_id=context["exam_id"],
        )
        exam = db.get(Exam, context["exam_id"])
        jobs = list(
            db.scalars(
                select(JobLog).where(
                    JobLog.exam_id == context["exam_id"],
                    JobLog.job_type == JobType.EMAIL_SEND.value,
                )
            ).all()
        )

    assert exam.status == ExamStatus.REVIEW_REQUIRED.value
    assert first["email_queued"] is True
    assert second["email_queued"] is False
    assert len(jobs) == 1
    assert jobs[0].queue_name == EMAIL_QUEUE
    assert jobs[0].entity_type == "exam"
    assert jobs[0].payload_json["email_type"] == EmailType.TEACHER_REVIEW_READY.value
    assert "/dashboard/classes/" in jobs[0].payload_json["template_payload"]["review_link"]
    assert len(fake_notification_celery) == 1
    assert fake_notification_celery[0]["queue"] == EMAIL_QUEUE


def test_deterministic_grading_worker_calls_review_decision(monkeypatch) -> None:
    calls: list[dict] = []

    class FakeReviewDecisionService:
        def __init__(self, db) -> None:
            pass

        def evaluate_submission(self, **kwargs):
            calls.append(kwargs)
            return {"exam_status": ExamStatus.SCHEDULED.value}

    monkeypatch.setattr(
        "apps.worker.services.grading_worker_service.ReviewDecisionService",
        FakeReviewDecisionService,
    )
    with SessionLocal() as db:
        context = _create_grading_context(db)
        submission_id = _create_submission_with_answers(db, context)
        job_id = _create_job(db, context, submission_id)

    result = DeterministicGradingWorkerService().run(
        {
            "job_id": str(job_id),
            "teacher_id": str(context["teacher_id"]),
            "class_id": str(context["class_id"]),
            "exam_id": str(context["exam_id"]),
            "submission_id": str(submission_id),
        }
    )

    assert result["success"] is True
    assert len(calls) == 1
    assert calls[0]["submission_id"] == submission_id


def test_ai_grading_worker_calls_review_decision(monkeypatch) -> None:
    calls: list[dict] = []

    class FakeReviewDecisionService:
        def __init__(self, db) -> None:
            pass

        def evaluate_submission(self, **kwargs):
            calls.append(kwargs)
            return {"exam_status": ExamStatus.SCHEDULED.value}

    monkeypatch.setattr(
        "apps.worker.services.grading_worker_service.ReviewDecisionService",
        FakeReviewDecisionService,
    )
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(db)

    result = AIGradingWorkerService().run(
        {
            "job_id": str(context["job_id"]),
            "teacher_id": str(context["teacher_id"]),
            "class_id": str(context["class_id"]),
            "exam_id": str(context["exam_id"]),
            "submission_id": str(context["submission_id"]),
        }
    )

    assert result["success"] is True
    assert len(calls) == 1
    assert calls[0]["submission_id"] == context["submission_id"]


def test_handled_ai_failure_can_still_lead_to_review_required_exam(monkeypatch, fake_notification_celery) -> None:
    def fail_ai_call(self, task_name, payload):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("app.modules.ai.gateway.ModelGateway.run", fail_ai_call)
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(db)

    result = AIGradingWorkerService().run(
        {
            "job_id": str(context["job_id"]),
            "teacher_id": str(context["teacher_id"]),
            "class_id": str(context["class_id"]),
            "exam_id": str(context["exam_id"]),
            "submission_id": str(context["submission_id"]),
        }
    )

    with SessionLocal() as db:
        submission = db.get(Submission, context["submission_id"])
        exam = db.get(Exam, context["exam_id"])
        email_job = db.scalar(
            select(JobLog).where(
                JobLog.exam_id == context["exam_id"],
                JobLog.job_type == JobType.EMAIL_SEND.value,
            )
        )

    assert result["success"] is True
    assert submission.status == SubmissionStatus.NEEDS_REVIEW.value
    assert submission.needs_review_count == 1
    assert exam.status == ExamStatus.REVIEW_REQUIRED.value
    assert email_job.queue_name == EMAIL_QUEUE
    assert email_job.status == JobStatus.QUEUED.value
