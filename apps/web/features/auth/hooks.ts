"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { login, logout, register } from "@/features/auth/api";
import { useAuth } from "@/features/auth/auth-provider";
import { routes } from "@/lib/routes";
import type { LoginPayload, RegisterPayload } from "@/types/auth";

export function useCurrentUser() {
  return useAuth();
}

export function useProtectedQueryEnabled() {
  return useAuth().isAuthenticated;
}

export function useLogin() {
  const router = useRouter();
  const auth = useAuth();

  return useMutation({
    mutationFn: (payload: LoginPayload) => login(payload),
    onSuccess: (user) => {
      auth.setAuthenticated(user);
      router.replace(routes.dashboard);
    }
  });
}

export function useRegister() {
  const router = useRouter();
  const auth = useAuth();

  return useMutation({
    mutationFn: (payload: RegisterPayload) => register(payload),
    onSuccess: (user) => {
      auth.setAuthenticated(user);
      router.replace(routes.dashboard);
    }
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const auth = useAuth();

  return useMutation({
    mutationFn: logout,
    onMutate: () => {
      auth.clearAuth();
      void queryClient.cancelQueries();
    },
    onSettled: () => {
      queryClient.clear();
      auth.clearAuth();
      router.replace(routes.login);
    }
  });
}
