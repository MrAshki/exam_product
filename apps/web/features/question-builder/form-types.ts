import type { FieldErrors, UseFormRegister, UseFormSetValue } from "react-hook-form";

export type QuestionFormValues = {
  text: string;
  points: string;
  grading_instructions: string;
  expected_answer: string;
  correct_answer: string;
  rubric: string;
  rubric_teacher_confirmed: boolean;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
};

export type QuestionFieldProps = {
  register: UseFormRegister<QuestionFormValues>;
  errors: FieldErrors<QuestionFormValues>;
  setValue: UseFormSetValue<QuestionFormValues>;
};
