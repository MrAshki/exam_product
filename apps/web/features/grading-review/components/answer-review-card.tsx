"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { AnswerReviewForm } from "@/features/grading-review/components/answer-review-form";
import type { ReviewAnswer } from "@/types/review";

type AnswerReviewCardProps = {
  classId: string;
  examId: string;
  answer: ReviewAnswer;
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

function score(value: string | number | null | undefined) {
  return value ?? "—";
}

export function AnswerReviewCard({ classId, examId, answer, index }: AnswerReviewCardProps) {
  const studentAnswer = answer.student_answer || readableData(answer.answer_data) || "بدون پاسخ";
  const correctAnswer = answer.correct_answer || readableData(answer.correct_answer_data);

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>پاسخ {index + 1}</Badge>
          <Badge>{typeLabels[answer.question_type] ?? answer.question_type}</Badge>
          {answer.needs_review ? <Badge className="bg-amber-50 text-amber-800">نیازمند بازبینی</Badge> : null}
          {answer.reviewed_by_teacher ? <Badge className="bg-brand-50 text-brand-700">بازبینی‌شده</Badge> : null}
        </div>
        <span className="text-sm font-medium text-ink-700">
          نمره نهایی: {score(answer.final_score)} / {score(answer.max_score)}
        </span>
      </div>

      <p className="whitespace-pre-wrap text-sm leading-7 text-ink-900">
        {answer.question_text || "متن سوال ثبت نشده است."}
      </p>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-md bg-slate-50 p-3">
          <p className="text-xs font-medium text-ink-500">پاسخ دانش‌آموز</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink-800">{studentAnswer}</p>
        </div>
        {correctAnswer || answer.expected_answer ? (
          <div className="rounded-md bg-blue-50 p-3">
            <p className="text-xs font-medium text-blue-800">{correctAnswer ? "پاسخ صحیح" : "پاسخ مورد انتظار"}</p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-blue-950">
              {correctAnswer ?? answer.expected_answer}
            </p>
          </div>
        ) : null}
      </div>

      {answer.grading_instructions ? (
        <div className="rounded-md border border-slate-200 p-3">
          <p className="text-xs font-medium text-ink-500">راهنمای تصحیح</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink-800">{answer.grading_instructions}</p>
        </div>
      ) : null}

      <dl className="grid gap-3 text-sm md:grid-cols-4">
        <div>
          <dt className="text-ink-500">نمره پیشنهادی</dt>
          <dd className="mt-1 font-medium text-ink-900">{score(answer.auto_score)}</dd>
        </div>
        <div>
          <dt className="text-ink-500">نمره معلم</dt>
          <dd className="mt-1 font-medium text-ink-900">{score(answer.teacher_score)}</dd>
        </div>
        <div>
          <dt className="text-ink-500">نمره نهایی</dt>
          <dd className="mt-1 font-medium text-ink-900">{score(answer.final_score)}</dd>
        </div>
        <div>
          <dt className="text-ink-500">اطمینان AI</dt>
          <dd className="mt-1 font-medium text-ink-900">{score(answer.ai_confidence)}</dd>
        </div>
      </dl>

      {answer.ai_feedback ? (
        <div className="rounded-md bg-brand-50 p-3">
          <p className="text-xs font-medium text-brand-700">بازخورد</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-brand-950">{answer.ai_feedback}</p>
        </div>
      ) : null}

      <AnswerReviewForm classId={classId} examId={examId} answer={answer} />
    </Card>
  );
}
