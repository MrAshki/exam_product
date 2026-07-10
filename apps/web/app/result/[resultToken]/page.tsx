"use client";

import { useParams } from "next/navigation";

import { StudentResultPage } from "@/features/results/components/student-result-page";

function routeParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

export default function PublicResultPage() {
  const params = useParams();
  const resultToken = routeParam(params.resultToken);

  return <StudentResultPage resultToken={resultToken} />;
}
