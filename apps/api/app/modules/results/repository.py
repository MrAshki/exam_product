from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam
from app.modules.exams.status import QuestionStatus
from app.modules.jobs.models import JobLog
from app.modules.questions.models import Question
from app.modules.results.models import LeaderboardToken, ResultToken
from app.modules.students.models import ClassStudent, Student
from app.modules.submissions.models import Answer, Submission


class ResultsRepository:
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

    def get_teacher(self, teacher_id: UUID) -> User | None:
        return self.db.scalar(select(User).where(User.id == teacher_id, User.deleted_at.is_(None)))

    def list_publishable_submissions(self, class_id: UUID, exam_id: UUID, teacher_id: UUID) -> list[Submission]:
        return list(
            self.db.scalars(
                select(Submission)
                .join(Student, Student.id == Submission.student_id)
                .join(
                    ClassStudent,
                    (ClassStudent.class_id == Submission.class_id)
                    & (ClassStudent.student_id == Submission.student_id),
                )
                .where(
                    Submission.class_id == class_id,
                    Submission.exam_id == exam_id,
                    Submission.teacher_id == teacher_id,
                    Submission.deleted_at.is_(None),
                    Student.teacher_id == teacher_id,
                    Student.deleted_at.is_(None),
                    ClassStudent.deleted_at.is_(None),
                )
                .order_by(Submission.submitted_at.asc().nullslast(), Submission.created_at.asc())
            ).all()
        )

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

    def list_answers_for_submission(self, submission: Submission) -> list[Answer]:
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

    def get_student(self, student_id: UUID, teacher_id: UUID) -> Student | None:
        return self.db.scalar(
            select(Student).where(
                Student.id == student_id,
                Student.teacher_id == teacher_id,
                Student.deleted_at.is_(None),
            )
        )

    def get_result_token_for_submission(self, submission_id: UUID) -> ResultToken | None:
        return self.db.scalar(
            select(ResultToken).where(
                ResultToken.submission_id == submission_id,
                ResultToken.deleted_at.is_(None),
            )
        )

    def get_result_token_by_token(self, token: str) -> ResultToken | None:
        return self.db.scalar(
            select(ResultToken).where(
                ResultToken.token == token,
                ResultToken.deleted_at.is_(None),
            )
        )

    def token_value_exists(self, token: str) -> bool:
        return self.db.scalar(select(ResultToken.id).where(ResultToken.token == token)) is not None or self.db.scalar(
            select(LeaderboardToken.id).where(LeaderboardToken.token == token)
        ) is not None

    def create_result_token(self, submission: Submission, token: str) -> ResultToken:
        result_token = ResultToken(
            teacher_id=submission.teacher_id,
            class_id=submission.class_id,
            exam_id=submission.exam_id,
            student_id=submission.student_id,
            submission_id=submission.id,
            token=token,
        )
        self.db.add(result_token)
        self.db.flush()
        return result_token

    def get_leaderboard_token_for_exam(self, class_id: UUID, exam_id: UUID) -> LeaderboardToken | None:
        return self.db.scalar(
            select(LeaderboardToken).where(
                LeaderboardToken.class_id == class_id,
                LeaderboardToken.exam_id == exam_id,
                LeaderboardToken.deleted_at.is_(None),
            )
        )

    def get_leaderboard_token_by_token(self, token: str) -> LeaderboardToken | None:
        return self.db.scalar(
            select(LeaderboardToken).where(
                LeaderboardToken.token == token,
                LeaderboardToken.deleted_at.is_(None),
            )
        )

    def create_leaderboard_token(self, exam: Exam, token: str) -> LeaderboardToken:
        leaderboard_token = LeaderboardToken(
            teacher_id=exam.teacher_id,
            class_id=exam.class_id,
            exam_id=exam.id,
            token=token,
        )
        self.db.add(leaderboard_token)
        self.db.flush()
        return leaderboard_token

    def get_published_result_context(
        self,
        token: str,
    ) -> tuple[ResultToken, Exam, Classroom, Student, Submission] | None:
        statement = (
            select(ResultToken, Exam, Classroom, Student, Submission)
            .join(Exam, Exam.id == ResultToken.exam_id)
            .join(Classroom, Classroom.id == ResultToken.class_id)
            .join(Student, Student.id == ResultToken.student_id)
            .join(Submission, Submission.id == ResultToken.submission_id)
            .where(
                ResultToken.token == token,
                ResultToken.deleted_at.is_(None),
                Exam.deleted_at.is_(None),
                Classroom.deleted_at.is_(None),
                Student.deleted_at.is_(None),
                Submission.deleted_at.is_(None),
            )
        )
        return self.db.execute(statement).first()

    def get_leaderboard_context(self, token: str) -> tuple[LeaderboardToken, Exam, Classroom] | None:
        statement = (
            select(LeaderboardToken, Exam, Classroom)
            .join(Exam, Exam.id == LeaderboardToken.exam_id)
            .join(Classroom, Classroom.id == LeaderboardToken.class_id)
            .where(
                LeaderboardToken.token == token,
                LeaderboardToken.deleted_at.is_(None),
                Exam.deleted_at.is_(None),
                Classroom.deleted_at.is_(None),
            )
        )
        return self.db.execute(statement).first()

    def list_result_answer_rows(self, submission: Submission) -> list[tuple[Answer, Question]]:
        statement = (
            select(Answer, Question)
            .join(Question, Question.id == Answer.question_id)
            .where(
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
                Question.teacher_confirmed.is_(True),
                Question.status == QuestionStatus.CONFIRMED.value,
            )
            .order_by(Question.order_index.asc())
        )
        return list(self.db.execute(statement).all())

    def list_leaderboard_rows(self, class_id: UUID, exam_id: UUID) -> list[tuple[Submission, Student]]:
        statement = (
            select(Submission, Student)
            .join(Student, Student.id == Submission.student_id)
            .join(
                ClassStudent,
                (ClassStudent.class_id == Submission.class_id)
                & (ClassStudent.student_id == Submission.student_id),
            )
            .where(
                Submission.class_id == class_id,
                Submission.exam_id == exam_id,
                Submission.deleted_at.is_(None),
                Submission.published_at.is_not(None),
                Student.deleted_at.is_(None),
                ClassStudent.deleted_at.is_(None),
            )
            .order_by(Submission.total_score.desc().nullslast(), Submission.submitted_at.asc().nullslast(), Student.full_name.asc())
        )
        return list(self.db.execute(statement).all())

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
