"use client";

type TrueFalseAnswerProps = {
  name: string;
  value?: string;
  disabled?: boolean;
  onChange: (value: "true" | "false") => void;
};

export function TrueFalseAnswer({ name, value, disabled, onChange }: TrueFalseAnswerProps) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {[
        { label: "درست", value: "true" as const },
        { label: "غلط", value: "false" as const }
      ].map((option) => (
        <label
          key={option.value}
          className="flex cursor-pointer items-center gap-3 rounded-md border border-slate-200 bg-white p-3 text-sm transition hover:border-brand-200 hover:bg-brand-50/40"
        >
          <input
            type="radio"
            name={name}
            value={option.value}
            checked={value === option.value}
            disabled={disabled}
            onChange={() => onChange(option.value)}
          />
          <span className="font-medium text-ink-800">{option.label}</span>
        </label>
      ))}
    </div>
  );
}
