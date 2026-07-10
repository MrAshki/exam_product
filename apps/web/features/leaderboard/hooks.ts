import { useQuery } from "@tanstack/react-query";

import { getLeaderboard } from "@/features/leaderboard/api";

export const leaderboardQueryKeys = {
  detail: (leaderboardToken: string) => ["leaderboard", leaderboardToken] as const
};

export function useLeaderboard(leaderboardToken: string) {
  return useQuery({
    queryKey: leaderboardQueryKeys.detail(leaderboardToken),
    queryFn: () => getLeaderboard(leaderboardToken),
    enabled: Boolean(leaderboardToken),
    retry: false
  });
}
