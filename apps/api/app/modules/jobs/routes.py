from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.classrooms.permissions import get_current_teacher
from app.modules.jobs.schemas import JobRead
from app.modules.jobs.service import JobService


router = APIRouter()


def get_job_service(db: Session = Depends(get_db)) -> JobService:
    return JobService(db)


@router.get("/{job_id}")
def get_job(
    job_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: JobService = Depends(get_job_service),
) -> dict:
    job = service.get_for_teacher(job_id, teacher)
    return success_response(data=JobRead.model_validate(job).model_dump(mode="json"))

