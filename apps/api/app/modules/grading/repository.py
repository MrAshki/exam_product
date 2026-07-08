from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam
from app.modules.exams.status import QuestionStatus
from app.modules.grading.models import GradeChangeLog
from app.modules.questions.models import Question
from app.modules.students.models import Student
from app.modules.submissions.models import Answer, Submission


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_class_for_teacher(self, class_id: UUID, teacher_id: UUID) -> Classroom | None:
        return self.db.scalar(
            select(Classroom).where(
                Classroom.id == class_id,
                Classroom.teacher_id == teacher_id,
                Classroom.deleted_at.is_(None),
            )
        )

    def get_exam_for_teacher_class(self, class_id: UUID, exam_id: UUID, teacher_id: UUID) -> Exam | None:
        return self.db.scalar(
            select(Exam).where(
                Exam.id == exam_id,
                Exam.class_id == class_id,
                Exam.teacher_id == teacher_id,
                Exam.deleted_at.is_(None),
            )
        )

    def list_review_rows(self, class_id: UUID, exam_id: UUID, teacher_id: UUID) -> list[tuple[Submission, Student, Answer, Question]]:
        statement = (
            select(Submission, Student, Answer, Question)
            .join(Student, Student.id == Submission.student_id)
            .join(Answer, Answer.submission_id == Submission.id)
            .join(Question, Question.id == Answer.question_id)
            .where(
                Submission.class_id == class_id,
                Submission.exam_id == exam_id,
                Submission.teacher_id == teacher_id,
                Submission.deleted_at.is_(None),
                Student.teacher_id == teacher_id,
                Student.deleted_at.is_(None),
                Answer.class_id == class_id,
                Answer.exam_id == exam_id,
                Answer.teacher_id == teacher_id,
                Answer.deleted_at.is_(None),
                Question.class_id == class_id,
                Question.exam_id == exam_id,
                Question.teacher_id == teacher_id,
                Question.deleted_at.is_(None),
            )
            .order_by(Student.full_name.asc(), Question.order_index.asc())
        )
        return list(self.db.execute(statement).all())

    def list_submissions_with_students(self, class_id: UUID, exam_id: UUID, teacher_id: UUID) -> list[tuple[Submission, Student]]:
        statement = (
            select(Submission, Student)
            .join(Student, Student.id == Submission.student_id)
            .where(
                Submission.class_id == class_id,
                Submission.exam_id == exam_id,
                Submission.teacher_id == teacher_id,
                Submission.deleted_at.is_(None),
                Student.teacher_id == teacher_id,
                Student.deleted_at.is_(None),
            )
            .order_by(Student.full_name.asc())
        )
        return list(self.db.execute(statement).all())

    def get_answer_context(
        self,
        *,
        class_id: UUID,
        exam_id: UUID,
        answer_id: UUID,
        teacher_id: UUID,
    ) -> tuple[Answer, Submission, Question] | None:
        statement = (
            select(Answer, Submission, Question)
            .join(Submission, Submission.id == Answer.submission_id)
            .join(Question, Question.id == Answer.question_id)
            .where(
                Answer.id == answer_id,
                Answer.class_id == class_id,
                Answer.exam_id == exam_id,
                Answer.teacher_id == teacher_id,
                Answer.deleted_at.is_(None),
                Submission.class_id == class_id,
                Submission.exam_id == exam_id,
                Submission.teacher_id == teacher_id,
                Submission.deleted_at.is_(None),
                Question.class_id == class_id,
                Question.exam_id == exam_id,
                Question.teacher_id == teacher_id,
                Question.deleted_at.is_(None),
            )
        )
        return self.db.execute(statement).first()

    def list_confirmed_questions(self, class_id: UUID, exam_id: UUID, teacher_id: UUID) -> list[Question]:
        return list(
            self.db.scalars(
                select(Question).where(
                    Question.class_id == class_id,
                    Question.exam_id == exam_id,
                    Question.teacher_id == teacher_id,
                    Question.deleted_at.is_(None),
                    Question.teacher_confirmed.is_(True),
                    Question.status == QuestionStatus.CONFIRMED.value,
                )
            ).all()
        )

    def list_active_answers_for_submission(self, submission: Submission) -> list[Answer]:
        return list(
            self.db.scalars(
                select(Answer).where(
                    Answer.submission_id == submission.id,
                    Answer.teacher_id == submission.teacher_id,
                    Answer.class_id == submission.class_id,
                    Answer.exam_id == submission.exam_id,
                    Answer.student_id == submission.student_id,
                    Answer.deleted_at.is_(None),
                )
            ).all()
        )

    def create_grade_change_log(
        self,
        *,
        answer: Answer,
        old_score: Decimal | None,
        new_score: Decimal | None,
        reason: str | None,
    ) -> GradeChangeLog:
        log = GradeChangeLog(
            teacher_id=answer.teacher_id,
            class_id=answer.class_id,
            exam_id=answer.exam_id,
            student_id=answer.student_id,
            submission_id=answer.submission_id,
            answer_id=answer.id,
            old_score=old_score,
            new_score=new_score,
            reason=reason,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def save(self, *objects) -> None:
        for obj in objects:
            self.db.add(obj)
        self.db.commit()

    def refresh(self, *objects) -> None:
        for obj in objects:
            self.db.refresh(obj)

    def rollback(self) -> None:
        self.db.rollback()
