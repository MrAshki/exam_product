from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.appeals.schemas import (
    AppealCreate,
    AppealDetailRead,
    AppealListRead,
    AppealResolveRead,
    AppealResolveRequest,
    AppealSubmitRead,
)
from app.modules.appeals.service import AppealService
from app.modules.auth.models import User
from app.modules.exams.permissions import get_current_teacher


router = APIRouter()


def get_appeal_service(db: Session = Depends(get_db)) -> AppealService:
    return AppealService(db)


@router.post("/result/{result_token}/appeals")
def submit_appeal(
    result_token: str,
    payload: AppealCreate,
    service: AppealService = Depends(get_appeal_service),
) -> dict:
    result = service.submit_appeal(result_token, payload)
    return success_response(
        data=AppealSubmitRead.model_validate(result).model_dump(mode="json"),
        message="Appeal submitted successfully.",
    )


@router.get("/classes/{class_id}/appeals")
def list_appeals(
    class_id: UUID,
    status: str | None = None,
    exam_id: UUID | None = None,
    student_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    teacher: User = Depends(get_current_teacher),
    service: AppealService = Depends(get_appeal_service),
) -> dict:
    result = service.list_appeals(
        class_id=class_id,
        teacher=teacher,
        status=status,
        exam_id=exam_id,
        student_id=student_id,
        page=page,
        page_size=page_size,
    )
    return success_response(data=AppealListRead.model_validate(result).model_dump(mode="json"))


@router.get("/classes/{class_id}/appeals/{appeal_id}")
def get_appeal(
    class_id: UUID,
    appeal_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: AppealService = Depends(get_appeal_service),
) -> dict:
    result = service.get_appeal(class_id=class_id, appeal_id=appeal_id, teacher=teacher)
    return success_response(data=AppealDetailRead.model_validate(result).model_dump(mode="json"))


@router.post("/classes/{class_id}/appeals/{appeal_id}/resolve")
def resolve_appeal(
    class_id: UUID,
    appeal_id: UUID,
    payload: AppealResolveRequest,
    teacher: User = Depends(get_current_teacher),
    service: AppealService = Depends(get_appeal_service),
) -> dict:
    result = service.resolve_appeal(
        class_id=class_id,
        appeal_id=appeal_id,
        payload=payload,
        teacher=teacher,
    )
    return success_response(
        data=AppealResolveRead.model_validate(result).model_dump(mode="json"),
        message="Appeal resolved successfully.",
    )
