"use client";

import { ArrowRight, MessageSquare } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LoadingBlock } from "@/components/ui/loading-block";
import { AppealsTable } from "@/features/appeals/components/appeals-table";
import { useClassAppeals } from "@/features/appeals/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";

type AppealsListPageProps = {
  classId: string;
};

const statusOptions = [
  { label: "همه", value: "" },
  { label: "در انتظار بررسی", value: "pending" },
  { label: "پذیرفته‌شده", value: "accepted" },
  { label: "ردشده", value: "rejected" },
  { label: "رسیدگی‌شده", value: "resolved" }
];

export function AppealsListPage({ classId }: AppealsListPageProps) {
  const [status, setStatus] = useState("");
  const appeals = useClassAppeals(classId, { status: status || null, page: 1, page_size: 20 });

  return (
    <div className="space-y-6">
      <PageHeader
        title="اعتراض‌ها"
        description="اعتراض‌های ثبت‌شده برای این کلاس"
        action={
          <Link href={routes.classDetail(classId)}>
            <Button variant="secondary">
              <ArrowRight size={16} />
              بازگشت به کلاس
            </Button>
          </Link>
        }
      />

      <Card className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare size={18} className="text-brand-700" />
          <span className="text-sm text-ink-600">فیلتر وضعیت</span>
        </div>
        <select
          className="h-10 rounded-md border border-slate-200 bg-white px-3 text-sm text-ink-900 outline-none focus:border-brand-600 focus:ring-4 focus:ring-brand-100"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          {statusOptions.map((option) => (
            <option key={option.value || "all"} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Card>

      {appeals.isLoading ? <LoadingBlock label="در حال دریافت اعتراض‌ها" /> : null}
      {appeals.isError ? <Alert variant="error">{getErrorMessage(appeals.error)}</Alert> : null}
      {appeals.data ? (
        <div className="space-y-3">
          <p className="text-sm text-ink-500">تعداد کل: {appeals.data.total}</p>
          <AppealsTable classId={classId} appeals={appeals.data.items} />
        </div>
      ) : null}
    </div>
  );
}
