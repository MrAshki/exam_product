from app.infrastructure.email.templates.types import RenderedEmail


def render(payload: dict) -> RenderedEmail:
    student_name = payload.get("student_full_name", "")
    exam_title = payload.get("exam_title", "")
    class_title = payload.get("class_title", "")
    result_link = payload.get("result_link", "")

    subject = f"Results published: {exam_title}".strip()
    body_text = (
        f"Hello {student_name},\n\n"
        f"Your result for {exam_title} in {class_title} has been published.\n"
        f"Result link: {result_link}\n"
    )
    body_html = (
        f"<p>Hello {student_name},</p>"
        f"<p>Your result for <strong>{exam_title}</strong> in {class_title} has been published.</p>"
        f"<p><a href=\"{result_link}\">View result</a></p>"
    )
    return RenderedEmail(subject=subject, body_text=body_text, body_html=body_html)
