"use client";

import { ArrowLeft, LayoutDashboard } from "lucide-react";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { appConfig } from "@/config/app-config";
import { useCurrentUser } from "@/features/auth/hooks";
import { routes } from "@/lib/routes";

export default function HomePage() {
  const { isAuthenticated } = useCurrentUser();

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface px-4 py-10">
      <section className="w-full max-w-3xl text-center">
        <p className="text-sm font-medium text-brand-700">فاز ۱۵A</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-normal text-ink-900 md:text-5xl">
          {appConfig.name}
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-base leading-8 text-ink-500">
          پایه فرانت‌اند برای ورود، ثبت‌نام و داشبورد معلم آماده شده است.
        </p>
        <Card className="mx-auto mt-8 max-w-xl">
          {isAuthenticated ? (
            <div className="space-y-4">
              <p className="text-sm text-ink-500">شما وارد شده‌اید.</p>
              <Link
                href={routes.dashboard}
                className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-brand-600 px-4 text-sm font-medium text-white transition hover:bg-brand-700"
              >
                <LayoutDashboard size={18} />
                رفتن به داشبورد
              </Link>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              <Link
                href={routes.login}
                className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-brand-600 px-4 text-sm font-medium text-white transition hover:bg-brand-700"
              >
                ورود
                <ArrowLeft size={16} />
              </Link>
              <Link
                href={routes.register}
                className="inline-flex h-11 items-center justify-center rounded-md border border-slate-200 bg-white px-4 text-sm font-medium text-ink-900 transition hover:bg-slate-50"
              >
                ثبت‌نام
              </Link>
            </div>
          )}
        </Card>
      </section>
    </main>
  );
}
