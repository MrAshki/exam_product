import { apiClient } from "@/lib/api-client";
import type { InvitationPayload, InvitationResult, SchedulePayload, ScheduleResult } from "@/types/schedule";

export function scheduleExam(classId: string, examId: string, payload: SchedulePayload) {
  return apiClient.post<ScheduleResult>(`/classes/${classId}/exams/${examId}/schedule`, payload);
}

export function sendInvitations(classId: string, examId: string, payload: InvitationPayload) {
  return apiClient.post<InvitationResult>(`/classes/${classId}/exams/${examId}/send-invitations`, payload);
}
