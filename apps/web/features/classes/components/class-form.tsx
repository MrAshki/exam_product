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
import type { Classroom, ClassroomPayload } from "@/types/class";

const classSchema = z.object({
  title: z.string().trim().min(1, "نام کلاس را وارد کنید."),
  subject: z.string().trim().min(1, "موضوع کلاس را وارد کنید."),
  description: z.string().optional(),
  academic_year: z.string().optional(),
  grade_level: z.string().optional()
});

type ClassFormValues = z.infer<typeof classSchema>;

type ClassFormProps = {
  initialClass?: Classroom | null;
  submitLabel: string;
  pending?: boolean;
  error?: unknown;
  onSubmit: (payload: ClassroomPayload) => void;
};

function optionalText(value?: string) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export function ClassForm({ initialClass, submitLabel, pending, error, onSubmit }: ClassFormProps) {
  const form = useForm<ClassFormValues>({
    resolver: zodResolver(classSchema),
    defaultValues: {
      title: initialClass?.title ?? "",
      subject: initialClass?.subject ?? "",
      description: initialClass?.description ?? "",
      academic_year: initialClass?.academic_year ?? "",
      grade_level: initialClass?.grade_level ?? ""
    }
  });

  useEffect(() => {
    form.reset({
      title: initialClass?.title ?? "",
      subject: initialClass?.subject ?? "",
      description: initialClass?.description ?? "",
      academic_year: initialClass?.academic_year ?? "",
      grade_level: initialClass?.grade_level ?? ""
    });
  }, [form, initialClass]);

  return (
    <form
      className="space-y-4"
      onSubmit={form.handleSubmit((values) =>
        onSubmit({
          title: values.title.trim(),
          subject: values.subject.trim(),
          description: optionalText(values.description),
          academic_year: optionalText(values.academic_year),
          grade_level: optionalText(values.grade_level)
        })
      )}
    >
      <FormError message={error ? getErrorMessage(error) : null} />
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">نام کلاس</span>
        <Input {...form.register("title")} placeholder="مثلا ریاضی یازدهم" />
        {form.formState.errors.title ? (
          <span className="text-xs text-rose-700">{form.formState.errors.title.message}</span>
        ) : null}
      </label>
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">موضوع</span>
        <Input {...form.register("subject")} placeholder="مثلا ریاضی" />
        {form.formState.errors.subject ? (
          <span className="text-xs text-rose-700">{form.formState.errors.subject.message}</span>
        ) : null}
      </label>
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">توضیحات</span>
        <Textarea {...form.register("description")} placeholder="توضیح کوتاه برای خودتان" />
      </label>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-ink-700">سال تحصیلی</span>
          <Input {...form.register("academic_year")} placeholder="۱۴۰۵-۱۴۰۴" />
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-ink-700">پایه</span>
          <Input {...form.register("grade_level")} placeholder="یازدهم" />
        </label>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={pending}>
          <Save size={16} />
          {pending ? "در حال ذخیره" : submitLabel}
        </Button>
      </div>
    </form>
  );
}
