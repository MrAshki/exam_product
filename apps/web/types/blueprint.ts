export type Blueprint = {
  id: string;
  teacher_id: string;
  class_id: string;
  exam_id: string;
  multiple_choice_count: number;
  short_answer_count: number;
  essay_count: number;
  true_false_count: number;
  total_question_count: number;
  created_at: string;
  updated_at: string;
};

export type BlueprintPayload = {
  multiple_choice_count: number;
  short_answer_count: number;
  essay_count: number;
  true_false_count: number;
};
