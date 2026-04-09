export interface ApiOk<T> { ok: true; data: T }
export interface ApiError { ok: false; error: { code: string; message: string } }
export type ApiResponse<T> = ApiOk<T> | ApiError

export interface TokenPair {
  access_token: string
  token_type: string
  refresh_token: string
  expires_in: number
  session_id: string
}

export interface MeData {
  user_id: string
  username: string | null
  email: string | null
  account_type: string
  session_id: string
}

export interface UserData {
  id: string
  username: string | null
  email: string | null
  account_type: string
  auth_type: string
  is_active: boolean
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface OrgData {
  id: string
  name: string | null
  slug: string | null
  is_active: boolean
  description?: string | null
}

export interface WorkspaceData {
  id: string
  org_id: string
  name: string | null
  slug: string | null
  is_active: boolean
}

export interface OrgMembership {
  id: string
  user_id: string
  org_id: string
  org_slug: string | null
  org_name: string | null
  org_is_active: boolean
  created_at: string
}

export interface WorkspaceMembership {
  id: string
  user_id: string
  workspace_id: string
  org_id: string
  workspace_slug: string | null
  workspace_name: string | null
  workspace_is_active: boolean
  created_at: string
}

export interface ListData<T> {
  items: T[]
  total: number
  limit?: number
  offset?: number
}

// ---------------------------------------------------------------------------
// kbio — Behavioral Biometrics
// ---------------------------------------------------------------------------

export type KbioScoreAction = 'allow' | 'monitor' | 'challenge' | 'block'
export type KbioTrustLevel = 'high' | 'medium' | 'low' | 'critical'
export type KbioBaselineQuality = 'insufficient' | 'forming' | 'established' | 'strong'

export type KbioSessionData = {
  id: string
  sdk_session_id: string
  user_hash: string
  device_uuid: string
  status: string
  trust_level: KbioTrustLevel
  drift_score: number
  anomaly_score: number
  trust_score: number
  bot_score: number
  baseline_quality: KbioBaselineQuality
  pulse_count: number
  created_at: string
  last_active_at: string
}

export type KbioUserProfileData = {
  user_hash: string
  baseline_quality: KbioBaselineQuality
  profile_maturity: number
  total_sessions: number
  total_events: number
  last_seen_at: string
  centroids: KbioCentroidData[]
  credential_profiles: number
  device_count: number
}

export type KbioCentroidData = {
  id: string
  modality: string
  platform: string
  input_method: string
  weight: number
  sample_count: number
  created_at: string
}

export type KbioDeviceData = {
  device_uuid: string
  fingerprint_hash: string
  user_agent: string
  platform: string
  trust_status: string
  first_seen_at: string
  last_seen_at: string
  session_count: number
}

export type KbioPolicyData = {
  id: string
  code: string
  name: string
  description: string
  category: string
  default_action: string
  severity: number
  conditions: Record<string, unknown>
  default_config: Record<string, unknown>
  tags: string
  version: string
  is_active: boolean
  created_at: string
}

export type KbioOverviewStats = {
  total_sessions: number
  active_sessions: number
  avg_drift_score: number
  anomaly_alerts: number
  bot_detections: number
  avg_trust_score: number
}

export type KbioDriftTrendPoint = {
  timestamp: number
  drift_score: number
  confidence: number
}
