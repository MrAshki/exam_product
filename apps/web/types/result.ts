export type ResultAnswer = {
  question_text: string | null;
  question_type: string;
  student_answer: string | null;
  answer_data: Record<string, unknown> | unknown[] | null;
  correct_answer?: string | null;
  correct_answer_data?: Record<string, unknown> | unknown[] | null;
  final_score: string | null;
  max_score: string | null;
  feedback?: string | null;
};

export type StudentResult = {
  student_full_name: string;
  class_title: string;
  exam_title: string;
  total_score: string | null;
  max_score: string | null;
  answers: ResultAnswer[];
  can_appeal: boolean;
};

export type ResultAppealPayload = {
  answer_id?: string | null;
  message: string;
};

export type ResultAppeal = {
  appeal_id: string;
  status: string;
};
