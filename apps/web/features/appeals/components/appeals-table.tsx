"use client";

import { Eye } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AppealStatusBadge } from "@/features/appeals/components/appeal-status-badge";
import { routes } from "@/lib/routes";
import type { AppealListItem } from "@/types/appeal";

type AppealsTableProps = {
  classId: string;
  appeals: AppealListItem[];
};

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function AppealsTable({ classId, appeals }: AppealsTableProps) {
  if (appeals.length === 0) {
    return <EmptyState title="اعتراضی ثبت نشده است" description="وقتی دانش‌آموزان اعتراض ثبت کنند، اینجا نمایش داده می‌شود." />;
  }

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeader>دانش‌آموز</TableHeader>
          <TableHeader>آزمون</TableHeader>
          <TableHeader>وضعیت</TableHeader>
          <TableHeader>تاریخ</TableHeader>
          <TableHeader>عملیات</TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {appeals.map((appeal) => (
          <TableRow key={appeal.id}>
            <TableCell className="font-medium text-ink-900">{appeal.student_full_name}</TableCell>
            <TableCell>{appeal.exam_title}</TableCell>
            <TableCell>
              <AppealStatusBadge status={appeal.status} />
            </TableCell>
            <TableCell>{formatDateTime(appeal.created_at)}</TableCell>
            <TableCell>
              <Link href={routes.appealDetail(classId, appeal.id)}>
                <Button variant="secondary" className="h-9">
                  <Eye size={15} />
                  بررسی اعتراض
                </Button>
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
