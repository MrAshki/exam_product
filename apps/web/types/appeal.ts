export type AppealStatus = "pending" | "accepted" | "rejected" | "resolved" | string;

export type AppealListParams = {
  status?: string | null;
  exam_id?: string | null;
  student_id?: string | null;
  page?: number;
  page_size?: number;
};

export type AppealListItem = {
  id: string;
  student_id: string;
  student_full_name: string;
  exam_id: string;
  exam_title: string;
  answer_id: string | null;
  status: AppealStatus;
  created_at: string;
};

export type AppealList = {
  items: AppealListItem[];
  page: number;
  page_size: number;
  total: number;
};

export type AppealAnswer = {
  answer_id: string;
  question_id: string;
  question_text: string | null;
  question_type: string;
  student_answer: string | null;
  answer_data: Record<string, unknown> | unknown[] | null;
  correct_answer: string | null;
  correct_answer_data: Record<string, unknown> | unknown[] | null;
  expected_answer: string | null;
  current_score: string | null;
  max_score: string | null;
  ai_feedback: string | null;
  teacher_feedback: string | null;
  ai_confidence: string | null;
};

export type AppealDetail = {
  id: string;
  student_id: string;
  student_full_name: string;
  student_email: string;
  exam_id: string;
  exam_title: string;
  submission_id: string;
  answer_id: string | null;
  message: string;
  status: AppealStatus;
  teacher_response: string | null;
  old_score: string | null;
  new_score: string | null;
  created_at: string;
  resolved_at: string | null;
  total_score?: string | null;
  max_score?: string | null;
  needs_review_count?: number | null;
  answer: AppealAnswer | null;
};

export type AppealResolvePayload = {
  status: "accepted" | "rejected";
  new_score?: string | null;
  teacher_response: string;
};

export type AppealResolveResult = {
  appeal_id: string;
  status: string;
  final_decision: string;
  score_changed: boolean;
};
