export type SubmissionStatus =
  | "not_started"
  | "in_progress"
  | "submitted"
  | "auto_graded"
  | "needs_review"
  | "teacher_reviewed"
  | "approved"
  | "published"
  | string;

export type ReviewSubmission = {
  submission_id: string;
  student_id: string;
  student_full_name: string;
  student_email: string | null;
  total_score: string | number | null;
  max_score: string | number | null;
  needs_review_count: number;
  status: SubmissionStatus;
};
