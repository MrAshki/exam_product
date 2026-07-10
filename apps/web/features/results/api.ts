import { apiClient } from "@/lib/api-client";
import type { ResultAppeal, ResultAppealPayload, StudentResult } from "@/types/result";

function resultPath(resultToken: string) {
  return `/result/${encodeURIComponent(resultToken)}`;
}

export function getStudentResult(resultToken: string) {
  return apiClient.get<StudentResult>(resultPath(resultToken));
}

export function submitResultAppeal(resultToken: string, payload: ResultAppealPayload) {
  return apiClient.post<ResultAppeal>(`${resultPath(resultToken)}/appeals`, payload);
}
