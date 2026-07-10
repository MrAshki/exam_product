"use client";

import { ArrowRight, Plus } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading-block";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { useClass } from "@/features/classes/hooks";
import { ExamForm } from "@/features/exams/components/exam-form";
import { ExamTable } from "@/features/exams/components/exam-table";
import { useCreateExam, useDeleteExam, useExams, useUpdateExam } from "@/features/exams/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";
import type { Exam, ExamPayload } from "@/types/exam";

function currentClassId(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

function ExamsContent() {
  const params = useParams();
  const classId = currentClassId(params.classId);
  const [createOpen, setCreateOpen] = useState(false);
  const [editingExam, setEditingExam] = useState<Exam | null>(null);
  const [deletingExam, setDeletingExam] = useState<Exam | null>(null);
  const classroom = useClass(classId);
  const exams = useExams(classId);
  const createExam = useCreateExam(classId);
  const updateExam = useUpdateExam(classId, editingExam?.id ?? "");
  const deleteExam = useDeleteExam(classId);

  const closeCreate = () => {
    setCreateOpen(false);
    createExam.reset();
  };

  const closeEdit = () => {
    setEditingExam(null);
    updateExam.reset();
  };

  function handleCreate(payload: ExamPayload) {
    createExam.mutate(payload, {
      onSuccess: closeCreate
    });
  }

  function handleUpdate(payload: ExamPayload) {
    updateExam.mutate(payload, {
      onSuccess: closeEdit
    });
  }

  function handleDelete() {
    if (!deletingExam) {
      return;
    }

    deleteExam.mutate(deletingExam.id, {
      onSuccess: () => setDeletingExam(null)
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="آزمون‌های کلاس"
        description={classroom.data ? classroom.data.title : "ساخت و مدیریت اطلاعات پایه آزمون‌ها"}
        action={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={16} />
            آزمون جدید
          </Button>
        }
      />
      <div className="flex flex-wrap gap-2">
        <Link href={routes.classDetail(classId)}>
          <Button variant="secondary">
            <ArrowRight size={16} />
            جزئیات کلاس
          </Button>
        </Link>
      </div>

      {classroom.isError ? <Alert variant="error">{getErrorMessage(classroom.error)}</Alert> : null}
      {exams.isLoading ? <LoadingBlock label="در حال دریافت آزمون‌ها" /> : null}
      {exams.isError ? <Alert variant="error">{getErrorMessage(exams.error)}</Alert> : null}
      {deleteExam.isError ? <Alert variant="error">{getErrorMessage(deleteExam.error)}</Alert> : null}

      {exams.isSuccess && exams.data.length === 0 ? (
        <EmptyState
          title="هنوز آزمونی ساخته نشده است"
          description="در این فاز فقط اطلاعات پایه آزمون ساخته می‌شود؛ سازنده سوال و زمان‌بندی غیرفعال هستند."
          action={
            <Button onClick={() => setCreateOpen(true)}>
              <Plus size={16} />
              ساخت آزمون
            </Button>
          }
        />
      ) : null}

      {exams.isSuccess && exams.data.length > 0 ? (
        <ExamTable exams={exams.data} onEdit={setEditingExam} onDelete={setDeletingExam} />
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        {["سازنده سوال", "زمان‌بندی و دعوت‌نامه", "بازبینی و انتشار"].map((item) => (
          <Card key={item} className="opacity-75">
            <h2 className="text-base font-semibold text-ink-900">{item}</h2>
            <p className="mt-2 text-sm leading-6 text-ink-500">این جریان در فازهای بعدی فرانت‌اند فعال می‌شود.</p>
          </Card>
        ))}
      </div>

      <Dialog open={createOpen} title="ساخت آزمون" onClose={closeCreate}>
        <ExamForm
          submitLabel="ساخت آزمون"
          pending={createExam.isPending}
          error={createExam.error}
          onSubmit={handleCreate}
        />
      </Dialog>

      <Dialog open={Boolean(editingExam)} title="ویرایش آزمون" onClose={closeEdit}>
        <ExamForm
          initialExam={editingExam}
          submitLabel="ذخیره آزمون"
          pending={updateExam.isPending}
          error={updateExam.error}
          onSubmit={handleUpdate}
        />
      </Dialog>

      <ConfirmDialog
        open={Boolean(deletingExam)}
        title="حذف آزمون"
        description="آزمون به صورت نرم حذف می‌شود و در فهرست عادی نمایش داده نخواهد شد."
        confirmLabel="حذف آزمون"
        loading={deleteExam.isPending}
        onConfirm={handleDelete}
        onClose={() => setDeletingExam(null)}
      />
    </div>
  );
}

export default function ClassExamsPage() {
  return <AuthGuard>{() => <ExamsContent />}</AuthGuard>;
}
