from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from apps.worker.shared.worker_context import worker_db_session
from app.core.constants import AI_GRADING_REVIEW_CONFIDENCE_THRESHOLD
from app.modules.ai.schemas import AICallContext
from app.modules.ai.service import AIService
from app.modules.classrooms.models import Classroom
from app.modules.exams.models import Exam
from app.modules.exams.status import QuestionStatus, QuestionType
from app.modules.grading.feedback import normalize_feedback
from app.modules.grading.review_decision import ReviewDecisionService
from app.modules.jobs.models import JobLog
from app.modules.jobs.status import JobStatus
from app.modules.questions.models import Question
from app.modules.students.models import Student
from app.modules.submissions.models import Answer, Submission
from app.modules.submissions.status import ReviewReasonCode, SubmissionStatus, apply_grading_status_transition


class DeterministicGradingWorkerService:
    def run(self, payload: dict) -> dict:
        job_id = payload["job_id"]
        job_uuid = UUID(job_id)

        with worker_db_session() as db:
            job = db.scalar(select(JobLog).where(JobLog.id == job_uuid))
            if job is None:
                return {"success": False, "error_message": f"Job log not found: {job_id}"}

            self._mark_running(db, job)
            try:
                result = self._grade(db, job, payload)
            except Exception as exc:
                db.rollback()
                self._mark_failed(db, job, str(exc))
                return {"success": False, "error_message": str(exc)}

            job.result_json = result
            job.status = JobStatus.SUCCESS.value
            job.error_code = None
            job.error_message = None
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            return result

    def _grade(self, db, job: JobLog, payload: dict) -> dict:
        teacher_id = self._required_uuid(payload, "teacher_id")
        class_id = self._required_uuid(payload, "class_id")
        exam_id = self._required_uuid(payload, "exam_id")
        submission_id = self._required_uuid(payload, "submission_id")

        if job.submission_id is not None and job.submission_id != submission_id:
            raise ValueError("Job submission_id does not match payload.")
        if job.exam_id is not None and job.exam_id != exam_id:
            raise ValueError("Job exam_id does not match payload.")

        submission = db.scalar(
            select(Submission).where(
                Submission.id == submission_id,
                Submission.teacher_id == teacher_id,
                Submission.class_id == class_id,
                Submission.exam_id == exam_id,
                Submission.deleted_at.is_(None),
            )
        )
        if submission is None:
            raise ValueError("Submission not found or mismatched.")

        exam = db.scalar(
            select(Exam).where(
                Exam.id == exam_id,
                Exam.teacher_id == teacher_id,
                Exam.class_id == class_id,
                Exam.deleted_at.is_(None),
            )
        )
        if exam is None:
            raise ValueError("Exam not found or mismatched.")

        classroom = db.scalar(
            select(Classroom).where(
                Classroom.id == class_id,
                Classroom.teacher_id == teacher_id,
                Classroom.deleted_at.is_(None),
            )
        )
        if classroom is None:
            raise ValueError("Class not found or mismatched.")

        student = db.scalar(
            select(Student).where(
                Student.id == submission.student_id,
                Student.teacher_id == teacher_id,
                Student.deleted_at.is_(None),
            )
        )
        if student is None:
            raise ValueError("Student not found or mismatched.")

        questions = list(
            db.scalars(
                select(Question).where(
                    Question.exam_id == exam_id,
                    Question.class_id == class_id,
                    Question.teacher_id == teacher_id,
                    Question.deleted_at.is_(None),
                    Question.teacher_confirmed.is_(True),
                    Question.status == "confirmed",
                )
            ).all()
        )
        questions_by_id = {question.id: question for question in questions}

        answers = list(
            db.scalars(
                select(Answer).where(
                    Answer.submission_id == submission_id,
                    Answer.teacher_id == teacher_id,
                    Answer.class_id == class_id,
                    Answer.exam_id == exam_id,
                    Answer.student_id == submission.student_id,
                    Answer.deleted_at.is_(None),
                )
            ).all()
        )
        if not answers:
            raise ValueError("Submission has no answers to grade.")

        objective_count = 0
        for answer in answers:
            question = questions_by_id.get(answer.question_id)
            if question is None:
                raise ValueError("Answer question not found or mismatched.")
            if question.type not in {QuestionType.MULTIPLE_CHOICE.value, QuestionType.TRUE_FALSE.value}:
                continue

            calculated_score = self._score_objective_answer(question, answer)
            answer.auto_score = calculated_score
            answer.max_score = Decimal(question.points)
            if answer.teacher_score is None:
                answer.final_score = calculated_score
                answer.reviewed_by_teacher = False
            elif answer.final_score is None:
                answer.final_score = answer.teacher_score
            answer.needs_review = False
            answer.review_reason_code = None
            db.add(answer)
            objective_count += 1

        submission.max_score = sum((Decimal(question.points) for question in questions), Decimal("0"))
        final_scores = [answer.final_score for answer in answers if answer.final_score is not None]
        submission.total_score = sum(final_scores, Decimal("0"))
        submission.needs_review_count = sum(1 for answer in answers if answer.needs_review)
        if questions and all(
            question.type in {QuestionType.MULTIPLE_CHOICE.value, QuestionType.TRUE_FALSE.value}
            for question in questions
        ):
            submission.status = apply_grading_status_transition(submission.status, SubmissionStatus.AUTO_GRADED)
        db.add(submission)
        db.commit()
        review_result = ReviewDecisionService(db).evaluate_submission(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            submission_id=submission_id,
        )
        db.refresh(submission)

        return {
            "success": True,
            "graded_answers": objective_count,
            "submission_id": str(submission.id),
            "status": submission.status,
            "total_score": str(submission.total_score) if submission.total_score is not None else None,
            "max_score": str(submission.max_score) if submission.max_score is not None else None,
            "review_decision": review_result,
        }

    @staticmethod
    def _score_objective_answer(question: Question, answer: Answer) -> Decimal:
        if question.type == QuestionType.MULTIPLE_CHOICE.value:
            expected = DeterministicGradingWorkerService._normalize_choice(question.correct_answer)
            if expected is None:
                expected = DeterministicGradingWorkerService._normalize_choice(
                    (question.correct_answer_data or {}).get("selected_option")
                    if isinstance(question.correct_answer_data, dict)
                    else None
                )
            if expected is None:
                expected = DeterministicGradingWorkerService._normalize_choice(
                    (question.correct_answer_data or {}).get("option_key")
                    if isinstance(question.correct_answer_data, dict)
                    else None
                )
            selected = DeterministicGradingWorkerService._normalize_choice(
                (answer.answer_data or {}).get("selected_option")
                if isinstance(answer.answer_data, dict)
                else None
            )
            if selected is None:
                selected = DeterministicGradingWorkerService._normalize_choice(
                    (answer.answer_data or {}).get("option_key")
                    if isinstance(answer.answer_data, dict)
                    else None
                )
            if selected is None:
                selected = DeterministicGradingWorkerService._normalize_choice(answer.student_answer)
            return Decimal(question.points) if selected is not None and selected == expected else Decimal("0")

        expected_bool = DeterministicGradingWorkerService._normalize_bool(
            (question.correct_answer_data or {}).get("value")
            if isinstance(question.correct_answer_data, dict)
            else None
        )
        if expected_bool is None:
            expected_bool = DeterministicGradingWorkerService._normalize_bool(question.correct_answer)
        selected_bool = DeterministicGradingWorkerService._normalize_bool(
            (answer.answer_data or {}).get("value")
            if isinstance(answer.answer_data, dict)
            else None
        )
        return Decimal(question.points) if selected_bool is not None and selected_bool == expected_bool else Decimal("0")

    @staticmethod
    def _normalize_choice(value) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        return normalized or None

    @staticmethod
    def _normalize_bool(value) -> bool | None:
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
        return None

    @staticmethod
    def _required_uuid(payload: dict, key: str) -> UUID:
        value = payload.get(key)
        if not value:
            raise ValueError(f"Missing payload field: {key}")
        return UUID(str(value))

    @staticmethod
    def _mark_running(db, job: JobLog) -> None:
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        job.finished_at = None
        job.attempts = (job.attempts or 0) + 1
        db.add(job)
        db.commit()

    @staticmethod
    def _mark_failed(db, job: JobLog, error_message: str) -> None:
        job.status = JobStatus.FAILED.value
        job.error_message = error_message
        job.finished_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()


