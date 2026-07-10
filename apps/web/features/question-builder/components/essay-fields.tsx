import { Textarea } from "@/components/ui/textarea";
import type { QuestionFieldProps } from "@/features/question-builder/form-types";

export function EssayFields({ register }: QuestionFieldProps) {
  return (
    <div className="space-y-4">
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">پاسخ مورد انتظار</span>
        <Textarea {...register("expected_answer")} placeholder="پاسخ معیار تشریحی را خودتان وارد کنید." />
      </label>
      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">rubric نهایی</span>
        <Textarea {...register("rubric")} placeholder="rubric تاییدشده معلم" />
      </label>
      <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm text-ink-700">
        <input type="checkbox" className="h-4 w-4" {...register("rubric_teacher_confirmed")} />
        rubric توسط معلم تایید شده است
      </label>
    </div>
  );
}
