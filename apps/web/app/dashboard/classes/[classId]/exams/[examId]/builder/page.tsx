"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
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
  useQuestions,
  useUpdateBlueprint
} from "@/features/question-builder/hooks";
import { getErrorMessage } from "@/lib/errors";
import { ApiError } from "@/lib/api-client";
import { routes } from "@/lib/routes";
import type { BlueprintPayload } from "@/types/blueprint";
import type { Question, QuestionSlot } from "@/types/question";

function routeParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

function BuilderContent() {
  const params = useParams();
  const classId = routeParam(params.classId);
  const examId = routeParam(params.examId);
  const exam = useBuilderExam(classId, examId);
  const blueprint = useBlueprint(classId, examId);
  const questions = useQuestions(classId, examId);
  const createBlueprint = useCreateBlueprint(classId, examId);
  const updateBlueprint = useUpdateBlueprint(classId, examId);
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);
  const [questionDetails, setQuestionDetails] = useState<Record<string, Question>>({});

  const mergedQuestions = useMemo(() => {
    return (questions.data ?? []).map((slot) => ({ ...slot, ...questionDetails[slot.id] }));
  }, [questionDetails, questions.data]);

  const selectedQuestion = mergedQuestions.find((question) => question.id === selectedQuestionId) ?? mergedQuestions[0] ?? null;
  const blueprintMissing = blueprint.error instanceof ApiError && blueprint.error.status === 404;

  function handleBlueprintSubmit(payload: BlueprintPayload) {
    const mutation = blueprint.data ? updateBlueprint : createBlueprint;
    mutation.mutate(payload, {
      onSuccess: () => setSelectedQuestionId(null)
    });
  }

  function rememberQuestion(question: Question) {
    setQuestionDetails((current) => ({
      ...current,
      [question.id]: question
    }));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="سازنده آزمون"
        description={exam.data ? exam.data.title : "ساختار آزمون و سوال‌ها"}
        action={<Badge>{exam.data?.status ?? "—"}</Badge>}
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
            با ساختار آزمون، backend جایگاه سوال‌ها را می‌سازد. اگر سوالی تایید شده باشد، backend اجازه تغییر ساختار را نمی‌دهد.
          </p>
        </div>
        {blueprint.isLoading ? <LoadingBlock label="در حال دریافت ساختار آزمون" /> : null}
        {blueprint.isError && !blueprintMissing ? <Alert variant="error">{getErrorMessage(blueprint.error)}</Alert> : null}
        {blueprintMissing ? <Alert>هنوز ساختاری برای این آزمون ساخته نشده است.</Alert> : null}
        <BlueprintForm
          blueprint={blueprint.data}
          pending={createBlueprint.isPending || updateBlueprint.isPending}
          error={createBlueprint.error || updateBlueprint.error}
          onSubmit={handleBlueprintSubmit}
        />
      </Card>

      <QuestionProgress exam={exam.data} questions={mergedQuestions} />

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
          onQuestionHydrated={rememberQuestion}
        />
      </div>

      <ExamReadinessPanel classId={classId} exam={exam.data} questions={mergedQuestions} />
    </div>
  );
}

export default function ExamBuilderPage() {
  return <AuthGuard>{() => <BuilderContent />}</AuthGuard>;
}
