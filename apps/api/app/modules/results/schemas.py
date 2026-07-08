from pydantic import BaseModel, ConfigDict


class PublishResultsRead(BaseModel):
    exam_id: str
    status: str
    created_result_tokens: int
    leaderboard_enabled: bool
    queued_result_emails: int


class ResultAnswerRead(BaseModel):
    question_text: str | None
    question_type: str
    student_answer: str | None
    answer_data: dict | list | None
    correct_answer: str | None = None
    correct_answer_data: dict | list | None = None
    final_score: str | None
    max_score: str | None
    feedback: str | None = None


class PublicResultRead(BaseModel):
    student_full_name: str
    class_title: str
    exam_title: str
    total_score: str | None
    max_score: str | None
    answers: list[ResultAnswerRead]
    can_appeal: bool


class LeaderboardItemRead(BaseModel):
    rank: int
    student_full_name: str
    score: str | None
    max_score: str | None
    percentage: float | None


class PublicLeaderboardRead(BaseModel):
    class_title: str
    exam_title: str
    items: list[LeaderboardItemRead]


class _OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
