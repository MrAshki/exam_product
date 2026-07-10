import { cn } from "@/lib/formatters";

type SpinnerProps = {
  className?: string;
  label?: string;
};

export function Spinner({ className, label = "در حال بارگذاری" }: SpinnerProps) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-ink-500">
      <span
        className={cn(
          "h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600",
          className
        )}
      />
      <span>{label}</span>
    </span>
  );
}
