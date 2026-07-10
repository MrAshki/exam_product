"use client";

import { PlayCircle } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { StudentExamAccess } from "@/types/student-exam";

type ExamStartPanelProps = {
  access: StudentExamAccess;
  loading: boolean;
  error?: string | null;
  onStart: () => void;
};

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function ExamStartPanel({ access, loading, error, onStart }: ExamStartPanelProps) {
  return (
    <Card className="mx-auto max-w-2xl">
      <div className="space-y-4">
        <div>
          <p className="text-sm text-ink-500">{access.class_title}</p>
          <h1 className="mt-1 text-2xl font-bold text-ink-900">{access.exam_title}</h1>
          <p className="mt-2 text-sm text-ink-600">دانش‌آموز: {access.student_full_name}</p>
        </div>

        <dl className="grid gap-3 rounded-md border border-slate-200 p-4 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-ink-500">شروع</dt>
            <dd className="mt-1 font-medium text-ink-900">{formatDateTime(access.start_time)}</dd>
          </div>
          <div>
            <dt className="text-ink-500">پایان</dt>
            <dd className="mt-1 font-medium text-ink-900">{formatDateTime(access.end_time)}</dd>
          </div>
          <div>
            <dt className="text-ink-500">مدت آزمون</dt>
            <dd className="mt-1 font-medium text-ink-900">{access.duration_minutes} دقیقه</dd>
          </div>
        </dl>

        <Alert>آزمون آماده شروع است. بعد از شروع، زمان باقی‌مانده فقط برای راهنمایی نمایش داده می‌شود.</Alert>
        {error ? <Alert variant="error">{error}</Alert> : null}

        <div className="flex justify-end">
          <Button onClick={onStart} disabled={loading}>
            <PlayCircle size={18} />
            {loading ? "در حال شروع" : "شروع آزمون"}
          </Button>
        </div>
      </div>
    </Card>
  );
}
