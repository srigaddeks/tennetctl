import { NetworkError, mapError } from "./errors.js";

export const SESSION_COOKIE = "tnt_session";

const RETRY_STATUSES = new Set([502, 503, 504]);
const RETRY_BACKOFFS_MS = [500, 1000, 2000] as const;
const MAX_ATTEMPTS = RETRY_BACKOFFS_MS.length + 1;

export type FetchFn = typeof fetch;

export interface TransportOptions {
  baseUrl: string;
  apiKey?: string;
  sessionToken?: string;
  timeoutMs?: number;
  fetchFn?: FetchFn;
  sleepFn?: (ms: number) => Promise<void>;
}

const defaultSleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

export class Transport {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private sessionToken?: string;
  private readonly timeoutMs: number;
  private readonly fetchFn: FetchFn;
  private readonly sleepFn: (ms: number) => Promise<void>;

  constructor(opts: TransportOptions) {
    this.baseUrl = opts.baseUrl.replace(/\/+$/, "");
    this.apiKey = opts.apiKey;
    this.sessionToken = opts.sessionToken;
    this.timeoutMs = opts.timeoutMs ?? 30_000;
    this.fetchFn = opts.fetchFn ?? fetch;
    this.sleepFn = opts.sleepFn ?? defaultSleep;
  }

  getSessionToken(): string | undefined {
    return this.sessionToken;
  }

  setSessionToken(token: string | undefined): void {
    this.sessionToken = token;
  }

  async request<T = unknown>(
    method: string,
    path: string,
    opts: {
      body?: unknown;
      params?: Record<string, string | number | boolean | undefined>;
      headers?: Record<string, string>;
    } = {},
  ): Promise<T> {
    const url = this.buildUrl(path, opts.params);
    const headers = this.buildHeaders(opts.body !== undefined, opts.headers);

    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeoutMs);

      let response: Response;
      try {
        response = await this.fetchFn(url, {
          method: method.toUpperCase(),
          headers,
          body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
          credentials: "include",
          signal: controller.signal,
        });
      } catch (err) {
        clearTimeout(timer);
        if (attempt < MAX_ATTEMPTS - 1) {
          await this.sleepFn(RETRY_BACKOFFS_MS[attempt]!);
          continue;
        }
        throw new NetworkError(err instanceof Error ? err.message : String(err), {
          code: "NETWORK",
          status: null,
        });
      } finally {
        clearTimeout(timer);
      }

      if (RETRY_STATUSES.has(response.status) && attempt < MAX_ATTEMPTS - 1) {
        await this.sleepFn(RETRY_BACKOFFS_MS[attempt]!);
        continue;
      }

      return this.parseResponse<T>(response);
    }

    throw new NetworkError("retry loop exhausted", { code: "NETWORK" });
  }

  private buildUrl(
    path: string,
    params?: Record<string, string | number | boolean | undefined>,
  ): string {
    const url = new URL(path.startsWith("/") ? path.slice(1) : path, this.baseUrl + "/");
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined) url.searchParams.set(k, String(v));
      }
    }
    return url.toString();
  }

  private buildHeaders(
    hasBody: boolean,
    extra?: Record<string, string>,
  ): Record<string, string> {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (hasBody) headers["Content-Type"] = "application/json";
    if (this.apiKey) headers["Authorization"] = `Bearer ${this.apiKey}`;
    if (extra) {
      for (const [k, v] of Object.entries(extra)) {
        headers[k] = v;
      }
    }
    // Cookie handled by fetch with credentials: "include" in browser;
    // in Node runtime the server must be same-origin or configure CORS.
    return headers;
  }

  private async parseResponse<T>(response: Response): Promise<T> {
    if (response.status === 204) {
      return undefined as T;
    }

    let envelope: unknown = null;
    const text = await response.text();
    if (text.length > 0) {
      try {
        envelope = JSON.parse(text);
      } catch {
        envelope = null;
      }
    }

    if (response.status >= 200 && response.status < 300) {
      if (
        envelope &&
        typeof envelope === "object" &&
        (envelope as { ok?: unknown }).ok === true
      ) {
        return (envelope as { data?: unknown }).data as T;
      }
      return envelope as T;
    }

    const body =
      envelope ??
      {
        ok: false,
        error: { code: "HTTP_ERROR", message: text || `HTTP ${response.status}` },
      };
    throw mapError(response.status, body);
  }
}
