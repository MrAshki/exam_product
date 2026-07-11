"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { FormError } from "@/components/common/form-error";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/errors";
import type { Blueprint, BlueprintPayload } from "@/types/blueprint";

const blueprintSchema = z
  .object({
    multiple_choice_count: z.coerce.number().int().min(0),
    short_answer_count: z.coerce.number().int().min(0),
    essay_count: z.coerce.number().int().min(0),
    true_false_count: z.coerce.number().int().min(0)
  })
  .refine(
    (value) =>
      value.multiple_choice_count + value.short_answer_count + value.essay_count + value.true_false_count > 0,
    "حداقل یک سوال برای ساختار آزمون لازم است."
  );

type BlueprintFormInput = z.input<typeof blueprintSchema>;
type BlueprintFormValues = z.output<typeof blueprintSchema>;

type BlueprintFormProps = {
  blueprint?: Blueprint | null;
  pending?: boolean;
  error?: unknown;
  disabled?: boolean;
  onSubmit: (payload: BlueprintPayload) => void;
};

export function BlueprintForm({ blueprint, pending, error, disabled, onSubmit }: BlueprintFormProps) {
  const form = useForm<BlueprintFormInput, unknown, BlueprintFormValues>({
    resolver: zodResolver(blueprintSchema),
    defaultValues: {
      multiple_choice_count: blueprint?.multiple_choice_count ?? 1,
      short_answer_count: blueprint?.short_answer_count ?? 0,
      essay_count: blueprint?.essay_count ?? 0,
      true_false_count: blueprint?.true_false_count ?? 0
    }
  });
  const counts = useWatch({ control: form.control });

  useEffect(() => {
    if (blueprint) {
      form.reset({
        multiple_choice_count: blueprint.multiple_choice_count,
        short_answer_count: blueprint.short_answer_count,
        essay_count: blueprint.essay_count,
        true_false_count: blueprint.true_false_count
      });
    }
  }, [blueprint, form]);

  const total = Number(counts.multiple_choice_count || 0)
    + Number(counts.short_answer_count || 0)
    + Number(counts.essay_count || 0)
    + Number(counts.true_false_count || 0);

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
      <FormError message={error ? getErrorMessage(error) : null} />
      {form.formState.errors.root ? (
        <p className="text-sm text-rose-700">{form.formState.errors.root.message}</p>
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <label className="space-y-1.5">
          <span className="text-sm font-medium text-ink-700">تعداد سوال تستی</span>
          <Input type="number" min={0} {...form.register("multiple_choice_count")} disabled={disabled} />
        </label>
        <label className="space-y-1.5">
          <span className="text-sm font-medium text-ink-700">تعداد سوال کوتاه‌پاسخ</span>
          <Input type="number" min={0} {...form.register("short_answer_count")} disabled={disabled} />
        </label>
        <label className="space-y-1.5">
          <span className="text-sm font-medium text-ink-700">تعداد سوال تشریحی</span>
          <Input type="number" min={0} {...form.register("essay_count")} disabled={disabled} />
        </label>
        <label className="space-y-1.5">
          <span className="text-sm font-medium text-ink-700">تعداد سوال درست/غلط</span>
          <Input type="number" min={0} {...form.register("true_false_count")} disabled={disabled} />
        </label>
      </div>
      {form.formState.errors.root ? null : (
        <p className="text-sm text-ink-500">مجموع سوال‌ها: {total}</p>
      )}
      {Object.values(form.formState.errors).length ? (
        <p className="text-sm text-rose-700">همه تعدادها باید عدد صحیح نامنفی باشند و مجموع از صفر بیشتر باشد.</p>
      ) : null}
      {blueprint ? (
        <p className="text-sm text-ink-500">ساختار فعلی {blueprint.total_question_count} جایگاه سوال دارد.</p>
      ) : null}
      <div className="flex justify-end">
        <Button type="submit" disabled={pending || disabled}>
          <Save size={16} />
          {pending ? "در حال ذخیره" : blueprint ? "به‌روزرسانی ساختار آزمون" : "ساخت ساختار آزمون"}
        </Button>
      </div>
    </form>
  );
}
