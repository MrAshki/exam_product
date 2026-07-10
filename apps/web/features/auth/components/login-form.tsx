"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormError } from "@/components/common/form-error";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useCurrentUser, useLogin } from "@/features/auth/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";

const loginSchema = z.object({
  email: z.string().email("ایمیل معتبر وارد کنید."),
  password: z.string().min(1, "رمز عبور را وارد کنید.")
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const login = useLogin();
  const auth = useCurrentUser();
  const router = useRouter();
  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: ""
    }
  });

  useEffect(() => {
    if (auth.isAuthenticated) {
      router.replace(routes.dashboard);
    }
  }, [auth.isAuthenticated, router]);

  return (
    <Card className="w-full max-w-md">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-ink-900">ورود معلم</h1>
        <p className="mt-2 text-sm text-ink-500">برای ادامه وارد حساب خود شوید.</p>
      </div>
      <form
        className="space-y-4"
        onSubmit={handleSubmit((values) => {
          if (!login.isPending) {
            login.mutate(values);
          }
        })}
      >
        <FormError message={login.isError ? getErrorMessage(login.error) : null} />
        <label className="block space-y-2">
          <span className="text-sm font-medium text-ink-700">ایمیل</span>
          <Input type="email" autoComplete="email" {...register("email")} />
          {errors.email ? <span className="text-xs text-rose-700">{errors.email.message}</span> : null}
        </label>
        <label className="block space-y-2">
          <span className="text-sm font-medium text-ink-700">رمز عبور</span>
          <Input type="password" autoComplete="current-password" {...register("password")} />
          {errors.password ? (
            <span className="text-xs text-rose-700">{errors.password.message}</span>
          ) : null}
        </label>
        <Button type="submit" className="w-full" disabled={login.isPending}>
          {login.isPending ? "در حال ورود..." : "ورود"}
        </Button>
      </form>
      <p className="mt-5 text-center text-sm text-ink-500">
        حساب ندارید؟{" "}
        <Link href={routes.register} className="font-medium text-brand-700 hover:underline">
          ثبت‌نام
        </Link>
      </p>
    </Card>
  );
}
