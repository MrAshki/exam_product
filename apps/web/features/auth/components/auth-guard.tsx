"use client";

import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useRef } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/features/auth/auth-provider";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";
import type { User } from "@/types/auth";

type AuthGuardProps = {
  children: (user: User) => ReactNode;
};

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const auth = useAuth();
  const redirectedRef = useRef(false);

  useEffect(() => {
    if (auth.status === "idle") {
      void auth.verifySession();
    }
  }, [auth]);

  useEffect(() => {
    if (auth.status === "unauthenticated" && !redirectedRef.current) {
      redirectedRef.current = true;
      router.replace(routes.login);
    }
  }, [auth.status, router]);

  if (auth.status === "idle" || auth.status === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface">
        <Spinner label="در حال بررسی ورود" />
      </main>
    );
  }

  if (auth.status === "error") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface px-4">
        <Alert variant="error">{auth.error ? getErrorMessage(auth.error) : "بررسی نشست با خطا مواجه شد."}</Alert>
      </main>
    );
  }

  if (auth.status === "unauthenticated" || !auth.user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface px-4">
        <Alert variant="error">برای مشاهده این بخش باید وارد شوید.</Alert>
      </main>
    );
  }

  return <AppShell user={auth.user}>{children(auth.user)}</AppShell>;
}
