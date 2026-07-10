from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import SessionLocal, engine
from app.main import app
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.questions.models import Question, QuestionOption
from app.modules.students.models import ClassStudent, Student


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


def _create_builder_context(db, *, scheduled: bool = False) -> dict:
    teacher = User(
        full_name="Builder Teacher",
        email=_email("phase15c-teacher"),
        password_hash="not-used",
    )
    db.add(teacher)
    db.flush()

    classroom = Classroom(
        teacher_id=teacher.id,
        title=f"Builder Class {uuid.uuid4().hex[:8]}",
        subject="Literature",
    )
    db.add(classroom)
    db.flush()

    student = Student(
        teacher_id=teacher.id,
        full_name="Builder Student",
        email=_email("phase15c-student"),
    )
    db.add(student)
    db.flush()
    membership = ClassStudent(class_id=classroom.id, student_id=student.id)
    db.add(membership)
    db.flush()

    exam = Exam(
        teacher_id=teacher.id,
        class_id=classroom.id,
        title=f"Builder Exam {uuid.uuid4().hex[:8]}",
        status=ExamStatus.SCHEDULED.value if scheduled else ExamStatus.DRAFT.value,
        start_time=_now() - timedelta(minutes=5) if scheduled else None,
        end_time=_now() + timedelta(hours=1) if scheduled else None,
        duration_minutes=60 if scheduled else None,
        total_points=12,
    )
    db.add(exam)
    db.flush()

    blueprint = ExamBlueprint(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        multiple_choice_count=1,
        essay_count=1,
        total_question_count=2,
    )
    multiple_choice = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.MULTIPLE_CHOICE.value,
        status=QuestionStatus.EMPTY.value,
        order_index=1,
    )
    essay = Question(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        type=QuestionType.ESSAY.value,
        status=QuestionStatus.EMPTY.value,
        order_index=2,
    )
    token = ExamToken(
        teacher_id=teacher.id,
        class_id=classroom.id,
        exam_id=exam.id,
        student_id=student.id,
        token=f"phase15c-{uuid.uuid4().hex}",
        expires_at=exam.end_time,
    )
    db.add_all([blueprint, multiple_choice, essay, token])
    db.commit()

    for instance in [teacher, classroom, student, membership, exam, multiple_choice, essay, token]:
        db.refresh(instance)

    return {
        "teacher": teacher,
        "classroom": classroom,
        "exam": exam,
        "multiple_choice": multiple_choice,
        "essay": essay,
        "token": token,
        "teacher_id": teacher.id,
        "class_id": classroom.id,
        "exam_id": exam.id,
        "multiple_choice_id": multiple_choice.id,
        "essay_id": essay.id,
        "token_value": token.token,
        "cookies": _auth_cookies(teacher.id),
    }


def _questions_url(context: dict) -> str:
    return f"/api/v1/classes/{context['class_id']}/exams/{context['exam_id']}/questions/"


