import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useProtectedQueryEnabled } from "@/features/auth/hooks";
import { getClassAppeal, listClassAppeals, resolveClassAppeal } from "@/features/appeals/api";
import type { AppealListParams, AppealResolvePayload } from "@/types/appeal";

export const appealQueryKeys = {
  list: (classId: string, params?: AppealListParams) => ["appeals", classId, params ?? {}] as const,
  detail: (classId: string, appealId: string) => ["appeal", classId, appealId] as const
};

export function useClassAppeals(classId: string, params: AppealListParams = {}) {
  const enabled = useProtectedQueryEnabled();

  return useQuery({
    queryKey: appealQueryKeys.list(classId, params),
    queryFn: () => listClassAppeals(classId, params),
    enabled: enabled && Boolean(classId)
  });
}

export function useClassAppeal(classId: string, appealId: string) {
  const enabled = useProtectedQueryEnabled();

  return useQuery({
    queryKey: appealQueryKeys.detail(classId, appealId),
    queryFn: () => getClassAppeal(classId, appealId),
    enabled: enabled && Boolean(classId && appealId)
  });
}

export function useResolveClassAppeal(classId: string, appealId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: AppealResolvePayload) => resolveClassAppeal(classId, appealId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["appeals", classId] });
      void queryClient.invalidateQueries({ queryKey: appealQueryKeys.detail(classId, appealId) });
    }
  });
}
