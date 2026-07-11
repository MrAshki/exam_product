from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.exams.errors import (
    blueprint_not_found,
    class_not_found,
    email_send_failed,
    exam_already_draft,
    exam_already_scheduled,
    exam_already_has_blueprint,
    exam_cannot_be_reopened,
    exam_has_submissions,
    exam_has_tokens,
    exam_in_progress,
    exam_not_draft,
    exam_not_finalized,
    exam_not_found,
    exam_not_ready,
    exam_not_scheduled,
    exam_requires_students,
    exam_schedule_invalid,
    exam_title_already_exists,
    validation_error,
)
from app.modules.exams.models import Exam, ExamBlueprint, ExamToken
from app.modules.exams.readiness import ExamReadinessValidator
from app.modules.exams.repository import ExamRepository
from app.modules.exams.schemas import (
    BlueprintCreate,
    BlueprintUpdate,
    ExamCreate,
    ExamInvitationRequest,
    ExamScheduleRequest,
    ExamUpdate,
)
from app.modules.exams.status import ExamStatus, QuestionStatus, QuestionType
from app.modules.notifications.constants import EmailType
from app.modules.notifications.service import NotificationService
from app.modules.questions.models import Question
from app.modules.students.models import Student


class ExamService:
    def __init__(self, db: Session) -> None:
        self.repository = ExamRepository(db)

    def create(self, class_id: UUID, payload: ExamCreate, teacher: User) -> Exam:
        self._ensure_class_owned(class_id, teacher)
        if not self.repository.class_has_active_students(class_id, teacher.id):
            raise exam_requires_students()

        title = payload.title.strip()
        if self.repository.get_by_title_for_class(title, class_id, teacher.id):
            raise exam_title_already_exists()

        exam = Exam(
            teacher_id=teacher.id,
            class_id=class_id,
            title=title,
            description=self._clean_optional(payload.description),
            start_time=payload.start_time,
            end_time=payload.end_time,
            duration_minutes=payload.duration_minutes,
            status=ExamStatus.DRAFT.value,
            total_points=payload.total_points,
            show_leaderboard=payload.show_leaderboard,
            allow_appeals=payload.allow_appeals,
            show_correct_answers=payload.show_correct_answers,
            show_feedback=payload.show_feedback,
        )

        try:
            return self.repository.create(exam)
        except IntegrityError:
            self.repository.rollback()
            raise exam_title_already_exists() from None

    def list(self, class_id: UUID, teacher: User) -> list[Exam]:
        self._ensure_class_owned(class_id, teacher)
        return self.repository.list_by_class_for_teacher(class_id, teacher.id)

    def get(self, class_id: UUID, exam_id: UUID, teacher: User) -> Exam:
        self._ensure_class_owned(class_id, teacher)
        exam = self.repository.get_by_id_for_teacher_class(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        return exam

    def update(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: ExamUpdate,
        teacher: User,
    ) -> Exam:
        exam = self.get(class_id, exam_id, teacher)
        self._ensure_exam_is_draft(exam)
        update_data = payload.model_dump(exclude_unset=True)

        if "title" in update_data and update_data["title"] is not None:
            title = update_data["title"].strip()
            duplicate = self.repository.get_by_title_for_class(
                title,
                class_id,
                teacher.id,
                exclude_exam_id=exam.id,
            )
            if duplicate is not None:
                raise exam_title_already_exists()
            exam.title = title

        for field_name in [
            "start_time",
            "end_time",
            "duration_minutes",
            "total_points",
            "show_leaderboard",
            "allow_appeals",
            "show_correct_answers",
            "show_feedback",
        ]:
            if field_name in update_data:
                setattr(exam, field_name, update_data[field_name])

        if "description" in update_data:
            exam.description = self._clean_optional(update_data["description"])

        try:
            return self.repository.save(exam)
        except IntegrityError:
            self.repository.rollback()
            raise exam_title_already_exists() from None

    def delete(self, class_id: UUID, exam_id: UUID, teacher: User) -> None:
        exam = self.get(class_id, exam_id, teacher)
        self.repository.soft_delete_exam_tree(exam)

    def schedule(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: ExamScheduleRequest,
        teacher: User,
    ) -> dict:
        self._ensure_schedule_window(payload)
        self._ensure_class_owned(class_id, teacher)
        exam = self.repository.get_by_id_for_teacher_class(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        if exam.status == ExamStatus.SCHEDULED.value:
            raise exam_already_scheduled()
        if exam.status != ExamStatus.FINALIZED.value:
            raise exam_not_finalized({"status": exam.status})

        students = self.repository.list_active_students_for_class(class_id, teacher.id)
        if not students:
            raise exam_not_ready({"students": ["Class must have at least one active student."]})
        readiness = self._build_readiness(exam, teacher)
        if not readiness["is_ready"]:
            raise exam_not_ready({"readiness": readiness})

        exam.start_time = payload.start_time
        exam.end_time = payload.end_time
        exam.duration_minutes = payload.duration_minutes
        exam.status = ExamStatus.SCHEDULED.value
        tokens = self._build_missing_tokens(exam, students)

        try:
            saved_exam = self.repository.save_exam_with_tokens(exam, tokens)
        except IntegrityError:
            self.repository.rollback()
            raise exam_not_ready({"exam_tokens": ["Exam tokens could not be created."]}) from None

        return {
            "id": saved_exam.id,
            "status": saved_exam.status,
            "start_time": saved_exam.start_time,
            "end_time": saved_exam.end_time,
            "duration_minutes": saved_exam.duration_minutes,
            "created_exam_tokens": len(tokens),
        }

    def get_readiness(self, class_id: UUID, exam_id: UUID, teacher: User) -> dict:
        exam = self.get(class_id, exam_id, teacher)
        readiness = self._build_readiness(exam, teacher)
        readiness.update(self._build_reopen_state(exam, teacher))
        return readiness

    def finalize(self, class_id: UUID, exam_id: UUID, teacher: User) -> dict:
        self._ensure_class_owned(class_id, teacher)
        exam = self.repository.get_by_id_for_teacher_class_for_update(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        self._ensure_exam_is_draft(exam)

        readiness = self._build_readiness(exam, teacher)
        if not readiness["is_ready"]:
            raise exam_not_ready({"readiness": readiness})

        questions = self.repository.list_questions_for_exam(exam.id, class_id, teacher.id)
        for question in questions:
            question.status = QuestionStatus.CONFIRMED.value
            question.teacher_confirmed = True
            question.needs_teacher_review = False

        exam.status = ExamStatus.FINALIZED.value
        try:
            saved_exam = self.repository.save_exam_with_questions(exam, questions)
        except IntegrityError:
            self.repository.rollback()
            raise exam_not_ready({"exam": ["Exam could not be finalized."]}) from None

        finalized_readiness = self._build_readiness(saved_exam, teacher)
        return {
            "exam_id": saved_exam.id,
            "status": saved_exam.status,
            "total_question_count": finalized_readiness["total_question_count"],
            "complete_question_count": finalized_readiness["complete_question_count"],
            "calculated_question_points": finalized_readiness["calculated_question_points"],
            "exam_total_points": finalized_readiness["exam_total_points"],
            "scheduling_allowed": finalized_readiness["scheduling_allowed"],
            "pdf_download_allowed": False,
        }

    def reopen(self, class_id: UUID, exam_id: UUID, teacher: User) -> dict:
        self._ensure_class_owned(class_id, teacher)
        exam = self.repository.get_by_id_for_teacher_class_for_update(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        previous_status = exam.status
        reopen_state = self._build_reopen_state(exam, teacher)
        submission_count = self.repository.count_active_submissions_for_exam(exam.id, class_id, teacher.id)
        if submission_count:
            raise exam_has_submissions(self._reopen_details(exam, submission_count=submission_count))
        if previous_status == ExamStatus.DRAFT.value:
            raise exam_already_draft(self._reopen_details(exam))
        if previous_status == ExamStatus.FINALIZED.value:
            if self.repository.has_active_tokens_for_exam(exam.id, class_id, teacher.id):
                raise exam_has_tokens({"exam_id": str(exam.id)})
        elif previous_status == ExamStatus.SCHEDULED.value:
            self._ensure_scheduled_reopen_allowed(exam)
        else:
            raise exam_cannot_be_reopened(self._reopen_details(exam))

        questions = self.repository.list_questions_for_exam(exam.id, class_id, teacher.id)
        for question in questions:
            question.status = QuestionStatus.DRAFT.value if self._question_has_content(question) else QuestionStatus.EMPTY.value
            question.teacher_confirmed = False

        tokens_to_invalidate: list[ExamToken] = []
        if previous_status == ExamStatus.SCHEDULED.value:
            tokens_to_invalidate = self.repository.list_active_tokens_for_exam(exam.id, class_id, teacher.id)
            for token in tokens_to_invalidate:
                token.soft_delete()
            exam.start_time = None
            exam.end_time = None

        exam.status = ExamStatus.DRAFT.value
        try:
            saved_exam = self.repository.save_reopened_exam(exam, questions, tokens_to_invalidate)
        except IntegrityError:
            self.repository.rollback()
            raise exam_not_ready({"exam": ["Exam could not be reopened."]}) from None
        scheduled_reopen = previous_status == ExamStatus.SCHEDULED.value
        return {
            "exam_id": saved_exam.id,
            "previous_status": previous_status,
            "status": saved_exam.status,
            "invalidated_token_count": len(tokens_to_invalidate),
            "start_time": saved_exam.start_time,
            "end_time": saved_exam.end_time,
            "questions_reset": len(questions),
            "message": (
                "زمان‌بندی لغو شد و آزمون برای ویرایش بازگشایی شد."
                if scheduled_reopen
                else "آزمون برای ویرایش بازگشایی شد."
            ),
        }

    def send_invitations(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: ExamInvitationRequest,
        teacher: User,
    ) -> dict:
        if not payload.send_to_all:
            raise validation_error({"send_to_all": ["Only send_to_all=true is supported in this phase."]})

        self._ensure_class_owned(class_id, teacher)
        exam = self.repository.get_by_id_for_teacher_class(exam_id, class_id, teacher.id)
        if exam is None:
            raise exam_not_found()
        if exam.status != ExamStatus.SCHEDULED.value:
            raise exam_not_scheduled()

        students = self.repository.list_active_students_for_class(class_id, teacher.id)
        if not students:
            raise exam_not_ready({"students": ["Class must have at least one active student."]})

        self._ensure_tokens_for_active_students(exam, students)
        tokens_by_student_id = {
            token.student_id: token
            for token in self.repository.list_active_tokens_for_exam(exam.id, class_id, teacher.id)
        }

        notification_service = NotificationService(self.repository.db)
        queued_emails = 0
        for student in students:
            token = tokens_by_student_id.get(student.id)
            if token is None:
                raise exam_not_ready({"exam_tokens": ["Missing exam token for an active student."]})
            try:
                notification_service.enqueue_email(
                    email_type=EmailType.EXAM_INVITATION.value,
                    teacher_id=teacher.id,
                    class_id=class_id,
                    exam_id=exam.id,
                    student_id=student.id,
                    to_email=student.email,
                    template_payload=self._build_invitation_payload(
                        exam=exam,
                        student=student,
                        teacher=teacher,
                        token=token,
                    ),
                )
            except Exception as exc:
                raise email_send_failed({"student_id": str(student.id), "email": student.email}) from exc
            queued_emails += 1

        return {"queued_emails": queued_emails}

    def create_blueprint(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: BlueprintCreate,
        teacher: User,
    ) -> ExamBlueprint:
        exam = self.get(class_id, exam_id, teacher)
        self._ensure_exam_is_draft(exam)
        if self.repository.get_blueprint_for_exam(exam.id, class_id, teacher.id):
            raise exam_already_has_blueprint()

        blueprint = self._build_blueprint(class_id, exam_id, payload, teacher)
        questions = self._build_question_slots(class_id, exam_id, teacher, payload)

        try:
            return self.repository.create_blueprint_with_slots(blueprint, questions)
        except IntegrityError:
            self.repository.rollback()
            raise exam_already_has_blueprint() from None

    def get_blueprint(self, class_id: UUID, exam_id: UUID, teacher: User) -> ExamBlueprint:
        exam = self.get(class_id, exam_id, teacher)
        blueprint = self.repository.get_blueprint_for_exam(exam.id, class_id, teacher.id)
        if blueprint is None:
            raise blueprint_not_found()
        return blueprint

    def update_blueprint(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: BlueprintUpdate,
        teacher: User,
    ) -> ExamBlueprint:
        exam = self.get(class_id, exam_id, teacher)
        self._ensure_exam_is_draft(exam)
        blueprint = self.repository.get_blueprint_for_exam(exam.id, class_id, teacher.id)
        if blueprint is None:
            raise blueprint_not_found()

        self._apply_blueprint_counts(blueprint, payload)
        questions = self._build_question_slots(class_id, exam_id, teacher, payload)

        try:
            return self.repository.update_blueprint_and_recreate_slots(blueprint, questions)
        except IntegrityError:
            self.repository.rollback()
            raise exam_already_has_blueprint() from None

    def _ensure_class_owned(self, class_id: UUID, teacher: User) -> None:
        classroom = self.repository.get_class_for_teacher(class_id, teacher.id)
        if classroom is None:
            raise class_not_found()

    @staticmethod
    def _ensure_exam_is_draft(exam: Exam) -> None:
        if exam.status != ExamStatus.DRAFT.value:
            raise exam_not_draft()

    @staticmethod
    def _ensure_schedule_window(payload: ExamScheduleRequest) -> None:
        if payload.start_time >= payload.end_time:
            raise validation_error({"end_time": ["End time must be after start time."]})
        window_minutes = (payload.end_time - payload.start_time) / timedelta(minutes=1)
        if payload.duration_minutes > window_minutes:
            raise validation_error(
                {"duration_minutes": ["Duration must not exceed the scheduled time window."]}
            )

    def _build_readiness(self, exam: Exam, teacher: User) -> dict:
        blueprint = self.repository.get_blueprint_for_exam(exam.id, exam.class_id, teacher.id)
        questions = self.repository.list_questions_for_exam(exam.id, exam.class_id, teacher.id)
        options = self.repository.list_options_for_exam(exam.id, exam.class_id, teacher.id)
        return ExamReadinessValidator().validate(
            exam=exam,
            blueprint=blueprint,
            questions=questions,
            options=options,
        )

    def _build_reopen_state(self, exam: Exam, teacher: User) -> dict:
        submission_count = self.repository.count_active_submissions_for_exam(
            exam.id,
            exam.class_id,
            teacher.id,
        )
        if submission_count:
            return self._reopen_state(
                allowed=False,
                mode="blocked",
                code="EXAM_HAS_SUBMISSIONS",
                message="برای این آزمون پاسخ دانش‌آموز ثبت شده است و تغییر نسخه اصلی آزمون مجاز نیست.",
                has_submissions=True,
            )
        if exam.status == ExamStatus.DRAFT.value:
            return self._reopen_state(
                allowed=False,
                mode="blocked",
                code="EXAM_ALREADY_DRAFT",
                message="آزمون در حال حاضر پیش‌نویس است.",
            )
        if exam.status == ExamStatus.FINALIZED.value:
            has_tokens = self.repository.has_active_tokens_for_exam(exam.id, exam.class_id, teacher.id)
            if has_tokens:
                return self._reopen_state(
                    allowed=False,
                    mode="blocked",
                    code="EXAM_HAS_TOKENS",
                    message="برای این آزمون لینک فعال وجود دارد و بازگشایی مستقیم مجاز نیست.",
                )
            return self._reopen_state(
                allowed=True,
                mode="finalized_reopen",
                message="آزمون می‌تواند برای ویرایش بازگشایی شود.",
            )
        if exam.status == ExamStatus.SCHEDULED.value:
            try:
                schedule_state = self._scheduled_reopen_state(exam)
            except ValueError:
                return self._reopen_state(
                    allowed=False,
                    mode="blocked",
                    code="EXAM_SCHEDULE_INVALID",
                    message="زمان‌بندی آزمون نامعتبر است و بازگشایی امن نیست.",
                )
            if schedule_state == "active":
                return self._reopen_state(
                    allowed=False,
                    mode="blocked",
                    code="EXAM_IN_PROGRESS",
                    message="آزمون در حال برگزاری است و تا پایان بازه آزمون قابل ویرایش نیست.",
                    is_in_progress=True,
                    invalidates_tokens=True,
                )
            return self._reopen_state(
                allowed=True,
                mode=schedule_state,
                message=(
                    "زمان‌بندی لغو می‌شود و لینک‌های قبلی دانش‌آموزان غیرفعال خواهند شد."
                ),
                invalidates_tokens=True,
            )
        return self._reopen_state(
            allowed=False,
            mode="blocked",
            code="EXAM_CANNOT_BE_REOPENED",
            message="این آزمون در این وضعیت قابل بازگشایی نیست.",
        )

    @staticmethod
    def _reopen_state(
        *,
        allowed: bool,
        mode: str,
        message: str,
        code: str | None = None,
        invalidates_tokens: bool = False,
        has_submissions: bool = False,
        is_in_progress: bool = False,
    ) -> dict:
        return {
            "reopen_allowed": allowed,
            "reopen_mode": mode,
            "reopen_block_code": None if allowed else code,
            "reopen_block_message": None if allowed else message,
            "invalidates_tokens": invalidates_tokens,
            "has_submissions": has_submissions,
            "is_in_progress": is_in_progress,
        }

    def _ensure_scheduled_reopen_allowed(self, exam: Exam) -> None:
        try:
            state = self._scheduled_reopen_state(exam)
        except ValueError:
            raise exam_schedule_invalid(self._reopen_details(exam)) from None
        if state == "active":
            raise exam_in_progress(self._reopen_details(exam))

    def _scheduled_reopen_state(self, exam: Exam) -> str:
        if exam.start_time is None or exam.end_time is None:
            raise ValueError("Scheduled exam is missing start_time or end_time.")
        start_time = self._as_aware_utc(exam.start_time)
        end_time = self._as_aware_utc(exam.end_time)
        if start_time >= end_time:
            raise ValueError("Scheduled exam has an invalid time window.")
        now = self._now()
        if now < start_time:
            return "scheduled_before_start"
        if start_time <= now < end_time:
            return "active"
        return "scheduled_after_end"

    def _reopen_details(self, exam: Exam, *, submission_count: int = 0) -> dict:
        return {
            "status": exam.status,
            "start_time": exam.start_time.isoformat() if exam.start_time else None,
            "end_time": exam.end_time.isoformat() if exam.end_time else None,
            "current_time": self._now().isoformat(),
            "submission_count": submission_count,
        }

    @staticmethod
    def _question_has_content(question: Question) -> bool:
        return any(
            [
                bool(question.text),
                bool(question.correct_answer),
                bool(question.correct_answer_data),
                bool(question.expected_answer),
                question.points > 0,
                bool(question.grading_instructions),
                bool(question.rubric),
                bool(question.rubric_ai_suggested),
            ]
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _as_aware_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _ensure_tokens_for_active_students(self, exam: Exam, students: list[Student]) -> None:
        tokens = self._build_missing_tokens(exam, students)
        if not tokens:
            return
        try:
            self.repository.create_tokens(tokens)
        except IntegrityError:
            self.repository.rollback()
            raise exam_not_ready({"exam_tokens": ["Exam tokens could not be created."]}) from None

    def _build_missing_tokens(self, exam: Exam, students: list[Student]) -> list[ExamToken]:
        active_tokens = self.repository.list_active_tokens_for_exam(
            exam_id=exam.id,
            class_id=exam.class_id,
            teacher_id=exam.teacher_id,
        )
        existing_student_ids = {token.student_id for token in active_tokens}
        return [
            ExamToken(
                teacher_id=exam.teacher_id,
                class_id=exam.class_id,
                exam_id=exam.id,
                student_id=student.id,
                token=self._generate_unique_token(),
                expires_at=exam.end_time,
            )
            for student in students
            if student.id not in existing_student_ids
        ]

    def _generate_unique_token(self) -> str:
        for _ in range(10):
            token = secrets.token_urlsafe(48)
            if not self.repository.token_exists(token):
                return token
        raise exam_not_ready({"exam_tokens": ["Could not generate a unique exam token."]})

    @staticmethod
    def _build_invitation_payload(
        *,
        exam: Exam,
        student: Student,
        teacher: User,
        token: ExamToken,
    ) -> dict:
        frontend_base_url = settings.FRONTEND_BASE_URL.rstrip("/")
        return {
            "student_full_name": student.full_name,
            "exam_title": exam.title,
            "class_title": exam.classroom.title if exam.classroom is not None else "",
            "teacher_name": teacher.full_name,
            "start_time": exam.start_time.isoformat() if exam.start_time else None,
            "duration_minutes": exam.duration_minutes,
            "exam_link": f"{frontend_base_url}/exam/access/{token.token}",
        }

    def _build_blueprint(
        self,
        class_id: UUID,
        exam_id: UUID,
        payload: BlueprintCreate | BlueprintUpdate,
        teacher: User,
    ) -> ExamBlueprint:
        blueprint = ExamBlueprint(
            teacher_id=teacher.id,
            class_id=class_id,
            exam_id=exam_id,
        )
        self._apply_blueprint_counts(blueprint, payload)
        return blueprint

    @staticmethod
    def _apply_blueprint_counts(
        blueprint: ExamBlueprint,
        payload: BlueprintCreate | BlueprintUpdate,
    ) -> None:
        blueprint.multiple_choice_count = payload.multiple_choice_count
        blueprint.short_answer_count = payload.short_answer_count
        blueprint.essay_count = payload.essay_count
        blueprint.true_false_count = payload.true_false_count
        blueprint.total_question_count = (
            payload.multiple_choice_count
            + payload.short_answer_count
            + payload.essay_count
            + payload.true_false_count
        )

    @staticmethod
    def _build_question_slots(
        class_id: UUID,
        exam_id: UUID,
        teacher: User,
        payload: BlueprintCreate | BlueprintUpdate,
    ) -> list[Question]:
        slot_types = (
            [QuestionType.MULTIPLE_CHOICE.value] * payload.multiple_choice_count
            + [QuestionType.SHORT_ANSWER.value] * payload.short_answer_count
            + [QuestionType.ESSAY.value] * payload.essay_count
            + [QuestionType.TRUE_FALSE.value] * payload.true_false_count
        )
        return [
            Question(
                teacher_id=teacher.id,
                class_id=class_id,
                exam_id=exam_id,
                type=question_type,
                order_index=index,
            )
            for index, question_type in enumerate(slot_types, start=1)
        ]

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
