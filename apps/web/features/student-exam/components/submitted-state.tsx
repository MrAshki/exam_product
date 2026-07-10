"use client";

import { ExamAccessState } from "@/features/student-exam/components/exam-access-state";
import type { StudentExamSubmitResult } from "@/types/student-exam";

type SubmittedStateProps = {
  result?: StudentExamSubmitResult | null;
};

function formatDateTime(value?: string) {
  if (!value) {
    return null;
  }

  return new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function SubmittedState({ result }: SubmittedStateProps) {
  const submittedAt = formatDateTime(result?.submitted_at);

  return (
    <ExamAccessState
      kind="success"
      title="پاسخ شما ثبت شد"
      message="پاسخ شما ثبت شد. نتیجه بعد از بررسی معلم منتشر می‌شود."
      detail={submittedAt ? `زمان ثبت: ${submittedAt}` : undefined}
    />
  );
}
