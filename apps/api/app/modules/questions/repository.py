from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam
from app.modules.questions.models import Question, QuestionOption


class QuestionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_class_for_teacher(
        self,
        class_id: UUID,
        teacher_id: UUID,
    ) -> Classroom | None:
        statement = select(Classroom).where(
            Classroom.id == class_id,
            Classroom.teacher_id == teacher_id,
            Classroom.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def get_exam_for_teacher_class(
        self,
        exam_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
    ) -> Exam | None:
        statement = select(Exam).where(
            Exam.id == exam_id,
            Exam.class_id == class_id,
            Exam.teacher_id == teacher_id,
            Exam.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def list_slots_for_exam(
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
            )
            .order_by(Question.order_index.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_question_for_exam(
        self,
        question_id: UUID,
        exam_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
    ) -> Question | None:
        statement = select(Question).where(
            Question.id == question_id,
            Question.exam_id == exam_id,
            Question.class_id == class_id,
            Question.teacher_id == teacher_id,
            Question.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def list_options_for_question(
        self,
        question_id: UUID,
        exam_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
    ) -> list[QuestionOption]:
        statement = (
            select(QuestionOption)
            .where(
                QuestionOption.question_id == question_id,
                QuestionOption.exam_id == exam_id,
                QuestionOption.class_id == class_id,
                QuestionOption.teacher_id == teacher_id,
                QuestionOption.deleted_at.is_(None),
            )
            .order_by(QuestionOption.option_key.asc())
        )
        return list(self.db.scalars(statement).all())

    def replace_options(
        self,
        question: Question,
        options: list[QuestionOption],
    ) -> None:
        existing_options = self.list_options_for_question(
            question_id=question.id,
            exam_id=question.exam_id,
            class_id=question.class_id,
            teacher_id=question.teacher_id,
        )
        for option in existing_options:
            option.soft_delete()
            self.db.add(option)
        self.db.flush()
        self.db.add_all(options)

    def clear_options(self, question: Question) -> None:
        existing_options = self.list_options_for_question(
            question_id=question.id,
            exam_id=question.exam_id,
            class_id=question.class_id,
            teacher_id=question.teacher_id,
        )
        for option in existing_options:
            option.soft_delete()
            self.db.add(option)

    def save_question(self, question: Question) -> Question:
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def save_question_with_options(
        self,
        question: Question,
        options: list[QuestionOption] | None,
    ) -> Question:
        self.db.add(question)
        if options is None:
            self.clear_options(question)
        else:
            self.replace_options(question, options)
        self.db.commit()
        self.db.refresh(question)
        return question

    def rollback(self) -> None:
        self.db.rollback()
