"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormError } from "@/components/common/form-error";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useRegister } from "@/features/auth/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";

const registerSchema = z
  .object({
    full_name: z.string().min(1, "نام را وارد کنید.").max(255, "نام بیش از حد طولانی است."),
    email: z.string().email("ایمیل معتبر وارد کنید."),
    password: z.string().min(8, "رمز عبور باید حداقل ۸ نویسه باشد.").max(128),
    confirmPassword: z.string().min(1, "تکرار رمز عبور را وارد کنید.")
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: "رمز عبور و تکرار آن یکسان نیستند.",
    path: ["confirmPassword"]
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const registerTeacher = useRegister();
  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      confirmPassword: ""
    }
  });

  return (
    <Card className="w-full max-w-md">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-ink-900">ثبت‌نام معلم</h1>
        <p className="mt-2 text-sm text-ink-500">حساب معلم خود را برای شروع بسازید.</p>
      </div>
      <form
        className="space-y-4"
        onSubmit={handleSubmit(({ confirmPassword: _confirmPassword, ...values }) =>
          registerTeacher.mutate(values)
        )}
      >
        <FormError message={registerTeacher.isError ? getErrorMessage(registerTeacher.error) : null} />
        <label className="block space-y-2">
          <span className="text-sm font-medium text-ink-700">نام کامل</span>
          <Input autoComplete="name" {...register("full_name")} />
          {errors.full_name ? (
            <span className="text-xs text-rose-700">{errors.full_name.message}</span>
          ) : null}
        </label>
        <label className="block space-y-2">
          <span className="text-sm font-medium text-ink-700">ایمیل</span>
          <Input type="email" autoComplete="email" {...register("email")} />
          {errors.email ? <span className="text-xs text-rose-700">{errors.email.message}</span> : null}
        </label>
        <label className="block space-y-2">
          <span className="text-sm font-medium text-ink-700">رمز عبور</span>
          <Input type="password" autoComplete="new-password" {...register("password")} />
          {errors.password ? (
            <span className="text-xs text-rose-700">{errors.password.message}</span>
          ) : null}
        </label>
        <label className="block space-y-2">
          <span className="text-sm font-medium text-ink-700">تکرار رمز عبور</span>
          <Input type="password" autoComplete="new-password" {...register("confirmPassword")} />
          {errors.confirmPassword ? (
            <span className="text-xs text-rose-700">{errors.confirmPassword.message}</span>
          ) : null}
        </label>
        <Button type="submit" className="w-full" disabled={registerTeacher.isPending}>
          {registerTeacher.isPending ? "در حال ثبت‌نام..." : "ثبت‌نام"}
        </Button>
      </form>
      <p className="mt-5 text-center text-sm text-ink-500">
        حساب دارید؟{" "}
        <Link href={routes.login} className="font-medium text-brand-700 hover:underline">
          ورود
        </Link>
      </p>
    </Card>
  );
}
