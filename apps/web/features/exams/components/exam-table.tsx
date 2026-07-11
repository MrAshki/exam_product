"use client";

import { ClipboardCheck, Edit, Hammer, Send, Trash2 } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDecimal } from "@/lib/decimal";
import { routes } from "@/lib/routes";
import type { Exam } from "@/types/exam";

type ExamTableProps = {
  classId: string;
  exams: Exam[];
  onEdit: (exam: Exam) => void;
  onDelete: (exam: Exam) => void;
};

const examStatusLabels: Record<string, string> = {
  draft: "پیش‌نویس",
  finalized: "نهایی‌شده",
  scheduled: "زمان‌بندی‌شده",
  review_required: "نیازمند بازبینی",
  approved: "تأییدشده",
  published: "منتشرشده"
};

export function ExamTable({ classId, exams, onEdit, onDelete }: ExamTableProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeader>عنوان</TableHeader>
          <TableHeader>وضعیت</TableHeader>
          <TableHeader>مدت</TableHeader>
          <TableHeader>نمره</TableHeader>
          <TableHeader>مرحله‌های بعدی</TableHeader>
          <TableHeader className="w-40">عملیات</TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {exams.map((exam) => (
          <TableRow key={exam.id}>
            <TableCell>
              <div className="space-y-1">
                <p className="font-medium text-ink-900">{exam.title}</p>
                {exam.description ? <p className="line-clamp-1 text-xs text-ink-500">{exam.description}</p> : null}
              </div>
            </TableCell>
            <TableCell>
              <Badge>{examStatusLabels[exam.status] ?? exam.status}</Badge>
            </TableCell>
            <TableCell>{exam.duration_minutes ? `${exam.duration_minutes} دقیقه` : "—"}</TableCell>
            <TableCell>{formatDecimal(exam.total_points)}</TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-2">
                <Link
                  href={routes.examBuilder(classId, exam.id)}
                  className="inline-flex items-center gap-1 rounded-md bg-brand-50 px-2 py-1 text-xs font-medium text-brand-700 transition hover:bg-brand-100"
                >
                  <Hammer size={13} />
                  سازنده
                </Link>
                <Link
                  href={routes.examSchedule(classId, exam.id)}
                  className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-ink-700 transition hover:bg-slate-200"
                >
                  <Send size={13} />
                  زمان‌بندی
                </Link>
                <Link
                  href={routes.examReview(classId, exam.id)}
                  className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-800 transition hover:bg-blue-100"
                >
                  <ClipboardCheck size={13} />
                  بازبینی
                </Link>
              </div>
            </TableCell>
            <TableCell>
              <div className="flex gap-2">
                <Button variant="secondary" className="h-9 w-9 px-0" onClick={() => onEdit(exam)} aria-label="ویرایش">
                  <Edit size={16} />
                </Button>
                <Button variant="ghost" className="h-9 w-9 px-0 text-rose-700" onClick={() => onDelete(exam)} aria-label="حذف آزمون">
                  <Trash2 size={16} />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
