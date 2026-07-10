"use client";

import { useQueryClient } from "@tanstack/react-query";
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { getCurrentUser } from "@/features/auth/api";
import { ApiError, setUnauthorizedHandler } from "@/lib/api-client";
import type { User } from "@/types/auth";

export type AuthStatus = "idle" | "loading" | "authenticated" | "unauthenticated" | "error";

type AuthContextValue = {
  status: AuthStatus;
  user: User | null;
  error: ApiError | null;
  isAuthenticated: boolean;
  verifySession: () => Promise<User | null>;
  setAuthenticated: (user: User) => void;
  clearAuth: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const protectedQueryRoots = new Set([
  "classes",
  "class",
  "students",
  "exams",
  "exam",
  "blueprint",
  "questions",
  "appeals",
  "appeal",
  "exam-review"
]);

function isProtectedQueryKey(queryKey: readonly unknown[]) {
  return typeof queryKey[0] === "string" && protectedQueryRoots.has(queryKey[0]);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<AuthStatus>("idle");
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const sessionRequestRef = useRef<Promise<User | null> | null>(null);

  const clearProtectedQueries = useCallback(() => {
    void queryClient.cancelQueries({
      predicate: (query) => isProtectedQueryKey(query.queryKey)
    });
    queryClient.removeQueries({
      predicate: (query) => isProtectedQueryKey(query.queryKey)
    });
  }, [queryClient]);

  const clearAuth = useCallback(() => {
    setUser(null);
    setError(null);
    setStatus("unauthenticated");
    clearProtectedQueries();
  }, [clearProtectedQueries]);

  const setAuthenticated = useCallback((nextUser: User) => {
    setUser(nextUser);
    setError(null);
    setStatus("authenticated");
  }, []);

  const verifySession = useCallback(async () => {
    if (status === "authenticated" && user) {
      return user;
    }

    if (sessionRequestRef.current) {
      return sessionRequestRef.current;
    }

    setStatus("loading");
    setError(null);

    sessionRequestRef.current = getCurrentUser()
      .then((currentUser) => {
        setAuthenticated(currentUser);
        return currentUser;
      })
      .catch((sessionError: unknown) => {
        if (sessionError instanceof ApiError && sessionError.status === 401) {
          setUser(null);
          setError(null);
          setStatus("unauthenticated");
          clearProtectedQueries();
          return null;
        }

        const apiError =
          sessionError instanceof ApiError
            ? sessionError
            : new ApiError({
                code: "SESSION_CHECK_FAILED",
                message: "بررسی نشست با خطا مواجه شد.",
                status: 0
              });
        setUser(null);
        setError(apiError);
        setStatus("error");
        clearProtectedQueries();
        return null;
      })
      .finally(() => {
        sessionRequestRef.current = null;
      });

    return sessionRequestRef.current;
  }, [clearProtectedQueries, setAuthenticated, status, user]);

  useEffect(() => {
    setUnauthorizedHandler((authError) => {
      setUser(null);
      setError(authError);
      setStatus("unauthenticated");
      clearProtectedQueries();
    });

    return () => setUnauthorizedHandler(null);
  }, [clearProtectedQueries]);

  const value = useMemo(
    () => ({
      status,
      user,
      error,
      isAuthenticated: status === "authenticated" && Boolean(user),
      verifySession,
      setAuthenticated,
      clearAuth
    }),
    [clearAuth, error, setAuthenticated, status, user, verifySession]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }

  return context;
}
