import { InputHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/formatters";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-ink-900 outline-none transition placeholder:text-slate-400 focus:border-brand-600 focus:ring-4 focus:ring-brand-100",
        className
      )}
      {...props}
    />
  )
);

Input.displayName = "Input";
