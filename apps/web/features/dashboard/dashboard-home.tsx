import { BookOpen, ClipboardCheck, FileText, GraduationCap, MessageSquare, Trophy } from "lucide-react";

import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

const foundationCards = [
  {
    title: "کلاس‌ها",
    description: "مدیریت کلاس‌ها در فاز بعدی فعال می‌شود.",
    icon: BookOpen
  },
  {
    title: "دانش‌آموزان",
    description: "فهرست و عضویت دانش‌آموزان بعدا تکمیل می‌شود.",
    icon: GraduationCap
  },
  {
    title: "آزمون‌ها",
    description: "ساخت آزمون و بانک سوال هنوز در این فاز فعال نیست.",
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

export function DashboardHome() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="داشبورد"
        description="زیرساخت فرانت‌اند آماده است؛ جریان‌های عملیاتی در فازهای بعدی اضافه می‌شوند."
        action={<Badge>فاز ۱۵A</Badge>}
      />
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
                <Badge>به‌زودی</Badge>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
