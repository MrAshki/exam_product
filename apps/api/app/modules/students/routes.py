from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.students.permissions import get_current_teacher
from app.modules.students.schemas import StudentCreate, StudentList, StudentRead, StudentUpdate
from app.modules.students.service import StudentService


router = APIRouter()


def get_student_service(db: Session = Depends(get_db)) -> StudentService:
    return StudentService(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_student_to_class(
    class_id: UUID,
    payload: StudentCreate,
    teacher: User = Depends(get_current_teacher),
    service: StudentService = Depends(get_student_service),
) -> dict:
    student = service.add_to_class(class_id, payload, teacher)
    return success_response(data=StudentRead.model_validate(student).model_dump(mode="json"))


@router.get("/")
def list_students(
    class_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    teacher: User = Depends(get_current_teacher),
    service: StudentService = Depends(get_student_service),
) -> dict:
    students, total = service.list(class_id, teacher, page, page_size, search)
    data = StudentList(
        items=[StudentRead.model_validate(student) for student in students],
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_response(data=data.model_dump(mode="json"))


@router.get("/{student_id}")
def get_student(
    class_id: UUID,
    student_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: StudentService = Depends(get_student_service),
) -> dict:
    student = service.get(class_id, student_id, teacher)
    return success_response(data=StudentRead.model_validate(student).model_dump(mode="json"))


@router.put("/{student_id}")
def update_student(
    class_id: UUID,
    student_id: UUID,
    payload: StudentUpdate,
    teacher: User = Depends(get_current_teacher),
    service: StudentService = Depends(get_student_service),
) -> dict:
    student = service.update(class_id, student_id, payload, teacher)
    return success_response(data=StudentRead.model_validate(student).model_dump(mode="json"))


@router.delete("/{student_id}")
def remove_student_from_class(
    class_id: UUID,
    student_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: StudentService = Depends(get_student_service),
) -> dict:
    service.remove_from_class(class_id, student_id, teacher)
    return success_response(data={})
