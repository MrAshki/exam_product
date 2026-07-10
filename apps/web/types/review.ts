import type { ReviewSubmission } from "@/types/submission";

export type ReviewExam = {
  id: string;
  title: string;
  status: string;
  total_points?: number | string | null;
};

export type ReviewAnswer = {
  answer_id: string;
  question_id: string;
  question_type: string;
  question_text: string | null;
  student_answer: string | null;
  answer_data: Record<string, unknown> | unknown[] | null;
  correct_answer: string | null;
  correct_answer_data: Record<string, unknown> | unknown[] | null;
  expected_answer: string | null;
  rubric?: unknown;
  grading_instructions?: string | null;
  auto_score: string | number | null;
  teacher_score: string | number | null;
  final_score: string | number | null;
  max_score: string | number | null;
  ai_feedback: string | null;
  ai_confidence: string | number | null;
  needs_review: boolean;
  reviewed_by_teacher: boolean;
};

export type ReviewSubmissionWithAnswers = ReviewSubmission & {
  answers: ReviewAnswer[];
};

export type ReviewSummary = {
  submission_count: number;
  needs_review_submission_count: number;
  needs_review_answer_count: number;
  approved_count: number;
};

export type ExamReview = {
  exam: ReviewExam;
  summary: ReviewSummary;
  submissions: ReviewSubmissionWithAnswers[];
};

export type AnswerReviewPayload = {
  teacher_score: string | number;
  feedback?: string | null;
  reason?: string | null;
};

export type AnswerReviewResult = {
  answer_id: string;
  submission_id: string;
  teacher_score: string | number;
  final_score: string | number;
  reviewed_by_teacher: boolean;
  needs_review: boolean;
  submission_total_score: string | number;
  submission_max_score: string | number;
  submission_needs_review_count: number;
};

export type ApproveResultsResult = {
  exam_id: string;
  status: string;
  approved_submissions: number;
};

export type PublishResultsResult = {
  exam_id: string;
  status: string;
  created_result_tokens: number;
  leaderboard_enabled: boolean;
  queued_result_emails: number;
};
