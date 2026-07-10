"use client";

import { WandSparkles } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getErrorMessage } from "@/lib/errors";

type RubricSuggestionPanelProps = {
  suggestion?: unknown;
  pending?: boolean;
  error?: unknown;
  disabled?: boolean;
  onSuggest: () => void;
  onAccept: () => void;
};

function renderSuggestion(value: unknown) {
  if (!value) {
    return "هنوز پیشنهادی دریافت نشده است.";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

export function RubricSuggestionPanel({
  suggestion,
  pending,
  error,
  disabled,
  onSuggest,
  onAccept
}: RubricSuggestionPanelProps) {
  return (
    <Card className="space-y-4 bg-slate-50 shadow-none">
      <div>
        <h3 className="text-base font-semibold text-ink-900">پیشنهاد rubric با AI</h3>
        <p className="mt-1 text-sm leading-6 text-ink-500">
          AI فقط از متن سوال، پاسخ مورد انتظار و نمره‌ای که معلم وارد کرده پیشنهاد می‌دهد؛ این پیشنهاد تا تایید معلم رسمی نیست.
        </p>
      </div>
      {error ? <Alert variant="error">{getErrorMessage(error)}</Alert> : null}
      <div className="whitespace-pre-wrap rounded-md border border-slate-200 bg-white p-3 text-sm leading-6 text-ink-700">
        {renderSuggestion(suggestion)}
      </div>
      <div className="flex flex-wrap gap-2">
        <Button onClick={onSuggest} disabled={pending || disabled}>
          <WandSparkles size={16} />
          {pending ? "در حال دریافت پیشنهاد" : "پیشنهاد rubric با AI"}
        </Button>
        <Button variant="secondary" onClick={onAccept} disabled={!suggestion}>
          استفاده در rubric
        </Button>
      </div>
    </Card>
  );
}
