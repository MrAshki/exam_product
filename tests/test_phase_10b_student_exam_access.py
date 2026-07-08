from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.main import app
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.jobs.models import JobLog
from app.modules.questions.models import Question, QuestionOption
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus
from app.db.session import SessionLocal, engine


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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _create_context(
    db,
    *,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    duration_minutes: int = 60,
) -> dict:
    now = _now()
    teacher = User(
        full_name="Grace Teacher",
        email=_email("phase10b-teacher"),
        password_hash="not-used-in-tests",
    )
    db.add(teacher)
    db.flush()

    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"Exam Access Class {uuid.uuid4().hex[:8]}",
        subject="Math",
    )
    db.add(classroom)
    db.flush()

    student = Student(
        teacher_id=teacher.id,
        full_name="Ali Ahmadi",
        email=_email("phase10b-student"),
    )
    db.add(student)
    db.flush()
    membership = ClassStudent(class_id=classroom.id, student_id=student.id)
    db.add(membership)
    db.flush()

    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Algebra Test {uuid.uuid4().hex[:8]}",
        status=ExamStatus.SCHEDULED.value,
        start_time=start_time or now - timedelta(minutes=5),
        end_time=end_time or now + timedelta(hours=1),
        duration_minutes=duration_minutes,
        total_points=12,
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
    multiple_choice = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.MULTIPLE_CHOICE.value,
        status=QuestionStatus.CONFIRMED.value,
        text="What is 2 + 2?",
        correct_answer="B",
        points=2,
        order_index=1,
        teacher_confirmed=True,
    )
    short_answer = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.SHORT_ANSWER.value,
        status=QuestionStatus.CONFIRMED.value,
        text="What do variables represent?",
        expected_answer="Variables represent unknown values.",
        points=10,
        order_index=2,
        teacher_confirmed=True,
    )
    token = ExamToken(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        token=f"phase10b-{uuid.uuid4().hex}",
        expires_at=exam.end_time,
    )
    db.add_all([blueprint, multiple_choice, short_answer, token])
    db.flush()
    db.add_all(
        [
            QuestionOption(
                teacher_id=teacher.id,
                class_id=classroom.id,
                exam_id=exam.id,
                question_id=multiple_choice.id,
                option_key="A",
                option_text="3",
                is_correct=False,
            ),
            QuestionOption(
                teacher_id=teacher.id,
                class_id=classroom.id,
                exam_id=exam.id,
                question_id=multiple_choice.id,
                option_key="B",
                option_text="4",
                is_correct=True,
            ),
        ]
    )
    db.commit()
    for instance in [
        teacher,
        classroom,
        student,
        membership,
        exam,
        multiple_choice,
        short_answer,
        token,
    ]:
        db.refresh(instance)
    return {
        "teacher": teacher,
        "classroom": classroom,
        "student": student,
        "membership": membership,
        "exam": exam,
        "multiple_choice": multiple_choice,
        "short_answer": short_answer,
        "token": token,
    }


def _start(token: str):
    return client.post(f"/api/v1/exam/access/{token}/start")


def _submit(token: str, answers: list[dict]):
    return client.post(f"/api/v1/exam/access/{token}/submit", json={"answers": answers})


def test_get_access_with_valid_token_before_start_returns_waiting() -> None:
    with SessionLocal() as db:
        context = _create_context(db, start_time=_now() + timedelta(hours=1), end_time=_now() + timedelta(hours=2))
        token = context["token"].token

    response = client.get(f"/api/v1/exam/access/{token}")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "waiting"


def test_get_access_with_valid_token_during_active_window_returns_ready() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        token = context["token"].token

    response = client.get(f"/api/v1/exam/access/{token}")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ready"


def test_get_access_with_invalid_token_returns_invalid_exam_token() -> None:
    response = client.get("/api/v1/exam/access/not-a-real-token")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_EXAM_TOKEN"


