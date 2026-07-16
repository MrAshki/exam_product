"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LoadingBlock } from "@/components/ui/loading-block";
import { AppealResolveForm } from "@/features/appeals/components/appeal-resolve-form";
import { AppealStatusBadge } from "@/features/appeals/components/appeal-status-badge";
import { useClassAppeal, useResolveClassAppeal } from "@/features/appeals/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";
import type { AppealAnswer, AppealResolvePayload, AppealResolveResult } from "@/types/appeal";

type AppealDetailPageProps = {
  classId: string;
  appealId: string;
};

function formatDateTime(value?: string | null) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function readableData(value: unknown): string | null {
  if (!value) {
    return null;
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.map(readableData).filter(Boolean).join("، ") || null;
  }

  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const preferred = record.selected_option ?? record.option_key ?? record.value ?? record.text;
    if (preferred !== undefined && preferred !== null) {
      return String(preferred);
    }
  }

  return null;
}

function AnswerContext({ answer }: { answer: AppealAnswer | null }) {
  if (!answer) {
    return <Alert>این اعتراض برای کل آزمون ثبت شده است.</Alert>;
  }

  const studentAnswer = answer.student_answer || readableData(answer.answer_data) || "بدون پاسخ";
  const correctAnswer = answer.correct_answer || readableData(answer.correct_answer_data);

  return (
    <Card className="space-y-4">
      <h2 className="text-lg font-semibold text-ink-900">جزئیات پاسخ</h2>
      <p className="whitespace-pre-wrap text-sm leading-7 text-ink-900">
        {answer.question_text || "متن سوال ثبت نشده است."}
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-md bg-slate-50 p-3">
          <p className="text-xs font-medium text-ink-500">پاسخ دانش‌آموز</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink-800">{studentAnswer}</p>
        </div>
        {correctAnswer ? (
          <div className="rounded-md bg-brand-50 p-3">
            <p className="text-xs font-medium text-brand-700">پاسخ صحیح</p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-brand-900">{correctAnswer}</p>
          </div>
        ) : null}
      </div>
      {answer.expected_answer ? (
        <div className="rounded-md bg-blue-50 p-3">
          <p className="text-xs font-medium text-blue-800">پاسخ مورد انتظار</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-blue-950">{answer.expected_answer}</p>
        </div>
      ) : null}
      <dl className="grid gap-3 text-sm md:grid-cols-3">
        <div>
          <dt className="text-ink-500">نمره فعلی</dt>
          <dd className="mt-1 font-medium text-ink-900">{answer.current_score ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-ink-500">نمره سوال</dt>
          <dd className="mt-1 font-medium text-ink-900">{answer.max_score ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-ink-500">اطمینان AI</dt>
          <dd className="mt-1 font-medium text-ink-900">{answer.ai_confidence ?? "—"}</dd>
        </div>
      </dl>
      {answer.ai_feedback ? (
        <div className="rounded-md border border-blue-100 bg-blue-50 p-3">
          <p className="text-xs font-medium text-blue-800">ارزیابی خودکار</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink-800">{answer.ai_feedback}</p>
        </div>
      ) : null}
      {answer.teacher_feedback ? (
        <div className="rounded-md border border-brand-100 bg-brand-50 p-3">
          <p className="text-xs font-medium text-brand-700">بازخورد معلم</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-brand-950">{answer.teacher_feedback}</p>
        </div>
      ) : null}
    </Card>
  );
}

export function AppealDetailPage({ classId, appealId }: AppealDetailPageProps) {
  const appeal = useClassAppeal(classId, appealId);
  const resolveAppeal = useResolveClassAppeal(classId, appealId);
  const [resolveResult, setResolveResult] = useState<AppealResolveResult | null>(null);

  async function handleResolve(payload: AppealResolvePayload) {
    const result = await resolveAppeal.mutateAsync(payload);
    setResolveResult(result);
    return result;
  }

  if (appeal.isLoading) {
    return <LoadingBlock label="در حال دریافت اعتراض" />;
  }

  if (appeal.isError) {
    return <Alert variant="error">{getErrorMessage(appeal.error)}</Alert>;
  }

  if (!appeal.data) {
    return <Alert variant="error">اعتراض پیدا نشد.</Alert>;
  }

  const resolved = appeal.data.status !== "pending" || Boolean(resolveResult);

  return (
    <div className="space-y-6">
      <PageHeader
        title="بررسی اعتراض"
        description={appeal.data.exam_title}
        action={
          <Link href={routes.appeals(classId)}>
            <Button variant="secondary">
              <ArrowRight size={16} />
              فهرست اعتراض‌ها
            </Button>
          </Link>
        }
      />

      <Card className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-ink-900">{appeal.data.student_full_name}</h2>
            <p className="mt-1 text-sm text-ink-500">{appeal.data.student_email}</p>
          </div>
          <AppealStatusBadge status={resolveResult?.status ?? appeal.data.status} />
        </div>
        <dl className="grid gap-3 text-sm md:grid-cols-4">
          <div>
            <dt className="text-ink-500">ثبت</dt>
            <dd className="mt-1 font-medium text-ink-900">{formatDateTime(appeal.data.created_at)}</dd>
          </div>
          <div>
            <dt className="text-ink-500">رسیدگی</dt>
            <dd className="mt-1 font-medium text-ink-900">{formatDateTime(appeal.data.resolved_at)}</dd>
          </div>
          <div>
            <dt className="text-ink-500">نمره قدیم</dt>
            <dd className="mt-1 font-medium text-ink-900">{appeal.data.old_score ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-ink-500">نمره جدید</dt>
            <dd className="mt-1 font-medium text-ink-900">{appeal.data.new_score ?? "—"}</dd>
          </div>
        </dl>
        <div className="rounded-md bg-slate-50 p-3">
          <p className="text-xs font-medium text-ink-500">پیام دانش‌آموز</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink-900">{appeal.data.message}</p>
        </div>
        {appeal.data.teacher_response ? (
          <div className="rounded-md bg-brand-50 p-3">
            <p className="text-xs font-medium text-brand-700">پاسخ معلم</p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-brand-950">{appeal.data.teacher_response}</p>
          </div>
        ) : null}
      </Card>

      <AnswerContext answer={appeal.data.answer} />

      <Card className="space-y-4">
        <h2 className="text-lg font-semibold text-ink-900">ثبت رسیدگی</h2>
        <AppealResolveForm
          disabled={resolved}
          loading={resolveAppeal.isPending}
          error={resolveAppeal.error}
          result={resolveResult}
          onSubmit={handleResolve}
        />
      </Card>
    </div>
  );
}
