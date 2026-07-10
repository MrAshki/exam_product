import { getExam } from "@/features/exams/api";
import { apiClient } from "@/lib/api-client";
import type { Blueprint, BlueprintPayload } from "@/types/blueprint";
import type { Exam } from "@/types/exam";
import type { Question, QuestionUpdatePayload, RubricSuggestion } from "@/types/question";

export { getExam };

export function getBuilderExam(classId: string, examId: string) {
  return getExam(classId, examId);
}

export function getBlueprint(classId: string, examId: string) {
  return apiClient.get<Blueprint>(`/classes/${classId}/exams/${examId}/blueprint`);
}

export function createBlueprint(classId: string, examId: string, payload: BlueprintPayload) {
  return apiClient.post<Blueprint>(`/classes/${classId}/exams/${examId}/blueprint`, payload);
}

export function updateBlueprint(classId: string, examId: string, payload: BlueprintPayload) {
  return apiClient.put<Blueprint>(`/classes/${classId}/exams/${examId}/blueprint`, payload);
}

export function listQuestions(classId: string, examId: string) {
  return apiClient.get<Question[]>(`/classes/${classId}/exams/${examId}/questions/`);
}

export function updateQuestion(classId: string, examId: string, questionId: string, payload: QuestionUpdatePayload) {
  return apiClient.put<Question>(`/classes/${classId}/exams/${examId}/questions/${questionId}`, payload);
}

export function confirmQuestion(classId: string, examId: string, questionId: string) {
  return apiClient.post<Question>(`/classes/${classId}/exams/${examId}/questions/${questionId}/confirm`);
}

export function suggestRubric(classId: string, examId: string, questionId: string) {
  return apiClient.post<RubricSuggestion>(`/classes/${classId}/exams/${examId}/questions/${questionId}/suggest-rubric`);
}

export type { Exam };
