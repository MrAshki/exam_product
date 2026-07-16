"use client";

import { Save } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useReviewAnswer } from "@/features/grading-review/hooks";
import { getErrorMessage } from "@/lib/errors";
import type { ReviewAnswer } from "@/types/review";

type AnswerReviewFormProps = {
  classId: string;
  examId: string;
  answer: ReviewAnswer;
};

function numberOrNull(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function scoreDefault(answer: ReviewAnswer) {
  return String(answer.teacher_score ?? answer.final_score ?? answer.auto_score ?? "");
}

export function AnswerReviewForm({ classId, examId, answer }: AnswerReviewFormProps) {
  const mutation = useReviewAnswer(classId, examId, answer.answer_id);
  const [teacherScore, setTeacherScore] = useState(scoreDefault(answer));
  const [feedback, setFeedback] = useState(answer.teacher_feedback ?? "");
  const [reason, setReason] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const maxScore = useMemo(() => numberOrNull(answer.max_score), [answer.max_score]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const score = numberOrNull(teacherScore);
    if (score === null) {
      setLocalError("نمره معلم باید عددی باشد.");
      return;
    }
    if (score < 0) {
      setLocalError("نمره معلم نمی‌تواند منفی باشد.");
      return;
    }
    if (maxScore !== null && score > maxScore) {
      setLocalError(`نمره معلم نمی‌تواند بیشتر از ${maxScore} باشد.`);
      return;
    }
    setLocalError(null);
    await mutation.mutateAsync({
      teacher_score: teacherScore,
      teacher_feedback: feedback.trim() || null,
      reason: reason.trim() || null
    });
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      {localError ? <Alert variant="error">{localError}</Alert> : null}
      {mutation.error ? <Alert variant="error">{getErrorMessage(mutation.error)}</Alert> : null}
      {mutation.isSuccess ? <Alert variant="success">بازبینی پاسخ ذخیره شد.</Alert> : null}

      <div className="grid gap-3 md:grid-cols-3">
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-ink-700">نمره معلم</span>
          <Input
            type="number"
            min={0}
            max={maxScore ?? undefined}
            step="0.25"
            value={teacherScore}
            disabled={mutation.isPending}
            onChange={(event) => setTeacherScore(event.target.value)}
          />
        </label>
        <label className="block space-y-1.5 md:col-span-2">
          <span className="text-sm font-medium text-ink-700">دلیل تغییر نمره</span>
          <Input
            value={reason}
            disabled={mutation.isPending}
            placeholder="اختیاری، برای ثبت در سابقه تغییر نمره"
            onChange={(event) => setReason(event.target.value)}
          />
        </label>
      </div>

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">بازخورد معلم</span>
        <Textarea
          value={feedback}
          disabled={mutation.isPending}
          placeholder="بازخوردی که برای این پاسخ نگه‌داری می‌شود."
          onChange={(event) => setFeedback(event.target.value)}
        />
      </label>

      <div className="flex justify-end">
        <Button type="submit" disabled={mutation.isPending}>
          <Save size={16} />
          {mutation.isPending ? "در حال ذخیره" : "ذخیره بازبینی"}
        </Button>
      </div>
    </form>
  );
}
