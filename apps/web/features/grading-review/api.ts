import { apiClient } from "@/lib/api-client";
import type {
  AnswerReviewPayload,
  AnswerReviewResult,
  ApproveResultsResult,
  ExamReview,
  PublishResultsResult
} from "@/types/review";

function examPath(classId: string, examId: string) {
  return `/classes/${encodeURIComponent(classId)}/exams/${encodeURIComponent(examId)}`;
}

export function getExamReview(classId: string, examId: string) {
  return apiClient.get<ExamReview>(`${examPath(classId, examId)}/review`);
}

export function reviewAnswer(classId: string, examId: string, answerId: string, payload: AnswerReviewPayload) {
  return apiClient.put<AnswerReviewResult>(
    `${examPath(classId, examId)}/answers/${encodeURIComponent(answerId)}/review`,
    payload
  );
}

export function approveResults(classId: string, examId: string) {
  return apiClient.post<ApproveResultsResult>(`${examPath(classId, examId)}/approve-results`);
}

export function publishResults(classId: string, examId: string) {
  return apiClient.post<PublishResultsResult>(`${examPath(classId, examId)}/publish-results`);
}
