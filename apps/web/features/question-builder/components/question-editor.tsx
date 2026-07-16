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
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { EssayFields } from "@/features/question-builder/components/essay-fields";
import { MultipleChoiceFields } from "@/features/question-builder/components/multiple-choice-fields";
import { RubricSuggestionPanel } from "@/features/question-builder/components/rubric-suggestion-panel";
import { ShortAnswerFields } from "@/features/question-builder/components/short-answer-fields";
import { TrueFalseFields } from "@/features/question-builder/components/true-false-fields";
import type { QuestionFormValues } from "@/features/question-builder/form-types";
import { useSuggestRubric, useUpdateQuestion } from "@/features/question-builder/hooks";
import { decimalToInput } from "@/lib/decimal";
import { getErrorMessage } from "@/lib/errors";
import type { Question, QuestionOption, QuestionSlot, QuestionUpdatePayload } from "@/types/question";

const questionSchema = z.object({
  text: z.string().trim().min(1, "متن سوال را وارد کنید."),
  points: z
    .string()
    .trim()
    .min(1, "نمره را وارد کنید.")
    .refine((value) => Number.isFinite(Number(value)) && Number(value) > 0, "نمره باید عدد مثبت باشد.")
    .refine((value) => Number.isInteger(Number(value) * 100), "نمره حداکثر دو رقم اعشار دارد."),
  grading_instructions: z.string(),
  expected_answer: z.string(),
  correct_answer: z.string(),
  rubric: z.string().refine(isValidRubricJson, "راهنمای تصحیح باید JSON معتبر با فهرست criteria باشد."),
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
  editable: boolean;
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

function isRubricValue(value: unknown): value is Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const criteria = (value as Record<string, unknown>).criteria;
  return (
    Array.isArray(criteria) &&
    criteria.length > 0 &&
    criteria.every(
      (criterion) =>
        Boolean(criterion) &&
        typeof criterion === "object" &&
        !Array.isArray(criterion) &&
        typeof (criterion as Record<string, unknown>).name === "string" &&
        Number.isFinite(Number((criterion as Record<string, unknown>).points))
    )
  );
}

function isValidRubricJson(value?: string) {
  const trimmed = value?.trim();
  if (!trimmed) {
    return true;
  }
  try {
    return isRubricValue(JSON.parse(trimmed));
  } catch {
    return false;
  }
}

function parseRubric(value?: string) {
  const trimmed = value?.trim();
  if (!trimmed) {
    return null;
  }

  return JSON.parse(trimmed) as unknown;
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
    points: values.points.trim(),
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

export function QuestionEditor({ classId, examId, question, editable, onQuestionHydrated }: QuestionEditorProps) {
  const [suggestions, setSuggestions] = useState<Record<string, unknown>>({});
  const [localError, setLocalError] = useState<string | null>(null);
  const [acceptRubricOpen, setAcceptRubricOpen] = useState(false);
  const updateQuestion = useUpdateQuestion(classId, examId, question?.id ?? "");
  const suggestRubric = useSuggestRubric(classId, examId, question?.id ?? "");
  const locked = !editable;
  const activeSuggestion = question ? suggestions[question.id] ?? (question as Question | undefined)?.rubric_ai_suggested : undefined;

  const defaultValues = useMemo<QuestionFormInput>(
    () => ({
      text: question?.text ?? "",
      points: question?.points ? decimalToInput(question.points) : "",
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
      setLocalError("برای پیشنهاد راهنمای تصحیح، متن سؤال، پاسخ مورد انتظار و نمره را وارد کنید.");
      return;
    }
    try {
      const saved = await saveDraft(values);
      const result = await suggestRubric.mutateAsync();
      if (!isRubricValue(result.rubric_ai_suggested)) {
        setLocalError("پیشنهاد هوش مصنوعی ساختار معتبری ندارد. دوباره تلاش کنید.");
        return;
      }
      setSuggestions((current) => ({ ...current, [saved.id]: result.rubric_ai_suggested }));
      onQuestionHydrated({ ...saved, rubric_ai_suggested: result.rubric_ai_suggested });
    } catch (error) {
      setLocalError(getErrorMessage(error));
    }
  }

  function acceptActiveSuggestion() {
    if (!isRubricValue(activeSuggestion)) {
      setLocalError("پیشنهاد هوش مصنوعی ساختار معتبری ندارد و قابل استفاده نیست.");
      return;
    }
    form.setValue("rubric", stringifyRubric(activeSuggestion), { shouldDirty: true, shouldValidate: true });
    setAcceptRubricOpen(false);
  }

  function requestAcceptSuggestion() {
    if (!isRubricValue(activeSuggestion)) {
      setLocalError("پیشنهاد هوش مصنوعی ساختار معتبری ندارد و قابل استفاده نیست.");
      return;
    }
    const currentRubric = form.getValues("rubric").trim();
    const suggestedRubric = stringifyRubric(activeSuggestion);
    if (currentRubric && currentRubric !== suggestedRubric) {
      setAcceptRubricOpen(true);
      return;
    }
    acceptActiveSuggestion();
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
          disabled={locked}
        />
      );
    }
    if (currentQuestion.type === "true_false") {
      return <TrueFalseFields register={form.register} errors={form.formState.errors} setValue={form.setValue} disabled={locked} />;
    }
    if (currentQuestion.type === "essay") {
      return <EssayFields register={form.register} errors={form.formState.errors} setValue={form.setValue} disabled={locked} />;
    }
    return <ShortAnswerFields register={form.register} errors={form.formState.errors} setValue={form.setValue} disabled={locked} />;
  }

  return (
    <div id={`question-editor-${question.id}`} className="scroll-mt-24 space-y-4" tabIndex={-1}>
      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-ink-900">
              سوال {question.order_index}، {typeLabels[question.type]}
            </h2>
            <p className="mt-1 text-sm text-ink-500">وضعیت سؤال: {question.status === "confirmed" ? "تأییدشده" : question.status === "draft" ? "پیش‌نویس" : question.status === "empty" ? "ناقص" : "نیازمند بررسی"}</p>
          </div>
          {locked ? <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">قفل شده</span> : null}
        </div>
        {locked ? (
          <Alert>این آزمون نهایی شده یا از مرحله draft عبور کرده است. برای ویرایش، قبل از زمان‌بندی آزمون را بازگشایی کنید.</Alert>
        ) : null}
        <form className="mt-4 space-y-4" onSubmit={form.handleSubmit(saveDraft)}>
          <FormError message={updateQuestion.error ? getErrorMessage(updateQuestion.error) : null} />
          {localError ? <Alert variant="error">{localError}</Alert> : null}
          <label className="block space-y-1.5">
            <span className="text-sm font-medium text-ink-700">متن سوال</span>
            <Textarea {...form.register("text")} placeholder="متن سوال را دستی وارد کنید." disabled={locked} />
            {form.formState.errors.text ? (
              <span className="text-xs text-rose-700">{form.formState.errors.text.message}</span>
            ) : null}
          </label>
          <label className="block max-w-xs space-y-1.5">
            <span className="text-sm font-medium text-ink-700">نمره</span>
            <Input type="number" min="0.01" step="0.01" inputMode="decimal" {...form.register("points")} disabled={locked} />
            {form.formState.errors.points ? (
              <span className="text-xs text-rose-700">{form.formState.errors.points.message}</span>
            ) : null}
          </label>
          {renderTypeFields()}
          <label className="block space-y-1.5">
            <span className="text-sm font-medium text-ink-700">راهنمای تصحیح</span>
            <Textarea {...form.register("grading_instructions")} placeholder="اختیاری" disabled={locked} />
          </label>
          <div className="flex justify-end">
            <Button type="submit" disabled={updateQuestion.isPending || locked}>
              <Save size={16} />
              {updateQuestion.isPending ? "در حال ذخیره" : "ذخیره draft"}
            </Button>
          </div>
        </form>
      </Card>

      {question.type === "essay" && !locked ? (
        <RubricSuggestionPanel
          suggestion={activeSuggestion}
          pending={suggestRubric.isPending}
          error={suggestRubric.error}
          disabled={updateQuestion.isPending}
          onSuggest={form.handleSubmit(handleSuggest)}
          onAccept={requestAcceptSuggestion}
        />
      ) : null}

      <ConfirmDialog
        open={acceptRubricOpen}
        title="جایگزینی راهنمای تصحیح"
        description="استفاده از پیشنهاد جدید، تغییرهای فعلی شما در راهنمای تصحیح را جایگزین می‌کند."
        confirmLabel="جایگزین کن"
        cancelLabel="انصراف"
        onConfirm={acceptActiveSuggestion}
        onClose={() => setAcceptRubricOpen(false)}
      />
    </div>
  );
}