def test_teacher_question_list_returns_full_saved_draft_fields_and_options() -> None:
    with SessionLocal() as db:
        context = _create_builder_context(db)

    multiple_choice_id = context["multiple_choice_id"]
    essay_id = context["essay_id"]

    update_mc_response = client.put(
        f"{_questions_url(context)}{multiple_choice_id}",
        cookies=context["cookies"],
        json={
            "text": "Which option is correct?",
            "points": 4,
            "correct_answer": "b",
            "correct_answer_data": {"option_key": "b"},
            "options": [
                {"option_key": "a", "option_text": "First option", "is_correct": False},
                {"option_key": "b", "option_text": "Second option", "is_correct": True},
                {"option_key": "c", "option_text": "Third option", "is_correct": False},
                {"option_key": "d", "option_text": "Fourth option", "is_correct": False},
            ],
        },
    )
    assert update_mc_response.status_code == 200

    update_essay_response = client.put(
        f"{_questions_url(context)}{essay_id}",
        cookies=context["cookies"],
        json={
            "text": "Explain the central theme.",
            "points": 8,
            "expected_answer": "A complete answer explains the central theme with evidence.",
            "grading_instructions": "Reward textual evidence.",
            "rubric": {"criteria": [{"name": "Evidence", "points": 4}], "total_points": 8},
            "rubric_teacher_confirmed": True,
        },
    )
    assert update_essay_response.status_code == 200

    with SessionLocal() as db:
        saved_essay = db.get(Question, essay_id)
        saved_essay.rubric_ai_suggested = {"criteria": [{"name": "AI suggestion", "points": 8}], "total_points": 8}
        db.add(saved_essay)
        db.commit()

    list_response = client.get(_questions_url(context), cookies=context["cookies"])

    assert list_response.status_code == 200
    questions = list_response.json()["data"]
    by_id = {question["id"]: question for question in questions}
    listed_mc = by_id[str(multiple_choice_id)]
    listed_essay = by_id[str(essay_id)]

    assert listed_mc["class_id"] == str(context["class_id"])
    assert listed_mc["exam_id"] == str(context["exam_id"])
    assert listed_mc["text"] == "Which option is correct?"
    assert listed_mc["points"] == 4
    assert listed_mc["correct_answer"] == "b"
    assert listed_mc["correct_answer_data"] == {"option_key": "b"}
    assert listed_mc["options"] == [
        {"id": listed_mc["options"][0]["id"], "option_key": "a", "option_text": "First option", "is_correct": False},
        {"id": listed_mc["options"][1]["id"], "option_key": "b", "option_text": "Second option", "is_correct": True},
        {"id": listed_mc["options"][2]["id"], "option_key": "c", "option_text": "Third option", "is_correct": False},
        {"id": listed_mc["options"][3]["id"], "option_key": "d", "option_text": "Fourth option", "is_correct": False},
    ]

    assert listed_essay["expected_answer"] == "A complete answer explains the central theme with evidence."
    assert listed_essay["grading_instructions"] == "Reward textual evidence."
    assert listed_essay["rubric"] == {"criteria": [{"name": "Evidence", "points": 4}], "total_points": 8}
    assert listed_essay["rubric_ai_suggested"] == {
        "criteria": [{"name": "AI suggestion", "points": 8}],
        "total_points": 8,
    }
    assert listed_essay["rubric_teacher_confirmed"] is True


def test_teacher_question_list_can_include_correct_answers_but_public_start_does_not() -> None:
    with SessionLocal() as db:
        context = _create_builder_context(db, scheduled=True)
        multiple_choice = context["multiple_choice"]
        essay = context["essay"]

        multiple_choice.status = QuestionStatus.CONFIRMED.value
        multiple_choice.teacher_confirmed = True
        multiple_choice.text = "Which option is correct?"
        multiple_choice.points = 4
        multiple_choice.correct_answer = "b"
        multiple_choice.correct_answer_data = {"option_key": "b"}

        essay.status = QuestionStatus.CONFIRMED.value
        essay.teacher_confirmed = True
        essay.text = "Explain the central theme."
        essay.points = 8
        essay.expected_answer = "A complete answer explains the central theme with evidence."
        essay.grading_instructions = "Reward textual evidence."
        essay.rubric = {"criteria": [{"name": "Evidence", "points": 4}], "total_points": 8}
        essay.rubric_ai_suggested = {"criteria": [{"name": "AI suggestion", "points": 8}], "total_points": 8}
        essay.rubric_teacher_confirmed = True

        db.add_all(
            [
                multiple_choice,
                essay,
                QuestionOption(
                    teacher_id=context["teacher"].id,
                    class_id=context["classroom"].id,
                    exam_id=context["exam"].id,
                    question_id=multiple_choice.id,
                    option_key="b",
                    option_text="Second option",
                    is_correct=True,
                ),
            ]
        )
        db.commit()
        token = context["token_value"]

    teacher_response = client.get(_questions_url(context), cookies=context["cookies"])
    public_access_response = client.get(f"/api/v1/exam/access/{token}")
    public_start_response = client.post(f"/api/v1/exam/access/{token}/start")

    assert teacher_response.status_code == 200
    assert "correct_answer" in teacher_response.text
    assert "rubric_ai_suggested" in teacher_response.text
    assert public_access_response.status_code == 200
    assert public_start_response.status_code == 200

    combined_public_text = f"{public_access_response.text} {public_start_response.text}"
    for forbidden in [
        "correct_answer",
        "correct_answer_data",
        "expected_answer",
        "rubric",
        "rubric_ai_suggested",
        "rubric_teacher_confirmed",
        "grading_instructions",
    ]:
        assert forbidden not in combined_public_text
