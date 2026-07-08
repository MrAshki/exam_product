from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select

from app.modules.ai.gateway import ModelGateway
from app.modules.ai.logs import AILog
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import AI_GRADING_QUEUE, DETERMINISTIC_GRADING_QUEUE, EMAIL_QUEUE, JobStatus, JobType
from app.modules.questions.models import Question
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus
from app.db.session import SessionLocal
from apps.worker.services.grading_worker_service import AIGradingWorkerService
from apps.worker.tasks.ai_grading_tasks import AI_GRADING_TASK_NAME
from apps.worker.tasks.deterministic_grading_tasks import DETERMINISTIC_GRADING_TASK_NAME
from apps.worker.tasks.email_tasks import EMAIL_SEND_TASK_NAME
from apps.worker.worker import celery_app
from tests.test_phase_10b_student_exam_access import _now, _start, _submit


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def _create_ai_context(
    db,
    *,
    include_objective: bool = False,
    include_short_answer: bool = True,
    include_essay: bool = False,
) -> dict:
    teacher = User(
        full_name="AI Teacher",
        email=_email("phase11b-teacher"),
        password_hash="not-used-in-tests",
    )
    db.add(teacher)
    db.flush()

    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"AI Grading Class {uuid.uuid4().hex[:8]}",
        subject="Writing",
    )
    db.add(classroom)
    db.flush()

    student = Student(
        teacher_id=teacher.id,
        full_name="AI Student",
        email=_email("phase11b-student"),
    )
    db.add(student)
    db.flush()
    db.add(ClassStudent(class_id=classroom.id, student_id=student.id))
    db.flush()

    total_points = 0
    questions: list[Question] = []
    if include_objective:
        total_points += 2
    if include_short_answer:
        total_points += 5
    if include_essay:
        total_points += 8

    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"AI Grading Exam {uuid.uuid4().hex[:8]}",
        status=ExamStatus.SCHEDULED.value,
        start_time=_now() - timedelta(minutes=5),
        end_time=_now() + timedelta(hours=1),
        duration_minutes=60,
        total_points=total_points,
    )
    db.add(exam)
    db.flush()

    order_index = 1
    objective_question = None
    short_question = None
    essay_question = None
    if include_objective:
        objective_question = Question(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            type=QuestionType.MULTIPLE_CHOICE.value,
            status=QuestionStatus.CONFIRMED.value,
            text="What is 1 + 1?",
            correct_answer_data={"selected_option": "A"},
            points=2,
            order_index=order_index,
            teacher_confirmed=True,
        )
        questions.append(objective_question)
        order_index += 1
    if include_short_answer:
        short_question = Question(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            type=QuestionType.SHORT_ANSWER.value,
            status=QuestionStatus.CONFIRMED.value,
            text="Define photosynthesis.",
            expected_answer="Plants use light to make food.",
            points=5,
            order_index=order_index,
            teacher_confirmed=True,
        )
        questions.append(short_question)
        order_index += 1
    if include_essay:
        essay_question = Question(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            type=QuestionType.ESSAY.value,
            status=QuestionStatus.CONFIRMED.value,
            text="Explain how evidence supports a claim.",
            expected_answer="Evidence should directly support the claim with reasoning.",
            rubric={"criteria": [{"name": "Reasoning", "points": 8}], "total_points": 8},
            points=8,
            order_index=order_index,
            teacher_confirmed=True,
        )
        questions.append(essay_question)

    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        multiple_choice_count=1 if include_objective else 0,
        short_answer_count=1 if include_short_answer else 0,
        essay_count=1 if include_essay else 0,
        total_question_count=len(questions),
    )
    token = ExamToken(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        token=f"phase11b-{uuid.uuid4().hex}",
        expires_at=exam.end_time,
    )
    db.add_all([blueprint, token, *questions])
    db.commit()
    for instance in [teacher, classroom, student, exam, token, *questions]:
        db.refresh(instance)

    return {
        "teacher_id": teacher.id,
        "class_id": classroom.id,
        "student_id": student.id,
        "exam_id": exam.id,
        "token_id": token.id,
        "token_value": token.token,
        "objective_question_id": objective_question.id if objective_question is not None else None,
        "short_question_id": short_question.id if short_question is not None else None,
        "essay_question_id": essay_question.id if essay_question is not None else None,
    }


