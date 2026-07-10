"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarClock } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormError } from "@/components/common/form-error";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/errors";
import type { Exam } from "@/types/exam";
import type { SchedulePayload } from "@/types/schedule";

const scheduleSchema = z
  .object({
    start_time: z.string().min(1, "زمان شروع را وارد کنید."),
    end_time: z.string().min(1, "زمان پایان را وارد کنید."),
    duration_minutes: z.coerce.number().int().positive("مدت آزمون باید مثبت باشد.")
  })
  .refine((value) => new Date(value.start_time) < new Date(value.end_time), {
    message: "زمان پایان باید بعد از شروع باشد.",
    path: ["end_time"]
  });

type ScheduleFormInput = z.input<typeof scheduleSchema>;
type ScheduleFormValues = z.output<typeof scheduleSchema>;

type ScheduleFormProps = {
  exam?: Exam;
  pending?: boolean;
  error?: unknown;
  resultMessage?: string;
  onSubmit: (payload: SchedulePayload) => void;
};

function toDatetimeLocal(value?: string | null) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toISOString().slice(0, 16);
}

function toIso(value: string) {
  return new Date(value).toISOString();
}

export function ScheduleForm({ exam, pending, error, resultMessage, onSubmit }: ScheduleFormProps) {
  const form = useForm<ScheduleFormInput, unknown, ScheduleFormValues>({
    resolver: zodResolver(scheduleSchema),
    defaultValues: {
      start_time: toDatetimeLocal(exam?.start_time),
      end_time: toDatetimeLocal(exam?.end_time),
      duration_minutes: exam?.duration_minutes ?? 60
    }
  });

  useEffect(() => {
    form.reset({
      start_time: toDatetimeLocal(exam?.start_time),
      end_time: toDatetimeLocal(exam?.end_time),
      duration_minutes: exam?.duration_minutes ?? 60
    });
  }, [exam, form]);

  return (
    <form
      className="space-y-4"
      onSubmit={form.handleSubmit((values) =>
        onSubmit({
          start_time: toIso(values.start_time),
          end_time: toIso(values.end_time),
          duration_minutes: values.duration_minutes
        })
      )}
    >
      <FormError message={error ? getErrorMessage(error) : null} />
      {resultMessage ? <Alert variant="success">{resultMessage}</Alert> : null}
      <div className="grid gap-4 md:grid-cols-3">
        <label className="space-y-1.5">
          <span className="text-sm font-medium text-ink-700">زمان شروع</span>
          <Input type="datetime-local" {...form.register("start_time")} />
          {form.formState.errors.start_time ? (
            <span className="text-xs text-rose-700">{form.formState.errors.start_time.message}</span>
          ) : null}
        </label>
        <label className="space-y-1.5">
          <span className="text-sm font-medium text-ink-700">زمان پایان</span>
          <Input type="datetime-local" {...form.register("end_time")} />
          {form.formState.errors.end_time ? (
            <span className="text-xs text-rose-700">{form.formState.errors.end_time.message}</span>
          ) : null}
        </label>
        <label className="space-y-1.5">
          <span className="text-sm font-medium text-ink-700">مدت آزمون</span>
          <Input type="number" min={1} {...form.register("duration_minutes")} />
          {form.formState.errors.duration_minutes ? (
            <span className="text-xs text-rose-700">{form.formState.errors.duration_minutes.message}</span>
          ) : null}
        </label>
      </div>
      <Alert>
        آمادگی آزمون را backend هنگام ثبت زمان‌بندی بررسی می‌کند. اگر سوالی تایید نشده باشد یا جمع نمره‌ها برابر نمره آزمون نباشد، خطای دقیق همین‌جا نمایش داده می‌شود.
      </Alert>
      <div className="flex justify-end">
        <Button type="submit" disabled={pending || exam?.status !== "draft"}>
          <CalendarClock size={16} />
          {pending ? "در حال زمان‌بندی" : "زمان‌بندی آزمون"}
        </Button>
      </div>
    </form>
  );
}
