from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.submissions.schemas import (
    ExamAccessRead,
    ExamStartRead,
    ExamSubmitRead,
    ExamSubmitRequest,
)
from app.modules.submissions.service import SubmissionService


router = APIRouter()


def get_submission_service(db: Session = Depends(get_db)) -> SubmissionService:
    return SubmissionService(db)


@router.get("/access/{exam_token}")
def get_exam_access(
    exam_token: str,
    service: SubmissionService = Depends(get_submission_service),
) -> dict:
    access_state = service.get_access_state(exam_token)
    return success_response(data=ExamAccessRead.model_validate(access_state).model_dump(mode="json"))


@router.post("/access/{exam_token}/start")
def start_exam(
    exam_token: str,
    service: SubmissionService = Depends(get_submission_service),
) -> dict:
    started_exam = service.start_exam(exam_token)
    return success_response(
        data=ExamStartRead.model_validate(started_exam).model_dump(mode="json"),
        message="Exam started.",
    )


@router.post("/access/{exam_token}/submit")
def submit_exam(
    exam_token: str,
    payload: ExamSubmitRequest,
    service: SubmissionService = Depends(get_submission_service),
) -> dict:
    submitted_exam = service.submit_exam(exam_token, payload)
    return success_response(data=ExamSubmitRead.model_validate(submitted_exam).model_dump(mode="json"))
