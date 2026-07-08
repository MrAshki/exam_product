from fastapi import APIRouter

from app.modules.auth.routes import router as auth_router
from app.modules.classrooms.routes import router as classrooms_router
from app.modules.exams.routes import router as exams_router
from app.modules.jobs.routes import router as jobs_router
from app.modules.questions.routes import router as questions_router
from app.modules.students.routes import router as students_router
from app.modules.submissions.routes import router as submissions_router


api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(classrooms_router, prefix="/classes", tags=["classes"])
api_v1_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_v1_router.include_router(
    students_router,
    prefix="/classes/{class_id}/students",
    tags=["students"],
)
api_v1_router.include_router(
    exams_router,
    prefix="/classes/{class_id}/exams",
    tags=["exams"],
)
api_v1_router.include_router(
    questions_router,
    prefix="/classes/{class_id}/exams/{exam_id}/questions",
    tags=["questions"],
)
api_v1_router.include_router(submissions_router, prefix="/exam", tags=["exam-access"])
