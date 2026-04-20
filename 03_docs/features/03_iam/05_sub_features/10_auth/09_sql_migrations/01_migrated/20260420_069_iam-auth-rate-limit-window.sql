-- Migration 069: IAM auth rate-limit sliding-window counter (Plan 38-01)
-- Sub-feature: 10_auth
-- Scope: 03_iam schema
--
-- Fixed-window IP-based rate limiter for unauthenticated auth endpoints
-- (signin, magic-link/request, password-reset/request). Designed as a
-- Postgres-native fallback; when Valkey is wired in, Valkey INCR is the
-- primary and this table serves as both fallback and audit trail.
--
-- Window keying: (endpoint, ip, window_start) where window_start is
-- CURRENT_TIMESTAMP truncated to the configured window boundary.

-- UP ====

CREATE TABLE IF NOT EXISTS "03_iam"."60_evt_auth_rate_limit_window" (
    endpoint      TEXT       NOT NULL,
    ip            TEXT       NOT NULL,
    window_start  TIMESTAMP  NOT NULL,
    count         INT        NOT NULL DEFAULT 0,
    first_seen_at TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at  TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_auth_rate_limit_window
        PRIMARY KEY (endpoint, ip, window_start)
);

COMMENT ON TABLE "03_iam"."60_evt_auth_rate_limit_window"
    IS 'Plan 38-01: per-IP request counter for unauthenticated auth endpoints. Postgres-native fallback when Valkey unavailable. Periodic GC drops rows by window_start.';
COMMENT ON COLUMN "03_iam"."60_evt_auth_rate_limit_window".endpoint
    IS 'Logical endpoint label — e.g. "auth.signin", "magic_link.request", "password_reset.request".';
COMMENT ON COLUMN "03_iam"."60_evt_auth_rate_limit_window".ip
    IS 'Client IP — from X-Forwarded-For first hop if present, else request.client.host.';
COMMENT ON COLUMN "03_iam"."60_evt_auth_rate_limit_window".window_start
    IS 'Truncated window boundary; UPSERT target — one row per (endpoint, ip, window).';

CREATE INDEX IF NOT EXISTS idx_auth_rate_limit_window_start
    ON "03_iam"."60_evt_auth_rate_limit_window" (window_start);

-- DOWN ====

DROP INDEX IF EXISTS "03_iam"."idx_auth_rate_limit_window_start";
DROP TABLE IF EXISTS "03_iam"."60_evt_auth_rate_limit_window";
