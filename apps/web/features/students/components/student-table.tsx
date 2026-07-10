"use client";

import { Edit, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Student } from "@/types/student";

type StudentTableProps = {
  students: Student[];
  onEdit: (student: Student) => void;
  onRemove: (student: Student) => void;
};

export function StudentTable({ students, onEdit, onRemove }: StudentTableProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeader>نام</TableHeader>
          <TableHeader>ایمیل</TableHeader>
          <TableHeader>کد</TableHeader>
          <TableHeader>وضعیت</TableHeader>
          <TableHeader className="w-40">عملیات</TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {students.map((student) => (
          <TableRow key={student.id}>
            <TableCell className="font-medium text-ink-900">{student.full_name}</TableCell>
            <TableCell dir="ltr" className="text-left">{student.email}</TableCell>
            <TableCell>{student.student_code || "—"}</TableCell>
            <TableCell>
              <Badge>{student.is_active ? "فعال" : "غیرفعال"}</Badge>
            </TableCell>
            <TableCell>
              <div className="flex gap-2">
                <Button variant="secondary" className="h-9 w-9 px-0" onClick={() => onEdit(student)} aria-label="ویرایش">
                  <Edit size={16} />
                </Button>
                <Button variant="ghost" className="h-9 w-9 px-0 text-rose-700" onClick={() => onRemove(student)} aria-label="حذف از کلاس">
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
