from __future__ import annotations

import uuid
from datetime import timedelta
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
from app.modules.grading.models import GradeChangeLog
from app.modules.questions.models import Question
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus


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


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def _create_review_context(
    db,
    *,
    exam_status: str = ExamStatus.REVIEW_REQUIRED.value,
    answer_needs_review: bool = True,
    include_second_answer: bool = True,
    second_final_score: Decimal | None = Decimal("6.00"),
) -> dict:
    teacher = User(
        full_name="Review Teacher",
        email=_email("phase12-teacher"),
        password_hash="not-used",
    )
    db.add(teacher)
    db.flush()

    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"Phase 12 Class {uuid.uuid4().hex[:8]}",
        subject="Math",
    )
    db.add(classroom)
    db.flush()

    student = Student(
        teacher_id=teacher.id,
        full_name="Ali Ahmadi",
        email=_email("phase12-student"),
    )
    db.add(student)
    db.flush()
    db.add(ClassStudent(class_id=classroom.id, student_id=student.id))
    db.flush()

    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Phase 12 Exam {uuid.uuid4().hex[:8]}",
        status=exam_status,
        start_time=_now() - timedelta(minutes=20),
        end_time=_now() + timedelta(hours=1),
        duration_minutes=60,
        total_points=10,
    )
    db.add(exam)
    db.flush()

    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        short_answer_count=1,
        essay_count=1,
        total_question_count=2,
    )
    short_question = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.SHORT_ANSWER.value,
        status=QuestionStatus.CONFIRMED.value,
        text="Explain variables.",
        correct_answer="They represent values.",
        correct_answer_data={"text": "They represent values."},
        expected_answer="Variables represent unknown or changing values.",
        points=4,
        grading_instructions="Award partial credit.",
        order_index=1,
        teacher_confirmed=True,
    )
    essay_question = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.ESSAY.value,
        status=QuestionStatus.CONFIRMED.value,
        text="Explain evidence.",
        expected_answer="Evidence supports claims with reasoning.",
        rubric={"criteria": [{"name": "Reasoning", "points": 6}], "total_points": 6},
        points=6,
        order_index=2,
        teacher_confirmed=True,
    )
    token = ExamToken(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        token=f"phase12-{uuid.uuid4().hex}",
    )
    db.add_all([blueprint, short_question, essay_question, token])
    db.flush()

    submission = Submission(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        token_id=token.id,
        status=SubmissionStatus.NEEDS_REVIEW.value if answer_needs_review else SubmissionStatus.AUTO_GRADED.value,
        started_at=_now() - timedelta(minutes=10),
        submitted_at=_now() - timedelta(minutes=5),
        total_score=Decimal("9.00") if not answer_needs_review else Decimal("8.50"),
        max_score=Decimal("10.00"),
        needs_review_count=1 if answer_needs_review else 0,
    )
    db.add(submission)
    db.flush()

    answer = Answer(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        submission_id=submission.id,
        question_id=short_question.id,
        student_answer="Variables are unknown values.",
        answer_data={"text": "Variables are unknown values."},
        auto_score=Decimal("2.50"),
        final_score=Decimal("2.50"),
        max_score=Decimal("4.00"),
        ai_feedback="Partially correct.",
        ai_confidence=Decimal("0.670"),
        needs_review=answer_needs_review,
        reviewed_by_teacher=False,
    )
    db.add(answer)
    second_answer = None
    if include_second_answer:
        second_answer = Answer(
            teacher_id=teacher.id,
            class_id=classroom.id,
            exam_id=exam.id,
            student_id=student.id,
            submission_id=submission.id,
            question_id=essay_question.id,
            student_answer="Evidence supports a claim.",
            answer_data={"text": "Evidence supports a claim."},
            auto_score=second_final_score,
            final_score=second_final_score,
            max_score=Decimal("6.00"),
            needs_review=False,
            reviewed_by_teacher=False,
        )
        db.add(second_answer)

    db.commit()
    for item in [teacher, classroom, student, exam, short_question, essay_question, submission, answer]:
        db.refresh(item)
    if second_answer is not None:
        db.refresh(second_answer)
    return {
        "teacher": teacher,
        "teacher_id": teacher.id,
        "class_id": classroom.id,
        "exam_id": exam.id,
        "student_id": student.id,
        "submission_id": submission.id,
        "answer_id": answer.id,
        "second_answer_id": second_answer.id if second_answer is not None else None,
        "classroom": classroom,
        "student": student,
        "exam": exam,
        "short_question": short_question,
        "essay_question": essay_question,
        "submission": submission,
        "answer": answer,
        "second_answer": second_answer,
        "cookies": _auth_cookies(teacher.id),
    }