def test_access_and_start_payloads_do_not_expose_teacher_only_answer_fields() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        token = context["token"].token

    access_response = client.get(f"/api/v1/exam/access/{token}")
    start_response = _start(token)
    combined_text = f"{access_response.text} {start_response.text}"

    for forbidden in ["correct_answer", "correct_answer_data", "expected_answer", "rubric", "grading_instructions"]:
        assert forbidden not in combined_text


def test_post_start_before_start_time_is_rejected() -> None:
    with SessionLocal() as db:
        context = _create_context(db, start_time=_now() + timedelta(hours=1), end_time=_now() + timedelta(hours=2))
        token = context["token"].token

    response = _start(token)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EXAM_NOT_ACTIVE"


def test_post_start_during_active_window_creates_submission_in_progress() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        token = context["token"].token
        exam_id = context["exam"].id
        student_id = context["student"].id

    response = _start(token)

    with SessionLocal() as db:
        submission = db.scalar(
            select(Submission).where(
                Submission.exam_id == exam_id,
                Submission.student_id == student_id,
                Submission.deleted_at.is_(None),
            )
        )

    assert response.status_code == 200
    assert submission.status == SubmissionStatus.IN_PROGRESS.value
    assert submission.started_at is not None


def test_post_start_returns_existing_in_progress_submission_if_called_again() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        token = context["token"].token

    first = _start(token)
    second = _start(token)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"]["submission_id"] == first.json()["data"]["submission_id"]


def test_post_start_rejects_already_submitted_submission() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        token = context["token"].token

    _start(token)
    _submit(
        token,
        [
            {
                "question_id": str(context["multiple_choice"].id),
                "student_answer": "B",
                "answer_data": {"selected_option": "B"},
            }
        ],
    )
    response = _start(token)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EXAM_ALREADY_SUBMITTED"


def test_post_start_question_payload_includes_options_without_is_correct() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        token = context["token"].token

    response = _start(token)
    first_question = response.json()["data"]["questions"][0]

    assert first_question["type"] == QuestionType.MULTIPLE_CHOICE.value
    assert first_question["options"] == [
        {"option_key": "A", "option_text": "3"},
        {"option_key": "B", "option_text": "4"},
    ]
    assert "is_correct" not in response.text


def test_post_submit_saves_answers_and_sets_submission_submitted() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        token = context["token"].token
        exam_id = context["exam"].id
        student_id = context["student"].id

    _start(token)
    response = _submit(
        token,
        [
            {
                "question_id": str(context["multiple_choice"].id),
                "student_answer": "B",
                "answer_data": {"selected_option": "B"},
            },
            {
                "question_id": str(context["short_answer"].id),
                "student_answer": "Variables represent unknown values.",
                "answer_data": {"text": "Variables represent unknown values."},
            },
        ],
    )

    with SessionLocal() as db:
        submission = db.scalar(select(Submission).where(Submission.exam_id == exam_id, Submission.student_id == student_id))
        answers = list(db.scalars(select(Answer).where(Answer.submission_id == submission.id)).all())

    assert response.status_code == 200
    assert submission.status == SubmissionStatus.SUBMITTED.value
    assert submission.submitted_at is not None
    assert len(answers) == 2
    assert {answer.max_score for answer in answers} == {2, 10}


def test_post_submit_rejects_duplicate_submit() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        token = context["token"].token

    _start(token)
    answer_payload = [
        {
            "question_id": str(context["multiple_choice"].id),
            "student_answer": "B",
            "answer_data": {"selected_option": "B"},
        }
    ]
    first = _submit(token, answer_payload)
    second = _submit(token, answer_payload)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "EXAM_ALREADY_SUBMITTED"


