import { Textarea } from "@/components/ui/textarea";
import type { QuestionFieldProps } from "@/features/question-builder/form-types";

export function ShortAnswerFields({ register }: QuestionFieldProps) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-ink-700">پاسخ مورد انتظار</span>
      <Textarea {...register("expected_answer")} placeholder="پاسخ معیار کوتاه را بنویسید." />
    </label>
  );
}
