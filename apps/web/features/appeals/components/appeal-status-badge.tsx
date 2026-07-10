"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/formatters";

type AppealStatusBadgeProps = {
  status: string;
};

const labels: Record<string, string> = {
  pending: "در انتظار بررسی",
  accepted: "پذیرفته‌شده",
  rejected: "ردشده",
  resolved: "رسیدگی‌شده"
};

const tones: Record<string, string> = {
  pending: "bg-amber-50 text-amber-800",
  accepted: "bg-brand-50 text-brand-700",
  rejected: "bg-rose-50 text-rose-700",
  resolved: "bg-blue-50 text-blue-800"
};

export function AppealStatusBadge({ status }: AppealStatusBadgeProps) {
  return <Badge className={cn(tones[status] ?? "bg-slate-100 text-ink-700")}>{labels[status] ?? status}</Badge>;
}
