export type Student = {
  id: string;
  teacher_id: string;
  full_name: string;
  email: string;
  student_code: string | null;
  is_active: boolean;
  teacher_note: string | null;
  created_at: string;
  updated_at: string;
};

export type StudentListResponse = {
  items: Student[];
  page: number;
  page_size: number;
  total: number;
};

export type StudentPayload = {
  full_name: string;
  email: string;
  student_code?: string | null;
  is_active?: boolean;
  teacher_note?: string | null;
};
