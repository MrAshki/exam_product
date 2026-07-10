export type LeaderboardItem = {
  rank: number;
  student_full_name: string;
  score: string | null;
  max_score: string | null;
  percentage: number | null;
};

export type Leaderboard = {
  class_title: string;
  exam_title: string;
  items: LeaderboardItem[];
};
