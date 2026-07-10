export type ApiSuccess<T> = {
  success: true;
  data: T;
  message: string | null;
};

export type ApiFailure = {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};

export type ApiEnvelope<T> = ApiSuccess<T> | ApiFailure;
