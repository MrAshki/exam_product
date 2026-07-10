import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getStudentResult, submitResultAppeal } from "@/features/results/api";
import type { ResultAppealPayload } from "@/types/result";

export const resultQueryKeys = {
  detail: (resultToken: string) => ["result", resultToken] as const
};

export function useStudentResult(resultToken: string) {
  return useQuery({
    queryKey: resultQueryKeys.detail(resultToken),
    queryFn: () => getStudentResult(resultToken),
    enabled: Boolean(resultToken),
    retry: false
  });
}

export function useSubmitResultAppeal(resultToken: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ResultAppealPayload) => submitResultAppeal(resultToken, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: resultQueryKeys.detail(resultToken) });
    }
  });
}
