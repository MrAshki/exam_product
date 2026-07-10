"use client";

import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { LeaderboardItem } from "@/types/leaderboard";

type LeaderboardTableProps = {
  items: LeaderboardItem[];
};

export function LeaderboardTable({ items }: LeaderboardTableProps) {
  if (items.length === 0) {
    return <EmptyState title="رتبه‌ای برای نمایش وجود ندارد" />;
  }

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeader>رتبه</TableHeader>
          <TableHeader>نام دانش‌آموز</TableHeader>
          <TableHeader>نمره</TableHeader>
          <TableHeader>درصد</TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {items.map((item) => (
          <TableRow key={`${item.rank}-${item.student_full_name}`}>
            <TableCell className="font-semibold text-ink-900">{item.rank}</TableCell>
            <TableCell>{item.student_full_name}</TableCell>
            <TableCell>
              {item.score ?? "—"} / {item.max_score ?? "—"}
            </TableCell>
            <TableCell>{item.percentage === null ? "—" : `${item.percentage.toFixed(1)}٪`}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
