"use client";

import { FileWarning } from "lucide-react";

import { Card } from "@/components/ui/card";
import { ApiError } from "@/lib/api-client";
import { getErrorMessage } from "@/lib/errors";

type ResultErrorStateProps = {
  error: unknown;
};

function resultErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    if (error.code === "INVALID_RESULT_TOKEN") {
      return "این لینک نتیجه معتبر نیست یا منقضی شده است.";
    }
    if (error.code === "RESULT_NOT_PUBLISHED") {
      return "نتیجه این آزمون هنوز منتشر نشده است.";
    }
  }

  return getErrorMessage(error);
}

export function ResultErrorState({ error }: ResultErrorStateProps) {
  return (
    <Card className="mx-auto max-w-2xl text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 text-rose-700">
        <FileWarning size={22} />
      </div>
      <h1 className="mt-4 text-2xl font-bold text-ink-900">نتیجه در دسترس نیست</h1>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-ink-600">{resultErrorMessage(error)}</p>
    </Card>
  );
}
