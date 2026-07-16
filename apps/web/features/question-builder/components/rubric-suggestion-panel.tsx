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

type Criterion = {
  name: string;
  points: string;
  description?: string;
};

function readCriteria(value: unknown): Criterion[] | null {
  if (!value) {
    return null;
  }
  if (typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  const criteria = (value as Record<string, unknown>).criteria;
  if (!Array.isArray(criteria) || criteria.length === 0) {
    return null;
  }
  const normalized: Criterion[] = [];
  for (const criterion of criteria) {
    if (!criterion || typeof criterion !== "object" || Array.isArray(criterion)) {
      return null;
    }
    const record = criterion as Record<string, unknown>;
    if (typeof record.name !== "string" || !Number.isFinite(Number(record.points))) {
      return null;
    }
    normalized.push({
      name: record.name,
      points: String(record.points),
      ...(typeof record.description === "string" ? { description: record.description } : {})
    });
  }
  return normalized;
}

export function RubricSuggestionPanel({
  suggestion,
  pending,
  error,
  disabled,
  onSuggest,
  onAccept
}: RubricSuggestionPanelProps) {
  const criteria = readCriteria(suggestion);
  const invalidSuggestion = Boolean(suggestion) && !criteria;

  return (
    <Card className="space-y-4 bg-slate-50 shadow-none">
      <div>
        <h3 className="text-base font-semibold text-ink-900">پیشنهاد راهنمای تصحیح با هوش مصنوعی</h3>
        <p className="mt-1 text-sm leading-6 text-ink-500">
          هوش مصنوعی فقط از متن سؤال، پاسخ مورد انتظار و نمره‌ای که معلم وارد کرده پیشنهاد می‌دهد؛ این پیشنهاد تا تأیید معلم رسمی نیست.
        </p>
      </div>
      {error ? <Alert variant="error">{getErrorMessage(error)}</Alert> : null}
      {invalidSuggestion ? <Alert variant="error">پیشنهاد دریافت‌شده ساختار معتبری ندارد و قابل استفاده نیست.</Alert> : null}
      {!suggestion ? <div className="rounded-md border border-slate-200 bg-white p-3 text-sm text-ink-500">هنوز پیشنهادی دریافت نشده است.</div> : null}
      {criteria ? (
        <div className="space-y-2">
          {criteria.map((criterion, index) => (
            <div key={`${criterion.name}-${index}`} className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex items-center justify-between gap-3 text-sm">
                <p className="font-medium text-ink-900">{criterion.name}</p>
                <span className="shrink-0 text-ink-600">{criterion.points} نمره</span>
              </div>
              {criterion.description ? <p className="mt-2 text-sm leading-6 text-ink-600">{criterion.description}</p> : null}
            </div>
          ))}
        </div>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button onClick={onSuggest} disabled={pending || disabled}>
          <WandSparkles size={16} />
          {pending ? "در حال دریافت پیشنهاد" : "پیشنهاد راهنمای تصحیح"}
        </Button>
        <Button variant="secondary" onClick={onAccept} disabled={!criteria}>
          استفاده در راهنمای تصحیح
        </Button>
      </div>
    </Card>
  );
}
