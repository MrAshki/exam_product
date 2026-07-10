"use client";

import { Trophy } from "lucide-react";

import { Card } from "@/components/ui/card";
import { ApiError } from "@/lib/api-client";
import { getErrorMessage } from "@/lib/errors";

type LeaderboardErrorStateProps = {
  error: unknown;
};

function leaderboardErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    if (error.code === "INVALID_LEADERBOARD_TOKEN") {
      return "این لینک لیدربورد معتبر نیست یا منقضی شده است.";
    }
    if (error.code === "LEADERBOARD_NOT_AVAILABLE") {
      return "لیدربورد این آزمون منتشر نشده یا فعال نیست.";
    }
  }

  return getErrorMessage(error);
}

export function LeaderboardErrorState({ error }: LeaderboardErrorStateProps) {
  return (
    <Card className="mx-auto max-w-2xl text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 text-amber-700">
        <Trophy size={22} />
      </div>
      <h1 className="mt-4 text-2xl font-bold text-ink-900">لیدربورد در دسترس نیست</h1>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-ink-600">{leaderboardErrorMessage(error)}</p>
    </Card>
  );
}
