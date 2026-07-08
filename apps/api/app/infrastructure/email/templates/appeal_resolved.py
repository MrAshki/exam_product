from app.infrastructure.email.templates.types import RenderedEmail


def render(payload: dict) -> RenderedEmail:
    student_name = payload.get("student_full_name", "")
    exam_title = payload.get("exam_title", "")
    class_title = payload.get("class_title", "")
    appeal_status = payload.get("appeal_status", "")
    teacher_response = payload.get("teacher_response", "")
    result_link = payload.get("result_link", "")

    subject = f"Appeal resolved: {exam_title}".strip()
    body_text = (
        f"Hello {student_name},\n\n"
        f"Your appeal for {exam_title} in {class_title} is now {appeal_status}.\n"
        f"Teacher response: {teacher_response}\n"
        f"Result link: {result_link}\n"
    )
    body_html = (
        f"<p>Hello {student_name},</p>"
        f"<p>Your appeal for <strong>{exam_title}</strong> in {class_title} "
        f"is now {appeal_status}.</p>"
        f"<p>Teacher response: {teacher_response}</p>"
        f"<p><a href=\"{result_link}\">View result</a></p>"
    )
    return RenderedEmail(subject=subject, body_text=body_text, body_html=body_html)
