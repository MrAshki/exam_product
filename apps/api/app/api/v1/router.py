from fastapi import APIRouter

from app.modules.auth.routes import router as auth_router
from app.modules.classrooms.routes import router as classrooms_router
from app.modules.students.routes import router as students_router


api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(classrooms_router, prefix="/classes", tags=["classes"])
api_v1_router.include_router(
    students_router,
    prefix="/classes/{class_id}/students",
    tags=["students"],
)
