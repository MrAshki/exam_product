"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormError } from "@/components/common/form-error";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/errors";
import type { Student, StudentPayload } from "@/types/student";

const studentSchema = z.object({
  full_name: z.string().trim().min(1, "نام دانش‌آموز را وارد کنید."),
  email: z.email("ایمیل معتبر وارد کنید."),
  student_code: z.string().optional(),
  is_active: z.boolean(),
  teacher_note: z.string().optional()
});

type StudentFormValues = z.infer<typeof studentSchema>;

type StudentFormProps = {
  initialStudent?: Student | null;
  submitLabel: string;
  pending?: boolean;
  error?: unknown;
  onSubmit: (payload: StudentPayload) => void;
};

function optionalText(value?: string) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export function StudentForm({ initialStudent, submitLabel, pending, error, onSubmit }: StudentFormProps) {
  const form = useForm<StudentFormValues>({
    resolver: zodResolver(studentSchema),
    defaultValues: {
      full_name: initialStudent?.full_name ?? "",
      email: initialStudent?.email ?? "",
      student_code: initialStudent?.student_code ?? "",
      is_active: initialStudent?.is_active ?? true,
      teacher_note: initialStudent?.teacher_note ?? ""
    }
  });

  useEffect(() => {
    form.reset({
      full_name: initialStudent?.full_name ?? "",
      email: initialStudent?.email ?? "",
      student_code: initialStudent?.student_code ?? "",
      is_active: initialStudent?.is_active ?? true,
      teacher_note: initialStudent?.teacher_note ?? ""
    });
  }, [form, initialStudent]);

  return (
    <form
      className="space-y-4"
      onSubmit={form.handleSubmit((values) =>
        onSubmit({
          full_name: values.full_name.trim(),
          email: values.email.trim(),
          student_code: optionalText(values.student_code),
          is_active: values.is_active,
          teacher_note: optionalText(values.teacher_note)
        })
      )}
    >
      <FormError message={error ? getErrorMessage(error) : null} />
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">نام کامل</span>
        <Input {...form.register("full_name")} placeholder="نام دانش‌آموز" />
        {form.formState.errors.full_name ? (
          <span className="text-xs text-rose-700">{form.formState.errors.full_name.message}</span>
        ) : null}
      </label>
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">ایمیل</span>
        <Input type="email" dir="ltr" {...form.register("email")} placeholder="student@example.com" />
        {form.formState.errors.email ? (
          <span className="text-xs text-rose-700">{form.formState.errors.email.message}</span>
        ) : null}
      </label>
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">کد دانش‌آموزی</span>
        <Input {...form.register("student_code")} placeholder="اختیاری" />
      </label>
      <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm text-ink-700">
        <input type="checkbox" className="h-4 w-4 rounded border-slate-300" {...form.register("is_active")} />
        فعال
      </label>
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">یادداشت معلم</span>
        <Textarea {...form.register("teacher_note")} placeholder="یادداشت داخلی" />
      </label>
      <div className="flex justify-end">
        <Button type="submit" disabled={pending}>
          <Save size={16} />
          {pending ? "در حال ذخیره" : submitLabel}
        </Button>
      </div>
    </form>
  );
}
