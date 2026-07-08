from app.infrastructure.email.templates.types import RenderedEmail


def render(payload: dict) -> RenderedEmail:
    teacher_name = payload.get("teacher_name", "")
    exam_title = payload.get("exam_title", "")
    class_title = payload.get("class_title", "")
    submission_count = payload.get("submission_count", "")
    needs_review_count = payload.get("needs_review_count", "")
    review_link = payload.get("review_link", "")

    subject = f"Review ready: {exam_title}".strip()
    body_text = (
        f"Hello {teacher_name},\n\n"
        f"{exam_title} for {class_title} is ready for review.\n"
        f"Submissions: {submission_count}\n"
        f"Need review: {needs_review_count}\n"
        f"Review link: {review_link}\n"
    )
    body_html = (
        f"<p>Hello {teacher_name},</p>"
        f"<p><strong>{exam_title}</strong> for {class_title} is ready for review.</p>"
        f"<p>Submissions: {submission_count}<br>Need review: {needs_review_count}</p>"
        f"<p><a href=\"{review_link}\">Open review</a></p>"
    )
    return RenderedEmail(subject=subject, body_text=body_text, body_html=body_html)