def _review_url(context: dict) -> str:
    return f"/api/v1/classes/{context['class_id']}/exams/{context['exam_id']}/review"


def _answer_review_url(context: dict, answer_id=None) -> str:
    answer_id = answer_id or context["answer_id"]
    return f"/api/v1/classes/{context['class_id']}/exams/{context['exam_id']}/answers/{answer_id}/review"


def _approve_url(context: dict) -> str:
    return f"/api/v1/classes/{context['class_id']}/exams/{context['exam_id']}/approve-results"


def test_grade_change_logs_table_and_indexes_exist() -> None:
    inspector = inspect(engine)
    assert inspector.has_table("grade_change_logs")
    index_names = {index["name"] for index in inspector.get_indexes("grade_change_logs")}
    assert {
        "idx_grade_change_logs_teacher_id",
        "idx_grade_change_logs_class_id",
        "idx_grade_change_logs_exam_id",
        "idx_grade_change_logs_student_id",
        "idx_grade_change_logs_submission_id",
        "idx_grade_change_logs_answer_id",
    }.issubset(index_names)


def test_review_endpoint_requires_teacher_auth() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)

    response = client.get(_review_url(context))

    assert response.status_code == 401


def test_review_endpoint_enforces_teacher_owns_class_and_exam_class_match() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        other_context = _create_review_context(db)

    wrong_teacher_response = client.get(_review_url(context), cookies=other_context["cookies"])
    wrong_class_url = f"/api/v1/classes/{other_context['class_id']}/exams/{context['exam_id']}/review"
    wrong_class_response = client.get(wrong_class_url, cookies=context["cookies"])

    assert wrong_teacher_response.status_code == 404
    assert wrong_teacher_response.json()["error"]["code"] == "CLASS_NOT_FOUND"
    assert wrong_class_response.status_code == 404
    assert wrong_class_response.json()["error"]["code"] == "CLASS_NOT_FOUND"


def test_review_endpoint_returns_summary_submissions_and_teacher_answer_details() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)

    response = client.get(_review_url(context), cookies=context["cookies"])
    data = response.json()["data"]
    answer = data["submissions"][0]["answers"][0]

    assert response.status_code == 200
    assert data["exam"]["status"] == ExamStatus.REVIEW_REQUIRED.value
    assert data["summary"]["submission_count"] == 1
    assert data["summary"]["needs_review_submission_count"] == 1
    assert data["summary"]["needs_review_answer_count"] == 1
    assert data["submissions"][0]["student_full_name"] == "Ali Ahmadi"
    assert answer["correct_answer"] == "They represent values."
    assert answer["correct_answer_data"] == {"text": "They represent values."}
    assert answer["expected_answer"] == "Variables represent unknown or changing values."
    assert answer["grading_instructions"] == "Award partial credit."
    assert answer["ai_feedback"] == "Partially correct."
    assert answer["ai_confidence"] == "0.670"


def test_review_endpoint_excludes_deleted_submissions_and_answers() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        deleted_context = _create_review_context(db)
        deleted_context["submission"].class_id = context["class_id"]
        deleted_context["submission"].exam_id = context["exam_id"]
        deleted_context["answer"].class_id = context["class_id"]
        deleted_context["answer"].exam_id = context["exam_id"]
        deleted_context["submission"].soft_delete()
        deleted_context["answer"].soft_delete()
        context["second_answer"].soft_delete()
        db.add_all([deleted_context["submission"], deleted_context["answer"], context["second_answer"]])
        db.commit()

    response = client.get(_review_url(context), cookies=context["cookies"])
    submissions = response.json()["data"]["submissions"]

    assert response.status_code == 200
    assert len(submissions) == 1
    assert len(submissions[0]["answers"]) == 1


