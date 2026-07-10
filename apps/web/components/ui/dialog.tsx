"use client";

import { X } from "lucide-react";
import { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/formatters";

type DialogProps = {
  open: boolean;
  title: string;
  description?: string;
  children: ReactNode;
  onClose: () => void;
  className?: string;
};

export function Dialog({ open, title, description, children, onClose, className }: DialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4 py-6">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        className={cn(
          "max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-slate-200 bg-white p-5 shadow-xl",
          className
        )}
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 id="dialog-title" className="text-lg font-semibold text-ink-900">
              {title}
            </h2>
            {description ? <p className="text-sm leading-6 text-ink-500">{description}</p> : null}
          </div>
          <Button variant="ghost" className="h-9 w-9 shrink-0 px-0" onClick={onClose} aria-label="بستن">
            <X size={18} />
          </Button>
        </div>
        {children}
      </div>
    </div>
  );
}
