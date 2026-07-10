"use client";

import { Trophy } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { LoadingBlock } from "@/components/ui/loading-block";
import { LeaderboardErrorState } from "@/features/leaderboard/components/leaderboard-error-state";
import { LeaderboardTable } from "@/features/leaderboard/components/leaderboard-table";
import { useLeaderboard } from "@/features/leaderboard/hooks";

type LeaderboardPageProps = {
  leaderboardToken: string;
};

export function LeaderboardPage({ leaderboardToken }: LeaderboardPageProps) {
  const leaderboard = useLeaderboard(leaderboardToken);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl space-y-5">
        {leaderboard.isLoading ? <LoadingBlock label="در حال دریافت لیدربورد" /> : null}
        {leaderboard.isError ? <LeaderboardErrorState error={leaderboard.error} /> : null}
        {leaderboard.data ? (
          <>
            <Card>
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <Badge>{leaderboard.data.class_title}</Badge>
                  <h1 className="mt-3 text-2xl font-bold text-ink-900">لیدربورد آزمون</h1>
                  <p className="mt-2 text-sm text-ink-600">{leaderboard.data.exam_title}</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 text-amber-700">
                  <Trophy size={24} />
                </div>
              </div>
            </Card>
            <LeaderboardTable items={leaderboard.data.items} />
          </>
        ) : null}
      </div>
    </main>
  );
}
