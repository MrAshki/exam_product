"use client";

import { Send } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { usePublishResults } from "@/features/grading-review/hooks";
import { ReviewStatusBadge } from "@/features/grading-review/components/review-status-badge";
import { getErrorMessage } from "@/lib/errors";
import type { ExamReview } from "@/types/review";

type PublishResultsPanelProps = {
  classId: string;
  examId: string;
  review: ExamReview;
};

export function PublishResultsPanel({ classId, examId, review }: PublishResultsPanelProps) {
  const publish = usePublishResults(classId, examId);

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ink-900">انتشار نتایج</h2>
        <p className="mt-1 text-sm leading-6 text-ink-500">
          بعد از انتشار، دانش‌آموزها می‌توانند نتیجه خود را ببینند و اعتراض ثبت کنند.
        </p>
      </div>
      <Alert>ایمیل‌های نتیجه و لیدربورد، اگر فعال باشد، توسط backend صف‌بندی می‌شوند.</Alert>
      <div className="flex items-center gap-2 text-sm text-ink-500">
        <span>وضعیت فعلی آزمون:</span>
        <ReviewStatusBadge status={review.exam.status} />
      </div>
      {publish.error ? <Alert variant="error">{getErrorMessage(publish.error)}</Alert> : null}
      {publish.data ? (
        <Alert variant="success">
          انتشار انجام شد. لینک‌های نتیجه ساخته‌شده: {publish.data.created_result_tokens}، ایمیل‌های صف‌شده:{" "}
          {publish.data.queued_result_emails}، لیدربورد:{" "}
          {publish.data.leaderboard_enabled ? "فعال" : "غیرفعال"}
        </Alert>
      ) : null}
      <div className="flex justify-end">
        <Button onClick={() => publish.mutate()} disabled={publish.isPending}>
          <Send size={16} />
          {publish.isPending ? "در حال انتشار" : "انتشار نتایج"}
        </Button>
      </div>
    </Card>
  );
}
