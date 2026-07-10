"use client";

import { Card } from "@/components/ui/card";
import type { ExamReview } from "@/types/review";

type ReviewSummaryProps = {
  review: ExamReview;
};

export function ReviewSummary({ review }: ReviewSummaryProps) {
  const reviewedCount = review.submissions.filter(
    (submission) => submission.status === "teacher_reviewed" || submission.status === "approved" || submission.status === "published"
  ).length;

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <p className="text-sm text-ink-500">ارسال‌ها</p>
        <p className="mt-2 text-2xl font-semibold text-ink-900">{review.summary.submission_count}</p>
      </Card>
      <Card>
        <p className="text-sm text-ink-500">پاسخ‌های نیازمند بازبینی</p>
        <p className="mt-2 text-2xl font-semibold text-amber-700">{review.summary.needs_review_answer_count}</p>
      </Card>
      <Card>
        <p className="text-sm text-ink-500">ارسال‌های بازبینی‌شده</p>
        <p className="mt-2 text-2xl font-semibold text-blue-700">{reviewedCount}</p>
      </Card>
      <Card>
        <p className="text-sm text-ink-500">تأییدشده</p>
        <p className="mt-2 text-2xl font-semibold text-brand-700">{review.summary.approved_count}</p>
      </Card>
    </div>
  );
}
