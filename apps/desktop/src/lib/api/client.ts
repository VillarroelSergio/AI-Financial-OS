import { getMockResponse } from "./mock-data";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";
const USE_MOCK = import.meta.env.VITE_USE_MOCK_DATA === "true";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit, signal?: AbortSignal): Promise<T> {
  if (USE_MOCK) {
    return Promise.resolve(getMockResponse<T>(path, init));
  }

  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { ...(isFormData ? {} : { "Content-Type": "application/json" }), ...init?.headers },
    ...init,
    ...(signal ? { signal } : {}),
  });

  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ error: { code: "UNKNOWN", message: response.statusText } }));
    const error = body.error ?? body.detail?.error;
    throw new ApiError(
      response.status,
      error?.code ?? `HTTP_${response.status}`,
      error?.message ?? body.detail ?? response.statusText,
    );
  }

  if (response.status === 204 || response.headers.get("content-length") === "0") {
    return undefined as T;
  }

  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, undefined, signal),
  post: <T>(path: string, body: unknown, signal?: AbortSignal) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }, signal),
  upload: <T>(path: string, body: FormData) => request<T>(path, { method: "POST", body }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
