import { HTMLAttributes } from "react";

import { cn } from "@/lib/formatters";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-lg border border-slate-200 bg-white p-5 shadow-soft", className)}
      {...props}
    />
  );
}
