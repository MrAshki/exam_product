from app.infrastructure.email.templates.types import RenderedEmail


def render(payload: dict) -> RenderedEmail:
    student_name = payload.get("student_full_name", "")
    exam_title = payload.get("exam_title", "")
    class_title = payload.get("class_title", "")
    start_time = payload.get("start_time", "")
    exam_link = payload.get("exam_link", "")

    subject = f"Exam reminder: {exam_title}".strip()
    body_text = (
        f"Hello {student_name},\n\n"
        f"This is a reminder for {exam_title} in {class_title}.\n"
        f"Start time: {start_time}\n"
        f"Exam link: {exam_link}\n"
    )
    body_html = (
        f"<p>Hello {student_name},</p>"
        f"<p>This is a reminder for <strong>{exam_title}</strong> in {class_title}.</p>"
        f"<p>Start time: {start_time}</p>"
        f"<p><a href=\"{exam_link}\">Open exam</a></p>"
    )
    return RenderedEmail(subject=subject, body_text=body_text, body_html=body_html)
