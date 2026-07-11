"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FormError } from "@/components/common/form-error";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { EssayFields } from "@/features/question-builder/components/essay-fields";
import { MultipleChoiceFields } from "@/features/question-builder/components/multiple-choice-fields";
import { QuestionConfirmPanel } from "@/features/question-builder/components/question-confirm-panel";
import { RubricSuggestionPanel } from "@/features/question-builder/components/rubric-suggestion-panel";
import { ShortAnswerFields } from "@/features/question-builder/components/short-answer-fields";
import { TrueFalseFields } from "@/features/question-builder/components/true-false-fields";
import type { QuestionFormValues } from "@/features/question-builder/form-types";
import { useConfirmQuestion, useSuggestRubric, useUpdateQuestion } from "@/features/question-builder/hooks";
import { getErrorMessage } from "@/lib/errors";
import type { Question, QuestionOption, QuestionSlot, QuestionUpdatePayload } from "@/types/question";

const questionSchema = z.object({
  text: z.string().trim().min(1, "متن سوال را وارد کنید."),
  points: z
    .string()
    .trim()
    .min(1, "نمره را وارد کنید.")
    .refine((value) => Number.isInteger(Number(value)) && Number(value) > 0, "نمره باید عدد صحیح مثبت باشد."),
  grading_instructions: z.string(),
  expected_answer: z.string(),
  correct_answer: z.string(),
  rubric: z.string(),
  rubric_teacher_confirmed: z.boolean(),
  option_a: z.string(),
  option_b: z.string(),
  option_c: z.string(),
  option_d: z.string()
});

type QuestionFormInput = QuestionFormValues;
type QuestionFormOutput = QuestionFormValues;

type QuestionEditorProps = {
  classId: string;
  examId: string;
  question?: Question | QuestionSlot | null;
  onQuestionHydrated: (question: Question) => void;
};

const typeLabels: Record<string, string> = {
  multiple_choice: "تستی",
  short_answer: "کوتاه‌پاسخ",
  essay: "تشریحی",
  true_false: "درست/غلط"
};

const MULTIPLE_CHOICE_KEYS = ["A", "B", "C", "D"] as const;
type MultipleChoiceKey = (typeof MULTIPLE_CHOICE_KEYS)[number];

function normalizeMultipleChoiceKey(value: unknown): MultipleChoiceKey | "" {
  const normalized = String(value ?? "")
    .trim()
    .toUpperCase();
  return MULTIPLE_CHOICE_KEYS.includes(normalized as MultipleChoiceKey) ? (normalized as MultipleChoiceKey) : "";
}

function optionValue(question: Question | QuestionSlot | null | undefined, key: string) {
  const detailed = question as Question | undefined;
  return (
    detailed?.options?.find((option) => normalizeMultipleChoiceKey(option.option_key) === normalizeMultipleChoiceKey(key))
      ?.option_text ?? ""
  );
}

function correctAnswerValue(question: Question | QuestionSlot | null | undefined) {
  const detailed = question as Question | undefined;
  const directAnswer = normalizeMultipleChoiceKey(detailed?.correct_answer);
  if (directAnswer) {
    return directAnswer;
  }

  if (detailed?.correct_answer_data && typeof detailed.correct_answer_data === "object") {
    const answerData = detailed.correct_answer_data as Record<string, unknown>;
    const selectedOption = normalizeMultipleChoiceKey(answerData.selected_option ?? answerData.option_key);
    if (selectedOption) {
      return selectedOption;
    }
  }

  const correctOption = detailed?.options?.find((option) => option.is_correct);
  return normalizeMultipleChoiceKey(correctOption?.option_key);
}

