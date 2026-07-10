"use client";

import { CheckCircle2 } from "lucide-react";
import { FormEvent, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/errors";
import type { AppealResolvePayload, AppealResolveResult } from "@/types/appeal";

type AppealResolveFormProps = {
  disabled?: boolean;
  loading?: boolean;
  error?: unknown;
  result?: AppealResolveResult | null;
  onSubmit: (payload: AppealResolvePayload) => Promise<AppealResolveResult>;
};

export function AppealResolveForm({ disabled, loading, error, result, onSubmit }: AppealResolveFormProps) {
  const [status, setStatus] = useState<"accepted" | "rejected">("rejected");
  const [newScore, setNewScore] = useState("");
  const [teacherResponse, setTeacherResponse] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const response = teacherResponse.trim();
    if (!response) {
      setLocalError("پاسخ معلم را وارد کنید.");
      return;
    }
    setLocalError(null);
    await onSubmit({
      status,
      new_score: newScore.trim() ? newScore.trim() : null,
      teacher_response: response
    });
  }

  if (disabled) {
    return <Alert>این اعتراض قبلاً رسیدگی شده است.</Alert>;
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      {result ? (
        <Alert variant="success">
          اعتراض رسیدگی شد. تصمیم نهایی: {result.final_decision}، تغییر نمره: {result.score_changed ? "بله" : "خیر"}
        </Alert>
      ) : null}
      {localError ? <Alert variant="error">{localError}</Alert> : null}
      {error ? <Alert variant="error">{getErrorMessage(error)}</Alert> : null}

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">تصمیم</span>
        <select
          className="h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-ink-900 outline-none focus:border-brand-600 focus:ring-4 focus:ring-brand-100"
          value={status}
          disabled={loading}
          onChange={(event) => setStatus(event.target.value as "accepted" | "rejected")}
        >
          <option value="rejected">رد اعتراض</option>
          <option value="accepted">پذیرش اعتراض</option>
        </select>
      </label>

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">نمره جدید، اختیاری</span>
        <Input
          type="number"
          min={0}
          step="0.25"
          value={newScore}
          disabled={loading}
          onChange={(event) => setNewScore(event.target.value)}
        />
      </label>

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-ink-700">پاسخ معلم</span>
        <Textarea
          value={teacherResponse}
          disabled={loading}
          placeholder="توضیح تصمیم را بنویسید."
          onChange={(event) => setTeacherResponse(event.target.value)}
        />
      </label>

      <div className="flex justify-end">
        <Button type="submit" disabled={loading}>
          <CheckCircle2 size={16} />
          {loading ? "در حال ثبت" : "ثبت رسیدگی"}
        </Button>
      </div>
    </form>
  );
}
