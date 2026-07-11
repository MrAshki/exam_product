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
import { decimalToInput } from "@/lib/decimal";
import { getErrorMessage } from "@/lib/errors";
import type { Exam, ExamPayload } from "@/types/exam";

const examSchema = z.object({
  title: z.string().trim().min(1, "عنوان آزمون را وارد کنید."),
  description: z.string().optional(),
  duration_minutes: z.coerce.number().int().positive("مدت آزمون باید مثبت باشد.").optional().or(z.literal("")),
  total_points: z.coerce
    .number()
    .min(0, "نمره کل نمی‌تواند منفی باشد.")
    .refine((value) => Number.isInteger(value * 100), "نمره کل حداکثر دو رقم اعشار دارد.")
    .optional()
    .or(z.literal(""))
});

type ExamFormInput = z.input<typeof examSchema>;
type ExamFormValues = z.output<typeof examSchema>;

type ExamFormProps = {
  initialExam?: Exam | null;
  submitLabel: string;
  pending?: boolean;
  error?: unknown;
  onSubmit: (payload: ExamPayload) => void;
};

function optionalText(value?: string) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function optionalNumber(value: number | "" | undefined) {
  return value === "" || value === undefined ? null : value;
}

export function ExamForm({ initialExam, submitLabel, pending, error, onSubmit }: ExamFormProps) {
  const form = useForm<ExamFormInput, unknown, ExamFormValues>({
    resolver: zodResolver(examSchema),
    defaultValues: {
      title: initialExam?.title ?? "",
      description: initialExam?.description ?? "",
      duration_minutes: initialExam?.duration_minutes ?? "",
      total_points: decimalToInput(initialExam?.total_points) || 0
    }
  });

  useEffect(() => {
    form.reset({
      title: initialExam?.title ?? "",
      description: initialExam?.description ?? "",
      duration_minutes: initialExam?.duration_minutes ?? "",
      total_points: decimalToInput(initialExam?.total_points) || 0
    });
  }, [form, initialExam]);

  return (
    <form
      className="space-y-4"
      onSubmit={form.handleSubmit((values) =>
        onSubmit({
          title: values.title.trim(),
          description: optionalText(values.description),
          duration_minutes: optionalNumber(values.duration_minutes),
          total_points: optionalNumber(values.total_points) ?? 0,
          show_leaderboard: initialExam?.show_leaderboard ?? true,
          allow_appeals: initialExam?.allow_appeals ?? true,
          show_correct_answers: initialExam?.show_correct_answers ?? true,
          show_feedback: initialExam?.show_feedback ?? true
        })
      )}
    >
      <FormError message={error ? getErrorMessage(error) : null} />
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">عنوان آزمون</span>
        <Input {...form.register("title")} placeholder="مثلا میان‌ترم فصل اول" />
        {form.formState.errors.title ? (
          <span className="text-xs text-rose-700">{form.formState.errors.title.message}</span>
        ) : null}
      </label>
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">توضیحات</span>
        <Textarea {...form.register("description")} placeholder="توضیح کوتاه برای معلم" />
      </label>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-ink-700">مدت آزمون به دقیقه</span>
          <Input type="number" min={1} {...form.register("duration_minutes")} placeholder="اختیاری" />
          {form.formState.errors.duration_minutes ? (
            <span className="text-xs text-rose-700">{form.formState.errors.duration_minutes.message}</span>
          ) : null}
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-ink-700">نمره کل</span>
          <Input type="number" min={0} step="0.01" inputMode="decimal" {...form.register("total_points")} />
          {form.formState.errors.total_points ? (
            <span className="text-xs text-rose-700">{form.formState.errors.total_points.message}</span>
          ) : null}
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
