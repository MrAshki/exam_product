"use client";

import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ReviewStatusBadge } from "@/features/grading-review/components/review-status-badge";
import { cn } from "@/lib/formatters";
import type { ReviewSubmissionWithAnswers } from "@/types/review";

type SubmissionFilter = "all" | "needs_review" | "reviewed";

type SubmissionListProps = {
  submissions: ReviewSubmissionWithAnswers[];
  selectedSubmissionId?: string | null;
  filter: SubmissionFilter;
  onFilterChange: (filter: SubmissionFilter) => void;
  onSelect: (submission: ReviewSubmissionWithAnswers) => void;
};

const filters: Array<{ label: string; value: SubmissionFilter }> = [
  { label: "همه", value: "all" },
  { label: "نیازمند بازبینی", value: "needs_review" },
  { label: "بازبینی‌شده", value: "reviewed" }
];

function score(value: string | number | null | undefined) {
  return value ?? "—";
}

export function filterSubmissions(submissions: ReviewSubmissionWithAnswers[], filter: SubmissionFilter) {
  if (filter === "needs_review") {
    return submissions.filter((submission) => submission.needs_review_count > 0);
  }
  if (filter === "reviewed") {
    return submissions.filter(
      (submission) =>
        submission.needs_review_count === 0 &&
        (submission.status === "teacher_reviewed" || submission.status === "approved" || submission.status === "published")
    );
  }
  return submissions;
}

export function SubmissionList({
  submissions,
  selectedSubmissionId,
  filter,
  onFilterChange,
  onSelect
}: SubmissionListProps) {
  const filteredSubmissions = filterSubmissions(submissions, filter);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {filters.map((item) => (
          <Button
            key={item.value}
            variant={filter === item.value ? "primary" : "secondary"}
            className="h-9"
            onClick={() => onFilterChange(item.value)}
          >
            {item.label}
          </Button>
        ))}
      </div>
      <Table>
        <TableHead>
          <TableRow>
            <TableHeader>دانش‌آموز</TableHeader>
            <TableHeader>وضعیت</TableHeader>
            <TableHeader>نمره</TableHeader>
            <TableHeader>نیازمند بازبینی</TableHeader>
          </TableRow>
        </TableHead>
        <TableBody>
          {filteredSubmissions.map((submission) => (
            <TableRow
              key={submission.submission_id}
              className={cn(
                "cursor-pointer",
                selectedSubmissionId === submission.submission_id ? "bg-brand-50 hover:bg-brand-50" : ""
              )}
              onClick={() => onSelect(submission)}
            >
              <TableCell>
                <div>
                  <p className="font-medium text-ink-900">{submission.student_full_name}</p>
                  {submission.student_email ? <p className="text-xs text-ink-500">{submission.student_email}</p> : null}
                </div>
              </TableCell>
              <TableCell>
                <ReviewStatusBadge status={submission.status} />
              </TableCell>
              <TableCell>
                {score(submission.total_score)} / {score(submission.max_score)}
              </TableCell>
              <TableCell>{submission.needs_review_count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export type { SubmissionFilter };
