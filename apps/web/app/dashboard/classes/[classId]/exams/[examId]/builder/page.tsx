"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { LoadingBlock } from "@/components/ui/loading-block";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { BlueprintForm } from "@/features/question-builder/components/blueprint-form";
import { ExamReadinessPanel } from "@/features/question-builder/components/exam-readiness-panel";
import { QuestionEditor } from "@/features/question-builder/components/question-editor";
import { QuestionProgress } from "@/features/question-builder/components/question-progress";
import { QuestionSlotList } from "@/features/question-builder/components/question-slot-list";
import {
  useBlueprint,
  useBuilderExam,
  useCreateBlueprint,
  useExamReadiness,
  useFinalizeExam,
  useQuestions,
  useReopenExam,
  useUpdateBlueprint
} from "@/features/question-builder/hooks";
import { getErrorMessage } from "@/lib/errors";
import { ApiError } from "@/lib/api-client";
import { routes } from "@/lib/routes";
import type { BlueprintPayload } from "@/types/blueprint";
import type { Question, QuestionSlot } from "@/types/question";

type BlueprintImpact = {
  completed: number;
  confirmed: number;
  affected: number;
};

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

function BuilderContent() {
  const params = useParams();
  const classId = routeParam(params.classId);
  const examId = routeParam(params.examId);
  const exam = useBuilderExam(classId, examId);
  const blueprint = useBlueprint(classId, examId);
  const questions = useQuestions(classId, examId);
  const readiness = useExamReadiness(classId, examId);
  const createBlueprint = useCreateBlueprint(classId, examId);
  const updateBlueprint = useUpdateBlueprint(classId, examId);
  const finalizeExam = useFinalizeExam(classId, examId);
  const reopenExam = useReopenExam(classId, examId);
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);
  const pendingScrollQuestionId = useRef<string | null>(null);
  const [questionDetails, setQuestionDetails] = useState<Record<string, Question>>({});
  const [pendingBlueprint, setPendingBlueprint] = useState<BlueprintPayload | null>(null);
  const [blueprintImpact, setBlueprintImpact] = useState<BlueprintImpact | null>(null);

  const mergedQuestions = useMemo(() => {
    return (questions.data ?? []).map((slot) => ({ ...slot, ...questionDetails[slot.id] }));
  }, [questionDetails, questions.data]);

  const selectedQuestion = mergedQuestions.find((question) => question.id === selectedQuestionId) ?? mergedQuestions[0] ?? null;
  const blueprintMissing = blueprint.error instanceof ApiError && blueprint.error.status === 404;
  const editable = exam.data?.status === "draft";

  function blueprintCountsChanged(payload: BlueprintPayload) {
    return Boolean(
      blueprint.data &&
        (blueprint.data.multiple_choice_count !== payload.multiple_choice_count ||
          blueprint.data.short_answer_count !== payload.short_answer_count ||
          blueprint.data.essay_count !== payload.essay_count ||
          blueprint.data.true_false_count !== payload.true_false_count)
    );
  }

  function currentBlueprintImpact(): BlueprintImpact {
    const completed = mergedQuestions.filter(
      (question) =>
        Boolean(question.text) ||
        Number(question.points) > 0 ||
        Boolean(question.expected_answer) ||
        Boolean(question.correct_answer) ||
        Boolean(question.rubric) ||
        Boolean(question.options?.length)
    ).length;
    return {
      completed,
      confirmed: mergedQuestions.filter((question) => question.teacher_confirmed || question.status === "confirmed").length,
      affected: mergedQuestions.length
    };
  }

  function runBlueprintUpdate(payload: BlueprintPayload, confirmed: boolean) {
    updateBlueprint.mutate(
      { ...payload, confirm_destructive_update: confirmed },
      {
        onSuccess: () => {
          setSelectedQuestionId(null);
          setPendingBlueprint(null);
          setBlueprintImpact(null);
        },
        onError: (error) => {
          if (error instanceof ApiError && error.code === "BLUEPRINT_UPDATE_REQUIRES_CONFIRMATION") {
            const details = error.details ?? {};
            setPendingBlueprint(payload);
            setBlueprintImpact({
              completed: Number(details.completed_question_count ?? 0),
              confirmed: Number(details.confirmed_question_count ?? 0),
              affected: Number(details.affected_question_slot_count ?? mergedQuestions.length)
            });
          }
        }
      }
    );
  }

  function handleBlueprintSubmit(payload: BlueprintPayload) {
    if (!blueprint.data) {
      createBlueprint.mutate(payload, {
        onSuccess: () => setSelectedQuestionId(null)
      });
      return;
    }

    const impact = currentBlueprintImpact();
    if (blueprintCountsChanged(payload) && impact.completed > 0) {
      setPendingBlueprint(payload);
      setBlueprintImpact(impact);
      return;
    }

    runBlueprintUpdate(payload, false);
  }

  function rememberQuestion(question: Question) {
    setQuestionDetails((current) => ({
      ...current,
      [question.id]: question
    }));
  }

  function scrollToQuestionEditor(questionId: string) {
    const target = document.getElementById(`question-editor-${questionId}`);
    if (!target) {
      return;
    }
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    target.focus({ preventScroll: true });
  }

  function selectAndScrollToQuestion(questionId?: string | null, orderIndex?: number | null) {
    const targetId = questionId ?? mergedQuestions.find((question) => question.order_index === orderIndex)?.id;
    if (!targetId) {
      return;
    }
    if (selectedQuestion?.id === targetId) {
      scrollToQuestionEditor(targetId);
      return;
    }
    pendingScrollQuestionId.current = targetId;
    setSelectedQuestionId(targetId);
  }

  useEffect(() => {
    if (!pendingScrollQuestionId.current || selectedQuestion?.id !== pendingScrollQuestionId.current) {
      return;
    }
    scrollToQuestionEditor(pendingScrollQuestionId.current);
    pendingScrollQuestionId.current = null;
  }, [selectedQuestion?.id]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="سازنده آزمون"
        description={exam.data ? exam.data.title : "ساختار آزمون و سوال‌ها"}
        action={<Badge>{exam.data ? examStatusLabels[exam.data.status] ?? "وضعیت نامشخص" : "در حال دریافت"}</Badge>}
      />
      <div className="flex flex-wrap gap-2">
        <Link href={routes.classExams(classId)}>
          <Button variant="secondary">
            <ArrowRight size={16} />
            آزمون‌های کلاس
          </Button>
        </Link>
        <Link href={routes.examSchedule(classId, examId)}>
          <Button variant="secondary">زمان‌بندی</Button>
        </Link>
      </div>

      {exam.isLoading ? <LoadingBlock label="در حال دریافت آزمون" /> : null}
      {exam.isError ? <Alert variant="error">{getErrorMessage(exam.error)}</Alert> : null}

      <Card className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-ink-900">ساخت/به‌روزرسانی ساختار آزمون</h2>
          <p className="mt-1 text-sm leading-6 text-ink-500">
            با ساختار آزمون، backend جایگاه سوال‌ها را می‌سازد. تا وقتی آزمون draft است می‌توانید ساختار و سوال‌ها را اصلاح کنید.
          </p>
        </div>
        {blueprint.isLoading ? <LoadingBlock label="در حال دریافت ساختار آزمون" /> : null}
        {blueprint.isError && !blueprintMissing ? <Alert variant="error">{getErrorMessage(blueprint.error)}</Alert> : null}
        {blueprintMissing ? <Alert>هنوز ساختاری برای این آزمون ساخته نشده است.</Alert> : null}
        {!editable && exam.data ? <Alert>برای تغییر ساختار، قبل از زمان‌بندی آزمون را بازگشایی کنید.</Alert> : null}
        <BlueprintForm
          blueprint={blueprint.data}
          pending={createBlueprint.isPending || updateBlueprint.isPending}
          error={createBlueprint.error || updateBlueprint.error}
          disabled={!editable}
          onSubmit={handleBlueprintSubmit}
        />
      </Card>

      <QuestionProgress exam={exam.data} questions={mergedQuestions} readiness={readiness.data} />

      {questions.isLoading ? <LoadingBlock label="در حال دریافت سوال‌ها" /> : null}
      {questions.isError ? <Alert variant="error">{getErrorMessage(questions.error)}</Alert> : null}

      <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <div className="xl:sticky xl:top-24 xl:self-start">
          <QuestionSlotList
            questions={mergedQuestions}
            selectedQuestionId={selectedQuestion?.id}
            onSelect={(question: QuestionSlot) => setSelectedQuestionId(question.id)}
          />
        </div>
        <QuestionEditor
          classId={classId}
          examId={examId}
          question={selectedQuestion}
          editable={editable}
          onQuestionHydrated={rememberQuestion}
        />
      </div>

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
        onSelectQuestion={selectAndScrollToQuestion}
      />

      <ConfirmDialog
        open={Boolean(pendingBlueprint && blueprintImpact)}
        title="تأیید تغییر ساختار آزمون"
        description={`تغییر ساختار آزمون ممکن است سؤال‌های فعلی و گزینه‌های آن‌ها را حذف کند. این عملیات قابل بازگشت خودکار نیست. سؤال‌های دارای محتوا: ${blueprintImpact?.completed ?? 0}، سؤال‌های تأییدشده: ${blueprintImpact?.confirmed ?? 0}، جایگاه‌های تحت تأثیر: ${blueprintImpact?.affected ?? 0}.`}
        confirmLabel="ساختار را تغییر بده"
        cancelLabel="انصراف"
        loading={updateBlueprint.isPending}
        onConfirm={() => {
          if (pendingBlueprint) {
            runBlueprintUpdate(pendingBlueprint, true);
          }
        }}
        onClose={() => {
          setPendingBlueprint(null);
          setBlueprintImpact(null);
          updateBlueprint.reset();
        }}
      />
    </div>
  );
}

export default function ExamBuilderPage() {
  return <AuthGuard>{() => <BuilderContent />}</AuthGuard>;
}
