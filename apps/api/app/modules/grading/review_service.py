from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.modules.auth.models import User
from app.modules.exams.status import ExamStatus
from app.modules.grading import errors
from app.modules.grading.repository import ReviewRepository
from app.modules.grading.schemas import AnswerReviewRequest
from app.modules.questions.models import Question
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import SubmissionStatus


class ReviewService:
    REVIEWABLE_EXAM_STATUSES = {
        ExamStatus.REVIEW_REQUIRED.value,
        ExamStatus.APPROVED.value,
        "auto_graded",
        "needs_review",
        "published",
    }
    APPROVABLE_EXAM_STATUSES = {
        ExamStatus.REVIEW_REQUIRED.value,
        ExamStatus.APPROVED.value,
        "auto_graded",
        "needs_review",
        SubmissionStatus.TEACHER_REVIEWED.value,
    }
    RELEVANT_SUBMISSION_STATUSES = {
        SubmissionStatus.SUBMITTED.value,
        SubmissionStatus.AUTO_GRADED.value,
        SubmissionStatus.NEEDS_REVIEW.value,
        SubmissionStatus.TEACHER_REVIEWED.value,
        SubmissionStatus.APPROVED.value,
        SubmissionStatus.PUBLISHED.value,
    }

    def __init__(self, repository: ReviewRepository) -> None:
        self.repository = repository

    def get_review(self, class_id: UUID, exam_id: UUID, teacher: User) -> dict:
        exam = self._ensure_exam_context(class_id, exam_id, teacher)
        if exam.status not in self.REVIEWABLE_EXAM_STATUSES:
            raise errors.exam_not_reviewable({"status": exam.status})

        submission_rows = self.repository.list_submissions_with_students(class_id, exam_id, teacher.id)
        answer_rows = self.repository.list_review_rows(class_id, exam_id, teacher.id)
        submissions: dict[UUID, dict] = {}
        for submission, student in submission_rows:
            submissions[submission.id] = {
                "submission_id": submission.id,
                "student_id": student.id,
                "student_full_name": student.full_name,
                "student_email": student.email,
                "total_score": submission.total_score,
                "max_score": submission.max_score,
                "needs_review_count": submission.needs_review_count,
                "status": submission.status,
                "answers": [],
            }

        for submission, _student, answer, question in answer_rows:
            submission_payload = submissions.get(submission.id)
            if submission_payload is None:
                continue
            submission_payload["answers"].append(self._answer_payload(answer, question))

        submission_payloads = list(submissions.values())
        return {
            "exam": {
                "id": exam.id,
                "title": exam.title,
                "status": exam.status,
                "total_points": exam.total_points,
            },
            "summary": {
                "submission_count": len(submission_payloads),
                "needs_review_submission_count": sum(
                    1 for submission in submission_payloads if submission["needs_review_count"] > 0
                ),
                "needs_review_answer_count": sum(
                    1
                    for submission in submission_payloads
                    for answer in submission["answers"]
                    if answer["needs_review"]
                ),
                "approved_count": sum(
                    1 for submission in submission_payloads if submission["status"] == SubmissionStatus.APPROVED.value
                ),
            },
            "submissions": submission_payloads,
        }

    def review_answer(
        self,
        *,
        class_id: UUID,
        exam_id: UUID,
        answer_id: UUID,
        payload: AnswerReviewRequest,
        teacher: User,
    ) -> dict:
        exam = self._ensure_exam_context(class_id, exam_id, teacher)
        if exam.status not in self.REVIEWABLE_EXAM_STATUSES:
            raise errors.exam_not_reviewable({"status": exam.status})

        context = self.repository.get_answer_context(
            class_id=class_id,
            exam_id=exam_id,
            answer_id=answer_id,
            teacher_id=teacher.id,
        )
        if context is None:
            raise errors.answer_not_found()
        answer, submission, question = context
        self._validate_score(payload.teacher_score, answer, question)

        old_score = answer.final_score
        answer.teacher_score = payload.teacher_score
        answer.final_score = payload.teacher_score
        answer.reviewed_by_teacher = True
        answer.needs_review = False
        if payload.feedback is not None:
            answer.ai_feedback = payload.feedback

        try:
            if old_score != payload.teacher_score:
                self.repository.create_grade_change_log(
                    answer=answer,
                    old_score=old_score,
                    new_score=payload.teacher_score,
                    reason=payload.reason,
                )
            self._recalculate_submission(submission)
            self.repository.save(answer, submission)
            self.repository.refresh(answer, submission)
        except SQLAlchemyError as exc:
            self.repository.rollback()
            raise errors.grade_change_log_failed() from exc

        return {
            "answer_id": answer.id,
            "submission_id": submission.id,
            "teacher_score": answer.teacher_score,
            "final_score": answer.final_score,
            "reviewed_by_teacher": answer.reviewed_by_teacher,
            "needs_review": answer.needs_review,
            "submission_total_score": submission.total_score,
            "submission_max_score": submission.max_score,
            "submission_needs_review_count": submission.needs_review_count,
        }

    def approve_results(self, class_id: UUID, exam_id: UUID, teacher: User) -> dict:
        exam = self._ensure_exam_context(class_id, exam_id, teacher)
        if exam.status not in self.APPROVABLE_EXAM_STATUSES:
            raise errors.exam_not_reviewable({"status": exam.status})

        submissions = [
            submission
            for submission, _student in self.repository.list_submissions_with_students(class_id, exam_id, teacher.id)
            if submission.status in self.RELEVANT_SUBMISSION_STATUSES
        ]
        if not submissions:
            raise errors.exam_not_reviewable({"submissions": ["No submitted or graded submissions exist."]})

        confirmed_questions = self.repository.list_confirmed_questions(class_id, exam_id, teacher.id)
        if not confirmed_questions:
            raise errors.exam_not_reviewable({"questions": ["No confirmed questions exist."]})

        missing: dict[str, list[str]] = defaultdict(list)
        for submission in submissions:
            answers = self.repository.list_active_answers_for_submission(submission)
            if not answers:
                missing["submissions"].append(str(submission.id))
                continue
            if any(answer.needs_review for answer in answers):
                missing["needs_review"].append(str(submission.id))
            answers_by_question_id = {answer.question_id: answer for answer in answers}
            for question in confirmed_questions:
                answer = answers_by_question_id.get(question.id)
                if answer is None or answer.final_score is None:
                    missing["final_scores"].append(str(submission.id))
                    break

        if missing:
            raise errors.exam_not_reviewable(dict(missing))

        now = datetime.now(timezone.utc)
        for submission in submissions:
            submission.status = SubmissionStatus.APPROVED.value
            submission.teacher_approved_at = now
        exam.status = ExamStatus.APPROVED.value
        self.repository.save(exam, *submissions)

        return {
            "exam_id": exam.id,
            "status": exam.status,
            "approved_submissions": len(submissions),
        }

    def _ensure_exam_context(self, class_id: UUID, exam_id: UUID, teacher: User):
        classroom = self.repository.get_class_for_teacher(class_id, teacher.id)
        if classroom is None:
            raise errors.class_not_found()
        exam = self.repository.get_exam_for_teacher_class(class_id, exam_id, teacher.id)
        if exam is None:
            raise errors.exam_not_found()
        return exam

    def _recalculate_submission(self, submission: Submission) -> None:
        confirmed_questions = self.repository.list_confirmed_questions(
            submission.class_id,
            submission.exam_id,
            submission.teacher_id,
        )
        answers = self.repository.list_active_answers_for_submission(submission)
        question_ids = {question.id for question in confirmed_questions}
        answer_question_ids = {answer.question_id for answer in answers}
        submission.max_score = sum((Decimal(question.points) for question in confirmed_questions), Decimal("0"))
        submission.total_score = sum(
            (answer.final_score for answer in answers if answer.final_score is not None),
            Decimal("0"),
        )
        submission.needs_review_count = sum(1 for answer in answers if answer.needs_review)
        if submission.needs_review_count == 0 and question_ids.issubset(answer_question_ids) and all(
            answer.final_score is not None for answer in answers
        ):
            submission.status = SubmissionStatus.TEACHER_REVIEWED.value

    @staticmethod
    def _validate_score(score: Decimal, answer: Answer, question: Question) -> None:
        max_score = answer.max_score if answer.max_score is not None else Decimal(question.points)
        if score < 0 or score > max_score:
            raise errors.invalid_score({"teacher_score": [f"Score must be between 0 and {max_score}."]})

    @staticmethod
    def _answer_payload(answer: Answer, question: Question) -> dict:
        return {
            "answer_id": answer.id,
            "question_id": question.id,
            "question_type": question.type,
            "question_text": question.text,
            "student_answer": answer.student_answer,
            "answer_data": answer.answer_data,
            "correct_answer": question.correct_answer,
            "correct_answer_data": question.correct_answer_data,
            "expected_answer": question.expected_answer,
            "rubric": question.rubric,
            "grading_instructions": question.grading_instructions,
            "auto_score": answer.auto_score,
            "teacher_score": answer.teacher_score,
            "final_score": answer.final_score,
            "max_score": answer.max_score,
            "ai_feedback": answer.ai_feedback,
            "ai_confidence": answer.ai_confidence,
            "needs_review": answer.needs_review,
            "reviewed_by_teacher": answer.reviewed_by_teacher,
        }