def test_review_answer_updates_scores_flags_feedback_totals_and_grade_change_log() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)

    response = client.put(
        _answer_review_url(context),
        cookies=context["cookies"],
        json={
            "teacher_score": "3.50",
            "feedback": "Good answer, but missing one key detail.",
            "reason": "Adjusted after manual review.",
        },
    )

    with SessionLocal() as db:
        answer = db.get(Answer, context["answer_id"])
        submission = db.get(Submission, context["submission_id"])
        logs = list(db.scalars(select(GradeChangeLog).where(GradeChangeLog.answer_id == answer.id)).all())

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["teacher_score"] == "3.50"
    assert data["final_score"] == "3.50"
    assert data["reviewed_by_teacher"] is True
    assert data["needs_review"] is False
    assert data["submission_total_score"] == "9.50"
    assert data["submission_max_score"] == "10.00"
    assert data["submission_needs_review_count"] == 0
    assert answer.ai_feedback == "Good answer, but missing one key detail."
    assert submission.status == SubmissionStatus.TEACHER_REVIEWED.value
    assert len(logs) == 1
    assert logs[0].old_score == Decimal("2.50")
    assert logs[0].new_score == Decimal("3.50")
    assert logs[0].reason == "Adjusted after manual review."


def test_review_answer_noop_score_does_not_create_grade_change_log() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)

    response = client.put(
        _answer_review_url(context),
        cookies=context["cookies"],
        json={"teacher_score": "2.50", "reason": "No score change."},
    )

    with SessionLocal() as db:
        log_count = len(list(db.scalars(select(GradeChangeLog).where(GradeChangeLog.answer_id == context["answer_id"])).all()))

    assert response.status_code == 200
    assert log_count == 0


def test_review_answer_rejects_score_above_max_score() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)

    response = client.put(
        _answer_review_url(context),
        cookies=context["cookies"],
        json={"teacher_score": "5.00"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_SCORE"


def test_review_answer_rejects_answer_from_another_exam_class_or_teacher() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        other_context = _create_review_context(db)

    response = client.put(
        _answer_review_url(context, answer_id=other_context["answer_id"]),
        cookies=context["cookies"],
        json={"teacher_score": "1.00"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ANSWER_NOT_FOUND"


def test_approve_results_blocks_when_any_answer_still_needs_review() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db, answer_needs_review=True)

    response = client.post(_approve_url(context), cookies=context["cookies"])

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EXAM_NOT_REVIEWABLE"
    assert "needs_review" in response.json()["error"]["details"]


def test_approve_results_blocks_when_final_scores_are_incomplete() -> None:
    with SessionLocal() as db:
        context = _create_review_context(
            db,
            answer_needs_review=False,
            second_final_score=None,
        )

    response = client.post(_approve_url(context), cookies=context["cookies"])

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EXAM_NOT_REVIEWABLE"
    assert "final_scores" in response.json()["error"]["details"]


def test_approve_results_blocks_when_no_submitted_or_graded_submissions_exist() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db)
        context["submission"].status = SubmissionStatus.IN_PROGRESS.value
        db.add(context["submission"])
        db.commit()

    response = client.post(_approve_url(context), cookies=context["cookies"])

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EXAM_NOT_REVIEWABLE"


def test_approve_results_sets_exam_and_submission_approved_without_publishing() -> None:
    with SessionLocal() as db:
        context = _create_review_context(db, answer_needs_review=False)

    response = client.post(_approve_url(context), cookies=context["cookies"])

    with SessionLocal() as db:
        exam = db.get(Exam, context["exam_id"])
        submission = db.get(Submission, context["submission_id"])

    assert response.status_code == 200
    assert response.json()["data"]["status"] == ExamStatus.APPROVED.value
    assert response.json()["data"]["approved_submissions"] == 1
    assert exam.status == ExamStatus.APPROVED.value
    assert submission.status == SubmissionStatus.APPROVED.value
    assert submission.teacher_approved_at is not None
    assert submission.published_at is None
