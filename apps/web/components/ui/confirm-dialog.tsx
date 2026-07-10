"use client";

import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
  onConfirm: () => void;
  onClose: () => void;
};

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "تایید",
  cancelLabel = "انصراف",
  loading,
  onConfirm,
  onClose
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} title={title} onClose={onClose} className="max-w-md">
      <div className="space-y-5">
        <div className="flex gap-3 rounded-md border border-amber-100 bg-amber-50 p-3 text-amber-950">
          <AlertTriangle className="mt-0.5 shrink-0" size={18} />
          <p className="text-sm leading-6">{description}</p>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={loading}>
            {loading ? "در حال انجام" : confirmLabel}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
