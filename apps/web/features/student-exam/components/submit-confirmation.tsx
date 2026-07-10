"use client";

import { ConfirmDialog } from "@/components/ui/confirm-dialog";

type SubmitConfirmationProps = {
  open: boolean;
  unansweredCount: number;
  loading?: boolean;
  onConfirm: () => void;
  onClose: () => void;
};

export function SubmitConfirmation({
  open,
  unansweredCount,
  loading,
  onConfirm,
  onClose
}: SubmitConfirmationProps) {
  const description =
    unansweredCount > 0
      ? `${unansweredCount} سوال بدون پاسخ مانده است. بعد از ارسال، امکان تغییر پاسخ‌ها وجود ندارد.`
      : "بعد از ارسال، امکان تغییر پاسخ‌ها وجود ندارد.";

  return (
    <ConfirmDialog
      open={open}
      title="ارسال نهایی پاسخ‌ها"
      description={description}
      confirmLabel="ارسال پاسخ‌ها"
      cancelLabel="بازگشت"
      loading={loading}
      onConfirm={onConfirm}
      onClose={onClose}
    />
  );
}
