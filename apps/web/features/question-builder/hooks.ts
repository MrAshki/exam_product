import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useProtectedQueryEnabled } from "@/features/auth/hooks";
import {
  confirmQuestion,
  createBlueprint,
  finalizeExam,
  getBlueprint,
  getBuilderExam,
  getExamReadiness,
  listQuestions,
  reopenExam,
  suggestRubric,
  updateBlueprint,
  updateQuestion
} from "@/features/question-builder/api";
import { examQueryKeys } from "@/features/exams/hooks";
import type { BlueprintPayload, BlueprintUpdatePayload } from "@/types/blueprint";
import type { QuestionUpdatePayload } from "@/types/question";

export const builderQueryKeys = {
  exam: (classId: string, examId: string) => ["exam", classId, examId] as const,
  blueprint: (classId: string, examId: string) => ["blueprint", classId, examId] as const,
  questions: (classId: string, examId: string) => ["questions", classId, examId] as const,
  readiness: (classId: string, examId: string) => ["exam-readiness", classId, examId] as const
};

function useInvalidateBuilder(classId: string, examId: string) {
  const queryClient = useQueryClient();

  return () => {
    void queryClient.invalidateQueries({ queryKey: builderQueryKeys.exam(classId, examId) });
    void queryClient.invalidateQueries({ queryKey: builderQueryKeys.blueprint(classId, examId) });
    void queryClient.invalidateQueries({ queryKey: builderQueryKeys.questions(classId, examId) });
    void queryClient.invalidateQueries({ queryKey: builderQueryKeys.readiness(classId, examId) });
    void queryClient.invalidateQueries({ queryKey: examQueryKeys.list(classId) });
  };
}

export function useBuilderExam(classId: string, examId: string) {
  const enabled = useProtectedQueryEnabled();

  return useQuery({
    queryKey: builderQueryKeys.exam(classId, examId),
    queryFn: () => getBuilderExam(classId, examId),
    enabled: enabled && Boolean(classId && examId)
  });
}

export function useBlueprint(classId: string, examId: string) {
  const enabled = useProtectedQueryEnabled();

  return useQuery({
    queryKey: builderQueryKeys.blueprint(classId, examId),
    queryFn: () => getBlueprint(classId, examId),
    enabled: enabled && Boolean(classId && examId),
    retry: false
  });
}

export function useQuestions(classId: string, examId: string) {
  const enabled = useProtectedQueryEnabled();

  return useQuery({
    queryKey: builderQueryKeys.questions(classId, examId),
    queryFn: () => listQuestions(classId, examId),
    enabled: enabled && Boolean(classId && examId)
  });
}

export function useExamReadiness(classId: string, examId: string) {
  const enabled = useProtectedQueryEnabled();

  return useQuery({
    queryKey: builderQueryKeys.readiness(classId, examId),
    queryFn: () => getExamReadiness(classId, examId),
    enabled: enabled && Boolean(classId && examId),
    retry: false
  });
}

export function useCreateBlueprint(classId: string, examId: string) {
  const invalidate = useInvalidateBuilder(classId, examId);

  return useMutation({
    mutationFn: (payload: BlueprintPayload) => createBlueprint(classId, examId, payload),
    onSuccess: invalidate
  });
}

export function useUpdateBlueprint(classId: string, examId: string) {
  const invalidate = useInvalidateBuilder(classId, examId);

  return useMutation({
    mutationFn: (payload: BlueprintUpdatePayload) => updateBlueprint(classId, examId, payload),
    onSuccess: invalidate
  });
}

export function useUpdateQuestion(classId: string, examId: string, questionId: string) {
  const invalidate = useInvalidateBuilder(classId, examId);

  return useMutation({
    mutationFn: (payload: QuestionUpdatePayload) => updateQuestion(classId, examId, questionId, payload),
    onSuccess: invalidate
  });
}

export function useConfirmQuestion(classId: string, examId: string, questionId: string) {
  const invalidate = useInvalidateBuilder(classId, examId);

  return useMutation({
    mutationFn: () => confirmQuestion(classId, examId, questionId),
    onSuccess: invalidate
  });
}

export function useFinalizeExam(classId: string, examId: string) {
  const invalidate = useInvalidateBuilder(classId, examId);

  return useMutation({
    mutationFn: () => finalizeExam(classId, examId),
    onSuccess: invalidate
  });
}

export function useReopenExam(classId: string, examId: string) {
  const invalidate = useInvalidateBuilder(classId, examId);

  return useMutation({
    mutationFn: () => reopenExam(classId, examId),
    onSuccess: invalidate
  });
}

export function useSuggestRubric(classId: string, examId: string, questionId: string) {
  const invalidate = useInvalidateBuilder(classId, examId);

  return useMutation({
    mutationFn: () => suggestRubric(classId, examId, questionId),
    onSuccess: invalidate
  });
}
