"use client";

import { Alert } from "@/components/ui/alert";
import { LoadingBlock } from "@/components/ui/loading-block";
import { ExamAccessState } from "@/features/student-exam/components/exam-access-state";
import { ExamStartPanel } from "@/features/student-exam/components/exam-start-panel";
import { QuestionAnswerForm } from "@/features/student-exam/components/question-answer-form";
import { SubmittedState } from "@/features/student-exam/components/submitted-state";
import { useExamAccess, useStartExam, useSubmitExam } from "@/features/student-exam/hooks";
import { ApiError } from "@/lib/api-client";
import { getErrorMessage } from "@/lib/errors";
import type { StudentExamSession, StudentExamSubmitPayload, StudentExamSubmitResult } from "@/types/student-exam";
import { useState, type ReactNode } from "react";

type StudentExamPageProps = {
  examToken: string;
};

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function errorState(error: unknown) {
  if (error instanceof ApiError) {
    if (error.code === "INVALID_EXAM_TOKEN") {
      return {
        title: "لینک آزمون معتبر نیست",
        message: "این لینک معتبر نیست یا منقضی شده است."
      };
    }

    if (error.code === "EXAM_ALREADY_SUBMITTED") {
      return {
        title: "آزمون قبلاً ارسال شده است",
        message: "شما قبلاً این آزمون را ارسال کرده‌اید."
      };
    }

    if (error.code === "EXAM_TIME_EXPIRED" || error.code === "EXAM_NOT_ACTIVE") {
      return {
        title: "آزمون در دسترس نیست",
        message: "زمان آزمون به پایان رسیده است یا هنوز امکان شروع وجود ندارد."
      };
    }
  }

  return {
    title: "خطا در دریافت آزمون",
    message: getErrorMessage(error)
  };
}

export function StudentExamPage({ examToken }: StudentExamPageProps) {
  const access = useExamAccess(examToken);
  const startExam = useStartExam(examToken);
  const submitExam = useSubmitExam(examToken);
  const [session, setSession] = useState<StudentExamSession | null>(null);
  const [submittedResult, setSubmittedResult] = useState<StudentExamSubmitResult | null>(null);

  async function handleStart() {
    try {
      const started = await startExam.mutateAsync();
      setSession(started);
    } catch {
      return;
    }
  }

  async function handleSubmit(payload: StudentExamSubmitPayload) {
    const submitted = await submitExam.mutateAsync(payload);
    setSubmittedResult(submitted);
    return submitted;
  }

  if (!examToken) {
    return (
      <PublicExamShell>
        <ExamAccessState
          kind="error"
          title="لینک آزمون معتبر نیست"
          message="این لینک معتبر نیست یا منقضی شده است."
        />
      </PublicExamShell>
    );
  }

  if (submittedResult) {
    return (
      <PublicExamShell>
        <SubmittedState result={submittedResult} />
      </PublicExamShell>
    );
  }

  if (session) {
    return (
      <PublicExamShell>
        <QuestionAnswerForm
          session={session}
          loading={submitExam.isPending}
          error={submitExam.error}
          onSubmit={handleSubmit}
        />
      </PublicExamShell>
    );
  }

  if (access.isLoading) {
    return (
      <PublicExamShell>
        <LoadingBlock label="در حال دریافت آزمون" />
      </PublicExamShell>
    );
  }

  if (access.isError) {
    const state = errorState(access.error);
    return (
      <PublicExamShell>
        <ExamAccessState kind="error" title={state.title} message={state.message} />
      </PublicExamShell>
    );
  }

  if (!access.data) {
    return (
      <PublicExamShell>
        <ExamAccessState kind="error" title="آزمون پیدا نشد" message="امکان دریافت اطلاعات آزمون وجود ندارد." />
      </PublicExamShell>
    );
  }

  if (access.data.status === "waiting") {
    return (
      <PublicExamShell>
        <ExamAccessState
          kind="waiting"
          title="آزمون هنوز شروع نشده است"
          message="آزمون هنوز شروع نشده است. در زمان اعلام‌شده دوباره همین لینک را باز کنید."
          detail={`شروع آزمون: ${formatDateTime(access.data.start_time)}`}
        >
          <Alert>زمان رسمی آزمون را سامانه تعیین می‌کند؛ ممکن است با ساعت دستگاه شما کمی تفاوت داشته باشد.</Alert>
        </ExamAccessState>
      </PublicExamShell>
    );
  }

  if (access.data.status === "ready") {
    return (
      <PublicExamShell>
        <ExamStartPanel
          access={access.data}
          loading={startExam.isPending}
          error={startExam.error ? getErrorMessage(startExam.error) : null}
          onStart={handleStart}
        />
      </PublicExamShell>
    );
  }

  if (access.data.status === "submitted") {
    return (
      <PublicExamShell>
        <SubmittedState />
      </PublicExamShell>
    );
  }

  return (
    <PublicExamShell>
      <ExamAccessState
        kind="info"
        title="وضعیت آزمون مشخص نیست"
        message="وضعیت فعلی آزمون قابل شروع نیست."
        detail={`وضعیت: ${access.data.status}`}
      />
    </PublicExamShell>
  );
}

function PublicExamShell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">{children}</div>
    </main>
  );
}