def _submit_answers_for_context(context: dict) -> list[dict]:
    answers = []
    if context["objective_question_id"] is not None:
        answers.append(
            {
                "question_id": str(context["objective_question_id"]),
                "student_answer": "A",
                "answer_data": {"selected_option": "A"},
            }
        )
    if context["short_question_id"] is not None:
        answers.append(
            {
                "question_id": str(context["short_question_id"]),
                "student_answer": "Plants use sunlight to make food.",
                "answer_data": {"text": "Plants use sunlight to make food."},
            }
        )
    if context["essay_question_id"] is not None:
        answers.append(
            {
                "question_id": str(context["essay_question_id"]),
                "student_answer": "Evidence supports a claim when reasoning links them.",
                "answer_data": {"text": "Evidence supports a claim when reasoning links them."},
            }
        )
    return answers


def _create_submission_with_subjective_answer(
    db,
    *,
    question_type: str = QuestionType.SHORT_ANSWER.value,
    teacher_score: Decimal | None = None,
    final_score: Decimal | None = None,
) -> dict:
    context = _create_ai_context(
        db,
        include_short_answer=question_type == QuestionType.SHORT_ANSWER.value,
        include_essay=question_type == QuestionType.ESSAY.value,
    )
    question_id = context["short_question_id"] or context["essay_question_id"]
    submission = Submission(
        teacher_id=context["teacher_id"],
        class_id=context["class_id"],
        exam_id=context["exam_id"],
        student_id=context["student_id"],
        token_id=context["token_id"],
        status=SubmissionStatus.SUBMITTED.value,
        started_at=_now() - timedelta(minutes=3),
        submitted_at=_now(),
    )
    db.add(submission)
    db.flush()
    answer = Answer(
        teacher_id=context["teacher_id"],
        class_id=context["class_id"],
        exam_id=context["exam_id"],
        student_id=context["student_id"],
        submission_id=submission.id,
        question_id=question_id,
        student_answer="A useful student answer.",
        answer_data={"text": "A useful student answer."},
        teacher_score=teacher_score,
        final_score=final_score,
    )
    db.add(answer)
    db.flush()
    job = JobLog(
        teacher_id=context["teacher_id"],
        class_id=context["class_id"],
        exam_id=context["exam_id"],
        submission_id=submission.id,
        job_type=JobType.AI_GRADING.value,
        queue_name=AI_GRADING_QUEUE,
        status=JobStatus.QUEUED.value,
        entity_type="submission",
        entity_id=submission.id,
    )
    db.add(job)
    db.commit()
    db.refresh(submission)
    db.refresh(answer)
    db.refresh(job)
    return {**context, "submission_id": submission.id, "answer_id": answer.id, "job_id": job.id}


def _run_ai_worker(context: dict) -> dict:
    return AIGradingWorkerService().run(
        {
            "job_id": str(context["job_id"]),
            "teacher_id": str(context["teacher_id"]),
            "class_id": str(context["class_id"]),
            "exam_id": str(context["exam_id"]),
            "submission_id": str(context["submission_id"]),
        }
    )


class _FakeAsyncResult:
    id = f"task-{uuid.uuid4().hex}"


class _FakeCelery:
    sent_tasks: list[dict] = []

    def __init__(self, *args, **kwargs) -> None:
        pass

    def send_task(self, name, args=None, queue=None):
        self.sent_tasks.append({"name": name, "args": args, "queue": queue})
        return _FakeAsyncResult()


def _install_fake_celery(monkeypatch) -> list[dict]:
    _FakeCelery.sent_tasks = []
    monkeypatch.setattr("app.modules.grading.service.Celery", _FakeCelery)
    return _FakeCelery.sent_tasks


def test_submit_creates_ai_grading_job_log_when_short_answer_exists(monkeypatch) -> None:
    sent_tasks = _install_fake_celery(monkeypatch)
    with SessionLocal() as db:
        context = _create_ai_context(db, include_short_answer=True)

    _start(context["token_value"])
    response = _submit(context["token_value"], _submit_answers_for_context(context))

    with SessionLocal() as db:
        jobs = list(db.scalars(select(JobLog).where(JobLog.exam_id == context["exam_id"])).all())

    assert response.status_code == 200
    assert {job.job_type for job in jobs} == {JobType.DETERMINISTIC_GRADING.value, JobType.AI_GRADING.value}
    assert any(job.queue_name == AI_GRADING_QUEUE for job in jobs)
    assert any(task["name"] == AI_GRADING_TASK_NAME and task["queue"] == AI_GRADING_QUEUE for task in sent_tasks)


def test_submit_creates_ai_grading_job_log_when_essay_exists(monkeypatch) -> None:
    _install_fake_celery(monkeypatch)
    with SessionLocal() as db:
        context = _create_ai_context(db, include_short_answer=False, include_essay=True)

    _start(context["token_value"])
    response = _submit(context["token_value"], _submit_answers_for_context(context))

    with SessionLocal() as db:
        ai_job = db.scalar(
            select(JobLog).where(JobLog.exam_id == context["exam_id"], JobLog.job_type == JobType.AI_GRADING.value)
        )

    assert response.status_code == 200
    assert ai_job.queue_name == AI_GRADING_QUEUE
    assert ai_job.status == JobStatus.QUEUED.value


