from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus


class SubmissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_submission_for_exam_student(
        self,
        exam_id: UUID,
        student_id: UUID,
    ) -> Submission | None:
        statement = select(Submission).where(
            Submission.exam_id == exam_id,
            Submission.student_id == student_id,
            Submission.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

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
        submission = Submission(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            student_id=student_id,
            token_id=token_id,
            status=status,
            max_score=max_score,
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def get_submission_by_id(
        self,
        submission_id: UUID,
        include_deleted: bool = False,
    ) -> Submission | None:
        statement = select(Submission).where(Submission.id == submission_id)
        if not include_deleted:
            statement = statement.where(Submission.deleted_at.is_(None))
        return self.db.scalar(statement)

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
        answer = Answer(
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
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        return answer

    def bulk_create_answers(self, answers: list[Answer]) -> list[Answer]:
        self.db.add_all(answers)
        self.db.commit()
        for answer in answers:
            self.db.refresh(answer)
        return answers

    def list_answers_by_submission(self, submission_id: UUID) -> list[Answer]:
        statement = (
            select(Answer)
            .where(
                Answer.submission_id == submission_id,
                Answer.deleted_at.is_(None),
            )
            .order_by(Answer.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def save_submission(self, submission: Submission) -> Submission:
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def save_answer(self, answer: Answer) -> Answer:
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        return answer

    def rollback(self) -> None:
        self.db.rollback()

