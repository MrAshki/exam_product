"use client";

import { useRouter } from "next/navigation";
import { ReactNode, useEffect } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { useCurrentUser } from "@/features/auth/hooks";
import { routes } from "@/lib/routes";
import type { User } from "@/types/auth";

type AuthGuardProps = {
  children: (user: User) => ReactNode;
};

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const currentUser = useCurrentUser();

  useEffect(() => {
    if (currentUser.isError) {
      router.replace(routes.login);
    }
  }, [currentUser.isError, router]);

  if (currentUser.isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface">
        <Spinner label="در حال بررسی ورود" />
      </main>
    );
  }

  if (currentUser.isError || !currentUser.data) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface px-4">
        <Alert variant="error">برای مشاهده این بخش باید وارد شوید.</Alert>
      </main>
    );
  }

  return <AppShell user={currentUser.data}>{children(currentUser.data)}</AppShell>;
}