def test_submit_creates_both_deterministic_and_ai_jobs_for_mixed_exam(monkeypatch) -> None:
    _install_fake_celery(monkeypatch)
    with SessionLocal() as db:
        context = _create_ai_context(db, include_objective=True, include_short_answer=True)

    _start(context["token_value"])
    response = _submit(context["token_value"], _submit_answers_for_context(context))

    with SessionLocal() as db:
        jobs = list(db.scalars(select(JobLog).where(JobLog.exam_id == context["exam_id"])).all())

    assert response.status_code == 200
    assert [job.job_type for job in jobs].count(JobType.DETERMINISTIC_GRADING.value) == 1
    assert [job.job_type for job in jobs].count(JobType.AI_GRADING.value) == 1


def test_objective_only_exam_does_not_create_ai_grading_job(monkeypatch) -> None:
    _install_fake_celery(monkeypatch)
    with SessionLocal() as db:
        context = _create_ai_context(db, include_objective=True, include_short_answer=False)

    _start(context["token_value"])
    response = _submit(context["token_value"], _submit_answers_for_context(context))

    with SessionLocal() as db:
        jobs = list(db.scalars(select(JobLog).where(JobLog.exam_id == context["exam_id"])).all())

    assert response.status_code == 200
    assert len(jobs) == 1
    assert jobs[0].job_type == JobType.DETERMINISTIC_GRADING.value


def test_ai_grading_task_routes_to_ai_queue_and_existing_routes_stay_intact() -> None:
    assert celery_app.conf.task_routes[AI_GRADING_TASK_NAME]["queue"] == AI_GRADING_QUEUE
    assert celery_app.conf.task_routes[DETERMINISTIC_GRADING_TASK_NAME]["queue"] == DETERMINISTIC_GRADING_QUEUE
    assert celery_app.conf.task_routes[EMAIL_SEND_TASK_NAME]["queue"] == EMAIL_QUEUE


