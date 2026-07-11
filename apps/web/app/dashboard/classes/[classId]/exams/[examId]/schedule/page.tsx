"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LoadingBlock } from "@/components/ui/loading-block";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { ExamReadinessPanel } from "@/features/question-builder/components/exam-readiness-panel";
import { QuestionProgress } from "@/features/question-builder/components/question-progress";
import { useBuilderExam, useExamReadiness, useFinalizeExam, useQuestions, useReopenExam } from "@/features/question-builder/hooks";
import { InvitationPanel } from "@/features/scheduling/components/invitation-panel";
import { ScheduleForm } from "@/features/scheduling/components/schedule-form";
import { useScheduleExam, useSendInvitations } from "@/features/scheduling/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";
import type { SchedulePayload } from "@/types/schedule";

function routeParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

const examStatusLabels: Record<string, string> = {
  draft: "پیش‌نویس",
  finalized: "نهایی‌شده",
  scheduled: "زمان‌بندی‌شده",
  review_required: "نیازمند بازبینی",
  approved: "تأییدشده",
  published: "منتشرشده"
};

function ScheduleContent() {
  const params = useParams();
  const classId = routeParam(params.classId);
  const examId = routeParam(params.examId);
  const exam = useBuilderExam(classId, examId);
  const questions = useQuestions(classId, examId);
  const readiness = useExamReadiness(classId, examId);
  const finalizeExam = useFinalizeExam(classId, examId);
  const reopenExam = useReopenExam(classId, examId);
  const scheduleExam = useScheduleExam(classId, examId);
  const sendInvitations = useSendInvitations(classId, examId);
  const [scheduleMessage, setScheduleMessage] = useState<string | undefined>();

  function handleSchedule(payload: SchedulePayload) {
    setScheduleMessage(undefined);
    scheduleExam.mutate(payload, {
      onSuccess: (result) => {
        setScheduleMessage(`${result.created_exam_tokens} توکن آزمون ساخته شد و آزمون زمان‌بندی شد.`);
      }
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="زمان‌بندی آزمون"
        description={exam.data ? exam.data.title : "ثبت بازه زمانی و ارسال دعوت‌نامه"}
        action={<Badge>{exam.data ? examStatusLabels[exam.data.status] ?? exam.data.status : "—"}</Badge>}
      />
      <div className="flex flex-wrap gap-2">
        <Link href={routes.examBuilder(classId, examId)}>
          <Button variant="secondary">
            <ArrowRight size={16} />
            سازنده آزمون
          </Button>
        </Link>
        <Link href={routes.classExams(classId)}>
          <Button variant="secondary">آزمون‌های کلاس</Button>
        </Link>
      </div>

      {exam.isLoading ? <LoadingBlock label="در حال دریافت آزمون" /> : null}
      {exam.isError ? <Alert variant="error">{getErrorMessage(exam.error)}</Alert> : null}
      {questions.isError ? <Alert variant="error">{getErrorMessage(questions.error)}</Alert> : null}

      <QuestionProgress exam={exam.data} questions={questions.data ?? []} readiness={readiness.data} />

      <ExamReadinessPanel
        classId={classId}
        exam={exam.data}
        readiness={readiness.data}
        loading={readiness.isLoading}
        error={readiness.error}
        finalizePending={finalizeExam.isPending}
        finalizeError={finalizeExam.error}
        reopenPending={reopenExam.isPending}
        reopenError={reopenExam.error}
        onFinalize={() => finalizeExam.mutate()}
        onReopen={() => reopenExam.mutate()}
      />

      <Card>
        <h2 className="mb-4 text-base font-semibold text-ink-900">فرم زمان‌بندی</h2>
        <ScheduleForm
          exam={exam.data}
          pending={scheduleExam.isPending}
          error={scheduleExam.error}
          resultMessage={scheduleMessage}
          onSubmit={handleSchedule}
        />
      </Card>

      <InvitationPanel
        exam={exam.data}
        pending={sendInvitations.isPending}
        queuedEmails={sendInvitations.data?.queued_emails}
        error={sendInvitations.error}
        onSend={() => sendInvitations.mutate({ send_to_all: true })}
      />
    </div>
  );
}

export default function ExamSchedulePage() {
  return <AuthGuard>{() => <ScheduleContent />}</AuthGuard>;
}
