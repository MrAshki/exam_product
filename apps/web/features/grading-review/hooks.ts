import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { examQueryKeys } from "@/features/exams/hooks";
import { approveResults, getExamReview, publishResults, reviewAnswer } from "@/features/grading-review/api";
import { builderQueryKeys } from "@/features/question-builder/hooks";
import type { AnswerReviewPayload } from "@/types/review";

export const reviewQueryKeys = {
  detail: (classId: string, examId: string) => ["exam-review", classId, examId] as const
};

function useInvalidateReview(classId: string, examId: string) {
  const queryClient = useQueryClient();

  return () => {
    void queryClient.invalidateQueries({ queryKey: reviewQueryKeys.detail(classId, examId) });
    void queryClient.invalidateQueries({ queryKey: builderQueryKeys.exam(classId, examId) });
    void queryClient.invalidateQueries({ queryKey: examQueryKeys.list(classId) });
  };
}

export function useExamReview(classId: string, examId: string) {
  return useQuery({
    queryKey: reviewQueryKeys.detail(classId, examId),
    queryFn: () => getExamReview(classId, examId),
    enabled: Boolean(classId && examId),
    retry: false
  });
}

export function useReviewAnswer(classId: string, examId: string, answerId: string) {
  const invalidate = useInvalidateReview(classId, examId);

  return useMutation({
    mutationFn: (payload: AnswerReviewPayload) => reviewAnswer(classId, examId, answerId, payload),
    onSuccess: invalidate
  });
}

export function useApproveResults(classId: string, examId: string) {
  const invalidate = useInvalidateReview(classId, examId);

  return useMutation({
    mutationFn: () => approveResults(classId, examId),
    onSuccess: invalidate
  });
}

export function usePublishResults(classId: string, examId: string) {
  const invalidate = useInvalidateReview(classId, examId);

  return useMutation({
    mutationFn: () => publishResults(classId, examId),
    onSuccess: invalidate
  });
}
