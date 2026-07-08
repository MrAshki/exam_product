from app.infrastructure.email.templates.types import RenderedEmail


def render(payload: dict) -> RenderedEmail:
    student_name = payload.get("student_full_name", "")
    exam_title = payload.get("exam_title", "")
    class_title = payload.get("class_title", "")
    teacher_name = payload.get("teacher_name", "")
    start_time = payload.get("start_time", "")
    duration_minutes = payload.get("duration_minutes", "")
    exam_link = payload.get("exam_link", "")

    subject = f"Exam invitation: {exam_title}".strip()
    body_text = (
        f"Hello {student_name},\n\n"
        f"{teacher_name} invited you to take {exam_title} for {class_title}.\n"
        f"Start time: {start_time}\n"
        f"Duration: {duration_minutes} minutes\n"
        f"Exam link: {exam_link}\n"
    )
    body_html = (
        f"<p>Hello {student_name},</p>"
        f"<p>{teacher_name} invited you to take <strong>{exam_title}</strong> "
        f"for {class_title}.</p>"
        f"<p>Start time: {start_time}<br>Duration: {duration_minutes} minutes</p>"
        f"<p><a href=\"{exam_link}\">Open exam</a></p>"
    )
    return RenderedEmail(subject=subject, body_text=body_text, body_html=body_html)
