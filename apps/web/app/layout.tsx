import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthProvider } from "@/features/auth/auth-provider";
import { QueryProvider } from "@/lib/query-client";

import "./globals.css";

export const metadata: Metadata = {
  title: "سامانه آزمون هوشمند کلاس‌محور",
  description: "زیرساخت فرانت‌اند سامانه آزمون هوشمند کلاس‌محور"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fa" dir="rtl">
      <body>
        <QueryProvider>
          <AuthProvider>{children}</AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
