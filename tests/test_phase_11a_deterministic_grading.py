from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select

from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import DETERMINISTIC_GRADING_QUEUE, EMAIL_QUEUE, JobStatus, JobType
from app.modules.questions.models import Question
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus
from app.db.session import SessionLocal
from apps.worker.services.grading_worker_service import DeterministicGradingWorkerService
from apps.worker.tasks.deterministic_grading_tasks import DETERMINISTIC_GRADING_TASK_NAME
from apps.worker.tasks.email_tasks import EMAIL_SEND_TASK_NAME
from apps.worker.worker import celery_app
from tests.test_phase_10b_student_exam_access import _now, _start, _submit


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def _create_grading_context(db, *, include_subjective: bool = False) -> dict:
    teacher = User(
        full_name="Grace Teacher",
        email=_email("phase11a-teacher"),
        password_hash="not-used-in-tests",
    )
    db.add(teacher)
    db.flush()

    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"Grading Class {uuid.uuid4().hex[:8]}",
        subject="Math",
    )
    db.add(classroom)
    db.flush()

    student = Student(
        teacher_id=teacher.id,
        full_name="Ada Student",
        email=_email("phase11a-student"),
    )
    db.add(student)
    db.flush()
    db.add(ClassStudent(class_id=classroom.id, student_id=student.id))
    db.flush()

    total_points = 10 + (5 if include_subjective else 0)
    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Grading Exam {uuid.uuid4().hex[:8]}",
        status=ExamStatus.SCHEDULED.value,
        start_time=_now() - timedelta(minutes=5),
        end_time=_now() + timedelta(hours=1),
        duration_minutes=60,
        total_points=total_points,
    )
    db.add(exam)
    db.flush()

    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        multiple_choice_count=1,
        true_false_count=1,
        short_answer_count=1 if include_subjective else 0,
        total_question_count=3 if include_subjective else 2,
    )
    mc_question = Question(
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
    tf_question = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.TRUE_FALSE.value,
        status=QuestionStatus.CONFIRMED.value,
        text="The sky is blue.",
        correct_answer_data={"value": True},
        points=6,
        order_index=2,
        teacher_confirmed=True,
    )
    token = ExamToken(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        token=f"phase11a-{uuid.uuid4().hex}",
    )
    db.add_all([blueprint, mc_question, tf_question, token])
    short_answer = None
    if include_subjective:
        short_answer = Question(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            type=QuestionType.SHORT_ANSWER.value,
            status=QuestionStatus.CONFIRMED.value,
            text="Explain variables.",
            expected_answer="Unknown values.",
            points=5,
            order_index=3,
            teacher_confirmed=True,
        )
        db.add(short_answer)
    db.commit()
    for instance in [teacher, classroom, student, exam, mc_question, tf_question, token]:
        db.refresh(instance)
    if short_answer is not None:
        db.refresh(short_answer)

    return {
        "teacher": teacher,
        "teacher_id": teacher.id,
        "classroom": classroom,
        "class_id": classroom.id,
        "student": student,
        "student_id": student.id,
        "exam": exam,
        "exam_id": exam.id,
        "mc_question": mc_question,
        "mc_question_id": mc_question.id,
        "tf_question": tf_question,
        "tf_question_id": tf_question.id,
        "short_answer": short_answer,
        "short_answer_id": short_answer.id if short_answer is not None else None,
        "token": token,
        "token_id": token.id,
        "token_value": token.token,
    }


def _create_submission_with_answers(
    db,
    context: dict,
    *,
    mc_selected: str = "B",
    tf_value: bool = True,
    include_subjective: bool = False,
) -> uuid.UUID:
    submission = Submission(
        teacher_id=context["teacher"].id,
        class_id=context["classroom"].id,
        exam_id=context["exam"].id,
        student_id=context["student"].id,
        token_id=context["token"].id,
        status=SubmissionStatus.SUBMITTED.value,
        started_at=_now() - timedelta(minutes=2),
        submitted_at=_now(),
    )
    db.add(submission)
    db.flush()
    answers = [
        Answer(
            teacher_id=context["teacher"].id,
            class_id=context["classroom"].id,
            exam_id=context["exam"].id,
            student_id=context["student"].id,
            submission_id=submission.id,
            question_id=context["mc_question"].id,
            student_answer=mc_selected,
            answer_data={"selected_option": mc_selected},
            needs_review=True,
        ),
        Answer(
            teacher_id=context["teacher"].id,
            class_id=context["classroom"].id,
            exam_id=context["exam"].id,
            student_id=context["student"].id,
            submission_id=submission.id,
            question_id=context["tf_question"].id,
            student_answer=str(tf_value).lower(),
            answer_data={"value": tf_value},
            needs_review=True,
        ),
    ]
    if include_subjective:
        answers.append(
            Answer(
                teacher_id=context["teacher"].id,
                class_id=context["classroom"].id,
                exam_id=context["exam"].id,
                student_id=context["student"].id,
                submission_id=submission.id,
                question_id=context["short_answer"].id,
                student_answer="Variables are unknown values.",
                answer_data={"text": "Variables are unknown values."},
            )
        )
    db.add_all(answers)
    db.commit()
    db.refresh(submission)
    return submission.id


