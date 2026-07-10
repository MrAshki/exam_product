import { HTMLAttributes } from "react";

import { cn } from "@/lib/formatters";

type AlertVariant = "info" | "error" | "success";

const variants: Record<AlertVariant, string> = {
  info: "border-accent-100 bg-blue-50 text-blue-900",
  error: "border-rose-100 bg-rose-50 text-rose-900",
  success: "border-brand-100 bg-brand-50 text-brand-700"
};

type AlertProps = HTMLAttributes<HTMLDivElement> & {
  variant?: AlertVariant;
};

export function Alert({ className, variant = "info", ...props }: AlertProps) {
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={cn("rounded-md border px-4 py-3 text-sm", variants[variant], className)}
      {...props}
    />
  );
}
