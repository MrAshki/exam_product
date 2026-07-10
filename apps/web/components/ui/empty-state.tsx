import { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: ReactNode;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white px-4 py-10 text-center">
      <h3 className="text-base font-semibold text-ink-900">{title}</h3>
      {description ? <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-ink-500">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
