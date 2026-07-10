"use client";

import { useParams } from "next/navigation";

import { AuthGuard } from "@/features/auth/components/auth-guard";
import { ReviewPage } from "@/features/grading-review/components/review-page";

function routeParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value ?? "";
}

function ReviewRouteContent() {
  const params = useParams();
  const classId = routeParam(params.classId);
  const examId = routeParam(params.examId);

  return <ReviewPage classId={classId} examId={examId} />;
}

export default function ExamReviewPage() {
  return <AuthGuard>{() => <ReviewRouteContent />}</AuthGuard>;
}
