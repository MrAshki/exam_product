"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { getCurrentUser, login, logout, register } from "@/features/auth/api";
import { authQueryKeys } from "@/lib/auth";
import { routes } from "@/lib/routes";
import type { LoginPayload, RegisterPayload } from "@/types/auth";

export function useCurrentUser() {
  return useQuery({
    queryKey: authQueryKeys.currentUser,
    queryFn: getCurrentUser,
    retry: false
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (payload: LoginPayload) => login(payload),
    onSuccess: async (user) => {
      queryClient.setQueryData(authQueryKeys.currentUser, user);
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.currentUser });
      router.replace(routes.dashboard);
    }
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (payload: RegisterPayload) => register(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.currentUser });
      router.replace(routes.login);
    }
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: logout,
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: authQueryKeys.currentUser });
      router.replace(routes.login);
    }
  });
}
