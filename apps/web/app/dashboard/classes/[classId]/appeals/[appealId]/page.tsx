"use client";

import { useParams } from "next/navigation";

import { AuthGuard } from "@/features/auth/components/auth-guard";
import { AppealDetailPage } from "@/features/appeals/components/appeal-detail-page";

function routeParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

function AppealDetailRouteContent() {
  const params = useParams();
  const classId = routeParam(params.classId);
  const appealId = routeParam(params.appealId);

  return <AppealDetailPage classId={classId} appealId={appealId} />;
}

export default function ClassAppealDetailPage() {
  return <AuthGuard>{() => <AppealDetailRouteContent />}</AuthGuard>;
}
