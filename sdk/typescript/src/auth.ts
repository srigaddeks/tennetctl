import type { Transport } from "./transport.js";

export interface SignedInResponse {
  token?: string;
  session_token?: string;
  user?: Record<string, unknown>;
  session?: Record<string, unknown>;
  [key: string]: unknown;
}

export class Sessions {
  constructor(private readonly t: Transport) {}

  async list(): Promise<Array<Record<string, unknown>>> {
    const data = await this.t.request<Array<Record<string, unknown>>>("GET", "/v1/sessions");
    return Array.isArray(data) ? data : [];
  }

  async get(id: string): Promise<Record<string, unknown>> {
    return this.t.request("GET", `/v1/sessions/${id}`);
  }

  async update(id: string, patch: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.t.request("PATCH", `/v1/sessions/${id}`, { body: patch });
  }

  async revoke(id: string): Promise<void> {
    await this.t.request("DELETE", `/v1/sessions/${id}`);
  }
}

export class ApiKeys {
  constructor(private readonly t: Transport) {}

  async list(): Promise<Array<Record<string, unknown>>> {
    const data = await this.t.request<Array<Record<string, unknown>>>("GET", "/v1/api-keys");
    return Array.isArray(data) ? data : [];
  }

  async create(args: {
    name: string;
    scopes: string[];
    expires_at?: string;
  }): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = { name: args.name, scopes: args.scopes };
    if (args.expires_at !== undefined) body.expires_at = args.expires_at;
    return this.t.request("POST", "/v1/api-keys", { body });
  }

  async revoke(id: string): Promise<void> {
    await this.t.request("DELETE", `/v1/api-keys/${id}`);
  }

  async rotate(id: string): Promise<Record<string, unknown>> {
    return this.t.request("POST", `/v1/api-keys/${id}/rotate`);
  }
}

function extractToken(data: SignedInResponse | undefined): string | undefined {
  if (!data) return undefined;
  if (typeof data.token === "string") return data.token;
  if (typeof data.session_token === "string") return data.session_token;
  if (data.session && typeof data.session === "object") {
    const tok = (data.session as { token?: unknown }).token;
    if (typeof tok === "string") return tok;
  }
  return undefined;
}

export class Auth {
  readonly sessions: Sessions;
  readonly api_keys: ApiKeys;

  constructor(private readonly t: Transport) {
    this.sessions = new Sessions(t);
    this.api_keys = new ApiKeys(t);
  }

  async signin(args: { email: string; password: string }): Promise<SignedInResponse> {
    const data = await this.t.request<SignedInResponse>("POST", "/v1/auth/signin", {
      body: args,
    });
    const tok = extractToken(data);
    if (tok) this.t.setSessionToken(tok);
    return data ?? {};
  }

  async signup(args: { email: string; password: string } & Record<string, unknown>): Promise<SignedInResponse> {
    const data = await this.t.request<SignedInResponse>("POST", "/v1/auth/signup", {
      body: args,
    });
    const tok = extractToken(data);
    if (tok) this.t.setSessionToken(tok);
    return data ?? {};
  }

  async signout(): Promise<void> {
    try {
      await this.t.request("POST", "/v1/auth/signout");
    } finally {
      this.t.setSessionToken(undefined);
    }
  }

  async me(): Promise<Record<string, unknown>> {
    return this.t.request("GET", "/v1/auth/me");
  }
}
