import type { DecimalValue } from "@/lib/decimal";

export type ExamStatus = "draft" | "finalized" | "scheduled" | "review_required" | "approved" | "published";

export type Exam = {
  id: string;
  teacher_id: string;
  class_id: string;
  title: string;
  description: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number | null;
  status: ExamStatus;
  total_points: DecimalValue;
  show_leaderboard: boolean;
  allow_appeals: boolean;
  show_correct_answers: boolean;
  show_feedback: boolean;
  created_at: string;
  updated_at: string;
};

export type ExamReadinessFailure = {
  question_id: string | null;
  order_index: number | null;
  question_type: string | null;
  code: string;
  field: string | null;
  message: string;
};

export type ExamReadiness = {
  exam_id: string;
  exam_status: ExamStatus;
  is_ready: boolean;
  finalization_allowed: boolean;
  scheduling_allowed: boolean;
  total_question_count: number;
  complete_question_count: number;
  incomplete_question_count: number;
  calculated_question_points: DecimalValue;
  exam_total_points: DecimalValue;
  points_match: boolean;
  blueprint_match: boolean;
  failures: ExamReadinessFailure[];
  reopen_allowed: boolean;
  reopen_mode: "finalized_reopen" | "scheduled_before_start" | "scheduled_after_end" | "blocked";
  reopen_block_code: string | null;
  reopen_block_message: string | null;
  invalidates_tokens: boolean;
  has_submissions: boolean;
  is_in_progress: boolean;
};

export type ExamFinalizeResult = {
  exam_id: string;
  status: ExamStatus;
  total_question_count: number;
  complete_question_count: number;
  calculated_question_points: DecimalValue;
  exam_total_points: DecimalValue;
  scheduling_allowed: boolean;
  pdf_download_allowed: boolean;
};

export type ExamReopenResult = {
  exam_id: string;
  previous_status: ExamStatus;
  status: ExamStatus;
  invalidated_token_count: number;
  start_time: string | null;
  end_time: string | null;
  questions_reset: number;
  message: string;
};

export type ExamPayload = {
  title: string;
  description?: string | null;
  duration_minutes?: number | null;
  total_points?: DecimalValue;
  show_leaderboard?: boolean;
  allow_appeals?: boolean;
  show_correct_answers?: boolean;
  show_feedback?: boolean;
};
