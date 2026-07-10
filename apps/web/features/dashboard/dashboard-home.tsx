import { ClipboardCheck, FileText, GraduationCap, MessageSquare, Sparkles, Trophy } from "lucide-react";

import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { ClassList } from "@/features/classes/components/class-list";
import { displayName } from "@/lib/formatters";
import type { User } from "@/types/auth";

const foundationCards = [
  {
    title: "دانش‌آموزان",
    description: "از داخل هر کلاس می‌توانید دانش‌آموز اضافه و مدیریت کنید.",
    icon: GraduationCap
  },
  {
    title: "آزمون‌ها",
    description: "آزمون‌های پایه از صفحه هر کلاس ساخته می‌شوند.",
    icon: FileText
  },
  {
    title: "بازبینی",
    description: "بازبینی نمره‌ها پس از اتصال جریان‌های آزمون اضافه می‌شود.",
    icon: ClipboardCheck
  },
  {
    title: "نتایج",
    description: "انتشار نتایج و لینک‌های عمومی در فازهای بعدی UI می‌گیرند.",
    icon: Trophy
  },
  {
    title: "اعتراض‌ها",
    description: "مدیریت اعتراض‌ها فعلا فقط در backend آماده است.",
    icon: MessageSquare
  }
];

type DashboardHomeProps = {
  user: User;
};

export function DashboardHome({ user }: DashboardHomeProps) {
  return (
    <div className="space-y-6">
      <PageHeader
        title="داشبورد"
        description={`خوش آمدید ${displayName(user.full_name, user.email)}. داده‌های اصلی معلم از API خوانده می‌شوند.`}
        action={<Badge>فاز ۱۵B</Badge>}
      />
      <Card className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-brand-700">
            <Sparkles size={16} />
            آماده برای شروع
          </div>
          <h2 className="text-xl font-semibold text-ink-900">کلاس را بسازید، سپس دانش‌آموز و آزمون اضافه کنید.</h2>
          <p className="text-sm leading-6 text-ink-500">
            این صفحه مرکز کارهای اصلی معلم است؛ بخش‌های پیشرفته مثل سازنده سوال، زمان‌بندی و انتشار نتایج فعلا فقط به صورت غیرفعال نمایش داده می‌شوند.
          </p>
        </div>
        <div className="rounded-md border border-slate-200 px-4 py-3 text-sm text-ink-600">
          <p className="font-medium text-ink-900">{user.full_name}</p>
          <p dir="ltr" className="mt-1 text-left">{user.email}</p>
        </div>
      </Card>
      <ClassList />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {foundationCards.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.title} className="min-h-40">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-2">
                  <h2 className="text-base font-semibold text-ink-900">{item.title}</h2>
                  <p className="text-sm leading-6 text-ink-500">{item.description}</p>
                </div>
                <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-brand-50 text-brand-700">
                  <Icon size={20} />
                </span>
              </div>
              <div className="mt-5">
                <Badge>مرحله بعدی</Badge>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
