import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getExamAccess, startExam, submitExam } from "@/features/student-exam/api";
import type { StudentExamSubmitPayload } from "@/types/student-exam";

export const studentExamQueryKeys = {
  access: (examToken: string) => ["student-exam-access", examToken] as const,
  session: (examToken: string) => ["student-exam-session", examToken] as const
};

export function useExamAccess(examToken: string) {
  return useQuery({
    queryKey: studentExamQueryKeys.access(examToken),
    queryFn: () => getExamAccess(examToken),
    enabled: Boolean(examToken),
    retry: false
  });
}

export function useStartExam(examToken: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => startExam(examToken),
    onSuccess: (session) => {
      queryClient.setQueryData(studentExamQueryKeys.session(examToken), session);
    }
  });
}

export function useSubmitExam(examToken: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: StudentExamSubmitPayload) => submitExam(examToken, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: studentExamQueryKeys.access(examToken) });
    }
  });
}
