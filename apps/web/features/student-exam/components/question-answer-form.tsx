"use client";

import { Send } from "lucide-react";
import { useMemo, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ExamTimer } from "@/features/student-exam/components/exam-timer";
import { QuestionCard } from "@/features/student-exam/components/question-card";
import { SubmitConfirmation } from "@/features/student-exam/components/submit-confirmation";
import { getErrorMessage } from "@/lib/errors";
import type {
  StudentExamAnswerSubmit,
  StudentExamQuestion,
  StudentExamSession,
  StudentExamSubmitPayload,
  StudentExamSubmitResult
} from "@/types/student-exam";

type QuestionAnswerFormProps = {
  session: StudentExamSession;
  loading?: boolean;
  error?: unknown;
  onSubmit: (payload: StudentExamSubmitPayload) => Promise<StudentExamSubmitResult>;
};

function normalizeAnswer(value?: string) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function buildAnswer(question: StudentExamQuestion, value?: string): StudentExamAnswerSubmit {
  const answer = normalizeAnswer(value);

  if (question.type === "multiple_choice") {
    return {
      question_id: question.id,
      student_answer: answer,
      answer_data: answer ? { selected_option: answer } : null
    };
  }

  if (question.type === "true_false") {
    return {
      question_id: question.id,
      student_answer: answer,
      answer_data: answer ? { value: answer === "true" } : null
    };
  }

  return {
    question_id: question.id,
    student_answer: answer,
    answer_data: answer ? { text: answer } : null
  };
}

export function QuestionAnswerForm({ session, loading, error, onSubmit }: QuestionAnswerFormProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [confirmOpen, setConfirmOpen] = useState(false);
  const sortedQuestions = useMemo(
    () => [...session.questions].sort((left, right) => left.order_index - right.order_index),
    [session.questions]
  );
  const unansweredCount = sortedQuestions.filter((question) => !normalizeAnswer(answers[question.id])).length;

  function buildPayload(): StudentExamSubmitPayload {
    return {
      answers: sortedQuestions.map((question) => buildAnswer(question, answers[question.id]))
    };
  }

  async function handleConfirmSubmit() {
    try {
      await onSubmit(buildPayload());
      setConfirmOpen(false);
    } catch {
      return;
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <Card className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-ink-900">پاسخ‌گویی به آزمون</h1>
            <p className="mt-2 text-sm text-ink-500">
              پاسخ‌ها تا زمان ارسال نهایی فقط در همین صفحه نگه‌داری می‌شوند.
            </p>
          </div>
          <ExamTimer allowedUntil={session.allowed_until} />
        </div>
        <Alert>زمان‌سنج فقط راهنماست. ثبت یا رد ارسال بر اساس زمان واقعی آزمون انجام می‌شود.</Alert>
      </Card>

      {error ? <Alert variant="error">{getErrorMessage(error)}</Alert> : null}

      <div className="space-y-4">
        {sortedQuestions.map((question) => (
          <QuestionCard
            key={question.id}
            question={question}
            value={answers[question.id] ?? ""}
            disabled={loading}
            onChange={(value) =>
              setAnswers((current) => ({
                ...current,
                [question.id]: value
              }))
            }
          />
        ))}
      </div>

      <div className="sticky bottom-0 -mx-4 border-t border-slate-200 bg-slate-50/95 px-4 py-4 backdrop-blur sm:mx-0 sm:rounded-md sm:border">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-ink-600">
            {unansweredCount > 0 ? `${unansweredCount} سوال هنوز پاسخ ندارد.` : "همه سوال‌ها پاسخ داده شده‌اند."}
          </p>
          <Button onClick={() => setConfirmOpen(true)} disabled={loading || sortedQuestions.length === 0}>
            <Send size={16} />
            {loading ? "در حال ارسال" : "ارسال نهایی"}
          </Button>
        </div>
      </div>

      <SubmitConfirmation
        open={confirmOpen}
        unansweredCount={unansweredCount}
        loading={loading}
        onConfirm={handleConfirmSubmit}
        onClose={() => setConfirmOpen(false)}
      />
    </div>
  );
}
