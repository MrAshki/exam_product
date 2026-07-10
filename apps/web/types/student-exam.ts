export type StudentExamAccessStatus = "waiting" | "ready" | "in_progress" | "submitted" | string;

export type StudentExamQuestionType = "multiple_choice" | "true_false" | "short_answer" | "essay";

export type StudentExamAccess = {
  status: StudentExamAccessStatus;
  exam_title: string;
  class_title: string;
  student_full_name: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
};

export type StudentExamOption = {
  option_key: string;
  option_text: string;
};

export type StudentExamQuestion = {
  id: string;
  order_index: number;
  type: StudentExamQuestionType;
  text: string;
  points: number;
  options: StudentExamOption[];
};

export type StudentExamSession = {
  submission_id: string;
  started_at: string;
  allowed_until: string;
  questions: StudentExamQuestion[];
};

export type StudentAnswerData = Record<string, string | boolean>;

export type StudentExamAnswerSubmit = {
  question_id: string;
  student_answer: string | null;
  answer_data: StudentAnswerData | null;
};

export type StudentExamSubmitPayload = {
  answers: StudentExamAnswerSubmit[];
};

export type StudentExamSubmitResult = {
  submission_id: string;
  status: string;
  submitted_at: string;
  saved_answers: number;
};
