"use client";

import { Badge } from "@/components/ui/badge";
import { formatDecimal } from "@/lib/decimal";
import { cn } from "@/lib/formatters";
import type { QuestionSlot } from "@/types/question";

const typeLabels: Record<string, string> = {
  multiple_choice: "تستی",
  short_answer: "کوتاه‌پاسخ",
  essay: "تشریحی",
  true_false: "درست/غلط"
};

const statusLabels: Record<string, string> = {
  empty: "خالی",
  draft: "پیش‌نویس",
  extracted: "استخراج‌شده",
  confirmed: "نهایی"
};

type QuestionSlotListProps = {
  questions: QuestionSlot[];
  selectedQuestionId?: string;
  onSelect: (question: QuestionSlot) => void;
};

export function QuestionSlotList({ questions, selectedQuestionId, onSelect }: QuestionSlotListProps) {
  return (
    <div className="max-h-[720px] space-y-2 overflow-y-auto pr-1">
      {questions.map((question) => (
        <button
          key={question.id}
          type="button"
          onClick={() => onSelect(question)}
          className={cn(
            "w-full rounded-md border p-3 text-right transition",
            selectedQuestionId === question.id ? "border-brand-300 bg-brand-50" : "border-slate-200 bg-white hover:bg-slate-50"
          )}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-ink-900">سوال {question.order_index}</p>
              <p className="mt-1 text-xs text-ink-500">{typeLabels[question.type] || question.type}</p>
            </div>
            <Badge>{statusLabels[question.status] ?? question.status}</Badge>
          </div>
          <p className="mt-2 line-clamp-2 text-xs leading-5 text-ink-500">{question.text || "هنوز متن سوال وارد نشده است."}</p>
          <p className="mt-2 text-xs text-ink-500">نمره: {formatDecimal(question.points)}</p>
        </button>
      ))}
      {questions.length === 0 ? (
        <div className="rounded-md border border-dashed border-slate-300 bg-white p-4 text-center text-sm text-ink-500">
          ابتدا ساختار آزمون را بسازید.
        </div>
      ) : null}
    </div>
  );
}
