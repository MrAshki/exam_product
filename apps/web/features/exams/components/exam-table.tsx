"use client";

import { Edit, Hammer, Send, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Exam } from "@/types/exam";

type ExamTableProps = {
  exams: Exam[];
  onEdit: (exam: Exam) => void;
  onDelete: (exam: Exam) => void;
};

export function ExamTable({ exams, onEdit, onDelete }: ExamTableProps) {
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
              <Badge>{exam.status}</Badge>
            </TableCell>
            <TableCell>{exam.duration_minutes ? `${exam.duration_minutes} دقیقه` : "—"}</TableCell>
            <TableCell>{exam.total_points}</TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-xs text-ink-500">
                  <Hammer size={13} />
                  سازنده
                </span>
                <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-xs text-ink-500">
                  <Send size={13} />
                  زمان‌بندی
                </span>
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
