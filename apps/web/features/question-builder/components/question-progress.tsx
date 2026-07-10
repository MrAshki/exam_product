import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { Exam } from "@/types/exam";
import type { QuestionSlot } from "@/types/question";

type QuestionProgressProps = {
  exam?: Exam;
  questions: QuestionSlot[];
};

export function QuestionProgress({ exam, questions }: QuestionProgressProps) {
  const total = questions.length;
  const confirmed = questions.filter((question) => question.teacher_confirmed || question.status === "confirmed").length;
  const percent = total ? Math.round((confirmed / total) * 100) : 0;
  const points = questions.reduce((sum, question) => sum + question.points, 0);

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink-900">{exam?.title || "آزمون"}</h2>
          <p className="mt-1 text-sm text-ink-500">وضعیت: {exam?.status || "—"}</p>
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
          <p className="text-ink-500">تایید شده</p>
          <p className="mt-1 text-xl font-semibold text-ink-900">{confirmed}</p>
        </div>
        <div className="rounded-md bg-slate-50 p-3">
          <p className="text-ink-500">نمره سوال‌ها / آزمون</p>
          <p className="mt-1 text-xl font-semibold text-ink-900">{points} / {exam?.total_points ?? "—"}</p>
        </div>
      </div>
    </Card>
  );
}
