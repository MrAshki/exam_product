"use client";

import { CheckCircle } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getErrorMessage } from "@/lib/errors";
import type { Question } from "@/types/question";

type QuestionConfirmPanelProps = {
  question: Question;
  pending?: boolean;
  error?: unknown;
  onConfirm: () => void;
};

export function QuestionConfirmPanel({ question, pending, error, onConfirm }: QuestionConfirmPanelProps) {
  const confirmed = question.teacher_confirmed || question.status === "confirmed";

  return (
    <Card className="space-y-4 bg-slate-50 shadow-none">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-ink-900">تایید سوال</h3>
          <p className="mt-1 text-sm leading-6 text-ink-500">
            تایید فقط از backend انجام می‌شود. اگر فیلدی ناقص باشد، خطای backend همین‌جا نمایش داده می‌شود.
          </p>
        </div>
        {confirmed ? <CheckCircle className="text-brand-700" size={22} /> : null}
      </div>
      {error ? <Alert variant="error">{getErrorMessage(error)}</Alert> : null}
      <Button onClick={onConfirm} disabled={pending || confirmed}>
        <CheckCircle size={16} />
        {confirmed ? "تایید شده" : pending ? "در حال تایید" : "تایید سوال"}
      </Button>
    </Card>
  );
}
