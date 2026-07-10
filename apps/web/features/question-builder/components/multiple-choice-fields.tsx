import { Input } from "@/components/ui/input";
import type { QuestionFieldProps } from "@/features/question-builder/form-types";

export function MultipleChoiceFields({ register, setValue }: QuestionFieldProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-ink-700">گزینه‌ها</p>
      {(["a", "b", "c", "d"] as const).map((key) => (
        <label key={key} className="grid gap-2 sm:grid-cols-[auto_1fr_auto] sm:items-center">
          <span className="text-sm font-semibold uppercase text-ink-700">{key}</span>
          <Input {...register(`option_${key}`)} placeholder={`گزینه ${key.toUpperCase()}`} />
          <button
            type="button"
            className="rounded-md border border-slate-200 px-3 py-2 text-sm text-ink-700 hover:bg-slate-50"
            onClick={() => setValue("correct_answer", key, { shouldDirty: true })}
          >
            پاسخ درست
          </button>
        </label>
      ))}
    </div>
  );
}
