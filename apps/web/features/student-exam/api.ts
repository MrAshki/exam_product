import { apiClient } from "@/lib/api-client";
import type {
  StudentExamAccess,
  StudentExamSession,
  StudentExamSubmitPayload,
  StudentExamSubmitResult
} from "@/types/student-exam";

function accessPath(examToken: string) {
  return `/exam/access/${encodeURIComponent(examToken)}`;
}

export function getExamAccess(examToken: string) {
  return apiClient.get<StudentExamAccess>(accessPath(examToken));
}

export function startExam(examToken: string) {
  return apiClient.post<StudentExamSession>(`${accessPath(examToken)}/start`);
}

export function submitExam(examToken: string, payload: StudentExamSubmitPayload) {
  return apiClient.post<StudentExamSubmitResult>(`${accessPath(examToken)}/submit`, payload);
}
