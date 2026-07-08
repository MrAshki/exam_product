from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.exams.permissions import get_current_teacher
from app.modules.grading.repository import ReviewRepository
from app.modules.grading.review_service import ReviewService
from app.modules.grading.schemas import AnswerReviewRead, AnswerReviewRequest, ApproveResultsRead


router = APIRouter()


def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(ReviewRepository(db))


@router.get("/{exam_id}/review")
def get_exam_review(
    class_id: UUID,
    exam_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: ReviewService = Depends(get_review_service),
) -> dict:
    return success_response(data=service.get_review(class_id, exam_id, teacher))


@router.put("/{exam_id}/answers/{answer_id}/review")
def review_answer(
    class_id: UUID,
    exam_id: UUID,
    answer_id: UUID,
    payload: AnswerReviewRequest,
    teacher: User = Depends(get_current_teacher),
    service: ReviewService = Depends(get_review_service),
) -> dict:
    result = service.review_answer(
        class_id=class_id,
        exam_id=exam_id,
        answer_id=answer_id,
        payload=payload,
        teacher=teacher,
    )
    return success_response(
        data=AnswerReviewRead.model_validate(result).model_dump(mode="json"),
        message="Answer reviewed successfully.",
    )


@router.post("/{exam_id}/approve-results")
def approve_results(
    class_id: UUID,
    exam_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: ReviewService = Depends(get_review_service),
) -> dict:
    result = service.approve_results(class_id, exam_id, teacher)
    return success_response(
        data=ApproveResultsRead.model_validate(result).model_dump(mode="json"),
        message="Results approved successfully.",
    )
