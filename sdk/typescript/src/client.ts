import { Audit } from "./audit.js";
import { Auth } from "./auth.js";
import { Catalog } from "./catalog.js";
import { Flags } from "./flags.js";
import { IAM } from "./iam.js";
import { Logs } from "./logs.js";
import { Metrics } from "./metrics.js";
import { Notify } from "./notify.js";
import { Traces } from "./traces.js";
import { Transport, type FetchFn } from "./transport.js";
import { Vault } from "./vault.js";

export interface TennetctlOptions {
  apiKey?: string;
  sessionToken?: string;
  timeoutMs?: number;
  fetchFn?: FetchFn;
  sleepFn?: (ms: number) => Promise<void>;
  flagsTtlSeconds?: number;
}

export class Tennetctl {
  private readonly t: Transport;
  readonly auth: Auth;
  readonly flags: Flags;
  readonly iam: IAM;
  readonly audit: Audit;
  readonly notify: Notify;
  readonly metrics: Metrics;
  readonly logs: Logs;
  readonly traces: Traces;
  readonly vault: Vault;
  readonly catalog: Catalog;

  constructor(baseUrl: string, opts: TennetctlOptions = {}) {
    this.t = new Transport({
      baseUrl,
      apiKey: opts.apiKey,
      sessionToken: opts.sessionToken,
      timeoutMs: opts.timeoutMs,
      fetchFn: opts.fetchFn,
      sleepFn: opts.sleepFn,
    });
    this.auth = new Auth(this.t);
    this.flags = new Flags(this.t, opts.flagsTtlSeconds);
    this.iam = new IAM(this.t);
    this.audit = new Audit(this.t);
    this.notify = new Notify(this.t);
    this.metrics = new Metrics(this.t);
    this.logs = new Logs(this.t);
    this.traces = new Traces(this.t);
    this.vault = new Vault(this.t);
    this.catalog = new Catalog(this.t);
  }

  get sessionToken(): string | undefined {
    return this.t.getSessionToken();
  }

  /** Internal — exposed for future modules layering on the same transport. */
  get _transport(): Transport {
    return this.t;
  }
}
