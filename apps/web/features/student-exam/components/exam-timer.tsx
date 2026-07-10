"use client";

import { Clock3 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { cn } from "@/lib/formatters";

type ExamTimerProps = {
  allowedUntil?: string | null;
};

function formatRemaining(milliseconds: number) {
  const totalSeconds = Math.max(0, Math.floor(milliseconds / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return [hours, minutes, seconds].map((part) => String(part).padStart(2, "0")).join(":");
}

export function ExamTimer({ allowedUntil }: ExamTimerProps) {
  const targetTime = useMemo(() => (allowedUntil ? new Date(allowedUntil).getTime() : null), [allowedUntil]);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!targetTime) {
      return;
    }

    const interval = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, [targetTime]);

  if (!targetTime) {
    return null;
  }

  const remaining = targetTime - now;
  const expired = remaining <= 0;

  return (
    <div className="space-y-3">
      <div
        className={cn(
          "inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium",
          expired ? "border-rose-100 bg-rose-50 text-rose-800" : "border-slate-200 bg-white text-ink-800"
        )}
      >
        <Clock3 size={16} />
        زمان باقی‌مانده: {formatRemaining(remaining)}
      </div>
      {expired ? (
        <Alert variant="error">زمان نمایش داده‌شده تمام شده است. نتیجه نهایی ارسال را سامانه تعیین می‌کند.</Alert>
      ) : null}
    </div>
  );
}
