"use client";

import { Send } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getErrorMessage } from "@/lib/errors";
import type { Exam } from "@/types/exam";

type InvitationPanelProps = {
  exam?: Exam;
  pending?: boolean;
  queuedEmails?: number;
  error?: unknown;
  onSend: () => void;
};

export function InvitationPanel({ exam, pending, queuedEmails, error, onSend }: InvitationPanelProps) {
  const scheduled = exam?.status === "scheduled";

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-base font-semibold text-ink-900">ارسال دعوت‌نامه</h2>
        <p className="mt-1 text-sm leading-6 text-ink-500">
          دعوت‌نامه‌ها از backend در صف ایمیل قرار می‌گیرند؛ فرانت‌اند ایمیل مستقیم ارسال نمی‌کند.
        </p>
      </div>
      {!scheduled ? <Alert>پس از زمان‌بندی موفق، ارسال دعوت‌نامه فعال می‌شود.</Alert> : null}
      {error ? <Alert variant="error">{getErrorMessage(error)}</Alert> : null}
      {queuedEmails !== undefined ? <Alert variant="success">{queuedEmails} ایمیل در صف ارسال قرار گرفت.</Alert> : null}
      <Button onClick={onSend} disabled={!scheduled || pending}>
        <Send size={16} />
        {pending ? "در حال ارسال به صف" : "ارسال دعوت‌نامه‌ها"}
      </Button>
    </Card>
  );
}
