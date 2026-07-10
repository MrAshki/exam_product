"use client";

import { EmptyState } from "@/components/ui/empty-state";
import { ResultAnswerCard } from "@/features/results/components/result-answer-card";
import type { ResultAnswer } from "@/types/result";

type ResultAnswerListProps = {
  answers: ResultAnswer[];
};

export function ResultAnswerList({ answers }: ResultAnswerListProps) {
  if (answers.length === 0) {
    return <EmptyState title="پاسخی برای نمایش وجود ندارد" />;
  }

  return (
    <div className="space-y-4">
      {answers.map((answer, index) => (
        <ResultAnswerCard key={`${answer.question_text ?? "question"}-${index}`} answer={answer} index={index} />
      ))}
    </div>
  );
}
