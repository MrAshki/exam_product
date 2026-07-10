"use client";

import { Alert } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { AnswerReviewCard } from "@/features/grading-review/components/answer-review-card";
import { ReviewStatusBadge } from "@/features/grading-review/components/review-status-badge";
import type { ReviewSubmissionWithAnswers } from "@/types/review";

type SubmissionReviewPanelProps = {
  classId: string;
  examId: string;
  submission?: ReviewSubmissionWithAnswers | null;
};

function score(value: string | number | null | undefined) {
  return value ?? "—";
}

export function SubmissionReviewPanel({ classId, examId, submission }: SubmissionReviewPanelProps) {
  if (!submission) {
    return (
      <Card>
        <p className="text-sm text-ink-500">یک ارسال را برای بازبینی انتخاب کنید.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-ink-900">{submission.student_full_name}</h2>
            {submission.student_email ? <p className="mt-1 text-sm text-ink-500">{submission.student_email}</p> : null}
          </div>
          <ReviewStatusBadge status={submission.status} />
        </div>
        <dl className="grid gap-3 text-sm md:grid-cols-3">
          <div>
            <dt className="text-ink-500">نمره کل</dt>
            <dd className="mt-1 font-medium text-ink-900">
              {score(submission.total_score)} / {score(submission.max_score)}
            </dd>
          </div>
          <div>
            <dt className="text-ink-500">پاسخ‌ها</dt>
            <dd className="mt-1 font-medium text-ink-900">{submission.answers.length}</dd>
          </div>
          <div>
            <dt className="text-ink-500">نیازمند بازبینی</dt>
            <dd className="mt-1 font-medium text-ink-900">{submission.needs_review_count}</dd>
          </div>
        </dl>
      </Card>

      {submission.answers.length === 0 ? (
        <Alert>backend برای این ارسال جزئیات پاسخ برنگردانده است؛ ویرایش نمره پاسخ غیرفعال است.</Alert>
      ) : (
        submission.answers.map((answer, index) => (
          <AnswerReviewCard
            key={answer.answer_id}
            classId={classId}
            examId={examId}
            answer={answer}
            index={index}
          />
        ))
      )}
    </div>
  );
}
