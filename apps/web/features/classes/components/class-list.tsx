"use client";

import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading-block";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { ClassCard } from "@/features/classes/components/class-card";
import { ClassForm } from "@/features/classes/components/class-form";
import { useClasses, useCreateClass, useDeleteClass, useUpdateClass } from "@/features/classes/hooks";
import { getErrorMessage } from "@/lib/errors";
import { routes } from "@/lib/routes";
import type { Classroom, ClassroomPayload } from "@/types/class";

export function ClassList() {
  const router = useRouter();
  const classes = useClasses();
  const createClass = useCreateClass();
  const deleteClass = useDeleteClass();
  const [editingClass, setEditingClass] = useState<Classroom | null>(null);
  const [deletingClass, setDeletingClass] = useState<Classroom | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const updateClass = useUpdateClass(editingClass?.id ?? "");

  const closeCreate = () => {
    setCreateOpen(false);
    createClass.reset();
  };

  const closeEdit = () => {
    setEditingClass(null);
    updateClass.reset();
  };

  function handleCreate(payload: ClassroomPayload) {
    createClass.mutate(payload, {
      onSuccess: (classroom) => {
        closeCreate();
        router.push(routes.classDetail(classroom.id));
      }
    });
  }

  function handleUpdate(payload: ClassroomPayload) {
    updateClass.mutate(payload, {
      onSuccess: closeEdit
    });
  }

  function handleDelete() {
    if (!deletingClass) {
      return;
    }

    deleteClass.mutate(deletingClass.id, {
      onSuccess: () => setDeletingClass(null)
    });
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink-900">کلاس‌ها</h2>
          <p className="text-sm text-ink-500">کلاس‌های فعال شما از backend خوانده می‌شوند.</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus size={16} />
          کلاس جدید
        </Button>
      </div>

      {classes.isLoading ? <LoadingBlock label="در حال دریافت کلاس‌ها" /> : null}
      {classes.isError ? <Alert variant="error">{getErrorMessage(classes.error)}</Alert> : null}
      {deleteClass.isError ? <Alert variant="error">{getErrorMessage(deleteClass.error)}</Alert> : null}

      {classes.isSuccess && classes.data.length === 0 ? (
        <EmptyState
          title="هنوز کلاسی ندارید"
          description="اولین کلاس را بسازید تا بتوانید دانش‌آموز و آزمون به آن اضافه کنید."
          action={
            <Button onClick={() => setCreateOpen(true)}>
              <Plus size={16} />
              ساخت کلاس
            </Button>
          }
        />
      ) : null}

      {classes.isSuccess && classes.data.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          {classes.data.map((classroom) => (
            <ClassCard
              key={classroom.id}
              classroom={classroom}
              onEdit={setEditingClass}
              onDelete={setDeletingClass}
            />
          ))}
        </div>
      ) : null}

      <Dialog open={createOpen} title="ساخت کلاس" description="اطلاعات پایه کلاس را وارد کنید." onClose={closeCreate}>
        <ClassForm
          submitLabel="ساخت کلاس"
          pending={createClass.isPending}
          error={createClass.error}
          onSubmit={handleCreate}
        />
      </Dialog>

      <Dialog
        open={Boolean(editingClass)}
        title="ویرایش کلاس"
        description="تغییرات فقط برای همین کلاس ذخیره می‌شود."
        onClose={closeEdit}
      >
        <ClassForm
          initialClass={editingClass}
          submitLabel="ذخیره کلاس"
          pending={updateClass.isPending}
          error={updateClass.error}
          onSubmit={handleUpdate}
        />
      </Dialog>

      <ConfirmDialog
        open={Boolean(deletingClass)}
        title="حذف کلاس"
        description="این کلاس به صورت نرم حذف می‌شود و دیگر در فهرست عادی نمایش داده نمی‌شود."
        confirmLabel="حذف کلاس"
        loading={deleteClass.isPending}
        onConfirm={handleDelete}
        onClose={() => setDeletingClass(null)}
      />
    </section>
  );
}
