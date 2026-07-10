"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { StudentResult } from "@/types/result";

type ResultSummaryCardProps = {
  result: StudentResult;
};

function scoreNumber(value?: string | null) {
  if (value === null || value === undefined) {
    return null;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function percentage(total?: string | null, max?: string | null) {
  const totalScore = scoreNumber(total);
  const maxScore = scoreNumber(max);

  if (totalScore === null || maxScore === null || maxScore === 0) {
    return null;
  }

  return (totalScore / maxScore) * 100;
}

export function ResultSummaryCard({ result }: ResultSummaryCardProps) {
  const percent = percentage(result.total_score, result.max_score);

  return (
    <Card>
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <Badge>{result.class_title}</Badge>
          <h1 className="mt-3 text-2xl font-bold text-ink-900">نتیجه آزمون {result.exam_title}</h1>
          <p className="mt-2 text-sm text-ink-600">دانش‌آموز: {result.student_full_name}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-center">
          <p className="text-sm text-ink-500">نمره کل</p>
          <p className="mt-1 text-2xl font-bold text-ink-900">
            {result.total_score ?? "—"} / {result.max_score ?? "—"}
          </p>
          {percent !== null ? <p className="mt-1 text-xs text-ink-500">{percent.toFixed(1)} درصد</p> : null}
        </div>
      </div>
    </Card>
  );
}
