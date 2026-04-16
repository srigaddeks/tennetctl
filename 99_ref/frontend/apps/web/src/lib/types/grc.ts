// ── Shared Dimension ────────────────────────────────────────────────────────

export interface DimensionResponse {
  id: string
  code: string
  name: string
  description: string
  sort_order: number
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Framework Library ───────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface FrameworkResponse {
  id: string
  tenant_key: string
  framework_code: string
  framework_type_code: string
  type_name: string
  framework_category_code: string
  category_name: string
  scope_org_id: string | null
  scope_workspace_id: string | null
  approval_status: string
  is_marketplace_visible: boolean
  name: string
  description: string
  short_description: string | null
  publisher_type: string | null
  publisher_name: string | null
  logo_url: string | null
  documentation_url: string | null
  latest_version_code: string | null
  control_count: number
  working_control_count: number
  is_active: boolean
  created_at: string
  updated_at: string
  has_pending_changes?: boolean
}

export interface FrameworkListResponse {
  items: FrameworkResponse[]
  total: number
}

export interface SubmitForReviewRequest {
  requirement_ids?: string[]
  control_ids?: string[]
  notes?: string
}

export interface ReviewSelectionResponse {
  framework_id: string
  requirement_ids: string[]
  control_ids: string[]
  notes: string | null
  submitted_at: string | null
}

export interface CreateFrameworkRequest {
  framework_code: string
  framework_type_code: string
  framework_category_code: string
  name: string
  description?: string
  scope_org_id?: string
  scope_workspace_id?: string
  publisher_type?: string
  publisher_name?: string
}

export interface UpdateFrameworkRequest {
  name?: string
  description?: string
  framework_category_code?: string
  is_marketplace_visible?: boolean
}

// ── Versions ────────────────────────────────────────────────────────────────

export interface VersionResponse {
  id: string
  framework_id: string
  version_code: string
  change_severity: string
  lifecycle_state: string
  control_count: number
  previous_version_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by?: string | null
  version_label: string | null
  release_notes: string | null
  change_summary: string | null
  auto_created?: boolean
  auto_change_type?: string
  auto_change_summary?: string
}

export interface VersionListResponse {
  items: VersionResponse[]
  total: number
}

export interface CreateVersionRequest {
  // version_code is auto-generated server-side as the next sequential integer
  version_label?: string
  source_version_id?: string
  change_severity?: string
}

// ── Requirements ────────────────────────────────────────────────────────────

export interface RequirementResponse {
  id: string
  framework_id: string
  requirement_code: string
  sort_order: number
  parent_requirement_id: string | null
  name: string
  description: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RequirementListResponse {
  items: RequirementResponse[]
  total: number
}

export interface CreateRequirementRequest {
  requirement_code: string
  name: string
  description?: string
  sort_order?: number
  parent_requirement_id?: string
}

export interface UpdateRequirementRequest {
  name?: string
  description?: string
  sort_order?: number
}

// ── Controls ────────────────────────────────────────────────────────────────

export interface ControlResponse {
  id: string
  framework_id: string
  requirement_id: string
  tenant_key: string
  control_code: string
  control_category_code: string
  category_name: string
  criticality_code: string
  criticality_name: string
  control_type: string
  automation_potential: string
  name: string
  description: string
  guidance: string | null
  implementation_notes: string | null
  // Rich EAV properties (JSON-backed)
  implementation_guidance: string[] | null
  owner_user_id: string | null
  owner_display_name: string | null
  owner_email: string | null
  responsible_teams: string[] | null
  tags: string[] | null
  // Context
  framework_code: string
  framework_name: string
  requirement_code: string
  requirement_name: string
  test_count: number
  version: number
  is_active: boolean
  created_at: string
  updated_at: string
  // All raw EAV properties
  properties: Record<string, string> | null
}

export interface ControlListResponse {
  items: ControlResponse[]
  total: number
}

export interface CreateControlRequest {
  control_code: string
  requirement_id?: string
  control_category_code: string
  criticality_code: string
  control_type: string
  automation_potential: string
  name: string
  description?: string
  guidance?: string
  implementation_notes?: string
  implementation_guidance?: string[]
  owner_user_id?: string
  responsible_teams?: string[]
  tags?: string[]
}

export interface UpdateControlRequest {
  name?: string
  description?: string
  control_category_code?: string
  criticality_code?: string
  control_type?: string
  automation_potential?: string
  requirement_id?: string
  guidance?: string
  implementation_notes?: string
  implementation_guidance?: string[]
  owner_user_id?: string
  responsible_teams?: string[]
  tags?: string[]
}

// ── Tests ───────────────────────────────────────────────────────────────────

export interface TestResponse {
  id: string
  tenant_key: string
  test_code: string
  test_type_code: string
  test_type_name: string
  integration_type: string
  monitoring_frequency: string
  is_platform_managed: boolean
  name: string
  description: string
  evaluation_rule: string | null
  signal_type: string | null
  integration_guide: string | null
  mapped_control_count: number
  scope_org_id: string | null
  scope_workspace_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TestListResponse {
  items: TestResponse[]
  total: number
}

export interface CreateTestRequest {
  test_code: string
  test_type_code: string
  integration_type: string
  monitoring_frequency: string
  is_platform_managed?: boolean
  name: string
  description?: string
  evaluation_rule?: string
  signal_type?: string
  integration_guide?: string
  scope_org_id?: string
  scope_workspace_id?: string
}

export interface UpdateTestRequest {
  name?: string
  description?: string
  test_type_code?: string
  integration_type?: string
  monitoring_frequency?: string
  is_platform_managed?: boolean
  evaluation_rule?: string
  signal_type?: string
  integration_guide?: string
}

// ── Test Executions ─────────────────────────────────────────────────────────

export interface TestExecutionResponse {
  id: string
  control_test_id: string
  control_id: string | null
  tenant_key: string
  result_status: string
  execution_type: string
  executed_by: string | null
  executed_at: string
  notes: string | null
  evidence_summary: string | null
  score: number | null
  is_active: boolean
  created_at: string
  updated_at: string
  test_code: string | null
  test_name: string | null
}

export interface TestExecutionListResponse {
  items: TestExecutionResponse[]
  total: number
}

export interface CreateTestExecutionRequest {
  control_test_id: string
  control_id?: string
  result_status?: string
  execution_type?: string
  notes?: string
  evidence_summary?: string
  score?: number
}

export interface UpdateTestExecutionRequest {
  result_status?: string
  notes?: string
  evidence_summary?: string
  score?: number
}

// ── Test-Control Mappings ───────────────────────────────────────────────────

export interface TestControlMappingResponse {
  id: string
  control_test_id: string
  control_id: string
  is_primary: boolean
  sort_order: number
  created_at: string
  created_by: string | null
  control_code: string | null
  control_name: string | null
  framework_code: string | null
}

export interface CreateTestControlMappingRequest {
  control_id: string
  is_primary?: boolean
  sort_order?: number
}

// ── Framework Settings ──────────────────────────────────────────────────────

export interface FrameworkSettingResponse {
  key: string
  value: string
}

export interface SetFrameworkSettingRequest {
  value: string
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Risk Registry ───────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface RiskLevelResponse extends DimensionResponse {
  score_min: number
  score_max: number
  color_hex: string
}

export interface RiskResponse {
  id: string
  tenant_key: string
  risk_code: string
  org_id: string
  workspace_id: string | null
  risk_category_code: string
  category_name: string
  risk_level_code: string
  risk_level_name: string
  risk_level_color: string
  treatment_type_code: string
  treatment_type_name: string
  source_type: string
  risk_status: string
  title: string
  description: string
  notes: string | null
  owner_user_id: string | null
  owner_display_name?: string | null
  business_impact: string | null
  inherent_risk_score: number | null
  residual_risk_score: number | null
  linked_control_count: number
  treatment_plan_status: string | null
  treatment_plan_target_date: string | null
  is_active: boolean
  version: number
  created_at: string
  updated_at: string
}

export interface RiskListResponse {
  items: RiskResponse[]
  total: number
}

export interface CreateRiskRequest {
  risk_code: string
  org_id: string
  risk_category_code: string
  risk_level_code: string
  treatment_type_code: string
  source_type: string
  title: string
  description?: string
  workspace_id?: string
  owner_user_id?: string
  business_impact?: string
}

export interface UpdateRiskRequest {
  title?: string
  description?: string
  risk_category_code?: string
  risk_level_code?: string
  treatment_type_code?: string
  risk_status?: string
  notes?: string
  owner_user_id?: string
  business_impact?: string
}

// ── Risk Assessments ────────────────────────────────────────────────────────

export interface RiskAssessmentResponse {
  id: string
  risk_id: string
  assessment_type: string
  likelihood_score: number
  impact_score: number
  risk_score: number
  assessed_by: string
  assessment_notes: string | null
  assessed_at: string
}

export interface CreateRiskAssessmentRequest {
  assessment_type: string
  likelihood_score: number
  impact_score: number
  assessment_notes?: string
}

// ── Treatment Plans ─────────────────────────────────────────────────────────

export interface TreatmentPlanResponse {
  id: string
  risk_id: string
  tenant_key: string
  plan_status: string
  target_date: string | null
  completed_at: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  properties: Record<string, string> | null
}

export interface CreateTreatmentPlanRequest {
  plan_status?: string
  target_date?: string
  plan_description?: string
  action_items?: string
  compensating_control_description?: string
  approver_user_id?: string
  approval_notes?: string
  review_frequency?: string
  properties?: Record<string, string>
}

export interface UpdateTreatmentPlanRequest {
  plan_status?: string
  target_date?: string
  plan_description?: string
  action_items?: string
  compensating_control_description?: string
  approver_user_id?: string
  approval_notes?: string
  review_frequency?: string
  properties?: Record<string, string>
}

// ── Risk-Control Mappings ───────────────────────────────────────────────────

export interface RiskControlMappingResponse {
  id: string
  risk_id: string
  control_id: string
  link_type: string
  notes: string | null
  created_at: string
  control_code: string | null
  control_name: string | null
  risk_code: string | null
  risk_title: string | null
}

export interface CreateRiskControlMappingRequest {
  control_id: string
  link_type?: string
  notes?: string
}

// ── Risk Review Events ──────────────────────────────────────────────────────

export interface RiskReviewEventResponse {
  id: string
  risk_id: string
  event_type: string
  old_status: string | null
  new_status: string | null
  actor_id: string
  comment: string | null
  occurred_at: string
}

export interface CreateRiskReviewEventRequest {
  event_type: string
  comment?: string
}

// ── Risk Heat Map ──
export interface HeatMapCell {
  likelihood_score: number
  impact_score: number
  risk_count: number
  risk_ids: string[]
}

export interface HeatMapResponse {
  cells: HeatMapCell[]
}

// ── Risk Summary / Dashboard KPIs ──
export interface RiskSummaryResponse {
  total_risks: number
  identified_count: number
  assessed_count: number
  treating_count: number
  accepted_count: number
  closed_count: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  open_count: number
  created_this_week: number
  closed_this_week: number
}

// ── Risk Group Assignment ──
export interface RiskGroupAssignmentResponse {
  id: string
  risk_id: string
  group_id: string
  group_name: string | null
  role: string
  assigned_by: string
  assigned_at: string
}

export interface CreateRiskGroupAssignmentRequest {
  group_id: string
  role?: string // 'responsible' | 'accountable' | 'consulted' | 'informed'
}

// ── Risk Appetite ──
export interface RiskAppetiteResponse {
  id: string
  org_id: string
  risk_category_code: string
  appetite_level_code: string
  tolerance_threshold: number
  max_acceptable_score: number
  description: string | null
}

export interface UpsertRiskAppetiteRequest {
  org_id: string
  risk_category_code: string
  appetite_level_code?: string
  tolerance_threshold?: number
  max_acceptable_score?: number
  description?: string
}

// ── Review Scheduling ──
export interface ReviewScheduleResponse {
  id: string
  risk_id: string
  review_frequency: string
  next_review_date: string
  last_reviewed_at: string | null
  last_reviewed_by: string | null
  assigned_reviewer_id: string | null
  is_overdue: boolean
}

export interface UpsertReviewScheduleRequest {
  review_frequency: string
  next_review_date: string
  assigned_reviewer_id?: string
}

export interface OverdueReviewResponse {
  id: string
  risk_id: string
  risk_title: string | null
  review_frequency: string
  next_review_date: string
  assigned_reviewer_id: string | null
  is_overdue: boolean
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Tasks ───────────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface TaskStatusResponse extends DimensionResponse {
  is_terminal: boolean
}

export interface TaskResponse {
  id: string
  tenant_key: string
  org_id: string
  workspace_id: string | null
  task_type_code: string
  task_type_name: string
  priority_code: string
  priority_name: string
  status_code: string
  status_name: string
  is_terminal: boolean
  entity_type: string | null
  entity_id: string | null
  assignee_user_id: string | null
  reporter_user_id: string | null
  due_date: string | null
  start_date: string | null
  completed_at: string | null
  title: string
  description: string | null
  acceptance_criteria: string | null
  resolution_notes: string | null
  estimated_hours: number | null
  actual_hours: number | null
  remediation_plan: string | null
  co_assignee_count: number
  blocker_count: number
  comment_count: number
  is_active: boolean
  version: number
  created_at: string
  updated_at: string
  entity_name?: string
}

export interface TaskListResponse {
  items: TaskResponse[]
  total: number
}

export interface CreateTaskRequest {
  task_type_code: string
  priority_code: string
  org_id: string
  title: string
  description?: string
  workspace_id?: string
  entity_type?: string
  entity_id?: string
  assignee_user_id?: string
  due_date?: string
  start_date?: string
  estimated_hours?: number
  acceptance_criteria?: string
  remediation_plan?: string
}

export interface UpdateTaskRequest {
  title?: string
  description?: string
  priority_code?: string
  status_code?: string
  assignee_user_id?: string
  due_date?: string
  start_date?: string
  estimated_hours?: number
  actual_hours?: number
  acceptance_criteria?: string
  resolution_notes?: string
  remediation_plan?: string
}

export interface TaskTypeSummary {
  task_type_code: string
  task_type_name: string
  count: number
}

export interface TaskSummaryResponse {
  open_count: number
  in_progress_count: number
  pending_verification_count: number
  resolved_count: number
  cancelled_count: number
  overdue_count: number
  resolved_this_week_count: number
  by_type: TaskTypeSummary[]
}

export interface TaskListFilters {
  status_code?: string
  priority_code?: string
  task_type_code?: string
  assignee_user_id?: string
  reporter_user_id?: string
  entity_type?: string
  entity_id?: string
  due_date_from?: string
  due_date_to?: string
  is_overdue?: boolean
  sort_by?: string
  sort_dir?: string
  limit?: number
  offset?: number
}

// ── Task Assignments ────────────────────────────────────────────────────────

export interface TaskAssignmentResponse {
  id: string
  task_id: string
  user_id: string
  role: string
  assigned_at: string
  assigned_by?: string | null
}

export interface CreateTaskAssignmentRequest {
  user_id?: string
  email?: string
  role: string
}

// ── Task Dependencies ───────────────────────────────────────────────────────

export interface TaskDependencyResponse {
  id: string
  blocking_task_id: string
  blocked_task_id: string
  created_at: string
  created_by: string | null
}

export interface TaskDependencyListResponse {
  blockers: TaskDependencyResponse[]
  blocked_by: TaskDependencyResponse[]
}

export interface CreateTaskDependencyRequest {
  blocking_task_id: string
}

// ── Task Events ─────────────────────────────────────────────────────────────

export interface TaskEventResponse {
  id: string
  task_id: string
  event_type: string
  old_value: string | null
  new_value: string | null
  comment: string | null
  actor_id: string
  occurred_at: string
}

export interface CreateTaskEventRequest {
  comment: string
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Framework Deployments ────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface FrameworkDeploymentResponse {
  id: string
  tenant_key: string
  org_id: string
  framework_id: string
  source_framework_id?: string | null
  deployed_version_id: string
  deployment_status: string
  workspace_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  framework_code: string | null
  framework_name: string | null
  framework_description: string | null
  publisher_name: string | null
  logo_url: string | null
  approval_status: string | null
  is_marketplace_visible: boolean
  deployed_version_code: string | null
  deployed_lifecycle_state: string | null
  latest_version_id: string | null
  latest_version_code: string | null
  has_update: boolean
  source_version_id?: string | null
  latest_release_notes?: string | null
  latest_change_severity?: string | null
  latest_change_summary?: string | null
}

export interface FrameworkDeploymentListResponse {
  items: FrameworkDeploymentResponse[]
  total: number
}

export interface DeployFrameworkRequest {
  framework_id: string
  version_id: string
  workspace_id?: string
}

export interface UpdateDeploymentRequest {
  version_id?: string
  deployment_status?: string
}

// ── Spreadsheet Import / Export ──────────────────────────────────────────────

export interface ImportControlError {
  row: number
  key?: string
  field?: string
  message: string
}

export interface ImportControlsResult {
  created: number
  updated: number
  skipped: number
  warnings: string[]
  errors: ImportControlError[]
  dry_run: boolean
}

export interface ImportTaskError {
  row: number
  key?: string
  field?: string
  message: string
}

export interface ImportTasksResult {
  created: number
  updated: number
  skipped: number
  warnings: string[]
  errors: ImportTaskError[]
  dry_run: boolean
}

export interface ImportRiskError {
  row: number
  key?: string
  field?: string
  message: string
}

export interface ImportRisksResult {
  created: number
  updated: number
  skipped: number
  warnings: string[]
  errors: ImportRiskError[]
  dry_run: boolean
}

// ── Framework Bundle ──────────────────────────────────────────────────────────

export interface BundleRequirement {
  requirement_code: string
  name?: string
  description?: string
  sort_order: number
  parent_requirement_code?: string
}

export interface BundleControl {
  control_code: string
  name?: string
  description?: string
  guidance?: string
  implementation_notes?: string
  criticality_code?: string
  control_type?: string
  automation_potential?: string
  control_category_code?: string
  requirement_code?: string
  tags?: string
  implementation_guidance?: string
  responsible_teams?: string
}

export interface BundleGlobalRisk {
  risk_code: string
  title?: string
  description?: string
  short_description?: string
  risk_category_code?: string
  risk_level_code?: string
  inherent_likelihood?: number
  inherent_impact?: number
  mitigation_guidance?: string
  detection_guidance?: string
  linked_control_codes: string[]
}

export interface FrameworkBundle {
  framework_code: string
  framework_type_code: string
  framework_category_code: string
  name?: string
  description?: string
  short_description?: string
  publisher_type?: string
  publisher_name?: string
  documentation_url?: string
  requirements: BundleRequirement[]
  controls: BundleControl[]
  global_risks: BundleGlobalRisk[]
}

export interface BundleImportError {
  section: string
  key?: string
  field?: string
  message: string
}

export interface BundleImportResult {
  framework_created: boolean
  framework_updated: boolean
  requirements_created: number
  requirements_updated: number
  controls_created: number
  controls_updated: number
  global_risks_created: number
  global_risks_updated: number
  risk_control_links_created: number
  warnings: string[]
  errors: BundleImportError[]
  dry_run: boolean
}

// ── Framework Diff ────────────────────────────────────────────────────────────

export interface ControlDiff {
  control_code: string
  control_name?: string | null
  control_description?: string | null
  status: 'added' | 'removed' | 'modified' | 'unchanged'
  field_changes: Record<string, [string | null, string | null]>
}

export interface RequirementDiff {
  requirement_code: string
  name?: string | null
  description?: string | null
  status: 'added' | 'removed' | 'modified' | 'unchanged'
  controls: ControlDiff[]
}

export interface FrameworkDiff {
  framework_id: string
  framework_code: string
  base_label: string
  compare_label: string
  requirements: RequirementDiff[]
  controls_added: number
  controls_removed: number
  controls_modified: number
  controls_unchanged: number
}

// ── Promoted Tests (Sandbox → k-control) ─────────────────────────────────────

export interface PromotedTestResponse {
  id: string
  tenant_key: string
  org_id: string
  promotion_id: string | null
  source_signal_id: string | null
  source_policy_id: string | null
  source_library_id: string | null
  source_pack_id: string | null
  test_code: string
  test_type_code: string
  monitoring_frequency: string
  linked_asset_id: string | null
  connector_type_code: string | null
  connector_name: string | null
  policy_container_code: string | null
  policy_container_name: string | null
  version_number: number
  is_active: boolean
  promoted_by: string
  promoted_at: string
  name: string | null
  description: string | null
  evaluation_rule: string | null
  signal_type: string | null
  integration_guide: string | null
  control_test_id: string | null
  created_at: string
  updated_at: string
}

export interface PromotedTestListResponse {
  items: PromotedTestResponse[]
  total: number
}

export interface UpdatePromotedTestRequest {
  name?: string | null
  description?: string | null
  linked_asset_id?: string | null
}
