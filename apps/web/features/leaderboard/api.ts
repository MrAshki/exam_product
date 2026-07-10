import { apiClient } from "@/lib/api-client";
import type { Leaderboard } from "@/types/leaderboard";

export function getLeaderboard(leaderboardToken: string) {
  return apiClient.get<Leaderboard>(`/leaderboard/${encodeURIComponent(leaderboardToken)}`);
}
