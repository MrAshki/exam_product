"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { ResultAnswer } from "@/types/result";

type ResultAnswerCardProps = {
  answer: ResultAnswer;
  index: number;
};

const typeLabels: Record<string, string> = {
  multiple_choice: "تستی",
  true_false: "درست/غلط",
  short_answer: "کوتاه‌پاسخ",
  essay: "تشریحی"
};

function readableData(value: unknown): string | null {
  if (!value) {
    return null;
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.map(readableData).filter(Boolean).join("، ") || null;
  }

  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const preferred = record.selected_option ?? record.option_key ?? record.value ?? record.text;
    if (preferred !== undefined && preferred !== null) {
      return String(preferred);
    }
  }

  return null;
}

export function ResultAnswerCard({ answer, index }: ResultAnswerCardProps) {
  const studentAnswer = answer.student_answer || readableData(answer.answer_data) || "بدون پاسخ";
  const correctAnswer = answer.correct_answer || readableData(answer.correct_answer_data);

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>سوال {index + 1}</Badge>
          <Badge>{typeLabels[answer.question_type] ?? answer.question_type}</Badge>
        </div>
        <span className="text-sm font-medium text-ink-700">
          {answer.final_score ?? "—"} / {answer.max_score ?? "—"}
        </span>
      </div>
      <div>
        <p className="whitespace-pre-wrap text-sm leading-7 text-ink-900">
          {answer.question_text || "متن سوال ثبت نشده است."}
        </p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-md bg-slate-50 p-3">
          <p className="text-xs font-medium text-ink-500">پاسخ شما</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink-800">{studentAnswer}</p>
        </div>
        {correctAnswer ? (
          <div className="rounded-md bg-brand-50 p-3">
            <p className="text-xs font-medium text-brand-700">پاسخ صحیح</p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-brand-900">{correctAnswer}</p>
          </div>
        ) : null}
      </div>
      {answer.feedback ? (
        <div className="rounded-md border border-blue-100 bg-blue-50 p-3">
          <p className="text-xs font-medium text-blue-800">بازخورد</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-blue-950">{answer.feedback}</p>
        </div>
      ) : null}
    </Card>
  );
}
