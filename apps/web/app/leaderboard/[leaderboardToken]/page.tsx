"use client";

import { useParams } from "next/navigation";

import { LeaderboardPage } from "@/features/leaderboard/components/leaderboard-page";

function routeParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

export default function PublicLeaderboardPage() {
  const params = useParams();
  const leaderboardToken = routeParam(params.leaderboardToken);

  return <LeaderboardPage leaderboardToken={leaderboardToken} />;
}
