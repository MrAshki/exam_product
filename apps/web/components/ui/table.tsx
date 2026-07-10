import { HTMLAttributes, TableHTMLAttributes } from "react";

import { cn } from "@/lib/formatters";

export function Table({ className, ...props }: TableHTMLAttributes<HTMLTableElement>) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className={cn("min-w-full divide-y divide-slate-200 text-sm", className)} {...props} />
    </div>
  );
}

export function TableHead({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <thead className={cn("bg-slate-50 text-right text-xs font-semibold text-ink-500", className)} {...props} />;
}

export function TableBody({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={cn("divide-y divide-slate-100", className)} {...props} />;
}

export function TableRow({ className, ...props }: HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={cn("transition hover:bg-slate-50", className)} {...props} />;
}

export function TableHeader({ className, ...props }: HTMLAttributes<HTMLTableCellElement>) {
  return <th className={cn("px-4 py-3 font-semibold", className)} {...props} />;
}

export function TableCell({ className, ...props }: HTMLAttributes<HTMLTableCellElement>) {
  return <td className={cn("px-4 py-3 align-middle text-ink-700", className)} {...props} />;
}
