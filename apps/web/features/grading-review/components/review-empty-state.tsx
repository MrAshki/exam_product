"use client";

import { EmptyState } from "@/components/ui/empty-state";

export function ReviewEmptyState() {
  return (
    <EmptyState
      title="داده‌ای برای بازبینی وجود ندارد"
      description="وقتی دانش‌آموزان آزمون را ارسال کنند و تصحیح انجام شود، این بخش قابل بازبینی خواهد بود."
    />
  );
}
