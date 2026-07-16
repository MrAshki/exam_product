"use client";

import { CheckCircle2 } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useApproveResults } from "@/features/grading-review/hooks";
import { ReviewStatusBadge } from "@/features/grading-review/components/review-status-badge";
import { getErrorMessage } from "@/lib/errors";
import type { ExamReview } from "@/types/review";

type ApproveResultsPanelProps = {
  classId: string;
  examId: string;
  review: ExamReview;
};

export function ApproveResultsPanel({ classId, examId, review }: ApproveResultsPanelProps) {
  const approve = useApproveResults(classId, examId);

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ink-900">تأیید نتایج</h2>
        <p className="mt-1 text-sm leading-6 text-ink-500">بعد از تأیید، نتایج برای انتشار آماده می‌شوند.</p>
      </div>
      <Alert className="flex flex-wrap items-center gap-2">
        <span>وضعیت فعلی آزمون:</span>
        <ReviewStatusBadge status={review.exam.status} />
        <span>پاسخ‌های نیازمند بازبینی: {review.summary.needs_review_answer_count}</span>
      </Alert>
      {approve.error ? <Alert variant="error">{getErrorMessage(approve.error)}</Alert> : null}
      {approve.data ? (
        <Alert variant="success">
          نتایج تأیید شد. تعداد ارسال‌های تأییدشده: {approve.data.approved_submissions}
        </Alert>
      ) : null}
      <div className="flex justify-end">
        <Button onClick={() => approve.mutate()} disabled={approve.isPending}>
          <CheckCircle2 size={16} />
          {approve.isPending ? "در حال تأیید" : "تأیید نهایی نمرات"}
        </Button>
      </div>
    </Card>
  );
}
