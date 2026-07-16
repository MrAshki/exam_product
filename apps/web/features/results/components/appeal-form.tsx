"use client";

import { Send } from "lucide-react";
import { FormEvent, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/errors";
import type { ResultAppeal } from "@/types/result";

type AppealFormProps = {
  canAppeal: boolean;
  loading?: boolean;
  error?: unknown;
  submitted?: ResultAppeal | null;
  onSubmit: (message: string) => Promise<ResultAppeal>;
};

export function AppealForm({ canAppeal, loading, error, submitted, onSubmit }: AppealFormProps) {
  const [message, setMessage] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      setLocalError("متن اعتراض را وارد کنید.");
      return;
    }
    setLocalError(null);
    await onSubmit(trimmed);
  }

  if (!canAppeal) {
    return (
      <Card>
        <p className="text-sm text-ink-600">برای این آزمون امکان ثبت اعتراض فعال نیست.</p>
      </Card>
    );
  }

  if (submitted) {
    return (
      <Alert variant="success">
        اعتراض شما ثبت شد و برای بررسی معلم ارسال شد.
      </Alert>
    );
  }

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ink-900">ثبت اعتراض</h2>
        <p className="mt-1 text-sm leading-6 text-ink-500">
          در حال حاضر API عمومی شناسه پاسخ را در نتیجه برنمی‌گرداند؛ بنابراین اعتراض به صورت کلی برای این نتیجه ثبت می‌شود.
        </p>
      </div>
      {localError ? <Alert variant="error">{localError}</Alert> : null}
      {error ? <Alert variant="error">{getErrorMessage(error)}</Alert> : null}
      <form className="space-y-3" onSubmit={handleSubmit}>
        <Textarea
          value={message}
          disabled={loading}
          placeholder="دلیل اعتراض خود را بنویسید."
          onChange={(event) => setMessage(event.target.value)}
        />
        <div className="flex justify-end">
          <Button type="submit" disabled={loading}>
            <Send size={16} />
            {loading ? "در حال ثبت" : "ثبت اعتراض"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
