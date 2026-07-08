from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.repository import SubmissionRepository
from app.modules.submissions.status import SubmissionStatus


class SubmissionService:
    def __init__(self, db: Session) -> None:
        self.repository = SubmissionRepository(db)

    def create_submission(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
        student_id: UUID,
        token_id: UUID,
        status: str = SubmissionStatus.NOT_STARTED.value,
        max_score: Decimal | None = None,
    ) -> Submission:
        return self.repository.create_submission(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            student_id=student_id,
            token_id=token_id,
            status=status,
            max_score=max_score,
        )

    def create_answer(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
        student_id: UUID,
        submission_id: UUID,
        question_id: UUID,
        student_answer: str | None = None,
        answer_data: dict | list | None = None,
        max_score: Decimal | None = None,
    ) -> Answer:
        return self.repository.create_answer(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            student_id=student_id,
            submission_id=submission_id,
            question_id=question_id,
            student_answer=student_answer,
            answer_data=answer_data,
            max_score=max_score,
        )

    def list_answers_by_submission(self, submission_id: UUID) -> list[Answer]:
        return self.repository.list_answers_by_submission(submission_id)

