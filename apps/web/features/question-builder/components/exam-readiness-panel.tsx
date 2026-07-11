"use client";

import { CheckCircle, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { FormError } from "@/components/common/form-error";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { LoadingBlock } from "@/components/ui/loading-block";
import { formatDecimal } from "@/lib/decimal";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";
import type { Exam, ExamReadiness, ExamReadinessFailure } from "@/types/exam";

type ExamReadinessPanelProps = {
  classId: string;
  exam?: Exam;
  readiness?: ExamReadiness;
  loading?: boolean;
  error?: unknown;
  finalizePending?: boolean;
  finalizeError?: unknown;
  reopenPending?: boolean;
  reopenError?: unknown;
  onFinalize: () => void;
  onReopen: () => void;
  onSelectQuestion?: (questionId?: string | null, orderIndex?: number | null) => void;
};

export function ExamReadinessPanel({
  classId,
  exam,
  readiness,
  loading,
  error,
  finalizePending,
  finalizeError,
  reopenPending,
  reopenError,
  onFinalize,
  onReopen,
  onSelectQuestion
}: ExamReadinessPanelProps) {
  const [finalizeOpen, setFinalizeOpen] = useState(false);
  const [reopenOpen, setReopenOpen] = useState(false);
  const canFinalize = Boolean(readiness?.finalization_allowed);
  const canSchedule = Boolean(readiness?.scheduling_allowed);
  const canReopen = Boolean(readiness?.reopen_allowed);
  const reopenLabel = readiness?.reopen_mode === "scheduled_before_start" ? "لغو زمان‌بندی و ویرایش" : "بازگشایی برای ویرایش";
  const reopenDialogTitle = readiness?.invalidates_tokens ? "لغو زمان‌بندی و ویرایش" : "بازگشایی آزمون";
  const reopenDialogDescription = readiness?.invalidates_tokens
    ? "زمان‌بندی لغو می‌شود، لینک‌های قبلی دانش‌آموزان غیرفعال می‌شوند، و دعوت‌نامه‌های قبلی قابل پس‌گرفتن نیستند. باید آزمون را دوباره نهایی و زمان‌بندی کنید."
    : "آزمون به پیش‌نویس برمی‌گردد، سوال‌ها دوباره قابل ویرایش می‌شوند و تأیید نهایی باید دوباره انجام شود.";
  const groupedFailures = useMemo(() => groupFailures(readiness?.failures ?? []), [readiness?.failures]);

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-ink-900">آمادگی آزمون</h2>
          <p className="mt-1 text-sm text-ink-500">بررسی نهایی از روی داده‌های ذخیره‌شده backend انجام می‌شود.</p>
        </div>
        {readiness?.is_ready ? (
          <span className="inline-flex items-center gap-1 rounded-md bg-brand-50 px-3 py-1 text-sm font-medium text-brand-700">
            <CheckCircle size={16} />
            آماده
          </span>
        ) : null}
      </div>

      {loading ? <LoadingBlock label="در حال بررسی آمادگی آزمون" /> : null}
      {error ? <Alert variant="error">{getErrorMessage(error)}</Alert> : null}
      <FormError message={finalizeError ? getErrorMessage(finalizeError) : null} />
      <FormError message={reopenError ? getErrorMessage(reopenError) : null} />

      {readiness ? (
        <>
          <div className="grid gap-3 text-sm sm:grid-cols-3">
            <div className="rounded-md bg-slate-50 p-3">
              <p className="text-ink-500">سوال‌های کامل</p>
              <p className="mt-1 text-xl font-semibold text-ink-900">
                {readiness.complete_question_count} / {readiness.total_question_count}
              </p>
            </div>
            <div className="rounded-md bg-slate-50 p-3">
              <p className="text-ink-500">نمره سوال‌ها / آزمون</p>
              <p className="mt-1 text-xl font-semibold text-ink-900">
                {formatDecimal(readiness.calculated_question_points)} / {formatDecimal(readiness.exam_total_points)}
              </p>
            </div>
            <div className="rounded-md bg-slate-50 p-3">
              <p className="text-ink-500">ساختار آزمون</p>
              <p className="mt-1 text-xl font-semibold text-ink-900">
                {readiness.blueprint_match ? "هماهنگ" : "نیازمند اصلاح"}
              </p>
            </div>
          </div>

          {!readiness.is_ready ? (
            <div className="space-y-2">
              <Alert>مشکل‌های زیر را اصلاح کنید و دوباره آزمون را نهایی کنید.</Alert>
              {groupedFailures.examFailures.length ? (
                <div className="space-y-2">
                  {groupedFailures.examFailures.map((failure, index) => (
                    <div
                      key={`exam-${failure.message}-${index}`}
                      className="rounded-md border border-slate-200 bg-white p-3 text-sm text-ink-700"
                    >
                      {failure.message}
                    </div>
                  ))}
                </div>
              ) : null}
              <div className="space-y-2">
                {groupedFailures.questionFailures.map((group) => (
                  <button
                    key={group.questionId ?? `order-${group.orderIndex}`}
                    type="button"
                    onClick={() => onSelectQuestion?.(group.questionId, group.orderIndex)}
                    className="w-full cursor-pointer rounded-md border border-slate-200 bg-white p-3 text-right text-sm text-ink-700 transition hover:border-brand-200 hover:bg-brand-50 focus:outline-none focus:ring-2 focus:ring-brand-300"
                  >
                    <span className="font-semibold">سوال {toPersianDigits(group.orderIndex ?? "—")}</span>
                    <ul className="mt-2 space-y-1 text-ink-500">
                      {group.messages.map((message) => (
                        <li key={message}>{message}</li>
                      ))}
                    </ul>
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          {!readiness.reopen_allowed && readiness.reopen_block_message && exam?.status !== "draft" ? (
            <Alert variant={readiness.is_in_progress || readiness.has_submissions ? "error" : "info"}>
              {readiness.reopen_block_message}
              {exam?.status === "scheduled" && exam.start_time && exam.end_time ? (
                <span className="mt-2 block text-xs text-ink-500">
                  بازه آزمون: {new Date(exam.start_time).toLocaleString("fa-IR")} تا {new Date(exam.end_time).toLocaleString("fa-IR")}
                </span>
              ) : null}
            </Alert>
          ) : null}
        </>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {exam?.status === "draft" ? (
          <Button onClick={() => setFinalizeOpen(true)} disabled={!canFinalize || finalizePending}>
            <CheckCircle size={16} />
            {finalizePending ? "در حال نهایی‌سازی" : "تأیید نهایی آزمون"}
          </Button>
        ) : null}
        {canReopen ? (
          <Button variant="secondary" onClick={() => setReopenOpen(true)} disabled={reopenPending}>
            <RefreshCw size={16} />
            {reopenPending ? "در حال بازگشایی" : reopenLabel}
          </Button>
        ) : null}
        {exam ? (
          <Link href={routes.examSchedule(classId, exam.id)}>
            <Button variant="secondary" disabled={!canSchedule}>رفتن به زمان‌بندی</Button>
          </Link>
        ) : null}
      </div>

      <ConfirmDialog
        open={finalizeOpen}
        title="تأیید نهایی آزمون"
        description="پس از نهایی‌سازی، ویرایش سوال‌ها قفل می‌شود و زمان‌بندی آزمون فعال خواهد شد."
        confirmLabel="نهایی‌سازی"
        loading={finalizePending}
        onConfirm={() => {
          setFinalizeOpen(false);
          onFinalize();
        }}
        onClose={() => setFinalizeOpen(false)}
      />
      <ConfirmDialog
        open={reopenOpen}
        title={reopenDialogTitle}
        description={reopenDialogDescription}
        confirmLabel={readiness?.invalidates_tokens ? "لغو زمان‌بندی" : "بازگشایی"}
        loading={reopenPending}
        onConfirm={() => {
          setReopenOpen(false);
          onReopen();
        }}
        onClose={() => setReopenOpen(false)}
      />
    </Card>
  );
}

function groupFailures(failures: ExamReadinessFailure[]) {
  const examFailures: ExamReadinessFailure[] = [];
  const groups = new Map<string, { questionId: string | null; orderIndex: number | null; messages: string[] }>();

  for (const failure of failures) {
    const hasQuestionTarget = Boolean(failure.question_id) || failure.order_index !== null;
    if (!hasQuestionTarget) {
      examFailures.push(failure);
      continue;
    }
    const key = failure.question_id || `order-${failure.order_index ?? "unknown"}`;
    const group = groups.get(key) ?? {
      questionId: failure.question_id,
      orderIndex: failure.order_index,
      messages: []
    };
    if (!group.messages.includes(failure.message)) {
      group.messages.push(failure.message);
    }
    groups.set(key, group);
  }

  return { examFailures, questionFailures: Array.from(groups.values()).sort((a, b) => (a.orderIndex ?? 0) - (b.orderIndex ?? 0)) };
}

function toPersianDigits(value: number | string) {
  return String(value).replace(/\d/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);
}
