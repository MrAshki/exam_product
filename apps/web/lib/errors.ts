import { ApiError } from "@/lib/api-client";

const apiErrorMessages: Record<string, string> = {
  AUTH_REQUIRED: "برای ادامه باید وارد شوید.",
  NOT_AUTHENTICATED: "برای ادامه باید وارد شوید.",
  INVALID_CREDENTIALS: "ایمیل یا رمز عبور نادرست است.",
  INACTIVE_USER: "حساب کاربری شما غیرفعال است.",
  EMAIL_ALREADY_REGISTERED: "با این ایمیل قبلا حساب ساخته شده است.",
  CLASS_NOT_FOUND: "کلاس پیدا نشد یا به آن دسترسی ندارید.",
  STUDENT_NOT_FOUND: "دانش‌آموز پیدا نشد.",
  STUDENT_NOT_IN_CLASS: "این دانش‌آموز در کلاس انتخاب‌شده نیست.",
  STUDENT_ALREADY_IN_CLASS: "این دانش‌آموز از قبل در این کلاس وجود دارد.",
  STUDENT_EMAIL_ALREADY_EXISTS: "دانش‌آموز دیگری با این ایمیل برای شما ثبت شده است.",
  VALIDATION_ERROR: "اطلاعات واردشده معتبر نیست. فیلدها را بررسی کنید."
};

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return apiErrorMessages[error.code] || error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "خطای ناشناخته رخ داد.";
}

export { ApiError };
