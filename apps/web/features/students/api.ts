import { apiClient } from "@/lib/api-client";
import type { Student, StudentListResponse, StudentPayload } from "@/types/student";

type ListStudentsParams = {
  page?: number;
  page_size?: number;
  search?: string;
};

export function listStudents(classId: string, params: ListStudentsParams = {}) {
  return apiClient.get<StudentListResponse>(`/classes/${classId}/students/`, { query: params });
}

export function getStudent(classId: string, studentId: string) {
  return apiClient.get<Student>(`/classes/${classId}/students/${studentId}`);
}

export function createStudent(classId: string, payload: StudentPayload) {
  return apiClient.post<Student>(`/classes/${classId}/students/`, payload);
}

export function updateStudent(classId: string, studentId: string, payload: Partial<StudentPayload>) {
  return apiClient.put<Student>(`/classes/${classId}/students/${studentId}`, payload);
}

export function removeStudent(classId: string, studentId: string) {
  return apiClient.delete<Record<string, never>>(`/classes/${classId}/students/${studentId}`);
}
