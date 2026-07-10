"use client";

import { useState } from "react";

import { LoadingBlock } from "@/components/ui/loading-block";
import { AppealForm } from "@/features/results/components/appeal-form";
import { ResultAnswerList } from "@/features/results/components/result-answer-list";
import { ResultErrorState } from "@/features/results/components/result-error-state";
import { ResultSummaryCard } from "@/features/results/components/result-summary-card";
import { useStudentResult, useSubmitResultAppeal } from "@/features/results/hooks";
import type { ResultAppeal } from "@/types/result";

type StudentResultPageProps = {
  resultToken: string;
};

export function StudentResultPage({ resultToken }: StudentResultPageProps) {
  const result = useStudentResult(resultToken);
  const submitAppeal = useSubmitResultAppeal(resultToken);
  const [submittedAppeal, setSubmittedAppeal] = useState<ResultAppeal | null>(null);

  async function handleAppealSubmit(message: string) {
    const appeal = await submitAppeal.mutateAsync({ answer_id: null, message });
    setSubmittedAppeal(appeal);
    return appeal;
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl space-y-5">
        {result.isLoading ? <LoadingBlock label="در حال دریافت نتیجه" /> : null}
        {result.isError ? <ResultErrorState error={result.error} /> : null}
        {result.data ? (
          <>
            <ResultSummaryCard result={result.data} />
            <AppealForm
              canAppeal={result.data.can_appeal}
              loading={submitAppeal.isPending}
              error={submitAppeal.error}
              submitted={submittedAppeal}
              onSubmit={handleAppealSubmit}
            />
            <ResultAnswerList answers={result.data.answers} />
          </>
        ) : null}
      </div>
    </main>
  );
}
