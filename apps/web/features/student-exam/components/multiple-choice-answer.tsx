"use client";

import type { StudentExamOption } from "@/types/student-exam";

type MultipleChoiceAnswerProps = {
  name: string;
  options: StudentExamOption[];
  value?: string;
  disabled?: boolean;
  onChange: (value: string) => void;
};

export function MultipleChoiceAnswer({ name, options, value, disabled, onChange }: MultipleChoiceAnswerProps) {
  if (options.length === 0) {
    return <p className="text-sm text-ink-500">گزینه‌ای برای این سوال ثبت نشده است.</p>;
  }

  return (
    <div className="space-y-2">
      {options.map((option) => (
        <label
          key={option.option_key}
          className="flex cursor-pointer items-start gap-3 rounded-md border border-slate-200 bg-white p-3 text-sm transition hover:border-brand-200 hover:bg-brand-50/40"
        >
          <input
            type="radio"
            name={name}
            className="mt-1"
            value={option.option_key}
            checked={value === option.option_key}
            disabled={disabled}
            onChange={() => onChange(option.option_key)}
          />
          <span className="font-medium text-ink-700">{option.option_key.toUpperCase()}</span>
          <span className="leading-6 text-ink-800">{option.option_text}</span>
        </label>
      ))}
    </div>
  );
}