def _create_job(db, context: dict, submission_id: uuid.UUID) -> uuid.UUID:
    job = JobLog(
        teacher_id=context["teacher_id"],
        class_id=context["class_id"],
        exam_id=context["exam_id"],
        submission_id=submission_id,
        job_type=JobType.DETERMINISTIC_GRADING.value,
        queue_name=DETERMINISTIC_GRADING_QUEUE,
        status=JobStatus.QUEUED.value,
        entity_type="submission",
        entity_id=submission_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id


def _run_worker(job_id: uuid.UUID, context: dict, submission_id: uuid.UUID) -> dict:
    return DeterministicGradingWorkerService().run(
        {
            "job_id": str(job_id),
            "teacher_id": str(context["teacher_id"]),
            "class_id": str(context["class_id"]),
            "exam_id": str(context["exam_id"]),
            "submission_id": str(submission_id),
        }
    )


def test_submit_creates_and_enqueues_deterministic_grading_job(monkeypatch) -> None:
    sent_tasks: list[dict] = []

    class FakeAsyncResult:
        id = f"task-{uuid.uuid4().hex}"

    class FakeCelery:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def send_task(self, name, args=None, queue=None):
            sent_tasks.append({"name": name, "args": args, "queue": queue})
            return FakeAsyncResult()

    monkeypatch.setattr("app.modules.grading.service.Celery", FakeCelery)

    with SessionLocal() as db:
        context = _create_grading_context(db)
        token = context["token"].token

    _start(token)
    response = _submit(
        token,
        [
            {
                "question_id": str(context["mc_question_id"]),
                "student_answer": "B",
                "answer_data": {"selected_option": "B"},
            }
        ],
    )

    with SessionLocal() as db:
        job = db.scalar(select(JobLog).where(JobLog.exam_id == context["exam_id"]))

    assert response.status_code == 200
    assert response.json()["message"] == "Your answers were submitted. Results will be available after teacher review."
    assert job.job_type == JobType.DETERMINISTIC_GRADING.value
    assert job.queue_name == DETERMINISTIC_GRADING_QUEUE
    assert job.status == JobStatus.QUEUED.value
    assert job.entity_type == "submission"
    assert len(sent_tasks) == 1
    assert sent_tasks[0]["name"] == DETERMINISTIC_GRADING_TASK_NAME
    assert sent_tasks[0]["queue"] == DETERMINISTIC_GRADING_QUEUE


def test_deterministic_grading_task_routes_to_deterministic_queue_and_email_route_stays_intact() -> None:
    assert celery_app.conf.task_routes[DETERMINISTIC_GRADING_TASK_NAME]["queue"] == DETERMINISTIC_GRADING_QUEUE
    assert celery_app.conf.task_routes[EMAIL_SEND_TASK_NAME]["queue"] == EMAIL_QUEUE


def test_worker_grades_objective_answers_and_updates_submission_totals() -> None:
    with SessionLocal() as db:
        context = _create_grading_context(db)
        submission = _create_submission_with_answers(db, context, mc_selected="B", tf_value=True)
        job = _create_job(db, context, submission)

    result = _run_worker(job, context, submission)

    with SessionLocal() as db:
        answers = list(db.scalars(select(Answer).where(Answer.submission_id == submission)).all())
        submission = db.get(Submission, submission)
        job = db.get(JobLog, job)

    assert result["success"] is True
    assert {answer.auto_score for answer in answers} == {Decimal("4.00"), Decimal("6.00")}
    assert {answer.final_score for answer in answers} == {Decimal("4.00"), Decimal("6.00")}
    assert {answer.max_score for answer in answers} == {Decimal("4.00"), Decimal("6.00")}
    assert all(answer.needs_review is False for answer in answers)
    assert all(answer.reviewed_by_teacher is False for answer in answers)
    assert submission.total_score == Decimal("10.00")
    assert submission.max_score == Decimal("10.00")
    assert submission.status == SubmissionStatus.AUTO_GRADED.value
    assert job.status == JobStatus.SUCCESS.value


def test_worker_grades_wrong_objective_answers_zero() -> None:
    with SessionLocal() as db:
        context = _create_grading_context(db)
        submission = _create_submission_with_answers(db, context, mc_selected="A", tf_value=False)
        job = _create_job(db, context, submission)

    _run_worker(job, context, submission)

    with SessionLocal() as db:
        answers = list(db.scalars(select(Answer).where(Answer.submission_id == submission)).all())
        submission = db.get(Submission, submission)

    assert {answer.auto_score for answer in answers} == {Decimal("0.00")}
    assert {answer.final_score for answer in answers} == {Decimal("0.00")}
    assert submission.total_score == Decimal("0.00")


def test_worker_uses_question_correct_answer_before_conflicting_answer_data() -> None:
    with SessionLocal() as db:
        context = _create_grading_context(db)
        context["mc_question"].correct_answer = "B"
        context["mc_question"].correct_answer_data = {"selected_option": "A"}
        db.add(context["mc_question"])
        db.commit()
        submission = _create_submission_with_answers(db, context, mc_selected="B", tf_value=True)
        job = _create_job(db, context, submission)

    _run_worker(job, context, submission)

    with SessionLocal() as db:
        mc_answer = db.scalar(select(Answer).where(Answer.question_id == context["mc_question_id"]))

    assert mc_answer.auto_score == Decimal("4.00")
    assert mc_answer.final_score == Decimal("4.00")


def test_worker_falls_back_to_legacy_selected_option_when_correct_answer_is_missing() -> None:
    with SessionLocal() as db:
        context = _create_grading_context(db)
        context["mc_question"].correct_answer = None
        context["mc_question"].correct_answer_data = {"selected_option": "c"}
        db.add(context["mc_question"])
        db.commit()
        submission = _create_submission_with_answers(db, context, mc_selected="c", tf_value=True)
        job = _create_job(db, context, submission)

    _run_worker(job, context, submission)

    with SessionLocal() as db:
        mc_answer = db.scalar(select(Answer).where(Answer.question_id == context["mc_question_id"]))

    assert mc_answer.auto_score == Decimal("4.00")
    assert mc_answer.final_score == Decimal("4.00")


def test_worker_falls_back_to_legacy_option_key_when_correct_answer_is_missing() -> None:
    with SessionLocal() as db:
        context = _create_grading_context(db)
        context["mc_question"].correct_answer = None
        context["mc_question"].correct_answer_data = {"option_key": "d"}
        db.add(context["mc_question"])
        db.commit()
        submission = _create_submission_with_answers(db, context, mc_selected="d", tf_value=True)
        job = _create_job(db, context, submission)

    _run_worker(job, context, submission)

    with SessionLocal() as db:
        mc_answer = db.scalar(select(Answer).where(Answer.question_id == context["mc_question_id"]))

    assert mc_answer.auto_score == Decimal("4.00")
    assert mc_answer.final_score == Decimal("4.00")


def test_mixed_objective_subjective_submission_keeps_submitted_status() -> None:
    with SessionLocal() as db:
        context = _create_grading_context(db, include_subjective=True)
        submission = _create_submission_with_answers(db, context, include_subjective=True)
        job = _create_job(db, context, submission)

    _run_worker(job, context, submission)

    with SessionLocal() as db:
        submission = db.get(Submission, submission)
        subjective_answer = db.scalar(
            select(Answer).where(Answer.submission_id == submission.id, Answer.question_id == context["short_answer_id"])
        )

    assert submission.status == SubmissionStatus.SUBMITTED.value
    assert submission.max_score == Decimal("15.00")
    assert subjective_answer.auto_score is None
    assert subjective_answer.final_score is None


def test_worker_does_not_overwrite_teacher_score_and_is_idempotent() -> None:
    with SessionLocal() as db:
        context = _create_grading_context(db)
        submission = _create_submission_with_answers(db, context, mc_selected="A", tf_value=True)
        mc_answer = db.scalar(select(Answer).where(Answer.question_id == context["mc_question_id"]))
        mc_answer.teacher_score = Decimal("3.00")
        mc_answer.final_score = Decimal("3.00")
        db.add(mc_answer)
        db.commit()
        job = _create_job(db, context, submission)

    first = _run_worker(job, context, submission)
    second = _run_worker(job, context, submission)

    with SessionLocal() as db:
        mc_answer = db.scalar(select(Answer).where(Answer.question_id == context["mc_question_id"]))
        submission = db.get(Submission, submission)

    assert first["success"] is True
    assert second["success"] is True
    assert mc_answer.teacher_score == Decimal("3.00")
    assert mc_answer.final_score == Decimal("3.00")
    assert mc_answer.auto_score == Decimal("0.00")
    assert submission.total_score == Decimal("9.00")


def test_worker_fails_job_log_cleanly_when_submission_missing_deleted_or_mismatched() -> None:
    with SessionLocal() as db:
        context = _create_grading_context(db)
        submission = _create_submission_with_answers(db, context)
        stored_submission = db.get(Submission, submission)
        stored_submission.soft_delete()
        db.add(stored_submission)
        db.commit()
        job = _create_job(db, context, submission)

    result = _run_worker(job, context, submission)

    with SessionLocal() as db:
        job = db.get(JobLog, job)

    assert result["success"] is False
    assert job.status == JobStatus.FAILED.value
    assert "Submission not found or mismatched." in job.error_message


def test_no_ai_call_is_made_during_deterministic_grading(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("AI gateway must not be called during deterministic grading.")

    monkeypatch.setattr("app.modules.ai.service.AIService", fail_if_called)

    with SessionLocal() as db:
        context = _create_grading_context(db)
        submission = _create_submission_with_answers(db, context)
        job = _create_job(db, context, submission)

    result = _run_worker(job, context, submission)

    assert result["success"] is True
