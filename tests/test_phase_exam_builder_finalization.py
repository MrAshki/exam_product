from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import OperationalError

from app.core.exceptions import AppException
from app.db.session import SessionLocal, engine
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.errors import ExamErrorCode
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.schemas import ExamScheduleRequest
from app.modules.exams.service import ExamService
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.questions.models import Question, QuestionOption
from app.modules.questions.schemas import QuestionUpdate
from app.modules.questions.service import QuestionService
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.errors import SubmissionErrorCode
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.service import SubmissionService
from app.modules.submissions.status import SubmissionStatus
from apps.worker.services.grading_worker_service import DeterministicGradingWorkerService


def _require_db() -> None:
    try:
        with engine.connect():
            return
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is unavailable: {exc}")


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def _create_teacher(db) -> User:
    teacher = User(
        full_name="Builder Teacher",
        email=_email("builder-finalize-teacher"),
        password_hash="not-used",
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def _create_classroom(db, teacher: User) -> Classroom:
    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"Builder Class {uuid.uuid4().hex[:8]}",
        subject="Math",
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def _create_student(db, teacher: User, classroom: Classroom) -> Student:
    student = Student(
        teacher_id=teacher.id,
        full_name=f"Builder Student {uuid.uuid4().hex[:6]}",
        email=_email("builder-finalize-student"),
    )
    db.add(student)
    db.flush()
    db.add(ClassStudent(class_id=classroom.id, student_id=student.id))
    db.commit()
    db.refresh(student)
    return student


def _create_ready_exam(db, teacher: User, classroom: Classroom) -> tuple[Exam, Question]:
    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Finalizable Exam {uuid.uuid4().hex[:8]}",
        total_points=4,
        status=ExamStatus.DRAFT.value,
    )
    db.add(exam)
    db.flush()
    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        multiple_choice_count=1,
        total_question_count=1,
    )
    question = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.MULTIPLE_CHOICE.value,
        order_index=1,
        text="Which option is correct?",
        points=4,
        correct_answer="A",
        correct_answer_data={"selected_option": "A"},
        status=QuestionStatus.DRAFT.value,
        teacher_confirmed=False,
    )
    db.add_all([blueprint, question])
    db.flush()
    db.add_all(
        [
            QuestionOption(
                teacher_id=teacher.id,
                class_id=classroom.id,
                exam_id=exam.id,
                question_id=question.id,
                option_key=key,
                option_text=f"Option {key}",
                is_correct=key == "A",
            )
            for key in ["A", "B", "C", "D"]
        ]
    )
    db.commit()
    db.refresh(exam)
    db.refresh(question)
    return exam, question


def _schedule_exam(db, teacher: User, classroom: Classroom, exam: Exam, *, start_time: datetime, end_time: datetime):
    ExamService(db).finalize(classroom.id, exam.id, teacher)
    ExamService(db).schedule(
        classroom.id,
        exam.id,
        ExamScheduleRequest(start_time=start_time, end_time=end_time, duration_minutes=30),
        teacher,
    )
    token = db.scalar(select(ExamToken).where(ExamToken.exam_id == exam.id, ExamToken.deleted_at.is_(None)))
    db.refresh(exam)
    assert token is not None
    return token


def test_readiness_reports_ready_draft_exam_and_finalize_marks_questions_confirmed() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        exam, question = _create_ready_exam(db, teacher, classroom)

        readiness = ExamService(db).get_readiness(classroom.id, exam.id, teacher)
        result = ExamService(db).finalize(classroom.id, exam.id, teacher)
        db.refresh(question)

    assert readiness["is_ready"] is True
    assert readiness["finalization_allowed"] is True
    assert result["status"] == ExamStatus.FINALIZED.value
    assert question.status == QuestionStatus.CONFIRMED.value
    assert question.teacher_confirmed is True


def test_schedule_requires_finalized_exam_even_if_questions_are_ready() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        exam, _question = _create_ready_exam(db, teacher, classroom)

        with pytest.raises(AppException) as exc_info:
            ExamService(db).schedule(
                classroom.id,
                exam.id,
                payload=ExamScheduleRequest(
                    start_time="2026-07-10T10:00:00Z",
                    end_time="2026-07-10T11:00:00Z",
                    duration_minutes=30,
                ),
                teacher=teacher,
            )

    assert exc_info.value.code == ExamErrorCode.EXAM_NOT_FINALIZED


