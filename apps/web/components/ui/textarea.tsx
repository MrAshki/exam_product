import { TextareaHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/formatters";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "min-h-28 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-ink-900 outline-none transition placeholder:text-slate-400 focus:border-brand-600 focus:ring-4 focus:ring-brand-100",
        className
      )}
      {...props}
    />
  )
);

Textarea.displayName = "Textarea";
