import { Spinner } from "@/components/ui/spinner";

type LoadingBlockProps = {
  label?: string;
};

export function LoadingBlock({ label = "در حال بارگذاری" }: LoadingBlockProps) {
  return (
    <div className="flex min-h-48 items-center justify-center rounded-lg border border-slate-200 bg-white">
      <Spinner label={label} />
    </div>
  );
}
