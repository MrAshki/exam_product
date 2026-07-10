"use client";

import { useParams } from "next/navigation";

import { StudentExamPage } from "@/features/student-exam/components/student-exam-page";

function routeParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

export default function PublicExamAccessPage() {
  const params = useParams();
  const examToken = routeParam(params.examToken);

  return <StudentExamPage examToken={examToken} />;
}
