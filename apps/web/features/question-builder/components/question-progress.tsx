import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { decimalToNumber, formatDecimal, sumDecimalValues } from "@/lib/decimal";
import type { Exam, ExamReadiness } from "@/types/exam";
import type { QuestionSlot } from "@/types/question";

type QuestionProgressProps = {
  exam?: Exam;
  questions: QuestionSlot[];
  readiness?: ExamReadiness;
};

const statusLabels: Record<string, string> = {
  draft: "پیش‌نویس",
  finalized: "نهایی‌شده",
  scheduled: "زمان‌بندی‌شده",
  review_required: "آماده بازبینی",
  approved: "تایید شده",
  published: "منتشر شده"
};

export function QuestionProgress({ exam, questions, readiness }: QuestionProgressProps) {
  const total = questions.length;
  const complete = readiness?.complete_question_count ?? questions.filter((question) => question.text && decimalToNumber(question.points) > 0).length;
  const percent = total ? Math.round((complete / total) * 100) : 0;
  const points = sumDecimalValues(questions.map((question) => question.points));

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink-900">{exam?.title || "آزمون"}</h2>
          <p className="mt-1 text-sm text-ink-500">وضعیت: {exam ? statusLabels[exam.status] ?? "وضعیت نامشخص" : "در حال دریافت"}</p>
        </div>
        <Badge>{percent}% تکمیل</Badge>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${percent}%` }} />
      </div>
      <div className="grid gap-3 text-sm sm:grid-cols-3">
        <div className="rounded-md bg-slate-50 p-3">
          <p className="text-ink-500">کل سوال‌ها</p>
          <p className="mt-1 text-xl font-semibold text-ink-900">{total}</p>
        </div>
        <div className="rounded-md bg-slate-50 p-3">
          <p className="text-ink-500">کامل</p>
          <p className="mt-1 text-xl font-semibold text-ink-900">{complete}</p>
        </div>
        <div className="rounded-md bg-slate-50 p-3">
          <p className="text-ink-500">نمره سوال‌ها / آزمون</p>
          <p className="mt-1 text-xl font-semibold text-ink-900">{points} / {exam ? formatDecimal(exam.total_points) : "—"}</p>
        </div>
      </div>
    </Card>
  );
}