function stringifyRubric(value: unknown) {
  if (!value) {
    return "";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

function parseRubric(value?: string) {
  const trimmed = value?.trim();
  if (!trimmed) {
    return null;
  }

  try {
    return JSON.parse(trimmed) as unknown;
  } catch {
    return { text: trimmed };
  }
}

function optionalText(value?: string) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function buildOptions(values: QuestionFormOutput): QuestionOption[] {
  const correct = normalizeMultipleChoiceKey(values.correct_answer);
  return MULTIPLE_CHOICE_KEYS
    .map((key) => ({
      option_key: key,
      option_text: values[`option_${key.toLowerCase() as "a" | "b" | "c" | "d"}`]?.trim() ?? "",
      is_correct: correct === key
    }))
    .filter((option) => option.option_text);
}

function buildPayload(question: Question | QuestionSlot, values: QuestionFormOutput): QuestionUpdatePayload {
  const common: QuestionUpdatePayload = {
    text: values.text.trim(),
    points: Number(values.points),
    grading_instructions: optionalText(values.grading_instructions)
  };

  if (question.type === "multiple_choice") {
    const correct = normalizeMultipleChoiceKey(values.correct_answer);
    return {
      ...common,
      correct_answer: correct || null,
      correct_answer_data: correct ? { selected_option: correct } : null,
      options: buildOptions(values)
    };
  }

  if (question.type === "true_false") {
    const correct = values.correct_answer === "true" ? "true" : values.correct_answer === "false" ? "false" : null;
    return {
      ...common,
      correct_answer: correct,
      correct_answer_data: correct ? { value: correct === "true" } : null
    };
  }

  if (question.type === "essay") {
    return {
      ...common,
      expected_answer: optionalText(values.expected_answer),
      rubric: parseRubric(values.rubric),
      rubric_teacher_confirmed: values.rubric_teacher_confirmed
    };
  }

  return {
    ...common,
    expected_answer: optionalText(values.expected_answer)
  };
}

export function QuestionEditor({ classId, examId, question, onQuestionHydrated }: QuestionEditorProps) {
  const [suggestions, setSuggestions] = useState<Record<string, unknown>>({});
  const [localError, setLocalError] = useState<Error | null>(null);
  const updateQuestion = useUpdateQuestion(classId, examId, question?.id ?? "");
  const confirmQuestion = useConfirmQuestion(classId, examId, question?.id ?? "");
  const suggestRubric = useSuggestRubric(classId, examId, question?.id ?? "");
  const confirmed = Boolean(question?.teacher_confirmed || question?.status === "confirmed");
  const activeSuggestion = question ? suggestions[question.id] ?? (question as Question | undefined)?.rubric_ai_suggested : undefined;

  const defaultValues = useMemo<QuestionFormInput>(
    () => ({
      text: question?.text ?? "",
      points: question?.points ? String(question.points) : "",
      grading_instructions: (question as Question | undefined)?.grading_instructions ?? "",
      expected_answer: (question as Question | undefined)?.expected_answer ?? "",
      correct_answer:
        question?.type === "multiple_choice" ? correctAnswerValue(question) : (question as Question | undefined)?.correct_answer ?? "",
      rubric: stringifyRubric((question as Question | undefined)?.rubric),
      rubric_teacher_confirmed: (question as Question | undefined)?.rubric_teacher_confirmed ?? false,
      option_a: optionValue(question, "a"),
      option_b: optionValue(question, "b"),
      option_c: optionValue(question, "c"),
      option_d: optionValue(question, "d")
    }),
    [question]
  );

  const form = useForm<QuestionFormInput, unknown, QuestionFormOutput>({
    resolver: zodResolver(questionSchema),
    defaultValues
  });

  useEffect(() => {
    form.reset(defaultValues);
  }, [defaultValues, form]);

  if (!question) {
    return (
      <Card>
        <p className="text-sm text-ink-500">یک سوال را از فهرست انتخاب کنید.</p>
      </Card>
    );
  }

  async function saveDraft(values: QuestionFormOutput) {
    if (!question) {
      throw new Error("سوالی انتخاب نشده است.");
    }
    const saved = await updateQuestion.mutateAsync(buildPayload(question, values));
    onQuestionHydrated({ ...saved, rubric_ai_suggested: activeSuggestion });
    return saved;
  }

  async function handleSuggest(values: QuestionFormOutput) {
    setLocalError(null);
    if (question?.type !== "essay") {
      return;
    }
    if (!values.text.trim() || !values.expected_answer?.trim() || !values.points) {
      setLocalError(new Error("برای پیشنهاد rubric، متن سوال، پاسخ مورد انتظار و نمره را وارد کنید."));
      return;
    }
    try {
      const saved = await saveDraft(values);
      const result = await suggestRubric.mutateAsync();
      setSuggestions((current) => ({ ...current, [saved.id]: result.rubric_ai_suggested }));
      onQuestionHydrated({ ...saved, rubric_ai_suggested: result.rubric_ai_suggested });
    } catch (error) {
      setLocalError(error instanceof Error ? error : new Error("دریافت پیشنهاد rubric ناموفق بود."));
    }
  }

  async function handleConfirm(values: QuestionFormOutput) {
    try {
      const saved = await saveDraft(values);
      const confirmedQuestion = await confirmQuestion.mutateAsync();
      onQuestionHydrated({ ...saved, ...confirmedQuestion, rubric_ai_suggested: activeSuggestion });
    } catch {
      return;
    }
  }

  function renderTypeFields() {
    const currentQuestion = question;
    if (!currentQuestion) {
      return null;
    }
    if (currentQuestion.type === "multiple_choice") {
      return (
        <MultipleChoiceFields
          control={form.control}
          register={form.register}
          errors={form.formState.errors}
          setValue={form.setValue}
        />
      );
    }
    if (currentQuestion.type === "true_false") {
      return <TrueFalseFields register={form.register} errors={form.formState.errors} setValue={form.setValue} />;
    }
    if (currentQuestion.type === "essay") {
      return <EssayFields register={form.register} errors={form.formState.errors} setValue={form.setValue} />;
    }
    return <ShortAnswerFields register={form.register} errors={form.formState.errors} setValue={form.setValue} />;
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-ink-900">
              سوال {question.order_index}، {typeLabels[question.type]}
            </h2>
            <p className="mt-1 text-sm text-ink-500">وضعیت: {confirmed ? "تایید شده" : question.status}</p>
          </div>
          {confirmed ? <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">نهایی</span> : null}
        </div>
        {confirmed ? (
          <Alert>سوال تایید شده است و backend اجازه ویرایش مستقیم آن را نمی‌دهد.</Alert>
        ) : null}
        <form className="mt-4 space-y-4" onSubmit={form.handleSubmit(saveDraft)}>
          <FormError message={updateQuestion.error ? getErrorMessage(updateQuestion.error) : null} />
          {localError ? <Alert variant="error">{localError.message}</Alert> : null}
          <label className="block space-y-1.5">
            <span className="text-sm font-medium text-ink-700">متن سوال</span>
            <Textarea {...form.register("text")} placeholder="متن سوال را دستی وارد کنید." disabled={confirmed} />
            {form.formState.errors.text ? (
              <span className="text-xs text-rose-700">{form.formState.errors.text.message}</span>
            ) : null}
          </label>
          <label className="block max-w-xs space-y-1.5">
            <span className="text-sm font-medium text-ink-700">نمره</span>
            <Input type="number" min={1} {...form.register("points")} disabled={confirmed} />
            {form.formState.errors.points ? (
              <span className="text-xs text-rose-700">{form.formState.errors.points.message}</span>
            ) : null}
          </label>
          {renderTypeFields()}
          <label className="block space-y-1.5">
            <span className="text-sm font-medium text-ink-700">راهنمای تصحیح</span>
            <Textarea {...form.register("grading_instructions")} placeholder="اختیاری" disabled={confirmed} />
          </label>
          <div className="flex justify-end">
            <Button type="submit" disabled={updateQuestion.isPending || confirmed}>
              <Save size={16} />
              {updateQuestion.isPending ? "در حال ذخیره" : "ذخیره draft"}
            </Button>
          </div>
        </form>
      </Card>

      {question.type === "essay" && !confirmed ? (
        <RubricSuggestionPanel
          suggestion={activeSuggestion}
          pending={suggestRubric.isPending}
          error={suggestRubric.error}
          disabled={updateQuestion.isPending}
          onSuggest={form.handleSubmit(handleSuggest)}
          onAccept={() => form.setValue("rubric", stringifyRubric(activeSuggestion), { shouldDirty: true })}
        />
      ) : null}

      <QuestionConfirmPanel
        question={question as Question}
        pending={confirmQuestion.isPending || updateQuestion.isPending}
        error={confirmQuestion.error}
        onConfirm={form.handleSubmit(handleConfirm)}
      />
    </div>
  );
}
