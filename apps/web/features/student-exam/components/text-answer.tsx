"use client";

import { Textarea } from "@/components/ui/textarea";

type TextAnswerProps = {
  value?: string;
  disabled?: boolean;
  large?: boolean;
  onChange: (value: string) => void;
};

export function TextAnswer({ value = "", disabled, large, onChange }: TextAnswerProps) {
  return (
    <Textarea
      className={large ? "min-h-56" : "min-h-32"}
      value={value}
      disabled={disabled}
      placeholder="پاسخ خود را بنویسید."
      onChange={(event) => onChange(event.target.value)}
    />
  );
}
