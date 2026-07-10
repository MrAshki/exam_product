import { apiClient } from "@/lib/api-client";
import type { Classroom, ClassroomPayload } from "@/types/class";

export function listClasses() {
  return apiClient.get<Classroom[]>("/classes/");
}

export function getClass(classId: string) {
  return apiClient.get<Classroom>(`/classes/${classId}`);
}

export function createClass(payload: ClassroomPayload) {
  return apiClient.post<Classroom>("/classes/", payload);
}

export function updateClass(classId: string, payload: Partial<ClassroomPayload>) {
  return apiClient.put<Classroom>(`/classes/${classId}`, payload);
}

export function deleteClass(classId: string) {
  return apiClient.delete<Record<string, never>>(`/classes/${classId}`);
}
