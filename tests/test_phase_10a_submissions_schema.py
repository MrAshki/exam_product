from __future__ import annotations

import subprocess
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db.session import SessionLocal, engine
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.status import QuestionStatus, QuestionType
from app.modules.questions.models import Question
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.repository import SubmissionRepository
from app.modules.submissions.status import SubmissionStatus


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def _require_db() -> None:
    try:
        with engine.connect():
            return
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is unavailable: {exc}")


def _create_context(db) -> dict:
    teacher = User(
        full_name="Grace Teacher",
        email=_email("phase10a-teacher"),
        password_hash="not-used-in-tests",
    )
    db.add(teacher)
    db.flush()

    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"Submissions Math {uuid.uuid4().hex[:8]}",
        subject="Math",
    )
    db.add(classroom)
    db.flush()

    student = Student(
        teacher_id=teacher.id,
        full_name="Ada Student",
        email=_email("phase10a-student"),
    )
    db.add(student)
    db.flush()
    db.add(ClassStudent(class_id=classroom.id, student_id=student.id))
    db.flush()

    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Submissions Exam {uuid.uuid4().hex[:8]}",
        total_points=10,
    )
    db.add(exam)
    db.flush()

    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        short_answer_count=1,
        total_question_count=1,
    )
    question = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.SHORT_ANSWER.value,
        status=QuestionStatus.CONFIRMED.value,
        text="What is x?",
        expected_answer="An unknown number.",
        points=10,
        order_index=1,
        teacher_confirmed=True,
    )
    token = ExamToken(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        token=f"phase10a-{uuid.uuid4().hex}",
    )
    db.add_all([blueprint, question, token])
    db.commit()

    for instance in [teacher, classroom, student, exam, blueprint, question, token]:
        db.refresh(instance)

    return {
        "teacher": teacher,
        "classroom": classroom,
        "student": student,
        "exam": exam,
        "blueprint": blueprint,
        "question": question,
        "token": token,
    }