def test_legacy_confirmed_question_can_be_edited_while_exam_is_draft() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        exam, question = _create_ready_exam(db, teacher, classroom)
        question.status = QuestionStatus.CONFIRMED.value
        question.teacher_confirmed = True
        db.add(question)
        db.commit()

        updated = QuestionService(db).update(
            classroom.id,
            exam.id,
            question.id,
            QuestionUpdate(text="Updated text", points=4),
            teacher,
        )

    assert updated.text == "Updated text"
    assert updated.status == QuestionStatus.DRAFT.value
    assert updated.teacher_confirmed is False


def test_finalized_exam_locks_question_editing_and_can_reopen_before_tokens() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        exam, question = _create_ready_exam(db, teacher, classroom)
        ExamService(db).finalize(classroom.id, exam.id, teacher)

        with pytest.raises(AppException) as exc_info:
            QuestionService(db).update(
                classroom.id,
                exam.id,
                question.id,
                QuestionUpdate(text="Blocked edit", points=4),
                teacher,
            )

        reopened = ExamService(db).reopen(classroom.id, exam.id, teacher)
        db.refresh(question)

    assert exc_info.value.code == ExamErrorCode.EXAM_NOT_DRAFT
    assert reopened["status"] == ExamStatus.DRAFT.value
    assert question.status == QuestionStatus.DRAFT.value
    assert question.teacher_confirmed is False


def test_reopen_rejects_exam_with_active_tokens() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        student = _create_student(db, teacher, classroom)
        exam, _question = _create_ready_exam(db, teacher, classroom)
        ExamService(db).finalize(classroom.id, exam.id, teacher)
        db.add(
            ExamToken(
                teacher_id=teacher.id,
                class_id=classroom.id,
                exam_id=exam.id,
                student_id=student.id,
                token=f"token-{uuid.uuid4().hex}",
            )
        )
        db.commit()

        with pytest.raises(AppException) as exc_info:
            ExamService(db).reopen(classroom.id, exam.id, teacher)

    assert exc_info.value.code == ExamErrorCode.EXAM_HAS_TOKENS


def test_scheduled_exam_before_start_reopens_and_invalidates_tokens() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        _student = _create_student(db, teacher, classroom)
        exam, question = _create_ready_exam(db, teacher, classroom)
        start_time = datetime.now(timezone.utc) + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)
        token = _schedule_exam(db, teacher, classroom, exam, start_time=start_time, end_time=end_time)
        token_value = token.token

        reopened = ExamService(db).reopen(classroom.id, exam.id, teacher)
        db.refresh(question)
        db.refresh(token)
        db.refresh(exam)

        with pytest.raises(AppException) as exc_info:
            SubmissionService(db).get_access_state(token_value)

    assert reopened["previous_status"] == ExamStatus.SCHEDULED.value
    assert reopened["status"] == ExamStatus.DRAFT.value
    assert reopened["invalidated_token_count"] == 1
    assert exam.start_time is None
    assert exam.end_time is None
    assert exam.duration_minutes == 30
    assert token.deleted_at is not None
    assert question.text == "Which option is correct?"
    assert question.status == QuestionStatus.DRAFT.value
    assert question.teacher_confirmed is False
    assert exc_info.value.code == SubmissionErrorCode.INVALID_EXAM_TOKEN


def test_scheduled_exam_at_exact_start_time_cannot_reopen_and_state_is_unchanged(monkeypatch) -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        _student = _create_student(db, teacher, classroom)
        exam, question = _create_ready_exam(db, teacher, classroom)
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        token = _schedule_exam(db, teacher, classroom, exam, start_time=start_time, end_time=end_time)
        monkeypatch.setattr(ExamService, "_now", staticmethod(lambda: start_time))

        with pytest.raises(AppException) as exc_info:
            ExamService(db).reopen(classroom.id, exam.id, teacher)

        db.refresh(exam)
        db.refresh(question)
        db.refresh(token)

    assert exc_info.value.code == ExamErrorCode.EXAM_IN_PROGRESS
    assert exam.status == ExamStatus.SCHEDULED.value
    assert token.deleted_at is None
    assert question.status == QuestionStatus.CONFIRMED.value
    assert question.teacher_confirmed is True


def test_ended_scheduled_exam_without_submissions_reopens_and_invalidates_tokens() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        _student = _create_student(db, teacher, classroom)
        exam, _question = _create_ready_exam(db, teacher, classroom)
        end_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        start_time = end_time - timedelta(hours=1)
        token = _schedule_exam(db, teacher, classroom, exam, start_time=start_time, end_time=end_time)

        reopened = ExamService(db).reopen(classroom.id, exam.id, teacher)
        db.refresh(token)

    assert reopened["status"] == ExamStatus.DRAFT.value
    assert reopened["invalidated_token_count"] == 1
    assert token.deleted_at is not None


