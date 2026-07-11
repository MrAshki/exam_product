import { useMutation, useQueryClient } from "@tanstack/react-query";

import { examQueryKeys } from "@/features/exams/hooks";
import { builderQueryKeys } from "@/features/question-builder/hooks";
import { scheduleExam, sendInvitations } from "@/features/scheduling/api";
import type { InvitationPayload, SchedulePayload } from "@/types/schedule";

export function useScheduleExam(classId: string, examId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SchedulePayload) => scheduleExam(classId, examId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: builderQueryKeys.exam(classId, examId) });
      void queryClient.invalidateQueries({ queryKey: builderQueryKeys.readiness(classId, examId) });
      void queryClient.invalidateQueries({ queryKey: examQueryKeys.list(classId) });
    }
  });
}

export function useSendInvitations(classId: string, examId: string) {
  return useMutation({
    mutationFn: (payload: InvitationPayload) => sendInvitations(classId, examId, payload)
  });
}
