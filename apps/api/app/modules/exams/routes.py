from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.exams.permissions import get_current_teacher
from app.modules.exams.schemas import (
    BlueprintCreate,
    BlueprintRead,
    BlueprintUpdate,
    ExamCreate,
    ExamInvitationRead,
    ExamInvitationRequest,
    ExamRead,
    ExamScheduleRead,
    ExamScheduleRequest,
    ExamUpdate,
)
from app.modules.exams.service import ExamService


router = APIRouter()


def get_exam_service(db: Session = Depends(get_db)) -> ExamService:
    return ExamService(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_exam(
    class_id: UUID,
    payload: ExamCreate,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    exam = service.create(class_id, payload, teacher)
    return success_response(data=ExamRead.model_validate(exam).model_dump(mode="json"))


@router.get("/")
def list_exams(
    class_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    exams = service.list(class_id, teacher)
    data = [ExamRead.model_validate(exam).model_dump(mode="json") for exam in exams]
    return success_response(data=data)


@router.get("/{exam_id}")
def get_exam(
    class_id: UUID,
    exam_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    exam = service.get(class_id, exam_id, teacher)
    return success_response(data=ExamRead.model_validate(exam).model_dump(mode="json"))


@router.put("/{exam_id}")
def update_exam(
    class_id: UUID,
    exam_id: UUID,
    payload: ExamUpdate,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    exam = service.update(class_id, exam_id, payload, teacher)
    return success_response(data=ExamRead.model_validate(exam).model_dump(mode="json"))


@router.delete("/{exam_id}")
def delete_exam(
    class_id: UUID,
    exam_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    service.delete(class_id, exam_id, teacher)
    return success_response(data={})


@router.post("/{exam_id}/schedule")
def schedule_exam(
    class_id: UUID,
    exam_id: UUID,
    payload: ExamScheduleRequest,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    result = service.schedule(class_id, exam_id, payload, teacher)
    return success_response(
        data=ExamScheduleRead.model_validate(result).model_dump(mode="json"),
        message="Exam scheduled successfully.",
    )


@router.post("/{exam_id}/send-invitations")
def send_exam_invitations(
    class_id: UUID,
    exam_id: UUID,
    payload: ExamInvitationRequest,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    result = service.send_invitations(class_id, exam_id, payload, teacher)
    return success_response(
        data=ExamInvitationRead.model_validate(result).model_dump(mode="json"),
        message="Invitation emails queued successfully.",
    )


@router.post("/{exam_id}/blueprint", status_code=status.HTTP_201_CREATED)
def create_blueprint(
    class_id: UUID,
    exam_id: UUID,
    payload: BlueprintCreate,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    blueprint = service.create_blueprint(class_id, exam_id, payload, teacher)
    return success_response(data=BlueprintRead.model_validate(blueprint).model_dump(mode="json"))


@router.get("/{exam_id}/blueprint")
def get_blueprint(
    class_id: UUID,
    exam_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    blueprint = service.get_blueprint(class_id, exam_id, teacher)
    return success_response(data=BlueprintRead.model_validate(blueprint).model_dump(mode="json"))


@router.put("/{exam_id}/blueprint")
def update_blueprint(
    class_id: UUID,
    exam_id: UUID,
    payload: BlueprintUpdate,
    teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
) -> dict:
    blueprint = service.update_blueprint(class_id, exam_id, payload, teacher)
    return success_response(data=BlueprintRead.model_validate(blueprint).model_dump(mode="json"))
