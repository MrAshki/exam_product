import { apiClient } from "@/lib/api-client";
import type { LoginPayload, RegisterPayload, User } from "@/types/auth";

export function getCurrentUser() {
  return apiClient.get<User>("/auth/me", { skipUnauthorizedHandler: true });
}

export function login(payload: LoginPayload) {
  return apiClient.post<User>("/auth/login", payload, { skipUnauthorizedHandler: true });
}

export function register(payload: RegisterPayload) {
  return apiClient.post<User>("/auth/register", payload, { skipUnauthorizedHandler: true });
}

export function logout() {
  return apiClient.post<Record<string, never>>("/auth/logout", {});
}
