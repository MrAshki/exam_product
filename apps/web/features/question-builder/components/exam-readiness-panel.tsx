import Link from "next/link";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { routes } from "@/lib/routes";
import type { Exam } from "@/types/exam";
import type { QuestionSlot } from "@/types/question";

type ExamReadinessPanelProps = {
  classId: string;
  exam?: Exam;
  questions: QuestionSlot[];
};

export function ExamReadinessPanel({ classId, exam, questions }: ExamReadinessPanelProps) {
  const confirmed = questions.filter((question) => question.teacher_confirmed || question.status === "confirmed").length;
  const allConfirmed = questions.length > 0 && confirmed === questions.length;
  const points = questions.reduce((sum, question) => sum + question.points, 0);
  const pointsMatch = exam ? points === exam.total_points : false;
  const canTrySchedule = allConfirmed && pointsMatch && exam?.status === "draft";

  return (
    <Card className="space-y-4">
      <h2 className="text-base font-semibold text-ink-900">آمادگی آزمون</h2>
      <div className="space-y-2 text-sm text-ink-600">
        <p>سوال‌های تایید شده: {confirmed} از {questions.length}</p>
        <p>جمع نمره سوال‌ها: {points} از {exam?.total_points ?? "—"}</p>
      </div>
      {!canTrySchedule ? (
        <Alert>
          آمادگی نهایی را backend هنگام زمان‌بندی بررسی می‌کند. قبل از زمان‌بندی همه سوال‌ها را تایید کنید و جمع نمره‌ها را با نمره آزمون برابر نگه دارید.
        </Alert>
      ) : null}
      {exam ? (
        <Link href={routes.examSchedule(classId, exam.id)}>
          <Button disabled={!canTrySchedule}>رفتن به زمان‌بندی</Button>
        </Link>
      ) : null}
    </Card>
  );
}
