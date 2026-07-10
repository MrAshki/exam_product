import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useProtectedQueryEnabled } from "@/features/auth/hooks";
import { createClass, deleteClass, getClass, listClasses, updateClass } from "@/features/classes/api";
import type { ClassroomPayload } from "@/types/class";

export const classQueryKeys = {
  all: ["classes"] as const,
  detail: (classId: string) => ["class", classId] as const
};

export function useClasses() {
  const enabled = useProtectedQueryEnabled();

  return useQuery({
    queryKey: classQueryKeys.all,
    queryFn: listClasses,
    enabled
  });
}

export function useClass(classId: string) {
  const enabled = useProtectedQueryEnabled();

  return useQuery({
    queryKey: classQueryKeys.detail(classId),
    queryFn: () => getClass(classId),
    enabled: enabled && Boolean(classId)
  });
}

export function useCreateClass() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createClass,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: classQueryKeys.all });
    }
  });
}

export function useUpdateClass(classId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: Partial<ClassroomPayload>) => updateClass(classId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: classQueryKeys.all });
      void queryClient.invalidateQueries({ queryKey: classQueryKeys.detail(classId) });
    }
  });
}

export function useDeleteClass() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteClass,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: classQueryKeys.all });
    }
  });
}
