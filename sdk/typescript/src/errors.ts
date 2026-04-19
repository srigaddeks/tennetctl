export interface ErrorEnvelope {
  ok: false;
  error: { code: string; message: string };
}

export class TennetctlError extends Error {
  readonly code: string;
  readonly status: number | null;
  readonly data: unknown;

  constructor(
    message: string,
    opts: { code?: string; status?: number | null; data?: unknown } = {},
  ) {
    super(message);
    this.name = new.target.name;
    this.code = opts.code ?? "UNKNOWN";
    this.status = opts.status ?? null;
    this.data = opts.data ?? null;
  }
}

export class AuthError extends TennetctlError {}
export class ValidationError extends TennetctlError {}
export class NotFoundError extends TennetctlError {}
export class ConflictError extends TennetctlError {}
export class RateLimitError extends TennetctlError {}
export class ServerError extends TennetctlError {}
export class NetworkError extends TennetctlError {}

const STATUS_MAP: Record<number, typeof TennetctlError> = {
  400: ValidationError,
  401: AuthError,
  403: AuthError,
  404: NotFoundError,
  409: ConflictError,
  422: ValidationError,
  429: RateLimitError,
};

export function mapError(
  status: number,
  envelope: unknown,
): TennetctlError {
  const cls =
    status >= 500 ? ServerError : STATUS_MAP[status] ?? TennetctlError;

  let code = "UNKNOWN";
  let message = `HTTP ${status}`;
  if (envelope && typeof envelope === "object") {
    const err = (envelope as { error?: unknown }).error;
    if (err && typeof err === "object") {
      const e = err as { code?: unknown; message?: unknown };
      if (typeof e.code === "string") code = e.code;
      if (typeof e.message === "string") message = e.message;
    }
  }
  return new cls(message, { code, status, data: envelope });
}
