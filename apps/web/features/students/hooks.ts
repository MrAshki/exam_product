import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createStudent, listStudents, removeStudent, updateStudent } from "@/features/students/api";
import type { StudentPayload } from "@/types/student";

export const studentQueryKeys = {
  list: (classId: string, page: number, pageSize: number, search: string) =>
    ["students", classId, page, pageSize, search] as const,
  classStudents: (classId: string) => ["students", classId] as const
};

export function useStudents(classId: string, page: number, pageSize: number, search: string) {
  return useQuery({
    queryKey: studentQueryKeys.list(classId, page, pageSize, search),
    queryFn: () => listStudents(classId, { page, page_size: pageSize, search: search || undefined }),
    enabled: Boolean(classId)
  });
}

export function useCreateStudent(classId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: StudentPayload) => createStudent(classId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: studentQueryKeys.classStudents(classId) });
    }
  });
}

export function useUpdateStudent(classId: string, studentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: Partial<StudentPayload>) => updateStudent(classId, studentId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: studentQueryKeys.classStudents(classId) });
    }
  });
}

export function useRemoveStudent(classId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (studentId: string) => removeStudent(classId, studentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: studentQueryKeys.classStudents(classId) });
    }
  });
}
