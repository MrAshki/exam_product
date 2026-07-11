import type { DecimalValue } from "@/lib/decimal";

export type QuestionType = "multiple_choice" | "short_answer" | "essay" | "true_false";

export type QuestionStatus = "empty" | "draft" | "extracted" | "needs_review" | "confirmed";

export type QuestionOption = {
  id?: string;
  option_key: string;
  option_text: string;
  is_correct: boolean;
};

export type QuestionSlot = {
  id: string;
  class_id?: string;
  exam_id?: string;
  order_index: number;
  type: QuestionType;
  status: QuestionStatus;
  text: string | null;
  points: DecimalValue;
  teacher_confirmed: boolean;
  needs_teacher_review: boolean;
};

export type Question = QuestionSlot & {
  correct_answer?: string | null;
  correct_answer_data?: unknown;
  expected_answer?: string | null;
  grading_instructions?: string | null;
  rubric?: unknown;
  rubric_ai_suggested?: unknown;
  rubric_teacher_confirmed?: boolean;
  options?: QuestionOption[];
};

export type QuestionUpdatePayload = {
  text?: string | null;
  points?: DecimalValue | null;
  correct_answer?: string | null;
  correct_answer_data?: unknown;
  expected_answer?: string | null;
  grading_instructions?: string | null;
  rubric?: unknown;
  rubric_teacher_confirmed?: boolean | null;
  options?: QuestionOption[] | null;
};

export type RubricSuggestion = {
  question_id: string;
  rubric_ai_suggested: unknown;
  rubric_teacher_confirmed: boolean;
  teacher_confirmed: boolean;
  needs_teacher_review: boolean;
};
