/**
 * `request<T>()` — the single fetch site. Its whole job is turning FastAPI's two different
 * error `detail` shapes into one typed `ApiError`, because the status codes ARE the app's
 * control flow (build_plan §5):
 *
 *   403 → seat token unknown  → run the rejoin flow
 *   409 → state conflict      → someone (or the AFK timer) already answered; clear + re-sync
 *   422 → contract violation  → the message is human-readable; render it verbatim
 *   503 → on /replays         → archive not configured
 */
import { apiUrl } from './config';

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }

  get isSeatLost(): boolean {
    return this.status === 403;
  }
  get isConflict(): boolean {
    return this.status === 409;
  }
  get isValidation(): boolean {
    return this.status === 422;
  }
  get isUnavailable(): boolean {
    return this.status === 503;
  }
}

/** FastAPI 422 bodies: `{detail: [{loc, msg, type}, …]}`. Everything else: `{detail: str}`. */
interface ValidationItem {
  loc?: (string | number)[];
  msg?: string;
}

function messageFromBody(body: unknown, status: number): string {
  if (typeof body === 'string' && body.trim()) return body;
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      const parts = (detail as ValidationItem[])
        .map((item) => {
          // Drop the conventional "body" prefix — it means nothing to a player.
          const field = (item.loc ?? []).filter((p) => p !== 'body').join('.');
          return field ? `${field}: ${item.msg ?? 'invalid'}` : (item.msg ?? 'invalid');
        })
        .filter(Boolean);
      if (parts.length) return parts.join('; ');
    }
  }
  return `Request failed (${status})`;
}

export interface RequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  signal?: AbortSignal;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = options;

  const response = await fetch(apiUrl(path), {
    method,
    signal,
    // Always: the seat cookie is how the server knows which seat is talking.
    credentials: 'include',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    let parsed: unknown = null;
    try {
      parsed = await response.json();
    } catch {
      // Non-JSON error body (proxy 502, HTML error page) — fall through to the generic text.
    }
    throw new ApiError(response.status, messageFromBody(parsed, response.status));
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
