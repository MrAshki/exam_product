from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.exams.permissions import get_current_teacher
from app.modules.results.schemas import PublicLeaderboardRead, PublicResultRead, PublishResultsRead
from app.modules.results.service import PublishResultsService


router = APIRouter()


def get_results_service(db: Session = Depends(get_db)) -> PublishResultsService:
    return PublishResultsService(db)


@router.post("/classes/{class_id}/exams/{exam_id}/publish-results")
def publish_results(
    class_id: UUID,
    exam_id: UUID,
    teacher: User = Depends(get_current_teacher),
    service: PublishResultsService = Depends(get_results_service),
) -> dict:
    result = service.publish_results(class_id, exam_id, teacher)
    return success_response(
        data=PublishResultsRead.model_validate(result).model_dump(mode="json"),
        message="Results published successfully.",
    )


@router.get("/result/{result_token}")
def get_public_result(
    result_token: str,
    service: PublishResultsService = Depends(get_results_service),
) -> dict:
    result = service.get_public_result(result_token)
    return success_response(data=PublicResultRead.model_validate(result).model_dump(mode="json"))


@router.get("/leaderboard/{leaderboard_token}")
def get_public_leaderboard(
    leaderboard_token: str,
    service: PublishResultsService = Depends(get_results_service),
) -> dict:
    result = service.get_public_leaderboard(leaderboard_token)
    return success_response(data=PublicLeaderboardRead.model_validate(result).model_dump(mode="json"))
