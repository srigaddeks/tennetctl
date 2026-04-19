export { Tennetctl, type TennetctlOptions } from "./client.js";
export { Auth, Sessions, ApiKeys, type SignedInResponse } from "./auth.js";
export { Flags, DEFAULT_FLAGS_TTL_SECONDS, type FlagResult } from "./flags.js";
export { IAM } from "./iam.js";
export { Audit, AuditEvents } from "./audit.js";
export { Notify } from "./notify.js";
export { Metrics } from "./metrics.js";
export { Logs } from "./logs.js";
export { Traces } from "./traces.js";
export { Vault, VaultSecrets, VaultConfigs } from "./vault.js";
export { Catalog } from "./catalog.js";
export {
  TennetctlError,
  AuthError,
  ValidationError,
  NotFoundError,
  ConflictError,
  RateLimitError,
  ServerError,
  NetworkError,
  mapError,
  type ErrorEnvelope,
} from "./errors.js";
export { Transport, type TransportOptions, type FetchFn, SESSION_COOKIE } from "./transport.js";

export const VERSION = "0.1.0";
