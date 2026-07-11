import { getMockResponse } from "./mock-data";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";
const USE_MOCK = import.meta.env.VITE_USE_MOCK_DATA === "true";

let apiToken: string | null = null;
// En Tauri empaquetado el launcher expone el token; en dev (navegador/vite) no hay
// token y el backend tampoco lo exige.
const tokenReady: Promise<void> = (async () => {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    apiToken = await invoke<string>("get_api_token");
  } catch {
    apiToken = null;
  }
})();

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

  await tokenReady;
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(apiToken ? { "X-Api-Token": apiToken } : {}),
      ...init?.headers,
    },
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

// Caché de GETs: evita repetir las mismas llamadas al navegar entre páginas.
// ponytail: TTL fijo de 30 s e invalidación total en cualquier mutación;
// si hace falta invalidación por recurso o revalidación en segundo plano, migrar a TanStack Query.
const CACHE_TTL_MS = 30_000;
const getCache = new Map<string, { at: number; promise: Promise<unknown> }>();

function cachedGet<T>(path: string): Promise<T> {
  const hit = getCache.get(path);
  if (hit && Date.now() - hit.at < CACHE_TTL_MS) {
    return hit.promise as Promise<T>;
  }
  // ponytail: el signal público se ignora — los GET son idempotentes y de 30 s
  // de vida; abortar un fetch compartido afectaría a otros consumidores del path.
  const promise = request<T>(path);
  getCache.set(path, { at: Date.now(), promise });
  promise.catch(() => getCache.delete(path)); // no cachear errores
  return promise;
}

function invalidateCache(): void {
  getCache.clear();
}

export const api = {
  get: <T>(path: string, _signal?: AbortSignal) => cachedGet<T>(path),
  getFresh: <T>(path: string) => {
    getCache.delete(path);
    return cachedGet<T>(path);
  },
  post: <T>(path: string, body: unknown, signal?: AbortSignal) => {
    invalidateCache();
    return request<T>(path, { method: "POST", body: JSON.stringify(body) }, signal);
  },
  upload: <T>(path: string, body: FormData) => {
    invalidateCache();
    return request<T>(path, { method: "POST", body });
  },
  put: <T>(path: string, body: unknown) => {
    invalidateCache();
    return request<T>(path, { method: "PUT", body: JSON.stringify(body) });
  },
  patch: <T>(path: string, body: unknown) => {
    invalidateCache();
    return request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
  },
  delete: <T>(path: string) => {
    invalidateCache();
    return request<T>(path, { method: "DELETE" });
  },
};
