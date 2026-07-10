"use client";

import { AuthGuard } from "@/features/auth/components/auth-guard";
import { DashboardHome } from "@/features/dashboard/dashboard-home";

export default function DashboardPage() {
  return (
    <AuthGuard>
      {(user) => <DashboardHome user={user} />}
    </AuthGuard>
  );
}
