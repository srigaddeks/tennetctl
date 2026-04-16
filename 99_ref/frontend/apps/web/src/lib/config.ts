/**
 * Application environment configuration.
 *
 * Reads NEXT_PUBLIC_APP_ENV and maps it to the feature flag environment field.
 * Backend uses APP_ENV with the same values.
 *
 * Mapping:
 *   NEXT_PUBLIC_APP_ENV     →  Feature flag field
 *   "development" / "dev"   →  env_dev
 *   "staging"               →  env_staging
 *   "production" / "prod"   →  env_prod
 */

export type FeatureFlagEnv = "dev" | "staging" | "prod"

const ENV_RAW = (process.env.NEXT_PUBLIC_APP_ENV ?? "development").toLowerCase()

function resolveEnv(raw: string): FeatureFlagEnv {
  if (raw === "production" || raw === "prod") return "prod"
  if (raw === "staging") return "staging"
  return "dev"
}

/** The current feature flag environment (dev/staging/prod) */
export const CURRENT_ENV: FeatureFlagEnv = resolveEnv(ENV_RAW)

/** Human-readable label for the current environment */
export const CURRENT_ENV_LABEL: string =
  CURRENT_ENV === "prod" ? "Production" :
  CURRENT_ENV === "staging" ? "Staging" :
  "Development"

/** Whether the app is running in production */
export const IS_PRODUCTION: boolean = CURRENT_ENV === "prod"
