"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { DashboardHome } from "@/features/dashboard/dashboard-home";
import { useCurrentUser } from "@/features/auth/hooks";
import { routes } from "@/lib/routes";

export default function DashboardPage() {
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
        <Alert variant="error">برای مشاهده داشبورد باید وارد شوید.</Alert>
      </main>
    );
  }

  return (
    <AppShell user={currentUser.data}>
      <DashboardHome />
    </AppShell>
  );
}