def _create_submission(db, context: dict) -> Submission:
    submission = Submission(
        teacher_id=context["teacher"].id,
        class_id=context["classroom"].id,
        exam_id=context["exam"].id,
        student_id=context["student"].id,
        token_id=context["token"].id,
        max_score=Decimal("10.00"),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def _create_answer(db, context: dict, submission: Submission, answer_data: dict | None = None) -> Answer:
    answer = Answer(
        teacher_id=context["teacher"].id,
        class_id=context["classroom"].id,
        exam_id=context["exam"].id,
        student_id=context["student"].id,
        submission_id=submission.id,
        question_id=context["question"].id,
        student_answer="An unknown number.",
        answer_data=answer_data,
        max_score=Decimal("10.00"),
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def test_submissions_table_exists_after_migration() -> None:
    _require_db()
    assert inspect(engine).has_table("submissions")


def test_answers_table_exists_after_migration() -> None:
    _require_db()
    assert inspect(engine).has_table("answers")


def test_submissions_has_required_indexes() -> None:
    _require_db()
    index_names = {index["name"] for index in inspect(engine).get_indexes("submissions")}
    assert {
        "idx_submissions_teacher_id",
        "idx_submissions_class_id",
        "idx_submissions_exam_id",
        "idx_submissions_student_id",
        "idx_submissions_exam_student",
        "idx_submissions_status",
        "idx_submissions_deleted_at",
        "uq_submissions_exam_student_active",
    }.issubset(index_names)


def test_answers_has_required_indexes() -> None:
    _require_db()
    index_names = {index["name"] for index in inspect(engine).get_indexes("answers")}
    assert {
        "idx_answers_teacher_id",
        "idx_answers_class_id",
        "idx_answers_exam_id",
        "idx_answers_student_id",
        "idx_answers_submission_id",
        "idx_answers_question_id",
        "idx_answers_needs_review",
        "idx_answers_deleted_at",
        "uq_answers_submission_question_active",
    }.issubset(index_names)


def test_unique_active_submission_per_exam_student_is_enforced() -> None:
    _require_db()
    with SessionLocal() as db:
        context = _create_context(db)
        _create_submission(db, context)
        duplicate = Submission(
            teacher_id=context["teacher"].id,
            class_id=context["classroom"].id,
            exam_id=context["exam"].id,
            student_id=context["student"].id,
            token_id=context["token"].id,
        )
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.commit()


def test_soft_deleted_submission_allows_new_active_submission_for_same_exam_student() -> None:
    _require_db()
    with SessionLocal() as db:
        context = _create_context(db)
        submission = _create_submission(db, context)
        submission.soft_delete()
        db.add(submission)
        db.commit()

        replacement = _create_submission(db, context)
        original_id = submission.id
        replacement_id = replacement.id
        replacement_deleted_at = replacement.deleted_at

    assert replacement_id != original_id
    assert replacement_deleted_at is None


def test_unique_active_answer_per_submission_question_is_enforced() -> None:
    _require_db()
    with SessionLocal() as db:
        context = _create_context(db)
        submission = _create_submission(db, context)
        _create_answer(db, context, submission)
        duplicate = Answer(
            teacher_id=context["teacher"].id,
            class_id=context["classroom"].id,
            exam_id=context["exam"].id,
            student_id=context["student"].id,
            submission_id=submission.id,
            question_id=context["question"].id,
        )
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.commit()


def test_soft_deleted_answer_allows_new_active_answer_for_same_submission_question() -> None:
    _require_db()
    with SessionLocal() as db:
        context = _create_context(db)
        submission = _create_submission(db, context)
        answer = _create_answer(db, context, submission)
        answer.soft_delete()
        db.add(answer)
        db.commit()

        replacement = _create_answer(db, context, submission)
        original_id = answer.id
        replacement_id = replacement.id
        replacement_deleted_at = replacement.deleted_at

    assert replacement_id != original_id
    assert replacement_deleted_at is None


def test_answer_data_jsonb_stores_selected_option_for_multiple_choice() -> None:
    _require_db()
    with SessionLocal() as db:
        context = _create_context(db)
        submission = _create_submission(db, context)
        answer = _create_answer(db, context, submission, {"selected_option": "B"})
        fetched = db.get(Answer, answer.id)

    assert fetched.answer_data["selected_option"] == "B"


@pytest.mark.parametrize("answer_data", [{"text": "It is an unknown number."}, {"text": "Student essay answer here"}])
def test_answer_data_jsonb_stores_text_for_written_answers(answer_data: dict) -> None:
    _require_db()
    with SessionLocal() as db:
        context = _create_context(db)
        submission = _create_submission(db, context)
        answer = _create_answer(db, context, submission, answer_data)
        fetched = db.get(Answer, answer.id)

    assert fetched.answer_data["text"] == answer_data["text"]


def test_repository_can_create_and_fetch_submission() -> None:
    _require_db()
    with SessionLocal() as db:
        context = _create_context(db)
        repository = SubmissionRepository(db)
        submission = repository.create_submission(
            teacher_id=context["teacher"].id,
            class_id=context["classroom"].id,
            exam_id=context["exam"].id,
            student_id=context["student"].id,
            token_id=context["token"].id,
            max_score=Decimal("10.00"),
        )
        fetched_by_id = repository.get_submission_by_id(submission.id)
        fetched_active = repository.get_active_submission_for_exam_student(
            context["exam"].id,
            context["student"].id,
        )

    assert submission.status == SubmissionStatus.NOT_STARTED.value
    assert fetched_by_id.id == submission.id
    assert fetched_active.id == submission.id


def test_repository_can_create_and_list_answers_for_submission() -> None:
    _require_db()
    with SessionLocal() as db:
        context = _create_context(db)
        repository = SubmissionRepository(db)
        submission = _create_submission(db, context)
        answer = repository.create_answer(
            teacher_id=context["teacher"].id,
            class_id=context["classroom"].id,
            exam_id=context["exam"].id,
            student_id=context["student"].id,
            submission_id=submission.id,
            question_id=context["question"].id,
            answer_data={"text": "It is an unknown number."},
            max_score=Decimal("10.00"),
        )
        answers = repository.list_answers_by_submission(submission.id)

    assert [item.id for item in answers] == [answer.id]
    assert answers[0].answer_data["text"] == "It is an unknown number."


def test_alembic_check_remains_clean() -> None:
    _require_db()
    result = subprocess.run(
        ["alembic", "check"],
        cwd="D:\\exam\\apps\\api",
        check=False,
        capture_output=True,
        text=True,
    )
    combined_output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0
    assert "No new upgrade operations detected." in combined_output
