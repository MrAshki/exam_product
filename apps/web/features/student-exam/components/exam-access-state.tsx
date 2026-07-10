"use client";

import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2, Clock3, Hourglass, ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/formatters";

type AccessStateKind = "info" | "waiting" | "error" | "success";

type ExamAccessStateProps = {
  kind?: AccessStateKind;
  title: string;
  message: string;
  detail?: string;
  actionLabel?: string;
  onAction?: () => void;
  children?: ReactNode;
};

const iconByKind = {
  info: Clock3,
  waiting: Hourglass,
  error: ShieldAlert,
  success: CheckCircle2
};

const toneByKind: Record<AccessStateKind, string> = {
  info: "bg-blue-50 text-blue-800",
  waiting: "bg-amber-50 text-amber-800",
  error: "bg-rose-50 text-rose-800",
  success: "bg-brand-50 text-brand-700"
};

export function ExamAccessState({
  kind = "info",
  title,
  message,
  detail,
  actionLabel,
  onAction,
  children
}: ExamAccessStateProps) {
  const Icon = iconByKind[kind] ?? AlertCircle;

  return (
    <Card className="mx-auto max-w-2xl text-center">
      <div className={cn("mx-auto flex h-12 w-12 items-center justify-center rounded-full", toneByKind[kind])}>
        <Icon size={22} />
      </div>
      <h1 className="mt-4 text-2xl font-bold text-ink-900">{title}</h1>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-ink-600">{message}</p>
      {detail ? <p className="mt-2 text-xs text-ink-500">{detail}</p> : null}
      {children ? <div className="mt-5">{children}</div> : null}
      {actionLabel && onAction ? (
        <div className="mt-6">
          <Button onClick={onAction}>{actionLabel}</Button>
        </div>
      ) : null}
    </Card>
  );
}