def test_worker_calls_model_gateway_and_writes_ai_log(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_run(self, task_name, payload):
        calls.append({"task_name": task_name, "payload": payload})
        return type(
            "Result",
            (),
            {
                "text": '{"score": 4, "feedback": "Good short answer.", "confidence": 0.9, "needs_review": false}',
                "provider": "mock",
                "model": "mock",
                "raw_response": "{}",
                "response_json": {"score": 4, "feedback": "Good short answer.", "confidence": 0.9, "needs_review": False},
                "prompt_tokens": None,
                "completion_tokens": None,
            },
        )()

    monkeypatch.setattr(ModelGateway, "run", fake_run)
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(db)

    result = _run_ai_worker(context)

    with SessionLocal() as db:
        ai_log_count = db.scalar(select(AILog).where(AILog.exam_id == context["exam_id"])).id

    assert result["success"] is True
    assert calls[0]["task_name"] == "short_answer_grading"
    assert "student_id" not in calls[0]["payload"]
    assert ai_log_count is not None


def test_short_answer_receives_ai_score_feedback_confidence_and_auto_graded_status(monkeypatch) -> None:
    def fake_run(self, task_name, payload):
        return type(
            "Result",
            (),
            {
                "text": '{"score": 4, "feedback": "Accurate.", "confidence": 0.95, "needs_review": false}',
                "provider": "mock",
                "model": "mock",
                "raw_response": "{}",
                "response_json": {"score": 4, "feedback": "Accurate.", "confidence": 0.95, "needs_review": False},
                "prompt_tokens": None,
                "completion_tokens": None,
            },
        )()

    monkeypatch.setattr(ModelGateway, "run", fake_run)
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(db)

    _run_ai_worker(context)

    with SessionLocal() as db:
        answer = db.get(Answer, context["answer_id"])
        submission = db.get(Submission, context["submission_id"])

    assert answer.auto_score == Decimal("4.00")
    assert answer.final_score == Decimal("4.00")
    assert answer.ai_feedback == "Accurate."
    assert answer.ai_confidence == Decimal("0.950")
    assert answer.needs_review is False
    assert submission.total_score == Decimal("4.00")
    assert submission.max_score == Decimal("5.00")
    assert submission.needs_review_count == 0
    assert submission.status == SubmissionStatus.AUTO_GRADED.value


def test_essay_receives_ai_score_feedback_confidence(monkeypatch) -> None:
    def fake_run(self, task_name, payload):
        assert task_name == "essay_grading"
        assert payload["rubric"]["total_points"] == 8
        return type(
            "Result",
            (),
            {
                "text": '{"score": 7, "feedback": "Strong essay.", "confidence": 0.88, "needs_review": false}',
                "provider": "mock",
                "model": "mock",
                "raw_response": "{}",
                "response_json": {"score": 7, "feedback": "Strong essay.", "confidence": 0.88, "needs_review": False},
                "prompt_tokens": None,
                "completion_tokens": None,
            },
        )()

    monkeypatch.setattr(ModelGateway, "run", fake_run)
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(db, question_type=QuestionType.ESSAY.value)

    _run_ai_worker(context)

    with SessionLocal() as db:
        answer = db.get(Answer, context["answer_id"])

    assert answer.auto_score == Decimal("7.00")
    assert answer.final_score == Decimal("7.00")
    assert answer.ai_feedback == "Strong essay."
    assert answer.ai_confidence == Decimal("0.880")


def test_low_confidence_sets_needs_review_and_submission_needs_review(monkeypatch) -> None:
    def fake_run(self, task_name, payload):
        return type(
            "Result",
            (),
            {
                "text": '{"score": 2, "feedback": "Uncertain.", "confidence": 0.5, "needs_review": false}',
                "provider": "mock",
                "model": "mock",
                "raw_response": "{}",
                "response_json": {"score": 2, "feedback": "Uncertain.", "confidence": 0.5, "needs_review": False},
                "prompt_tokens": None,
                "completion_tokens": None,
            },
        )()

    monkeypatch.setattr(ModelGateway, "run", fake_run)
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(db)

    _run_ai_worker(context)

    with SessionLocal() as db:
        answer = db.get(Answer, context["answer_id"])
        submission = db.get(Submission, context["submission_id"])

    assert answer.needs_review is True
    assert submission.needs_review_count == 1
    assert submission.status == SubmissionStatus.NEEDS_REVIEW.value


def test_ai_failure_marks_answer_for_review_without_fake_score(monkeypatch) -> None:
    def fake_run(self, task_name, payload):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(ModelGateway, "run", fake_run)
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(db)

    result = _run_ai_worker(context)

    with SessionLocal() as db:
        answer = db.get(Answer, context["answer_id"])
        job = db.get(JobLog, context["job_id"])

    assert result["success"] is True
    assert answer.auto_score is None
    assert answer.final_score is None
    assert answer.needs_review is True
    assert answer.ai_feedback == "AI grading failed. Teacher review required."
    assert answer.ai_confidence is None
    assert job.status == JobStatus.SUCCESS.value


def test_worker_does_not_overwrite_teacher_score_and_is_idempotent(monkeypatch) -> None:
    def fake_run(self, task_name, payload):
        return type(
            "Result",
            (),
            {
                "text": '{"score": 5, "feedback": "Complete.", "confidence": 0.9, "needs_review": false}',
                "provider": "mock",
                "model": "mock",
                "raw_response": "{}",
                "response_json": {"score": 5, "feedback": "Complete.", "confidence": 0.9, "needs_review": False},
                "prompt_tokens": None,
                "completion_tokens": None,
            },
        )()

    monkeypatch.setattr(ModelGateway, "run", fake_run)
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(
            db,
            teacher_score=Decimal("3.00"),
            final_score=Decimal("3.00"),
        )

    first = _run_ai_worker(context)
    second = _run_ai_worker(context)

    with SessionLocal() as db:
        answer = db.get(Answer, context["answer_id"])
        job = db.get(JobLog, context["job_id"])

    assert first["success"] is True
    assert second["success"] is True
    assert answer.teacher_score == Decimal("3.00")
    assert answer.auto_score == Decimal("5.00")
    assert answer.final_score == Decimal("3.00")
    assert job.attempts == 2


def test_worker_fails_job_log_cleanly_when_submission_is_deleted() -> None:
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(db)
        submission = db.get(Submission, context["submission_id"])
        submission.soft_delete()
        db.add(submission)
        db.commit()

    result = _run_ai_worker(context)

    with SessionLocal() as db:
        job = db.get(JobLog, context["job_id"])

    assert result["success"] is False
    assert job.status == JobStatus.FAILED.value
    assert "Submission not found or mismatched." in job.error_message


def test_no_real_gemini_or_openrouter_call_happens_in_ai_grading_tests(monkeypatch) -> None:
    def fail_if_http_called(*args, **kwargs):
        raise AssertionError("Automated AI grading tests must not call external providers.")

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fail_if_http_called)
    with SessionLocal() as db:
        context = _create_submission_with_subjective_answer(db)

    result = _run_ai_worker(context)

    with SessionLocal() as db:
        answer = db.get(Answer, context["answer_id"])

    assert result["success"] is True
    assert answer.ai_feedback == "Mock AI grading feedback."
    assert answer.auto_score == Decimal("5.00")
