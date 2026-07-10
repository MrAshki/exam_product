"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/formatters";

type ReviewStatusBadgeProps = {
  status: string;
};

const labels: Record<string, string> = {
  draft: "پیش‌نویس",
  scheduled: "زمان‌بندی‌شده",
  review_required: "نیازمند بازبینی",
  submitted: "ارسال‌شده",
  auto_graded: "تصحیح خودکار",
  needs_review: "نیازمند بازبینی",
  teacher_reviewed: "بازبینی‌شده",
  approved: "تأییدشده",
  published: "منتشرشده"
};

const tones: Record<string, string> = {
  review_required: "bg-amber-50 text-amber-800",
  needs_review: "bg-amber-50 text-amber-800",
  teacher_reviewed: "bg-blue-50 text-blue-800",
  auto_graded: "bg-blue-50 text-blue-800",
  approved: "bg-brand-50 text-brand-700",
  published: "bg-brand-50 text-brand-700",
  submitted: "bg-slate-100 text-ink-700"
};

export function ReviewStatusBadge({ status }: ReviewStatusBadgeProps) {
  return <Badge className={cn(tones[status] ?? "bg-slate-100 text-ink-700")}>{labels[status] ?? status}</Badge>;
}
