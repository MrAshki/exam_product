"use client";

import { ClipboardList, FileText, GraduationCap, type LucideIcon } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/formatters";
import { routes } from "@/lib/routes";

type ClassNavigationItem = "overview" | "students" | "exams";

type ClassNavigationProps = {
  classId: string;
  active: ClassNavigationItem;
};

const navItems: Array<{
  key: ClassNavigationItem;
  label: string;
  href: (classId: string) => string;
  icon: LucideIcon;
  badge?: string;
}> = [
  {
    key: "overview",
    label: "نمای کلی",
    href: routes.classDetail,
    icon: ClipboardList
  },
  {
    key: "students",
    label: "دانش‌آموزان",
    href: routes.classStudents,
    icon: GraduationCap
  },
  {
    key: "exams",
    label: "آزمون‌ها",
    href: routes.classExams,
    icon: FileText,
    badge: "بعدی"
  }
];

export function ClassNavigation({ classId, active }: ClassNavigationProps) {
  return (
    <nav className="flex flex-wrap gap-2" aria-label="ناوبری کلاس">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = item.key === active;

        return (
          <Link
            key={item.key}
            href={item.href(classId)}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "inline-flex h-10 items-center justify-center gap-2 rounded-md border px-4 text-sm font-medium transition",
              isActive
                ? "border-brand-200 bg-brand-50 text-brand-700"
                : "border-slate-200 bg-white text-ink-700 hover:bg-slate-50"
            )}
          >
            <Icon size={16} />
            {item.label}
            {item.badge ? <Badge>{item.badge}</Badge> : null}
          </Link>
        );
      })}
    </nav>
  );
}
