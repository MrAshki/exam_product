import { ArrowLeft, BookOpen, FileText, GraduationCap } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { routes } from "@/lib/routes";
import type { Classroom } from "@/types/class";

type ClassCardProps = {
  classroom: Classroom;
  onEdit: (classroom: Classroom) => void;
  onDelete: (classroom: Classroom) => void;
};

export function ClassCard({ classroom, onEdit, onDelete }: ClassCardProps) {
  return (
    <Card className="flex min-h-64 flex-col">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-2">
          <h2 className="truncate text-lg font-semibold text-ink-900">{classroom.title}</h2>
          <div className="flex flex-wrap gap-2">
            <Badge>{classroom.subject}</Badge>
            {classroom.grade_level ? <Badge>{classroom.grade_level}</Badge> : null}
            {classroom.academic_year ? <Badge>{classroom.academic_year}</Badge> : null}
          </div>
        </div>
        <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-brand-50 text-brand-700">
          <BookOpen size={20} />
        </span>
      </div>
      <p className="mt-4 line-clamp-3 min-h-16 text-sm leading-6 text-ink-500">
        {classroom.description || "برای این کلاس هنوز توضیحی ثبت نشده است."}
      </p>
      <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
        <Link
          href={routes.classStudents(classroom.id)}
          className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-ink-700 transition hover:bg-slate-50"
        >
          <GraduationCap size={16} />
          دانش‌آموزان
        </Link>
        <Link
          href={routes.classExams(classroom.id)}
          className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-ink-700 transition hover:bg-slate-50"
        >
          <FileText size={16} />
          آزمون‌ها
        </Link>
      </div>
      <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-5">
        <Link href={routes.classDetail(classroom.id)} className="inline-flex items-center gap-2 text-sm font-medium text-brand-700">
          جزئیات
          <ArrowLeft size={16} />
        </Link>
        <div className="flex gap-2">
          <Button variant="secondary" className="h-9 px-3" onClick={() => onEdit(classroom)}>
            ویرایش
          </Button>
          <Button variant="ghost" className="h-9 px-3 text-rose-700" onClick={() => onDelete(classroom)}>
            حذف
          </Button>
        </div>
      </div>
    </Card>
  );
}
