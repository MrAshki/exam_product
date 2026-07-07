from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.classrooms.permissions import get_current_teacher
from app.modules.classrooms.schemas import (
    ClassroomCreate,
    ClassroomOnboardingState,
    ClassroomRead,
    ClassroomUpdate,
)
from app.modules.classrooms.service import ClassroomService


router = APIRouter()


def get_classroom_service(db: Session = Depends(get_db)) -> ClassroomService:
    return ClassroomService(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_classroom(
    payload: ClassroomCreate,
    teacher: User = Depends(get_current_teacher),
    service: ClassroomService = Depends(get_classroom_service),
) -> dict:
    classroom = service.create(payload, teacher)
    return success_response(data=ClassroomRead.model_validate(classroom).model_dump(mode="json"))


@router.get("/")
def list_classrooms(
    teacher: User = Depends(get_current_teacher),
    service: ClassroomService = Depends(get_classroom_service),
) -> dict:
    classrooms = service.list(teacher)
    data = [
        ClassroomRead.model_validate(classroom).model_dump(mode="json")
        for classroom in classrooms
    ]
    return success_response(data=data)


@router.get("/{class_id}")
def get_classroom(
    class_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: ClassroomService = Depends(get_classroom_service),
) -> dict:
    classroom = service.get(class_id, teacher)
    return success_response(data=ClassroomRead.model_validate(classroom).model_dump(mode="json"))


@router.put("/{class_id}")
def update_classroom(
    class_id: UUID,
    payload: ClassroomUpdate,
    teacher: User = Depends(get_current_teacher),
    service: ClassroomService = Depends(get_classroom_service),
) -> dict:
    classroom = service.update(class_id, payload, teacher)
    return success_response(data=ClassroomRead.model_validate(classroom).model_dump(mode="json"))


@router.delete("/{class_id}")
def delete_classroom(
    class_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: ClassroomService = Depends(get_classroom_service),
) -> dict:
    service.delete(class_id, teacher)
    return success_response(data={})


@router.get("/{class_id}/onboarding-state")
def get_onboarding_state(
    class_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: ClassroomService = Depends(get_classroom_service),
) -> dict:
    state = service.onboarding_state(class_id, teacher)
    return success_response(
        data=ClassroomOnboardingState.model_validate(state).model_dump(mode="json")
    )
