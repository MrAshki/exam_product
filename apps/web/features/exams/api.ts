import { apiClient } from "@/lib/api-client";
import type { Exam, ExamPayload } from "@/types/exam";

export function listExams(classId: string) {
  return apiClient.get<Exam[]>(`/classes/${classId}/exams/`);
}

export function getExam(classId: string, examId: string) {
  return apiClient.get<Exam>(`/classes/${classId}/exams/${examId}`);
}

export function createExam(classId: string, payload: ExamPayload) {
  return apiClient.post<Exam>(`/classes/${classId}/exams/`, payload);
}

export function updateExam(classId: string, examId: string, payload: Partial<ExamPayload>) {
  return apiClient.put<Exam>(`/classes/${classId}/exams/${examId}`, payload);
}

export function deleteExam(classId: string, examId: string) {
  return apiClient.delete<Record<string, never>>(`/classes/${classId}/exams/${examId}`);
}
