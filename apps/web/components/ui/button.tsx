import { ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/formatters";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const variants: Record<ButtonVariant, string> = {
  primary: "bg-brand-600 text-white hover:bg-brand-700",
  secondary: "border border-slate-200 bg-white text-ink-900 hover:bg-slate-50",
  ghost: "text-ink-700 hover:bg-slate-100",
  danger: "bg-rose-600 text-white hover:bg-rose-700"
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60",
        variants[variant],
        className
      )}
      {...props}
    />
  )
);

Button.displayName = "Button";
