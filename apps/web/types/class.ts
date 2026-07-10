export type Classroom = {
  id: string;
  teacher_id: string;
  title: string;
  subject: string;
  description: string | null;
  academic_year: string | null;
  grade_level: string | null;
  created_at: string;
  updated_at: string;
};

export type ClassroomPayload = {
  title: string;
  subject: string;
  description?: string | null;
  academic_year?: string | null;
  grade_level?: string | null;
};
