"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { MultipleChoiceAnswer } from "@/features/student-exam/components/multiple-choice-answer";
import { TextAnswer } from "@/features/student-exam/components/text-answer";
import { TrueFalseAnswer } from "@/features/student-exam/components/true-false-answer";
import type { StudentExamQuestion } from "@/types/student-exam";

type QuestionCardProps = {
  question: StudentExamQuestion;
  value?: string;
  disabled?: boolean;
  onChange: (value: string) => void;
};

const typeLabels: Record<string, string> = {
  multiple_choice: "تستی",
  true_false: "درست/غلط",
  short_answer: "کوتاه‌پاسخ",
  essay: "تشریحی"
};

export function QuestionCard({ question, value, disabled, onChange }: QuestionCardProps) {
  function renderAnswer() {
    if (question.type === "multiple_choice") {
      return (
        <MultipleChoiceAnswer
          name={`question-${question.id}`}
          options={question.options}
          value={value}
          disabled={disabled}
          onChange={onChange}
        />
      );
    }

    if (question.type === "true_false") {
      return (
        <TrueFalseAnswer
          name={`question-${question.id}`}
          value={value}
          disabled={disabled}
          onChange={onChange}
        />
      );
    }

    return <TextAnswer value={value} disabled={disabled} large={question.type === "essay"} onChange={onChange} />;
  }

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge>سوال {question.order_index}</Badge>
            <Badge>{typeLabels[question.type] ?? question.type}</Badge>
            <span className="text-xs text-ink-500">{question.points} نمره</span>
          </div>
          <p className="whitespace-pre-wrap text-sm leading-7 text-ink-900">{question.text}</p>
        </div>
      </div>
      {renderAnswer()}
    </Card>
  );
}
