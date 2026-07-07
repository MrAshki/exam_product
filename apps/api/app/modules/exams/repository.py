from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam, ExamBlueprint
from app.modules.questions.models import Question, QuestionOption
from app.modules.students.models import ClassStudent, Student


class ExamRepository:
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

    def class_has_active_students(self, class_id: UUID, teacher_id: UUID) -> bool:
        statement = (
            select(Student.id)
            .join(ClassStudent, ClassStudent.student_id == Student.id)
            .where(
                ClassStudent.class_id == class_id,
                ClassStudent.deleted_at.is_(None),
                Student.teacher_id == teacher_id,
                Student.deleted_at.is_(None),
                Student.is_active.is_(True),
            )
            .limit(1)
        )
        return self.db.scalar(statement) is not None

    def list_by_class_for_teacher(
        self,
        class_id: UUID,
        teacher_id: UUID,
    ) -> list[Exam]:
        statement = (
            select(Exam)
            .where(
                Exam.class_id == class_id,
                Exam.teacher_id == teacher_id,
                Exam.deleted_at.is_(None),
            )
            .order_by(Exam.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id_for_teacher_class(
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

    def get_by_title_for_class(
        self,
        title: str,
        class_id: UUID,
        teacher_id: UUID,
        exclude_exam_id: UUID | None = None,
    ) -> Exam | None:
        statement = select(Exam).where(
            Exam.class_id == class_id,
            Exam.teacher_id == teacher_id,
            Exam.deleted_at.is_(None),
            func.lower(Exam.title) == title.lower(),
        )
        if exclude_exam_id is not None:
            statement = statement.where(Exam.id != exclude_exam_id)
        return self.db.scalar(statement)

    def create(self, exam: Exam) -> Exam:
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def save(self, exam: Exam) -> Exam:
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def get_blueprint_for_exam(
        self,
        exam_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
    ) -> ExamBlueprint | None:
        statement = select(ExamBlueprint).where(
            ExamBlueprint.exam_id == exam_id,
            ExamBlueprint.class_id == class_id,
            ExamBlueprint.teacher_id == teacher_id,
            ExamBlueprint.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def has_confirmed_questions(
        self,
        exam_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
    ) -> bool:
        statement = (
            select(Question.id)
            .where(
                Question.exam_id == exam_id,
                Question.class_id == class_id,
                Question.teacher_id == teacher_id,
                Question.deleted_at.is_(None),
                Question.teacher_confirmed.is_(True),
            )
            .limit(1)
        )
        return self.db.scalar(statement) is not None

    def create_blueprint_with_slots(
        self,
        blueprint: ExamBlueprint,
        questions: list[Question],
    ) -> ExamBlueprint:
        self.db.add(blueprint)
        self.db.add_all(questions)
        self.db.commit()
        self.db.refresh(blueprint)
        return blueprint

    def update_blueprint_and_recreate_slots(
        self,
        blueprint: ExamBlueprint,
        questions: list[Question],
    ) -> ExamBlueprint:
        existing_questions = self._active_questions_for_exam(
            blueprint.exam_id,
            blueprint.class_id,
            blueprint.teacher_id,
        )
        existing_question_ids = [question.id for question in existing_questions]
        if existing_question_ids:
            option_statement = select(QuestionOption).where(
                QuestionOption.question_id.in_(existing_question_ids),
                QuestionOption.deleted_at.is_(None),
            )
            for option in self.db.scalars(option_statement).all():
                option.soft_delete()
                self.db.add(option)

        for question in existing_questions:
            question.soft_delete()
            self.db.add(question)

        self.db.add(blueprint)
        self.db.flush()
        self.db.add_all(questions)
        self.db.commit()
        self.db.refresh(blueprint)
        return blueprint

    def soft_delete_exam_tree(self, exam: Exam) -> None:
        blueprint = self.get_blueprint_for_exam(exam.id, exam.class_id, exam.teacher_id)
        if blueprint is not None:
            blueprint.soft_delete()
            self.db.add(blueprint)

        questions = self._active_questions_for_exam(exam.id, exam.class_id, exam.teacher_id)
        question_ids = [question.id for question in questions]
        if question_ids:
            option_statement = select(QuestionOption).where(
                QuestionOption.question_id.in_(question_ids),
                QuestionOption.deleted_at.is_(None),
            )
            for option in self.db.scalars(option_statement).all():
                option.soft_delete()
                self.db.add(option)

        for question in questions:
            question.soft_delete()
            self.db.add(question)

        exam.soft_delete()
        self.db.add(exam)
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def _active_questions_for_exam(
        self,
        exam_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
    ) -> list[Question]:
        statement = select(Question).where(
            Question.exam_id == exam_id,
            Question.class_id == class_id,
            Question.teacher_id == teacher_id,
            Question.deleted_at.is_(None),
        )
        return list(self.db.scalars(statement).all())
