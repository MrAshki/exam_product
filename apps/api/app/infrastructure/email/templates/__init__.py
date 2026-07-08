from typing import Any, Callable

from app.infrastructure.email.templates.appeal_created import render as render_appeal_created
from app.infrastructure.email.templates.appeal_resolved import render as render_appeal_resolved
from app.infrastructure.email.templates.exam_invitation import render as render_exam_invitation
from app.infrastructure.email.templates.exam_reminder import render as render_exam_reminder
from app.infrastructure.email.templates.student_result_published import render as render_student_result_published
from app.infrastructure.email.templates.teacher_review_ready import render as render_teacher_review_ready
from app.infrastructure.email.templates.types import RenderedEmail
from app.modules.notifications.constants import EmailType


TemplateRenderer = Callable[[dict[str, Any]], RenderedEmail]


TEMPLATE_RENDERERS: dict[str, TemplateRenderer] = {
    EmailType.EXAM_INVITATION.value: render_exam_invitation,
    EmailType.EXAM_REMINDER.value: render_exam_reminder,
    EmailType.TEACHER_REVIEW_READY.value: render_teacher_review_ready,
    EmailType.STUDENT_RESULT_PUBLISHED.value: render_student_result_published,
    EmailType.APPEAL_CREATED.value: render_appeal_created,
    EmailType.APPEAL_RESOLVED.value: render_appeal_resolved,
}


def render_email_template(email_type: str, payload: dict[str, Any]) -> RenderedEmail:
    renderer = TEMPLATE_RENDERERS[email_type]
    return renderer(payload)
