import { HTMLAttributes } from "react";

import { cn } from "@/lib/formatters";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-ink-700",
        className
      )}
      {...props}
    />
  );
}
