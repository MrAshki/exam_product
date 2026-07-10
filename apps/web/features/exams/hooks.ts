import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useProtectedQueryEnabled } from "@/features/auth/hooks";
import { createExam, deleteExam, listExams, updateExam } from "@/features/exams/api";
import type { ExamPayload } from "@/types/exam";

export const examQueryKeys = {
  list: (classId: string) => ["exams", classId] as const
};

export function useExams(classId: string) {
  const enabled = useProtectedQueryEnabled();

  return useQuery({
    queryKey: examQueryKeys.list(classId),
    queryFn: () => listExams(classId),
    enabled: enabled && Boolean(classId)
  });
}

export function useCreateExam(classId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ExamPayload) => createExam(classId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: examQueryKeys.list(classId) });
    }
  });
}

export function useUpdateExam(classId: string, examId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: Partial<ExamPayload>) => updateExam(classId, examId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: examQueryKeys.list(classId) });
    }
  });
}

export function useDeleteExam(classId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (examId: string) => deleteExam(classId, examId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: examQueryKeys.list(classId) });
    }
  });
}
