from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.exams.permissions import get_current_teacher
from app.modules.questions.schemas import QuestionSlotRead
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
        QuestionSlotRead.model_validate(question).model_dump(mode="json")
        for question in questions
    ]
    return success_response(data=data)