def test_post_submit_rejects_answer_question_id_from_another_exam() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        other_context = _create_context(db)
        token = context["token"].token
        other_question_id = other_context["multiple_choice"].id

    _start(token)
    response = _submit(
        token,
        [{"question_id": str(other_question_id), "student_answer": "B", "answer_data": {"selected_option": "B"}}],
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "QUESTION_NOT_FOUND"


def test_post_submit_rejects_unconfirmed_question() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        context["short_answer"].status = QuestionStatus.DRAFT.value
        context["short_answer"].teacher_confirmed = False
        db.add(context["short_answer"])
        db.commit()
        token = context["token"].token
        question_id = context["short_answer"].id

    _start(token)
    response = _submit(
        token,
        [{"question_id": str(question_id), "student_answer": "x", "answer_data": {"text": "x"}}],
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "QUESTION_NOT_CONFIRMED"


def test_post_submit_rejects_expired_session_by_backend_timing() -> None:
    with SessionLocal() as db:
        context = _create_context(db, start_time=_now() - timedelta(hours=1), end_time=_now() + timedelta(hours=1), duration_minutes=5)
        submission = Submission(
            teacher_id=context["teacher"].id,
            class_id=context["classroom"].id,
            exam_id=context["exam"].id,
            student_id=context["student"].id,
            token_id=context["token"].id,
            status=SubmissionStatus.IN_PROGRESS.value,
            started_at=_now() - timedelta(minutes=30),
        )
        db.add(submission)
        db.commit()
        token = context["token"].token
        question_id = context["multiple_choice"].id

    response = _submit(
        token,
        [{"question_id": str(question_id), "student_answer": "B", "answer_data": {"selected_option": "B"}}],
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EXAM_TIME_EXPIRED"


def test_post_submit_does_not_grade_answers_yet() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        token = context["token"].token
        exam_id = context["exam"].id

    _start(token)
    _submit(
        token,
        [
            {
                "question_id": str(context["multiple_choice"].id),
                "student_answer": "B",
                "answer_data": {"selected_option": "B"},
            }
        ],
    )

    with SessionLocal() as db:
        answer = db.scalar(select(Answer).where(Answer.exam_id == exam_id))
        submission = db.scalar(select(Submission).where(Submission.exam_id == exam_id))
        jobs = list(db.scalars(select(JobLog).where(JobLog.exam_id == exam_id)).all())

    assert answer.auto_score is None
    assert answer.teacher_score is None
    assert answer.final_score is None
    assert submission.total_score is None
    assert jobs == []


def test_token_cannot_access_another_students_submission() -> None:
    with SessionLocal() as db:
        context = _create_context(db)
        other_student = Student(
            teacher_id=context["teacher"].id,
            full_name="Other Student",
            email=_email("phase10b-other-student"),
        )
        db.add(other_student)
        db.flush()
        db.add(ClassStudent(class_id=context["classroom"].id, student_id=other_student.id))
        other_token = ExamToken(
            teacher_id=context["teacher"].id,
            class_id=context["classroom"].id,
            exam_id=context["exam"].id,
            student_id=other_student.id,
            token=f"phase10b-other-{uuid.uuid4().hex}",
        )
        db.add(other_token)
        db.commit()
        token = context["token"].token
        other_token_value = other_token.token
        question_id = context["multiple_choice"].id

    _start(token)
    response = _submit(
        other_token_value,
        [{"question_id": str(question_id), "student_answer": "B", "answer_data": {"selected_option": "B"}}],
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SUBMISSION_NOT_FOUND"


def test_soft_deleted_token_class_exam_or_membership_is_rejected() -> None:
    mutators = [
        lambda context: context["token"].soft_delete(),
        lambda context: context["classroom"].soft_delete(),
        lambda context: context["exam"].soft_delete(),
        lambda context: context["membership"].soft_delete(),
    ]

    for mutator in mutators:
        with SessionLocal() as db:
            context = _create_context(db)
            token = context["token"].token
            mutator(context)
            db.commit()

        response = client.get(f"/api/v1/exam/access/{token}")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "INVALID_EXAM_TOKEN"
