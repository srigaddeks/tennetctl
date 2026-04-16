// ── Assessment Dimensions ─────────────────────────────────────────────────────

export interface AssessmentDimension {
  id: string
  code: string
  name: string
  description: string | null
  sort_order: number
  is_active: boolean
}

// ── Assessments ──────────────────────────────────────────────────────────────

export interface AssessmentResponse {
  id: string
  tenant_key: string
  assessment_code: string
  org_id: string
  workspace_id: string | null
  framework_id: string | null
  assessment_type_code: string
  assessment_status_code: string
  lead_assessor_id: string | null
  scheduled_start: string | null
  scheduled_end: string | null
  actual_start: string | null
  actual_end: string | null
  is_locked: boolean
  assessment_type_name: string | null
  assessment_status_name: string | null
  name: string | null
  description: string | null
  scope_notes: string | null
  finding_count: number
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
}

export interface AssessmentListResponse {
  items: AssessmentResponse[]
  total: number
  limit: number
  offset: number
}

export interface CreateAssessmentRequest {
  org_id: string
  workspace_id?: string
  framework_id?: string
  assessment_type_code: string
  lead_assessor_id?: string
  scheduled_start?: string
  scheduled_end?: string
  name: string
  description?: string
  scope_notes?: string
}

export interface UpdateAssessmentRequest {
  assessment_type_code?: string
  assessment_status_code?: string
  lead_assessor_id?: string
  scheduled_start?: string
  scheduled_end?: string
  name?: string
  description?: string
  scope_notes?: string
}

export interface AssessmentSummaryMatrix {
  open: number
  in_remediation: number
  verified_closed: number
  accepted: number
  disputed: number
}

export interface AssessmentSummaryResponse {
  assessment_id: string
  total_findings: number
  matrix: Record<string, AssessmentSummaryMatrix>
}

// ── Findings ─────────────────────────────────────────────────────────────────

export interface FindingResponse {
  id: string
  assessment_id: string
  control_id: string | null
  risk_id: string | null
  severity_code: string
  finding_type: string
  finding_status_code: string
  assigned_to: string | null
  remediation_due_date: string | null
  severity_name: string | null
  finding_status_name: string | null
  title: string | null
  description: string | null
  recommendation: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
}

export interface FindingListResponse {
  items: FindingResponse[]
  total: number
}

export interface CreateFindingRequest {
  severity_code: string
  finding_type: string
  title: string
  description?: string
  recommendation?: string
  control_id?: string
  risk_id?: string
  assigned_to?: string
  remediation_due_date?: string
}

export interface UpdateFindingRequest {
  finding_status_code?: string
  severity_code?: string
  assigned_to?: string
  remediation_due_date?: string
  title?: string
  description?: string
  recommendation?: string
}

// ── Finding Responses ────────────────────────────────────────────────────────

export interface FindingResponseResponse {
  id: string
  finding_id: string
  responder_id: string
  response_text: string | null
  responded_at: string
  created_at: string
}

export interface FindingResponseListResponse {
  items: FindingResponseResponse[]
}

export interface CreateFindingResponseRequest {
  response_text: string
}
