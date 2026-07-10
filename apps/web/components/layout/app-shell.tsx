"use client";

import { BookOpen, ClipboardCheck, FileText, GraduationCap, Home, LogOut, Menu, MessageSquare, PanelLeftClose, PanelLeftOpen, Trophy } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { appConfig } from "@/config/app-config";
import { useLogout } from "@/features/auth/hooks";
import { cn, displayName } from "@/lib/formatters";
import { routes } from "@/lib/routes";
import { useUiStore } from "@/stores/ui-store";
import type { User } from "@/types/auth";

type AppShellProps = {
  user: User;
  children: ReactNode;
};

const navItems = [
  { label: "داشبورد", href: routes.dashboard, icon: Home, disabled: false },
  { label: "کلاس‌ها", href: routes.dashboard, icon: BookOpen, disabled: false },
  { label: "دانش‌آموزان", icon: GraduationCap, disabled: true },
  { label: "آزمون‌ها", icon: FileText, disabled: true },
  { label: "بازبینی", icon: ClipboardCheck, disabled: true },
  { label: "نتایج", icon: Trophy, disabled: true },
  { label: "اعتراض‌ها", icon: MessageSquare, disabled: true }
];

export function AppShell({ user, children }: AppShellProps) {
  const pathname = usePathname();
  const sidebarCollapsed = useUiStore((state) => state.sidebarCollapsed);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);
  const logout = useLogout();

  return (
    <div className="min-h-screen bg-surface text-ink-900">
      <aside
        className={cn(
          "fixed inset-y-0 right-0 z-20 hidden border-l border-slate-200 bg-white p-4 transition-all md:block",
          sidebarCollapsed ? "w-20" : "w-64"
        )}
      >
        <div className="flex items-center justify-between gap-2">
          <Link href={routes.dashboard} className="min-w-0">
            <span className="block truncate text-sm font-semibold text-ink-900">
              {sidebarCollapsed ? "آزمون" : appConfig.name}
            </span>
          </Link>
          <Button
            variant="ghost"
            className="h-9 w-9 px-0"
            onClick={toggleSidebar}
            aria-label={sidebarCollapsed ? "باز کردن نوار کناری" : "بستن نوار کناری"}
          >
            {sidebarCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </Button>
        </div>
        <nav className="mt-8 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = item.href ? pathname === item.href : false;
            const className = cn(
              "flex h-10 w-full items-center gap-3 rounded-md px-3 text-right text-sm transition",
              active ? "bg-brand-50 text-brand-700" : "text-ink-600 hover:bg-slate-100",
              item.disabled ? "cursor-not-allowed opacity-60 hover:bg-transparent" : ""
            );

            if (item.disabled || !item.href) {
              return (
                <button key={item.label} type="button" disabled className={className}>
                  <Icon size={18} className="shrink-0" />
                  {!sidebarCollapsed ? <span className="truncate">{item.label}</span> : null}
                </button>
              );
            }

            return (
              <Link key={item.label} href={item.href} className={className}>
                <Icon size={18} className="shrink-0" />
                {!sidebarCollapsed ? <span className="truncate">{item.label}</span> : null}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className={cn("transition-all", sidebarCollapsed ? "md:mr-20" : "md:mr-64")}>
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Button variant="ghost" className="h-9 w-9 px-0 md:hidden" aria-label="منو">
                <Menu size={18} />
              </Button>
              <div>
                <p className="text-sm font-medium text-ink-900">{displayName(user.full_name, user.email)}</p>
                <p className="text-xs text-ink-500">{user.email}</p>
              </div>
            </div>
            <Button
              variant="secondary"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
              className="h-9"
            >
              <LogOut size={16} />
              خروج
            </Button>
          </div>
        </header>
        <main className="px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}
