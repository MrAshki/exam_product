import type { ApiEnvelope, ApiFailure, ApiSuccess } from "@/types/api";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

type QueryValue = string | number | boolean | null | undefined;

type RequestOptions = {
  body?: unknown;
  query?: Record<string, QueryValue | QueryValue[]>;
  headers?: HeadersInit;
};

export type { ApiFailure, ApiSuccess };

export class ApiError extends Error {
  code: string;
  details?: Record<string, unknown>;
  status: number;

  constructor({
    code,
    message,
    details,
    status
  }: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    status: number;
  }) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${getApiBaseUrl()}${cleanPath}`);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      const values = Array.isArray(value) ? value : [value];
      values.forEach((item) => {
        if (item !== undefined && item !== null) {
          url.searchParams.append(key, String(item));
        }
      });
    });
  }

  return url.toString();
}

async function request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(buildUrl(path, options.query), {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body)
  });

  let envelope: ApiEnvelope<T> | null = null;

  try {
    envelope = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiError({
      code: "API_RESPONSE_INVALID",
      message: "پاسخ سرور قابل خواندن نیست.",
      status: response.status
    });
  }

  if (!response.ok || envelope.success === false) {
    const failure = envelope as ApiFailure;
    throw new ApiError({
      code: failure.error?.code || "API_REQUEST_FAILED",
      message: failure.error?.message || "درخواست با خطا مواجه شد.",
      details: failure.error?.details,
      status: response.status
    });
  }

  return (envelope as ApiSuccess<T>).data;
}

export const apiClient = {
  get: <T>(path: string, options?: Pick<RequestOptions, "query" | "headers">) =>
    request<T>("GET", path, options),
  post: <T>(path: string, body?: unknown, options?: Pick<RequestOptions, "query" | "headers">) =>
    request<T>("POST", path, { ...options, body }),
  put: <T>(path: string, body?: unknown, options?: Pick<RequestOptions, "query" | "headers">) =>
    request<T>("PUT", path, { ...options, body }),
  delete: <T>(path: string, options?: Pick<RequestOptions, "query" | "headers">) =>
    request<T>("DELETE", path, options)
};