def test_scheduled_exam_with_any_submission_cannot_reopen_and_tokens_stay_active() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        student = _create_student(db, teacher, classroom)
        exam, _question = _create_ready_exam(db, teacher, classroom)
        start_time = datetime.now(timezone.utc) + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)
        token = _schedule_exam(db, teacher, classroom, exam, start_time=start_time, end_time=end_time)
        db.add(
            Submission(
                teacher_id=teacher.id,
                class_id=classroom.id,
                exam_id=exam.id,
                student_id=student.id,
                token_id=token.id,
                status=SubmissionStatus.NOT_STARTED.value,
            )
        )
        db.commit()

        with pytest.raises(AppException) as exc_info:
            ExamService(db).reopen(classroom.id, exam.id, teacher)

        db.refresh(exam)
        db.refresh(token)

    assert exc_info.value.code == ExamErrorCode.EXAM_HAS_SUBMISSIONS
    assert exam.status == ExamStatus.SCHEDULED.value
    assert token.deleted_at is None


def test_draft_and_malformed_scheduled_exam_reopen_fail_safely() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        draft_exam, _question = _create_ready_exam(db, teacher, classroom)

        with pytest.raises(AppException) as draft_exc:
            ExamService(db).reopen(classroom.id, draft_exam.id, teacher)

        malformed_exam, _other_question = _create_ready_exam(db, teacher, classroom)
        malformed_exam.status = ExamStatus.SCHEDULED.value
        malformed_exam.start_time = None
        malformed_exam.end_time = None
        db.add(malformed_exam)
        db.commit()

        with pytest.raises(AppException) as malformed_exc:
            ExamService(db).reopen(classroom.id, malformed_exam.id, teacher)

    assert draft_exc.value.code == ExamErrorCode.EXAM_ALREADY_DRAFT
    assert malformed_exc.value.code == ExamErrorCode.EXAM_SCHEDULE_INVALID


def test_points_columns_are_numeric_8_2_after_migration() -> None:
    _require_db()
    inspector = inspect(engine)
    exam_total = next(column for column in inspector.get_columns("exams") if column["name"] == "total_points")
    question_points = next(column for column in inspector.get_columns("questions") if column["name"] == "points")

    assert exam_total["type"].precision == 8
    assert exam_total["type"].scale == 2
    assert question_points["type"].precision == 8
    assert question_points["type"].scale == 2


def test_decimal_points_readiness_matches_exact_sum_and_finalizes() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        exam, question = _create_ready_exam(db, teacher, classroom)
        exam.total_points = Decimal("2.75")
        question.points = Decimal("2.50")
        db.add_all([exam, question])
        db.flush()
        second = Question(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            type=QuestionType.TRUE_FALSE.value,
            order_index=2,
            text="Decimals are supported.",
            points=Decimal("0.25"),
            correct_answer="true",
            status=QuestionStatus.DRAFT.value,
        )
        blueprint = db.scalar(select(ExamBlueprint).where(ExamBlueprint.exam_id == exam.id))
        blueprint.multiple_choice_count = 1
        blueprint.true_false_count = 1
        blueprint.total_question_count = 2
        db.add_all([blueprint, second])
        db.commit()

        readiness = ExamService(db).get_readiness(classroom.id, exam.id, teacher)
        result = ExamService(db).finalize(classroom.id, exam.id, teacher)

    assert readiness["is_ready"] is True
    assert readiness["calculated_question_points"] == Decimal("2.75")
    assert readiness["exam_total_points"] == Decimal("2.75")
    assert result["status"] == ExamStatus.FINALIZED.value


def test_decimal_points_mismatch_blocks_finalization_without_mutation() -> None:
    _require_db()
    with SessionLocal() as db:
        teacher = _create_teacher(db)
        classroom = _create_classroom(db, teacher)
        exam, question = _create_ready_exam(db, teacher, classroom)
        exam.total_points = Decimal("2.51")
        question.points = Decimal("2.50")
        db.add_all([exam, question])
        db.commit()

        with pytest.raises(AppException) as exc_info:
            ExamService(db).finalize(classroom.id, exam.id, teacher)

        db.refresh(exam)
        db.refresh(question)

    assert exc_info.value.code == ExamErrorCode.EXAM_NOT_READY
    assert exc_info.value.details["readiness"]["points_match"] is False
    assert exam.status == ExamStatus.DRAFT.value
    assert question.teacher_confirmed is False


def test_decimal_objective_grading_awards_decimal_points() -> None:
    question = Question(type=QuestionType.MULTIPLE_CHOICE.value, points=Decimal("2.50"), correct_answer="B")
    answer = Answer(answer_data={"selected_option": "B"})

    score = DeterministicGradingWorkerService._score_objective_answer(question, answer)

    assert score == Decimal("2.50")
