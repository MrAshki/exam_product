from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamToken
from app.modules.questions.models import Question, QuestionOption
from app.modules.students.models import ClassStudent, Student
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

    def get_valid_token_context(self, token_value: str) -> tuple[ExamToken, Exam, Classroom, Student] | None:
        statement = (
            select(ExamToken, Exam, Classroom, Student)
            .join(
                Exam,
                (Exam.id == ExamToken.exam_id)
                & (Exam.class_id == ExamToken.class_id)
                & (Exam.teacher_id == ExamToken.teacher_id),
            )
            .join(
                Classroom,
                (Classroom.id == ExamToken.class_id)
                & (Classroom.teacher_id == ExamToken.teacher_id),
            )
            .join(
                Student,
                (Student.id == ExamToken.student_id)
                & (Student.teacher_id == ExamToken.teacher_id),
            )
            .join(
                ClassStudent,
                (ClassStudent.class_id == ExamToken.class_id)
                & (ClassStudent.student_id == ExamToken.student_id),
            )
            .where(
                ExamToken.token == token_value,
                ExamToken.deleted_at.is_(None),
                Exam.deleted_at.is_(None),
                Classroom.deleted_at.is_(None),
                Student.deleted_at.is_(None),
                Student.is_active.is_(True),
                ClassStudent.deleted_at.is_(None),
            )
        )
        row = self.db.execute(statement).first()
        if row is None:
            return None
        return row[0], row[1], row[2], row[3]

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
        started_at: datetime | None = None,
    ) -> Submission:
        submission = Submission(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            student_id=student_id,
            token_id=token_id,
            status=status,
            max_score=max_score,
            started_at=started_at,
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def create_or_update_submission(
        self,
        submission: Submission,
    ) -> Submission:
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

    def get_active_answer_for_submission_question(
        self,
        submission_id: UUID,
        question_id: UUID,
    ) -> Answer | None:
        statement = select(Answer).where(
            Answer.submission_id == submission_id,
            Answer.question_id == question_id,
            Answer.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

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

    def list_confirmed_questions_for_exam(
        self,
        exam_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
    ) -> list[Question]:
        statement = (
            select(Question)
            .where(
                Question.exam_id == exam_id,
                Question.class_id == class_id,
                Question.teacher_id == teacher_id,
                Question.deleted_at.is_(None),
                Question.teacher_confirmed.is_(True),
                Question.status == "confirmed",
            )
            .order_by(Question.order_index.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_active_question_by_id(self, question_id: UUID) -> Question | None:
        statement = select(Question).where(
            Question.id == question_id,
            Question.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def list_options_for_questions(
        self,
        question_ids: list[UUID],
    ) -> list[QuestionOption]:
        if not question_ids:
            return []
        statement = (
            select(QuestionOption)
            .where(
                QuestionOption.question_id.in_(question_ids),
                QuestionOption.deleted_at.is_(None),
            )
            .order_by(QuestionOption.option_key.asc())
        )
        return list(self.db.scalars(statement).all())

    def save_submission_with_answers(
        self,
        submission: Submission,
        answers: list[Answer],
    ) -> Submission:
        self.db.add(submission)
        self.db.add_all(answers)
        self.db.commit()
        self.db.refresh(submission)
        return submission

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
