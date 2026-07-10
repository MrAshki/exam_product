import type { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  description?: string;
  action?: ReactNode;
};

export function PageHeader({ title, description, action }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-3 border-b border-slate-200 pb-5 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900">{title}</h1>
        {description ? <p className="mt-2 text-sm text-ink-500">{description}</p> : null}
      </div>
      {action ? <div>{action}</div> : null}
    </div>
  );
}
