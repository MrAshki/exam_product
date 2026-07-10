import type { QuestionFieldProps } from "@/features/question-builder/form-types";

export function TrueFalseFields({ register }: QuestionFieldProps) {
  return (
    <fieldset className="space-y-2">
      <legend className="text-sm font-medium text-ink-700">پاسخ درست</legend>
      <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm text-ink-700">
        <input type="radio" value="true" {...register("correct_answer")} />
        درست
      </label>
      <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm text-ink-700">
        <input type="radio" value="false" {...register("correct_answer")} />
        غلط
      </label>
    </fieldset>
  );
}
