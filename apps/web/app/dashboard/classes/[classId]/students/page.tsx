"use client";

import { ArrowRight, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/common/page-header";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { LoadingBlock } from "@/components/ui/loading-block";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { ClassNavigation } from "@/features/classes/components/class-navigation";
import { useClass } from "@/features/classes/hooks";
import { StudentForm } from "@/features/students/components/student-form";
import { StudentTable } from "@/features/students/components/student-table";
import { useCreateStudent, useRemoveStudent, useStudents, useUpdateStudent } from "@/features/students/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";
import type { Student, StudentPayload } from "@/types/student";

function currentClassId(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

function StudentsContent() {
  const params = useParams();
  const classId = currentClassId(params.classId);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [removingStudent, setRemovingStudent] = useState<Student | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const pageSize = 20;
  const classroom = useClass(classId);
  const students = useStudents(classId, page, pageSize, search);
  const createStudent = useCreateStudent(classId);
  const updateStudent = useUpdateStudent(classId, editingStudent?.id ?? "");
  const removeStudent = useRemoveStudent(classId);

  const closeCreate = () => {
    setCreateOpen(false);
    createStudent.reset();
  };

  const closeEdit = () => {
    setEditingStudent(null);
    updateStudent.reset();
  };

  function handleCreate(payload: StudentPayload) {
    if (createStudent.isPending) {
      return;
    }

    setSuccessMessage(null);
    createStudent.mutate(payload, {
      onSuccess: () => {
        setPage(1);
        closeCreate();
        setSuccessMessage("دانش‌آموز به این کلاس اضافه شد.");
      }
    });
  }

  function handleUpdate(payload: StudentPayload) {
    if (updateStudent.isPending) {
      return;
    }

    setSuccessMessage(null);
    updateStudent.mutate(payload, {
      onSuccess: () => {
        closeEdit();
        setSuccessMessage("اطلاعات دانش‌آموز ذخیره شد.");
      }
    });
  }

  function handleRemove() {
    if (!removingStudent) {
      return;
    }

    setSuccessMessage(null);
    removeStudent.mutate(removingStudent.id, {
      onSuccess: () => {
        setRemovingStudent(null);
        setSuccessMessage("دانش‌آموز از این کلاس حذف شد.");
      }
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="دانش‌آموزان کلاس"
        description={classroom.data ? classroom.data.title : "مدیریت عضویت دانش‌آموزان در کلاس"}
        action={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={16} />
            دانش‌آموز جدید
          </Button>
        }
      />
      <ClassNavigation classId={classId} active="students" />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link href={routes.classDetail(classId)}>
          <Button variant="secondary">
            <ArrowRight size={16} />
            جزئیات کلاس
          </Button>
        </Link>
        <label className="relative w-full max-w-sm">
          <Search className="absolute right-3 top-3 text-ink-500" size={16} />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            className="pr-9"
            placeholder="جستجوی نام یا ایمیل"
          />
        </label>
      </div>

      {classroom.isError ? <Alert variant="error">{getErrorMessage(classroom.error)}</Alert> : null}
      {successMessage ? <Alert variant="success">{successMessage}</Alert> : null}
      {students.isLoading ? <LoadingBlock label="در حال دریافت دانش‌آموزان" /> : null}
      {students.isError ? <Alert variant="error">{getErrorMessage(students.error)}</Alert> : null}
      {removeStudent.isError ? <Alert variant="error">{getErrorMessage(removeStudent.error)}</Alert> : null}

      {students.isSuccess && students.data.items.length === 0 ? (
        <EmptyState
          title="دانش‌آموزی در این کلاس نیست"
          description="دانش‌آموز جدید اضافه کنید یا عبارت جستجو را تغییر دهید."
          action={
            <Button onClick={() => setCreateOpen(true)}>
              <Plus size={16} />
              افزودن دانش‌آموز
            </Button>
          }
        />
      ) : null}

      {students.isSuccess && students.data.items.length > 0 ? (
        <div className="space-y-4">
          <StudentTable students={students.data.items} onEdit={setEditingStudent} onRemove={setRemovingStudent} />
          <div className="flex items-center justify-between gap-3 text-sm text-ink-500">
            <span>
              صفحه {students.data.page} از {Math.max(1, Math.ceil(students.data.total / students.data.page_size))}
            </span>
            <div className="flex gap-2">
              <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>
                قبلی
              </Button>
              <Button
                variant="secondary"
                disabled={page >= Math.ceil(students.data.total / students.data.page_size)}
                onClick={() => setPage((value) => value + 1)}
              >
                بعدی
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      <Dialog open={createOpen} title="افزودن دانش‌آموز" onClose={closeCreate}>
        <StudentForm
          submitLabel="افزودن"
          pending={createStudent.isPending}
          error={createStudent.error}
          onSubmit={handleCreate}
        />
      </Dialog>

      <Dialog open={Boolean(editingStudent)} title="ویرایش دانش‌آموز" onClose={closeEdit}>
        <StudentForm
          initialStudent={editingStudent}
          submitLabel="ذخیره"
          pending={updateStudent.isPending}
          error={updateStudent.error}
          onSubmit={handleUpdate}
        />
      </Dialog>

      <ConfirmDialog
        open={Boolean(removingStudent)}
        title="حذف از کلاس"
        description="عضویت دانش‌آموز از این کلاس به صورت نرم حذف می‌شود؛ خود رکورد دانش‌آموز باقی می‌ماند."
        confirmLabel="حذف از کلاس"
        loading={removeStudent.isPending}
        onConfirm={handleRemove}
        onClose={() => setRemovingStudent(null)}
      />
    </div>
  );
}

export default function ClassStudentsPage() {
  return <AuthGuard>{() => <StudentsContent />}</AuthGuard>;
}
