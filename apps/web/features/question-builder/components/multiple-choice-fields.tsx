import { useWatch } from "react-hook-form";

import { Input } from "@/components/ui/input";
import type { QuestionFieldProps } from "@/features/question-builder/form-types";

const OPTION_KEYS = ["A", "B", "C", "D"] as const;

export function MultipleChoiceFields({ control, register, setValue }: QuestionFieldProps) {
  const selectedAnswer = useWatch({ control, name: "correct_answer" });

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-ink-700">گزینه‌ها</p>
      {OPTION_KEYS.map((key) => {
        const fieldKey = key.toLowerCase() as "a" | "b" | "c" | "d";
        const isSelected = selectedAnswer?.toUpperCase() === key;

        return (
          <label key={key} className="grid gap-2 sm:grid-cols-[auto_1fr_auto] sm:items-center">
            <span className="text-sm font-semibold text-ink-700">{key}</span>
            <Input {...register(`option_${fieldKey}`)} placeholder={`گزینه ${key}`} />
            <button
              type="button"
              aria-pressed={isSelected}
              className={
                isSelected
                  ? "rounded-md border border-brand-600 bg-brand-50 px-3 py-2 text-sm font-semibold text-brand-700"
                  : "rounded-md border border-slate-200 px-3 py-2 text-sm text-ink-700 hover:bg-slate-50"
              }
              onClick={() => setValue("correct_answer", key, { shouldDirty: true })}
            >
              {isSelected ? "پاسخ درست" : "انتخاب پاسخ"}
            </button>
          </label>
        );
      })}
    </div>
  );
}
