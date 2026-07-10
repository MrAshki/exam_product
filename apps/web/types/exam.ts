export type Exam = {
  id: string;
  teacher_id: string;
  class_id: string;
  title: string;
  description: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number | null;
  status: string;
  total_points: number;
  show_leaderboard: boolean;
  allow_appeals: boolean;
  show_correct_answers: boolean;
  show_feedback: boolean;
  created_at: string;
  updated_at: string;
};

export type ExamPayload = {
  title: string;
  description?: string | null;
  duration_minutes?: number | null;
  total_points?: number;
  show_leaderboard?: boolean;
  allow_appeals?: boolean;
  show_correct_answers?: boolean;
  show_feedback?: boolean;
};
