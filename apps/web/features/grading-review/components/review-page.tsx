"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LoadingBlock } from "@/components/ui/loading-block";
import { ApproveResultsPanel } from "@/features/grading-review/components/approve-results-panel";
import { PublishResultsPanel } from "@/features/grading-review/components/publish-results-panel";
import { ReviewEmptyState } from "@/features/grading-review/components/review-empty-state";
import { ReviewStatusBadge } from "@/features/grading-review/components/review-status-badge";
import { ReviewSummary } from "@/features/grading-review/components/review-summary";
import { SubmissionFilter, filterSubmissions, SubmissionList } from "@/features/grading-review/components/submission-list";
import { SubmissionReviewPanel } from "@/features/grading-review/components/submission-review-panel";
import { useExamReview } from "@/features/grading-review/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";

type ReviewPageProps = {
  classId: string;
  examId: string;
};

export function ReviewPage({ classId, examId }: ReviewPageProps) {
  const review = useExamReview(classId, examId);
  const [filter, setFilter] = useState<SubmissionFilter>("all");
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<string | null>(null);

  const filteredSubmissions = useMemo(
    () => filterSubmissions(review.data?.submissions ?? [], filter),
    [filter, review.data?.submissions]
  );

  const activeSubmissionId =
    filteredSubmissions.find((submission) => submission.submission_id === selectedSubmissionId)?.submission_id ??
    filteredSubmissions[0]?.submission_id ??
    null;
  const selectedSubmission =
    review.data?.submissions.find((submission) => submission.submission_id === activeSubmissionId) ?? null;

  if (review.isLoading) {
    return <LoadingBlock label="در حال دریافت بازبینی آزمون" />;
  }

  if (review.isError) {
    return (
      <div className="space-y-4">
        <Link href={routes.classExams(classId)}>
          <Button variant="secondary">
            <ArrowRight size={16} />
            آزمون‌های کلاس
          </Button>
        </Link>
        <Alert variant="error">{getErrorMessage(review.error)}</Alert>
      </div>
    );
  }

  if (!review.data) {
    return <ReviewEmptyState />;
  }

  const hasAnswerDetails = review.data.submissions.some((submission) => submission.answers.length > 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="بازبینی نمره‌ها"
        description={review.data.exam.title}
        action={
          <div className="flex flex-wrap items-center gap-2">
            <ReviewStatusBadge status={review.data.exam.status} />
            <Badge>{review.data.exam.total_points ?? "—"} نمره</Badge>
          </div>
        }
      />

      <div className="flex flex-wrap gap-2">
        <Link href={routes.classExams(classId)}>
          <Button variant="secondary">
            <ArrowRight size={16} />
            آزمون‌های کلاس
          </Button>
        </Link>
        <Link href={routes.examBuilder(classId, examId)}>
          <Button variant="secondary">سازنده</Button>
        </Link>
        <Link href={routes.examSchedule(classId, examId)}>
          <Button variant="secondary">زمان‌بندی</Button>
        </Link>
      </div>

      <ReviewSummary review={review.data} />

      {!hasAnswerDetails ? (
        <Alert>backend جزئیات پاسخ‌ها را برنگردانده است؛ ویرایش نمره پاسخ در این صفحه غیرفعال می‌ماند.</Alert>
      ) : null}

      {review.data.submissions.length === 0 ? (
        <ReviewEmptyState />
      ) : (
        <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
          <div className="xl:sticky xl:top-24 xl:self-start">
            <SubmissionList
              submissions={review.data.submissions}
              selectedSubmissionId={activeSubmissionId}
              filter={filter}
              onFilterChange={setFilter}
              onSelect={(submission) => setSelectedSubmissionId(submission.submission_id)}
            />
          </div>
          <SubmissionReviewPanel classId={classId} examId={examId} submission={selectedSubmission} />
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-2">
        <ApproveResultsPanel classId={classId} examId={examId} review={review.data} />
        <PublishResultsPanel classId={classId} examId={examId} review={review.data} />
      </div>
    </div>
  );
}
