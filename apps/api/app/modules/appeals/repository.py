from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.appeals.models import Appeal
from app.modules.appeals.status import AppealStatus
from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam
from app.modules.exams.status import QuestionStatus
from app.modules.grading.models import GradeChangeLog
from app.modules.jobs.models import JobLog
from app.modules.questions.models import Question
from app.modules.results.models import ResultToken
from app.modules.students.models import Student
from app.modules.submissions.models import Answer, Submission


class AppealRepository:
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

    def get_result_context(
        self,
        token: str,
    ) -> tuple[ResultToken, Exam, Classroom, Student, Submission, User] | None:
        statement = (
            select(ResultToken, Exam, Classroom, Student, Submission, User)
            .join(Exam, Exam.id == ResultToken.exam_id)
            .join(Classroom, Classroom.id == ResultToken.class_id)
            .join(Student, Student.id == ResultToken.student_id)
            .join(Submission, Submission.id == ResultToken.submission_id)
            .join(User, User.id == ResultToken.teacher_id)
            .where(
                ResultToken.token == token,
                ResultToken.deleted_at.is_(None),
                Exam.deleted_at.is_(None),
                Classroom.deleted_at.is_(None),
                Student.deleted_at.is_(None),
                Submission.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
        )
        return self.db.execute(statement).first()

    def get_answer_for_submission(self, submission: Submission, answer_id: UUID) -> tuple[Answer, Question] | None:
        statement = (
            select(Answer, Question)
            .join(Question, Question.id == Answer.question_id)
            .where(
                Answer.id == answer_id,
                Answer.submission_id == submission.id,
                Answer.teacher_id == submission.teacher_id,
                Answer.class_id == submission.class_id,
                Answer.exam_id == submission.exam_id,
                Answer.student_id == submission.student_id,
                Answer.deleted_at.is_(None),
                Question.teacher_id == submission.teacher_id,
                Question.class_id == submission.class_id,
                Question.exam_id == submission.exam_id,
                Question.deleted_at.is_(None),
            )
        )
        return self.db.execute(statement).first()

    def pending_appeal_exists(self, submission_id: UUID, answer_id: UUID | None) -> bool:
        statement = select(Appeal.id).where(
            Appeal.submission_id == submission_id,
            Appeal.status == AppealStatus.PENDING.value,
            Appeal.deleted_at.is_(None),
        )
        if answer_id is None:
            statement = statement.where(Appeal.answer_id.is_(None))
        else:
            statement = statement.where(Appeal.answer_id == answer_id)
        return self.db.scalar(statement) is not None

    def create_appeal(self, appeal: Appeal) -> Appeal:
        self.db.add(appeal)
        self.db.flush()
        return appeal

    def list_appeals(
        self,
        *,
        class_id: UUID,
        teacher_id: UUID,
        status: str | None,
        exam_id: UUID | None,
        student_id: UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[Appeal, Student, Exam]], int]:
        filters = [
            Appeal.class_id == class_id,
            Appeal.teacher_id == teacher_id,
            Appeal.deleted_at.is_(None),
            Student.teacher_id == teacher_id,
            Student.deleted_at.is_(None),
            Exam.teacher_id == teacher_id,
            Exam.class_id == class_id,
            Exam.deleted_at.is_(None),
        ]
        if status:
            filters.append(Appeal.status == status)
        if exam_id:
            filters.append(Appeal.exam_id == exam_id)
        if student_id:
            filters.append(Appeal.student_id == student_id)

        total = self.db.scalar(
            select(func.count(Appeal.id))
            .join(Student, Student.id == Appeal.student_id)
            .join(Exam, Exam.id == Appeal.exam_id)
            .where(*filters)
        ) or 0
        rows = list(
            self.db.execute(
                select(Appeal, Student, Exam)
                .join(Student, Student.id == Appeal.student_id)
                .join(Exam, Exam.id == Appeal.exam_id)
                .where(*filters)
                .order_by(Appeal.created_at.desc(), Appeal.id.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return rows, total

    def get_appeal_context(
        self,
        *,
        class_id: UUID,
        appeal_id: UUID,
        teacher_id: UUID,
    ) -> tuple[Appeal, Student, Exam, Classroom, Submission, ResultToken | None, Answer | None, Question | None] | None:
        base = (
            select(Appeal, Student, Exam, Classroom, Submission, ResultToken)
            .join(Student, Student.id == Appeal.student_id)
            .join(Exam, Exam.id == Appeal.exam_id)
            .join(Classroom, Classroom.id == Appeal.class_id)
            .join(Submission, Submission.id == Appeal.submission_id)
            .outerjoin(
                ResultToken,
                (ResultToken.submission_id == Appeal.submission_id) & (ResultToken.deleted_at.is_(None)),
            )
            .where(
                Appeal.id == appeal_id,
                Appeal.class_id == class_id,
                Appeal.teacher_id == teacher_id,
                Appeal.deleted_at.is_(None),
                Student.teacher_id == teacher_id,
                Student.deleted_at.is_(None),
                Exam.teacher_id == teacher_id,
                Exam.class_id == class_id,
                Exam.deleted_at.is_(None),
                Classroom.teacher_id == teacher_id,
                Classroom.deleted_at.is_(None),
                Submission.teacher_id == teacher_id,
                Submission.class_id == class_id,
                Submission.deleted_at.is_(None),
            )
        )
        row = self.db.execute(base).first()
        if row is None:
            return None
        appeal, student, exam, classroom, submission, result_token = row
        answer = None
        question = None
        if appeal.answer_id is not None:
            answer_row = self.get_answer_for_submission(submission, appeal.answer_id)
            if answer_row is not None:
                answer, question = answer_row
        return appeal, student, exam, classroom, submission, result_token, answer, question

    def list_confirmed_questions(self, submission: Submission) -> list[Question]:
        return list(
            self.db.scalars(
                select(Question).where(
                    Question.teacher_id == submission.teacher_id,
                    Question.class_id == submission.class_id,
                    Question.exam_id == submission.exam_id,
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
        reason: str,
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

    def create_job_log(self, job: JobLog) -> JobLog:
        self.db.add(job)
        self.db.flush()
        return job

    def save(self, *objects) -> None:
        for obj in objects:
            self.db.add(obj)
        self.db.commit()

    def refresh(self, *objects) -> None:
        for obj in objects:
            self.db.refresh(obj)

    def rollback(self) -> None:
        self.db.rollback()
