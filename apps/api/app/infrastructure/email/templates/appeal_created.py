from app.infrastructure.email.templates.types import RenderedEmail


def render(payload: dict) -> RenderedEmail:
    teacher_name = payload.get("teacher_name", "")
    student_name = payload.get("student_full_name", "")
    exam_title = payload.get("exam_title", "")
    class_title = payload.get("class_title", "")
    appeal_message = payload.get("appeal_message", "")
    appeal_link = payload.get("appeal_link", "")

    subject = f"New appeal: {exam_title}".strip()
    body_text = (
        f"Hello {teacher_name},\n\n"
        f"{student_name} created an appeal for {exam_title} in {class_title}.\n"
        f"Message: {appeal_message}\n"
        f"Appeal link: {appeal_link}\n"
    )
    body_html = (
        f"<p>Hello {teacher_name},</p>"
        f"<p>{student_name} created an appeal for <strong>{exam_title}</strong> in {class_title}.</p>"
        f"<p>Message: {appeal_message}</p>"
        f"<p><a href=\"{appeal_link}\">Open appeal</a></p>"
    )
    return RenderedEmail(subject=subject, body_text=body_text, body_html=body_html)
