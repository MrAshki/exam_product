from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.exams.permissions import get_current_teacher
from app.modules.questions.models import Question
from app.modules.questions.schemas import QuestionRead, QuestionUpdate
from app.modules.questions.service import QuestionService


router = APIRouter()


def get_question_service(db: Session = Depends(get_db)) -> QuestionService:
    return QuestionService(db)


@router.get("/")
def list_question_slots(
    class_id: UUID,
    exam_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: QuestionService = Depends(get_question_service),
) -> dict:
    questions = service.list_slots(class_id, exam_id, teacher)
    data = [
        _serialize_question(question, service)
        for question in questions
    ]
    return success_response(data=data)


@router.put("/{question_id}")
def update_question(
    class_id: UUID,
    exam_id: UUID,
    question_id: UUID,
    payload: QuestionUpdate,
    teacher: User = Depends(get_current_teacher),
    service: QuestionService = Depends(get_question_service),
) -> dict:
    question = service.update(class_id, exam_id, question_id, payload, teacher)
    return success_response(data=_serialize_question(question, service))


@router.post("/{question_id}/confirm", deprecated=True)
def confirm_question(
    class_id: UUID,
    exam_id: UUID,
    question_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: QuestionService = Depends(get_question_service),
) -> dict:
    question = service.confirm(class_id, exam_id, question_id, teacher)
    return success_response(data=_serialize_question(question, service))


@router.delete("/{question_id}")
def clear_question(
    class_id: UUID,
    exam_id: UUID,
    question_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: QuestionService = Depends(get_question_service),
) -> dict:
    question = service.clear(class_id, exam_id, question_id, teacher)
    return success_response(data=_serialize_question(question, service))


@router.post("/{question_id}/suggest-rubric")
def suggest_rubric(
    class_id: UUID,
    exam_id: UUID,
    question_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: QuestionService = Depends(get_question_service),
) -> dict:
    suggestion = service.suggest_rubric(class_id, exam_id, question_id, teacher)
    return success_response(data=suggestion)


def _serialize_question(question: Question, service: QuestionService) -> dict:
    options = service.get_options(question)
    data = QuestionRead.model_validate(question).model_dump(mode="json")
    data["options"] = [
        {
            "id": str(option.id),
            "option_key": option.option_key,
            "option_text": option.option_text,
            "is_correct": option.is_correct,
        }
        for option in options
    ]
    return data
