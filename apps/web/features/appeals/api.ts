import { apiClient } from "@/lib/api-client";
import type { AppealDetail, AppealList, AppealListParams, AppealResolvePayload, AppealResolveResult } from "@/types/appeal";

function appealsPath(classId: string) {
  return `/classes/${encodeURIComponent(classId)}/appeals`;
}

export function listClassAppeals(classId: string, params: AppealListParams = {}) {
  return apiClient.get<AppealList>(appealsPath(classId), {
    query: {
      status: params.status,
      exam_id: params.exam_id,
      student_id: params.student_id,
      page: params.page,
      page_size: params.page_size
    }
  });
}

export function getClassAppeal(classId: string, appealId: string) {
  return apiClient.get<AppealDetail>(`${appealsPath(classId)}/${encodeURIComponent(appealId)}`);
}

export function resolveClassAppeal(classId: string, appealId: string, payload: AppealResolvePayload) {
  return apiClient.post<AppealResolveResult>(`${appealsPath(classId)}/${encodeURIComponent(appealId)}/resolve`, payload);
}
