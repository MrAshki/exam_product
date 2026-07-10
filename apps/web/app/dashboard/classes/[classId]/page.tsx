"use client";

import { ArrowRight, FileText, GraduationCap, MessageSquare } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { PageHeader } from "@/components/common/page-header";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LoadingBlock } from "@/components/ui/loading-block";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { useClass } from "@/features/classes/hooks";
import { useExams } from "@/features/exams/hooks";
import { useStudents } from "@/features/students/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";

function currentClassId(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

function ClassDetailContent() {
  const params = useParams();
  const classId = currentClassId(params.classId);
  const classroom = useClass(classId);
  const students = useStudents(classId, 1, 1, "");
  const exams = useExams(classId);

  if (classroom.isLoading) {
    return <LoadingBlock label="در حال دریافت کلاس" />;
  }

  if (classroom.isError) {
    return <Alert variant="error">{getErrorMessage(classroom.error)}</Alert>;
  }

  if (!classroom.data) {
    return <Alert variant="error">کلاس پیدا نشد.</Alert>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={classroom.data.title}
        description={classroom.data.description || "جزئیات کلاس و مسیرهای مدیریت دانش‌آموزان و آزمون‌ها."}
        action={<Badge>{classroom.data.subject}</Badge>}
      />
      <div className="flex flex-wrap gap-2">
        <Link href={routes.dashboard}>
          <Button variant="secondary">
            <ArrowRight size={16} />
            بازگشت به داشبورد
          </Button>
        </Link>
        <Link href={routes.classStudents(classId)}>
          <Button>
            <GraduationCap size={16} />
            مدیریت دانش‌آموزان
          </Button>
        </Link>
        <Link href={routes.classExams(classId)}>
          <Button variant="secondary">
            <FileText size={16} />
            مدیریت آزمون‌ها
          </Button>
        </Link>
        <Link href={routes.appeals(classId)}>
          <Button variant="secondary">
            <MessageSquare size={16} />
            اعتراض‌ها
          </Button>
        </Link>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <p className="text-sm text-ink-500">وضعیت</p>
          <p className="mt-2 text-2xl font-semibold text-ink-900">فعال</p>
        </Card>
        <Card>
          <p className="text-sm text-ink-500">دانش‌آموزان</p>
          <p className="mt-2 text-2xl font-semibold text-ink-900">{students.data?.total ?? "—"}</p>
        </Card>
        <Card>
          <p className="text-sm text-ink-500">آزمون‌ها</p>
          <p className="mt-2 text-2xl font-semibold text-ink-900">{exams.data?.length ?? "—"}</p>
        </Card>
        <Card>
          <p className="text-sm text-ink-500">پایه</p>
          <p className="mt-2 text-2xl font-semibold text-ink-900">{classroom.data.grade_level || "—"}</p>
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="text-base font-semibold text-ink-900">اطلاعات کلاس</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-ink-500">موضوع</dt>
              <dd className="font-medium text-ink-900">{classroom.data.subject}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-ink-500">سال تحصیلی</dt>
              <dd className="font-medium text-ink-900">{classroom.data.academic_year || "—"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-ink-500">ایجاد شده</dt>
              <dd dir="ltr" className="font-medium text-ink-900">{new Date(classroom.data.created_at).toLocaleDateString("fa-IR")}</dd>
            </div>
          </dl>
        </Card>
        <Card>
          <h2 className="text-base font-semibold text-ink-900">مرحله‌های آینده</h2>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {["سازنده آزمون", "زمان‌بندی", "بازبینی نمره", "نتایج و اعتراض‌ها"].map((item) => (
              <span key={item} className="rounded-md bg-slate-100 px-3 py-2 text-sm text-ink-500">
                {item}
              </span>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function ClassDetailPage() {
  return <AuthGuard>{() => <ClassDetailContent />}</AuthGuard>;
}
