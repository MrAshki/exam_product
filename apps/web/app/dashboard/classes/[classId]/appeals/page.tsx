"use client";

import { useParams } from "next/navigation";

import { AuthGuard } from "@/features/auth/components/auth-guard";
import { AppealsListPage } from "@/features/appeals/components/appeals-list-page";

function routeParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

function AppealsRouteContent() {
  const params = useParams();
  const classId = routeParam(params.classId);

  return <AppealsListPage classId={classId} />;
}

export default function ClassAppealsPage() {
  return <AuthGuard>{() => <AppealsRouteContent />}</AuthGuard>;
}