class AIGradingWorkerService:
    SUBJECTIVE_TYPES = {QuestionType.SHORT_ANSWER.value, QuestionType.ESSAY.value}

    def run(self, payload: dict) -> dict:
        job_id = payload["job_id"]
        job_uuid = UUID(job_id)

        with worker_db_session() as db:
            job = db.scalar(select(JobLog).where(JobLog.id == job_uuid))
            if job is None:
                return {"success": False, "error_message": f"Job log not found: {job_id}"}

            DeterministicGradingWorkerService._mark_running(db, job)
            try:
                result = self._grade_subjective_answers(db, job, payload)
            except Exception as exc:
                db.rollback()
                DeterministicGradingWorkerService._mark_failed(db, job, str(exc))
                return {"success": False, "error_message": str(exc)}

            job.result_json = result
            job.status = JobStatus.SUCCESS.value
            job.error_code = None
            job.error_message = None
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            return result

    def _grade_subjective_answers(self, db, job: JobLog, payload: dict) -> dict:
        teacher_id = DeterministicGradingWorkerService._required_uuid(payload, "teacher_id")
        class_id = DeterministicGradingWorkerService._required_uuid(payload, "class_id")
        exam_id = DeterministicGradingWorkerService._required_uuid(payload, "exam_id")
        submission_id = DeterministicGradingWorkerService._required_uuid(payload, "submission_id")

        if job.submission_id is not None and job.submission_id != submission_id:
            raise ValueError("Job submission_id does not match payload.")
        if job.exam_id is not None and job.exam_id != exam_id:
            raise ValueError("Job exam_id does not match payload.")

        submission = db.scalar(
            select(Submission).where(
                Submission.id == submission_id,
                Submission.teacher_id == teacher_id,
                Submission.class_id == class_id,
                Submission.exam_id == exam_id,
                Submission.deleted_at.is_(None),
            )
        )
        if submission is None:
            raise ValueError("Submission not found or mismatched.")

        exam = db.scalar(
            select(Exam).where(
                Exam.id == exam_id,
                Exam.teacher_id == teacher_id,
                Exam.class_id == class_id,
                Exam.deleted_at.is_(None),
            )
        )
        if exam is None:
            raise ValueError("Exam not found or mismatched.")

        classroom = db.scalar(
            select(Classroom).where(
                Classroom.id == class_id,
                Classroom.teacher_id == teacher_id,
                Classroom.deleted_at.is_(None),
            )
        )
        if classroom is None:
            raise ValueError("Class not found or mismatched.")

        student = db.scalar(
            select(Student).where(
                Student.id == submission.student_id,
                Student.teacher_id == teacher_id,
                Student.deleted_at.is_(None),
            )
        )
        if student is None:
            raise ValueError("Student not found or mismatched.")

        questions = list(
            db.scalars(
                select(Question).where(
                    Question.exam_id == exam_id,
                    Question.class_id == class_id,
                    Question.teacher_id == teacher_id,
                    Question.deleted_at.is_(None),
                    Question.teacher_confirmed.is_(True),
                    Question.status == QuestionStatus.CONFIRMED.value,
                )
            ).all()
        )
        questions_by_id = {question.id: question for question in questions}

        answers = list(
            db.scalars(
                select(Answer).where(
                    Answer.submission_id == submission_id,
                    Answer.teacher_id == teacher_id,
                    Answer.class_id == class_id,
                    Answer.exam_id == exam_id,
                    Answer.student_id == submission.student_id,
                    Answer.deleted_at.is_(None),
                )
            ).all()
        )
        if not answers:
            raise ValueError("Submission has no answers to grade.")

        ai_service = AIService(db)
        graded_count = 0
        failed_count = 0
        for answer in answers:
            question = questions_by_id.get(answer.question_id)
            if question is None:
                raise ValueError("Answer question not found or mismatched.")
            if question.type not in self.SUBJECTIVE_TYPES:
                continue

            if self._has_missing_grading_data(question):
                answer.ai_feedback = None
                answer.ai_confidence = None
                if answer.teacher_score is None:
                    answer.needs_review = True
                    answer.review_reason_code = ReviewReasonCode.MISSING_GRADING_DATA.value
                    answer.reviewed_by_teacher = False
                failed_count += 1
                db.add(answer)
                continue

            task_name = self._task_name_for_question(question)
            try:
                result = ai_service.grade_subjective_answer(
                    task_name=task_name,
                    payload=self._gateway_payload(
                        teacher_id=teacher_id,
                        class_id=class_id,
                        exam_id=exam_id,
                        submission_id=submission_id,
                        answer=answer,
                        question=question,
                    ),
                    max_score=Decimal(question.points),
                    context=AICallContext(
                        teacher_id=teacher_id,
                        class_id=class_id,
                        exam_id=exam_id,
                        question_id=question.id,
                    ),
                )
                confidence = result["confidence"]
                needs_review = bool(result["needs_review"])
                if confidence is None or confidence < Decimal(str(AI_GRADING_REVIEW_CONFIDENCE_THRESHOLD)):
                    needs_review = True

                answer.auto_score = result["score"]
                answer.max_score = Decimal(question.points)
                if answer.teacher_score is None:
                    answer.final_score = result["score"]
                elif answer.final_score is None:
                    answer.final_score = answer.teacher_score
                answer.ai_feedback = normalize_feedback(result["feedback"])
                answer.ai_confidence = confidence
                if answer.teacher_score is None:
                    answer.needs_review = needs_review
                    if confidence is None or confidence < Decimal(str(AI_GRADING_REVIEW_CONFIDENCE_THRESHOLD)):
                        answer.review_reason_code = ReviewReasonCode.AI_LOW_CONFIDENCE.value
                    elif needs_review:
                        answer.review_reason_code = ReviewReasonCode.POLICY_REQUIRES_TEACHER.value
                    else:
                        answer.review_reason_code = None
                    answer.reviewed_by_teacher = False
                graded_count += 1
            except Exception:
                answer.max_score = Decimal(question.points)
                answer.ai_feedback = None
                answer.ai_confidence = None
                if answer.teacher_score is None:
                    answer.needs_review = True
                    answer.review_reason_code = ReviewReasonCode.AI_UNAVAILABLE.value
                    answer.reviewed_by_teacher = False
                failed_count += 1
            db.add(answer)

        self._update_submission_after_ai_grading(submission, answers, questions)
        db.add(submission)
        db.commit()
        review_result = ReviewDecisionService(db).evaluate_submission(
            teacher_id=teacher_id,
            class_id=class_id,
            exam_id=exam_id,
            submission_id=submission_id,
        )
        db.refresh(submission)

        return {
            "success": True,
            "graded_answers": graded_count,
            "failed_answers": failed_count,
            "submission_id": str(submission.id),
            "status": submission.status,
            "total_score": str(submission.total_score) if submission.total_score is not None else None,
            "max_score": str(submission.max_score) if submission.max_score is not None else None,
            "needs_review_count": submission.needs_review_count,
            "review_decision": review_result,
        }

    @staticmethod
    def _task_name_for_question(question: Question) -> str:
        if question.type == QuestionType.SHORT_ANSWER.value:
            return "short_answer_grading"
        if question.type == QuestionType.ESSAY.value:
            return "essay_grading"
        raise ValueError(f"Question type is not AI gradable: {question.type}")

    @staticmethod
    def _gateway_payload(
        *,
        teacher_id: UUID,
        class_id: UUID,
        exam_id: UUID,
        submission_id: UUID,
        answer: Answer,
        question: Question,
    ) -> dict:
        payload = {
            "teacher_id": str(teacher_id),
            "class_id": str(class_id),
            "exam_id": str(exam_id),
            "submission_id": str(submission_id),
            "answer_id": str(answer.id),
            "question_id": str(question.id),
            "question_type": question.type,
            "question_text": question.text or "",
            "expected_answer": question.expected_answer or question.correct_answer or "",
            "student_answer": AIGradingWorkerService._student_answer_text(answer),
            "max_score": str(Decimal(question.points)),
        }
        if question.type == QuestionType.ESSAY.value:
            payload["rubric"] = question.rubric
        return payload

    @staticmethod
    def _student_answer_text(answer: Answer) -> str:
        if answer.student_answer:
            return answer.student_answer
        if isinstance(answer.answer_data, dict):
            value = answer.answer_data.get("text")
            if value is not None:
                return str(value)
        return ""

    @staticmethod
    def _has_missing_grading_data(question: Question) -> bool:
        expected_answer = question.expected_answer or question.correct_answer
        if not question.text or not expected_answer or Decimal(question.points) <= Decimal("0"):
            return True
        return question.type == QuestionType.ESSAY.value and not question.rubric

    @staticmethod
    def _update_submission_after_ai_grading(
        submission: Submission,
        answers: list[Answer],
        questions: list[Question],
    ) -> None:
        submission.max_score = sum((Decimal(question.points) for question in questions), Decimal("0"))
        final_scores = [answer.final_score for answer in answers if answer.final_score is not None]
        submission.total_score = sum(final_scores, Decimal("0"))
        submission.needs_review_count = sum(1 for answer in answers if answer.needs_review)

        confidences = [answer.ai_confidence for answer in answers if answer.ai_confidence is not None]
        if confidences:
            submission.ai_confidence_avg = sum(confidences, Decimal("0")) / Decimal(len(confidences))

        if submission.needs_review_count > 0:
            submission.status = apply_grading_status_transition(submission.status, SubmissionStatus.NEEDS_REVIEW)
        elif answers and all(answer.final_score is not None for answer in answers):
            submission.status = apply_grading_status_transition(submission.status, SubmissionStatus.AUTO_GRADED)
        else:
            submission.status = apply_grading_status_transition(submission.status, SubmissionStatus.SUBMITTED)
