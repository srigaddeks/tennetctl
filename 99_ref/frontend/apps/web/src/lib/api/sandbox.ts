import { fetchWithAuth } from "./apiClient"

// ═══════════════════════════════════════════════════════════════════════════════
// ── Types ────────────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface DimensionResponse {
  code: string
  name: string
  description: string | null
  sort_order: number
  is_active: boolean
}

export interface AssetVersionResponse {
  id: string
  connector_type_code: string
  version_code: string
  version_label: string
  is_latest: boolean
  is_active: boolean
}

export interface ConnectorConfigField {
  key: string
  label: string
  type: "text" | "password" | "textarea" | "select" | "boolean" | "number"
  required: boolean
  credential: boolean
  placeholder?: string
  hint?: string
  options?: string[]
  validation?: string
  order: number
}

export interface ConnectorConfigSchemaResponse {
  connector_type_code: string
  fields: ConnectorConfigField[]
  supports_steampipe: boolean
  steampipe_plugin: string | null
}

export interface DatasetTemplateResponse {
  id: string
  code: string
  connector_type_code: string
  name: string
  description: string | null
  json_schema: object
  sample_payload: object
}

export interface ConnectorInstanceResponse {
  id: string
  tenant_key: string
  org_id: string
  workspace_id: string | null
  instance_code: string
  connector_type_code: string
  connector_type_name: string
  connector_category_code: string
  connector_category_name: string
  asset_version_id: string | null
  collection_schedule: string
  last_collected_at: string | null
  health_status: string
  is_active: boolean
  is_draft: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
}

export interface ConnectorListResponse {
  items: ConnectorInstanceResponse[]
  total: number
}

export interface ConnectorTestResult {
  health_status: string
  message: string
  tested_at: string
}

export interface CollectionRunResponse {
  id: string
  tenant_key: string
  org_id: string
  connector_instance_id: string
  status: string
  trigger_type: string
  started_at: string | null
  completed_at: string | null
  assets_discovered: number
  assets_updated: number
  assets_deleted: number
  logs_ingested: number
  error_message: string | null
  triggered_by: string | null
  created_at: string
  updated_at: string
  duration_seconds: number | null
}

export interface CollectionRunListResponse {
  items: CollectionRunResponse[]
  total: number
}

export interface CollectionTriggerResult {
  dataset_id: string
  dataset_code: string
  version_number: number
}

export interface DatasetResponse {
  id: string
  tenant_key: string
  org_id: string
  workspace_id: string | null
  connector_instance_id: string | null
  dataset_code: string
  dataset_source_code: string
  version_number: number
  schema_fingerprint: string | null
  row_count: number | null
  byte_size: number | null
  is_locked: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  asset_ids: string[] | null
}

export interface DatasetListResponse {
  items: DatasetResponse[]
  total: number
}

export interface DatasetDataRecord {
  id: string
  dataset_id: string
  record_seq: number
  record_name: string
  recorded_at: string
  source_asset_id: string | null
  connector_instance_id: string | null
  record_data: Record<string, unknown>
  description: string
}

export interface DatasetRecordsResponse {
  dataset_id: string
  records: DatasetDataRecord[]
  total: number
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Dimensions (/api/v1/sb) ─────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listConnectorCategories(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/sb/dimensions/connector-categories")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list connector categories")
  return data as DimensionResponse[]
}

export async function listConnectorTypes(categoryCode?: string): Promise<DimensionResponse[]> {
  const params = new URLSearchParams()
  if (categoryCode) params.set("category_code", categoryCode)
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/sb/dimensions/connector-types${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list connector types")
  return data as DimensionResponse[]
}

export async function listAssetVersions(connectorTypeCode: string): Promise<AssetVersionResponse[]> {
  const res = await fetchWithAuth(`/api/v1/sb/dimensions/asset-versions?connector_type_code=${connectorTypeCode}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list asset versions")
  return data as AssetVersionResponse[]
}

export async function getConnectorConfigSchema(connectorTypeCode: string): Promise<ConnectorConfigSchemaResponse | null> {
  const res = await fetchWithAuth(`/api/v1/sb/dimensions/connector-config-schema?connector_type_code=${encodeURIComponent(connectorTypeCode)}`)
  if (res.status === 404) return null
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to load connector config schema")
  return data as ConnectorConfigSchemaResponse
}

export async function listSignalStatuses(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/sb/dimensions/signal-statuses")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list signal statuses")
  return data as DimensionResponse[]
}

export async function listDatasetSources(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/sb/dimensions/dataset-sources")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list dataset sources")
  return data as DimensionResponse[]
}

export async function listExecutionStatuses(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/sb/dimensions/execution-statuses")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list execution statuses")
  return data as DimensionResponse[]
}

export async function listThreatSeverities(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/sb/dimensions/threat-severities")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list threat severities")
  return data as DimensionResponse[]
}

export async function listPolicyActionTypes(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/sb/dimensions/policy-action-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list policy action types")
  return data as DimensionResponse[]
}

export async function listLibraryTypes(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/sb/dimensions/library-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list library types")
  return data as DimensionResponse[]
}

export async function listDatasetTemplates(connectorTypeCode?: string): Promise<DatasetTemplateResponse[]> {
  const params = new URLSearchParams()
  if (connectorTypeCode) params.set("connector_type_code", connectorTypeCode)
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/sb/dimensions/dataset-templates${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list dataset templates")
  return data as DatasetTemplateResponse[]
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Connector Instances (/api/v1/sb/connectors) ─────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listConnectors(params?: {
  org_id?: string
  workspace_id?: string
  connector_type_code?: string
  category_code?: string
  health_status?: string
}): Promise<ConnectorListResponse> {
  const qs = new URLSearchParams()
  if (params?.org_id) qs.set("org_id", params.org_id)
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id)
  if (params?.connector_type_code) qs.set("connector_type_code", params.connector_type_code)
  if (params?.category_code) qs.set("category_code", params.category_code)
  if (params?.health_status) qs.set("health_status", params.health_status)
  const query = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/connectors${query ? `?${query}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list connectors")
  return data as ConnectorListResponse
}

export async function getConnector(id: string): Promise<ConnectorInstanceResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/connectors/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get connector")
  return data as ConnectorInstanceResponse
}

export async function preflightTestConnector(payload: {
  connector_type_code: string
  credentials?: Record<string, string>
  properties?: Record<string, string>
}): Promise<ConnectorTestResult> {
  const res = await fetchWithAuth(`/api/v1/sb/connectors/preflight-test`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Preflight test failed")
  return data as ConnectorTestResult
}

export async function createConnector(
  orgId: string,
  payload: {
    instance_code: string
    connector_type_code: string
    workspace_id?: string
    asset_version_id?: string
    collection_schedule?: string
    name?: string
    description?: string
    properties?: Record<string, string>
    credentials?: Record<string, string>
    is_draft?: boolean
  },
): Promise<ConnectorInstanceResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/connectors?org_id=${orgId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create connector")
  return data as ConnectorInstanceResponse
}

export async function updateConnector(
  orgId: string,
  id: string,
  payload: {
    collection_schedule?: string
    is_active?: boolean
    properties?: Record<string, string>
    credentials?: Record<string, string>
  },
): Promise<ConnectorInstanceResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/connectors/${id}?org_id=${orgId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update connector")
  return data as ConnectorInstanceResponse
}

export async function deleteConnector(orgId: string, id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/connectors/${id}?org_id=${orgId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete connector")
  }
}

export async function getConnectorProperties(id: string): Promise<Record<string, string>> {
  const res = await fetchWithAuth(`/api/v1/sb/connectors/${id}/properties`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get connector properties")
  return data as Record<string, string>
}

export async function updateConnectorCredentials(
  orgId: string,
  id: string,
  credentials: Record<string, string>,
): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/connectors/${id}/credentials?org_id=${orgId}`, {
    method: "PATCH",
    body: JSON.stringify({ credentials }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to update credentials")
  }
}

export async function testConnector(id: string): Promise<ConnectorTestResult> {
  const res = await fetchWithAuth(`/api/v1/sb/connectors/${id}/test`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to test connector")
  return data as ConnectorTestResult
}

export async function triggerCollection(orgId: string, connectorId: string): Promise<CollectionRunResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/connectors/${connectorId}/collect?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    body: JSON.stringify({ connector_instance_id: connectorId }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    const detail = data.detail
    const msg = Array.isArray(detail) ? detail.map((d: { msg: string }) => d.msg).join(", ") : (data.error?.message || detail || "Collection failed")
    throw new Error(msg)
  }
  return await res.json() as CollectionRunResponse
}

export async function listCollectionRuns(orgId: string, connectorId?: string): Promise<CollectionRunListResponse> {
  const qs = new URLSearchParams({ org_id: orgId })
  if (connectorId) qs.set("connector_id", connectorId)
  const res = await fetchWithAuth(`/api/v1/sb/collection-runs?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list collection runs")
  return data as CollectionRunListResponse
}

export async function getCollectionRun(orgId: string, runId: string): Promise<CollectionRunResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/collection-runs/${runId}?org_id=${encodeURIComponent(orgId)}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get collection run")
  return data as CollectionRunResponse
}

export interface CollectionSnapshotItem {
  snapshot_id: string
  asset_id: string
  asset_type_code: string
  asset_external_id: string
  status_code: string
  snapshot_number: number
  property_count: number
  collected_at: string
  properties: Record<string, string>
}

export interface CollectionSnapshotsResponse {
  items: CollectionSnapshotItem[]
  total: number
  asset_type_summary: Record<string, number>
}

export async function listCollectionRunSnapshots(
  orgId: string,
  runId: string,
  params?: { asset_type?: string; limit?: number; offset?: number },
): Promise<CollectionSnapshotsResponse> {
  const qs = new URLSearchParams({ org_id: orgId })
  if (params?.asset_type) qs.set("asset_type", params.asset_type)
  if (params?.limit) qs.set("limit", String(params.limit))
  if (params?.offset) qs.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/sb/collection-runs/${runId}/snapshots?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list snapshots")
  return data as CollectionSnapshotsResponse
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Datasets (/api/v1/sb/datasets) ──────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listDatasets(orgId: string, params?: {
  connector_instance_id?: string
  dataset_source_code?: string
  is_locked?: boolean
}): Promise<DatasetListResponse> {
  const qs = new URLSearchParams({ org_id: orgId })
  if (params?.connector_instance_id) qs.set("connector_instance_id", params.connector_instance_id)
  if (params?.dataset_source_code) qs.set("dataset_source_code", params.dataset_source_code)
  if (params?.is_locked !== undefined) qs.set("is_locked", String(params.is_locked))
  const res = await fetchWithAuth(`/api/v1/sb/datasets?${qs.toString()}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list datasets")
  return data as DatasetListResponse
}

export async function getDataset(id: string): Promise<DatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get dataset")
  return data as DatasetResponse
}

export async function getDatasetRecords(id: string, params?: { limit?: number; offset?: number }): Promise<DatasetRecordsResponse> {
  const qs = new URLSearchParams()
  if (params?.limit) qs.set("limit", String(params.limit))
  if (params?.offset) qs.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${id}/records${qs.toString() ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get dataset records")
  return data as DatasetRecordsResponse
}

export async function updateRecordName(
  orgId: string,
  datasetId: string,
  recordId: string,
  recordName: string,
): Promise<DatasetDataRecord> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${datasetId}/records/${recordId}/name?org_id=${encodeURIComponent(orgId)}`, {
    method: "PATCH",
    body: JSON.stringify({ record_name: recordName }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to update name")
  return data as DatasetDataRecord
}

export async function updateRecordDescription(
  orgId: string,
  datasetId: string,
  recordId: string,
  description: string,
): Promise<DatasetDataRecord> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${datasetId}/records/${recordId}/description?org_id=${encodeURIComponent(orgId)}`, {
    method: "PATCH",
    body: JSON.stringify({ description }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to update description")
  return data as DatasetDataRecord
}

export interface GenerationStatus {
  status: "idle" | "started" | "running" | "completed" | "failed"
  processed: number
  total: number
  updated: number
  errors: number
}

export async function generateRecordDescriptions(
  orgId: string,
  datasetId: string,
  assetType?: string,
  connectorType?: string,
): Promise<GenerationStatus> {
  const qs = new URLSearchParams({ org_id: orgId })
  if (assetType) qs.set("asset_type", assetType)
  if (connectorType) qs.set("connector_type", connectorType)
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${datasetId}/generate-descriptions?${qs}`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to generate descriptions")
  return data as GenerationStatus
}

export async function getGenerationStatus(datasetId: string): Promise<GenerationStatus> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${datasetId}/generate-descriptions/status`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to get status")
  return data as GenerationStatus
}

export async function getAssetTypeDescriptions(datasetId: string): Promise<Record<string, string>> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${datasetId}/asset-type-descriptions`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to get descriptions")
  return data as Record<string, string>
}

export async function addDatasetRecords(orgId: string, id: string, payload: {
  records: Record<string, unknown>[]
  source_asset_id?: string
  connector_instance_id?: string
}): Promise<DatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${id}/records?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to add records")
  return data as DatasetResponse
}

export async function createDataset(orgId: string, payload: {
  dataset_source_code: string
  connector_instance_id?: string
  asset_ids?: string[]
  properties?: Record<string, string>
  records?: Record<string, unknown>[]
}): Promise<DatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create dataset")
  return data as DatasetResponse
}

export async function lockDataset(orgId: string, id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${id}/lock?org_id=${encodeURIComponent(orgId)}`, { method: "POST" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to lock dataset")
  }
}

export async function cloneDataset(orgId: string, id: string): Promise<DatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${id}/clone?org_id=${encodeURIComponent(orgId)}`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to clone dataset")
  return data as DatasetResponse
}

export async function deleteDataset(orgId: string, id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${id}?org_id=${encodeURIComponent(orgId)}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete dataset")
  }
}

export async function updateDataset(orgId: string, id: string, payload: {
  properties?: Record<string, string>
  asset_ids?: string[]
  connector_instance_id?: string | null
}): Promise<DatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${id}?org_id=${encodeURIComponent(orgId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to update dataset")
  }
  return res.json()
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Signal Types ────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface SignalResponse {
  id: string
  tenant_key: string
  org_id: string
  workspace_id: string | null
  signal_code: string
  version_number: number
  signal_status_code: string
  signal_status_name: string
  python_hash: string | null
  timeout_ms: number
  max_memory_mb: number
  is_active: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  properties: Record<string, string>
}

export interface SignalListResponse {
  items: SignalResponse[]
  total: number
}

export interface GenerateSignalResponse {
  generated_code: string
  compile_status: string
  test_result: any | null
  caep_event_type: string | null
  risc_event_type: string | null
  custom_event_type: string | null
  iterations_used: number
  signal_name_suggestion: string
  signal_description_suggestion: string
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Signal API (/api/v1/sb/signals) ─────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listSignals(params?: {
  org_id?: string
  workspace_id?: string
  signal_status_code?: string
  search?: string
}): Promise<SignalListResponse> {
  const qs = new URLSearchParams()
  if (params?.org_id) qs.set("org_id", params.org_id)
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id)
  if (params?.signal_status_code) qs.set("signal_status_code", params.signal_status_code)
  if (params?.search) qs.set("search", params.search)
  const q = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/signals${q ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list signals")
  return data as SignalListResponse
}

export async function getSignal(id: string): Promise<SignalResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/signals/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get signal")
  return data as SignalResponse
}

export async function createSignal(payload: {
  signal_code: string
  properties: Record<string, string>
  org_id: string
  workspace_id?: string
}): Promise<SignalResponse> {
  const qs = new URLSearchParams()
  qs.set("org_id", payload.org_id)
  if (payload.workspace_id) qs.set("workspace_id", payload.workspace_id)
  const res = await fetchWithAuth(`/api/v1/sb/signals?${qs.toString()}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      signal_code: payload.signal_code,
      properties: payload.properties,
    }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create signal")
  return data as SignalResponse
}

export async function updateSignal(
  id: string,
  payload: Record<string, any>,
  org_id: string,
): Promise<SignalResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/signals/${id}?org_id=${encodeURIComponent(org_id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update signal")
  return data as SignalResponse
}

export async function deleteSignal(orgId: string, id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/signals/${id}?org_id=${encodeURIComponent(orgId)}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete signal")
  }
}

export async function generateSignal(payload: {
  prompt: string
  connector_type_code: string
  sample_dataset_id?: string
}): Promise<GenerateSignalResponse> {
  const res = await fetchWithAuth("/api/v1/sb/signals/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to generate signal")
  return data as GenerateSignalResponse
}

export async function validateSignal(id: string): Promise<any> {
  const res = await fetchWithAuth(`/api/v1/sb/signals/${id}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to validate signal")
  return data
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Threat Type Types ───────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface ThreatTypeResponse {
  id: string
  threat_code: string
  version_number: number
  severity_code: string
  severity_name: string
  expression_tree: any
  is_active: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  properties: Record<string, string>
}

export interface ThreatTypeListResponse {
  items: ThreatTypeResponse[]
  total: number
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Threat Type API (/api/v1/sb/threat-types) ───────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listThreatTypes(params?: {
  org_id?: string
  workspace_id?: string
  severity_code?: string
  search?: string
}): Promise<ThreatTypeListResponse> {
  const qs = new URLSearchParams()
  if (params?.org_id) qs.set("org_id", params.org_id)
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id)
  if (params?.severity_code) qs.set("severity_code", params.severity_code)
  if (params?.search) qs.set("search", params.search)
  const q = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/threat-types${q ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list threat types")
  return data as ThreatTypeListResponse
}

export async function getThreatType(id: string): Promise<ThreatTypeResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/threat-types/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get threat type")
  return data as ThreatTypeResponse
}

export async function createThreatType(
  payload: Record<string, any> & { org_id: string },
): Promise<ThreatTypeResponse> {
  const { org_id, ...body } = payload
  const res = await fetchWithAuth(`/api/v1/sb/threat-types?org_id=${encodeURIComponent(org_id)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create threat type")
  return data as ThreatTypeResponse
}

export async function updateThreatType(
  id: string,
  org_id: string,
  payload: Record<string, any>,
): Promise<ThreatTypeResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/threat-types/${id}?org_id=${encodeURIComponent(org_id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update threat type")
  return data as ThreatTypeResponse
}

export async function deleteThreatType(id: string, org_id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/threat-types/${id}?org_id=${encodeURIComponent(org_id)}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete threat type")
  }
}

export async function simulateThreat(
  id: string,
  signal_results: Record<string, string>,
): Promise<{ is_triggered: boolean; evaluation_trace: any[] }> {
  const res = await fetchWithAuth(`/api/v1/sb/threat-types/${id}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ signal_results }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to simulate threat")
  return data as { is_triggered: boolean; evaluation_trace: any[] }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Library Types ──────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface LibraryResponse {
  id: string
  library_code: string
  library_type_code: string
  library_type_name: string
  version_number: number
  is_published: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  policy_count: number
  properties: Record<string, string>
}

export interface LibraryListResponse {
  items: LibraryResponse[]
  total: number
}

export interface LibraryPolicyResponse {
  library_id: string
  policy_id: string
  policy_code: string
  policy_name: string | null
  sort_order: number
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Library API (/api/v1/sb/libraries) ─────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listLibraries(params?: {
  org_id?: string
  workspace_id?: string
  library_type_code?: string
  is_published?: boolean
  search?: string
}): Promise<LibraryListResponse> {
  const qs = new URLSearchParams()
  if (params?.org_id) qs.set("org_id", params.org_id)
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id)
  if (params?.library_type_code) qs.set("library_type_code", params.library_type_code)
  if (params?.is_published !== undefined) qs.set("is_published", String(params.is_published))
  if (params?.search) qs.set("search", params.search)
  const q = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/libraries${q ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list libraries")
  return data as LibraryListResponse
}

export async function getLibrary(id: string): Promise<LibraryResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/libraries/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get library")
  return data as LibraryResponse
}

export async function createLibrary(orgId: string, payload: {
  library_code: string
  library_type_code: string
  properties?: Record<string, string>
}): Promise<LibraryResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/libraries?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create library")
  return data as LibraryResponse
}

export async function publishLibrary(orgId: string, id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/libraries/${id}/publish?org_id=${encodeURIComponent(orgId)}`, { method: "POST" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to publish library")
  }
}

export async function cloneLibrary(orgId: string, id: string): Promise<LibraryResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/libraries/${id}/clone?org_id=${encodeURIComponent(orgId)}`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to clone library")
  return data as LibraryResponse
}

export async function deleteLibrary(orgId: string, id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/libraries/${id}?org_id=${encodeURIComponent(orgId)}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete library")
  }
}

export async function listLibraryPolicies(libraryId: string): Promise<LibraryPolicyResponse[]> {
  const res = await fetchWithAuth(`/api/v1/sb/libraries/${libraryId}/policies`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list library policies")
  return data as LibraryPolicyResponse[]
}

export async function addPolicyToLibrary(
  orgId: string,
  libraryId: string,
  payload: { policy_id: string; sort_order?: number },
): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/libraries/${libraryId}/policies?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to add policy to library")
  }
}

export async function removePolicyFromLibrary(orgId: string, libraryId: string, policyId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/libraries/${libraryId}/policies/${policyId}?org_id=${encodeURIComponent(orgId)}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to remove policy from library")
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Promotion Types ────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface PromotionResponse {
  id: string
  signal_id: string | null
  policy_id: string | null
  library_id: string | null
  target_test_id: string | null
  target_test_code: string | null
  source_name: string | null
  source_code: string | null
  promotion_status: string
  promoted_at: string | null
  promoted_by: string | null
  review_notes: string | null
  created_at: string
}

export interface PromotionListResponse {
  items: PromotionResponse[]
  total: number
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Promotion API (/api/v1/sb/promotions) ──────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function promoteSignal(
  signalId: string,
  payload?: { target_test_code?: string; linked_asset_id?: string; workspace_id?: string },
): Promise<PromotionResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/promotions/signals/${signalId}/promote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload ?? {}),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to promote signal")
  return data as PromotionResponse
}

export async function promotePolicy(
  orgId: string,
  policyId: string,
  payload?: { target_test_code?: string; linked_asset_id?: string; workspace_id?: string },
): Promise<PromotionResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/promotions/policies/${policyId}/promote?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload ?? {}),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to promote policy")
  return data as PromotionResponse
}

export async function promoteLibrary(
  libraryId: string,
  payload?: { target_test_code_prefix?: string; linked_asset_id?: string; workspace_id?: string },
): Promise<PromotionResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/promotions/libraries/${libraryId}/promote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload ?? {}),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to promote library")
  return data as PromotionResponse
}

export async function listPromotions(params?: {
  org_id?: string
  promotion_status?: string
}): Promise<PromotionListResponse> {
  const qs = new URLSearchParams()
  if (params?.org_id) qs.set("org_id", params.org_id)
  if (params?.promotion_status) qs.set("promotion_status", params.promotion_status)
  const q = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/promotions${q ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list promotions")
  return data as PromotionListResponse
}

export async function getPromotion(id: string): Promise<PromotionResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/promotions/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get promotion")
  return data as PromotionResponse
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── SSF Stream Types ───────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface SSFStreamResponse {
  id: string
  stream_description: string | null
  receiver_url: string | null
  delivery_method: string
  events_requested: string[]
  stream_status: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SSFStreamListResponse {
  items: SSFStreamResponse[]
  total: number
}

export interface SSFVerifyResult {
  jti: string
  delivered: boolean
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── SSF Stream API (/api/v1/sb/ssf/streams) ────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listSSFStreams(orgId: string): Promise<SSFStreamListResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/ssf/streams?org_id=${encodeURIComponent(orgId)}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list SSF streams")
  return data as SSFStreamListResponse
}

export async function getSSFStream(id: string): Promise<SSFStreamResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/ssf/streams/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get SSF stream")
  return data as SSFStreamResponse
}

export async function createSSFStream(payload: {
  orgId: string
  delivery_method: string
  receiver_url?: string
  events_requested: string[]
  description?: string
  authorization_header?: string
}): Promise<SSFStreamResponse> {
  const { orgId, ...body } = payload
  const res = await fetchWithAuth(`/api/v1/sb/ssf/streams?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create SSF stream")
  return data as SSFStreamResponse
}

export async function updateSSFStreamStatus(id: string, orgId: string, status: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/ssf/streams/${id}/status?org_id=${encodeURIComponent(orgId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stream_status: status }),
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to update stream status")
  }
}

export async function deleteSSFStream(id: string, orgId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/ssf/streams/${id}?org_id=${encodeURIComponent(orgId)}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete SSF stream")
  }
}

export async function verifySSFStream(id: string): Promise<SSFVerifyResult> {
  const res = await fetchWithAuth(`/api/v1/sb/ssf/streams/${id}/verify`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to verify SSF stream")
  return data as SSFVerifyResult
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Policies (/api/v1/sb/policies) ──────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface PolicyActionConfig {
  action_type_code: string
  action_type_name?: string
  config: Record<string, unknown>
}

export interface PolicyResponse {
  id: string
  policy_code: string
  version_number: number
  threat_type_id: string
  threat_code: string
  actions: PolicyActionConfig[]
  is_enabled: boolean
  cooldown_minutes: number
  is_active: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  properties: Record<string, string>
}

export interface PolicyListResponse {
  items: PolicyResponse[]
  total: number
}

export interface PolicyTestResult {
  actions_simulated: PolicyActionConfig[]
  would_fire: boolean
}

export async function listPolicies(params?: {
  org_id?: string
  workspace_id?: string
  threat_type_id?: string
  is_enabled?: boolean
  search?: string
}): Promise<PolicyListResponse> {
  const qs = new URLSearchParams()
  if (params?.org_id) qs.set("org_id", params.org_id)
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id)
  if (params?.threat_type_id) qs.set("threat_type_id", params.threat_type_id)
  if (params?.is_enabled !== undefined) qs.set("is_enabled", String(params.is_enabled))
  if (params?.search) qs.set("search", params.search)
  const query = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/policies?${query}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list policies")
  return data as PolicyListResponse
}

export async function getPolicy(orgId: string, id: string): Promise<PolicyResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/policies/${id}?org_id=${encodeURIComponent(orgId)}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get policy")
  return data as PolicyResponse
}

export async function createPolicy(payload: {
  org_id: string
  workspace_id?: string
  policy_code: string
  threat_type_id: string
  actions: PolicyActionConfig[]
  cooldown_minutes?: number
  is_enabled?: boolean
  properties?: Record<string, string>
}): Promise<PolicyResponse> {
  const { org_id, ...body } = payload
  const res = await fetchWithAuth(`/api/v1/sb/policies?org_id=${encodeURIComponent(org_id)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create policy")
  return data as PolicyResponse
}

export async function updatePolicy(
  id: string,
  org_id: string,
  payload: {
    actions?: PolicyActionConfig[]
    cooldown_minutes?: number
    is_enabled?: boolean
    properties?: Record<string, string>
  },
): Promise<PolicyResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/policies/${id}?org_id=${encodeURIComponent(org_id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update policy")
  return data as PolicyResponse
}

export async function enablePolicy(id: string, org_id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/policies/${id}/enable?org_id=${encodeURIComponent(org_id)}`, { method: "POST" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to enable policy")
  }
}

export async function disablePolicy(id: string, org_id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/policies/${id}/disable?org_id=${encodeURIComponent(org_id)}`, { method: "POST" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to disable policy")
  }
}

export async function testPolicy(orgId: string, id: string): Promise<PolicyTestResult> {
  const res = await fetchWithAuth(`/api/v1/sb/policies/${id}/test?org_id=${encodeURIComponent(orgId)}`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to test policy")
  return data as PolicyTestResult
}

export async function deletePolicy(id: string, org_id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/policies/${id}?org_id=${encodeURIComponent(org_id)}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete policy")
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Runs (/api/v1/sb/runs) ──────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface RunResponse {
  id: string
  signal_id: string
  signal_code: string
  signal_name: string | null
  dataset_id: string | null
  live_session_id: string | null
  execution_status_code: string
  execution_status_name: string
  result_code: string | null
  result_summary: string | null
  result_details: unknown | null
  execution_time_ms: number | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface RunListResponse {
  items: RunResponse[]
  total: number
}

export interface BatchExecuteResponse {
  signal_results: Record<string, RunResponse>
  threat_evaluations: Array<Record<string, unknown>>
  policy_executions: Array<Record<string, unknown>>
}

export async function executeSignal(orgId: string, payload: {
  signal_id: string
  dataset_id: string
}): Promise<RunResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/runs?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to execute signal")
  return data as RunResponse
}

export async function triggerSignalRun(signalId: string, orgId?: string): Promise<RunResponse> {
  const qs = orgId ? `?org_id=${encodeURIComponent(orgId)}` : ""
  const res = await fetchWithAuth(`/api/v1/sb/signals/${signalId}/execute${qs}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to trigger signal run")
  return data as RunResponse
}

export async function batchExecute(orgId: string, payload: {
  signal_ids: string[]
  dataset_id: string
}): Promise<BatchExecuteResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/runs/batch?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to batch execute signals")
  return data as BatchExecuteResponse
}

export async function listRuns(params?: {
  org_id?: string
  signal_id?: string
  result_code?: string
  limit?: number
}): Promise<RunListResponse> {
  const qs = new URLSearchParams()
  if (params?.org_id) qs.set("org_id", params.org_id)
  if (params?.signal_id) qs.set("signal_id", params.signal_id)
  if (params?.result_code) qs.set("result_code", params.result_code)
  if (params?.limit !== undefined) qs.set("limit", String(params.limit))
  const query = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/runs${query ? `?${query}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list runs")
  return data as RunListResponse
}

export async function getRun(id: string): Promise<RunResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/runs/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get run")
  return data as RunResponse
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Live Sessions (/api/v1/sb/live-sessions) ────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface LiveSessionResponse {
  id: string
  connector_instance_id: string
  connector_name: string | null
  connector_type_code: string | null
  session_status: string
  duration_minutes: number
  started_at: string | null
  expires_at: string | null
  data_points_received: number
  bytes_received: number
  signals_executed: number
  threats_evaluated: number
  created_at: string
  attached_signals: { signal_id: string; signal_code: string; signal_name: string | null }[]
  attached_threats: { threat_type_id: string; threat_code: string; threat_name: string | null }[]
}

export interface LiveSessionListResponse {
  items: LiveSessionResponse[]
  total: number
}

export interface LiveStreamEvent {
  sequence: number
  event_type: string
  payload: unknown
  timestamp: string
}

export interface LiveStreamResponse {
  events: LiveStreamEvent[]
  has_more: boolean
}

export async function startLiveSession(payload: {
  org_id: string
  connector_instance_id: string
  signal_ids?: string[]
  threat_type_ids?: string[]
  duration_minutes?: number
  workspace_id: string
}): Promise<LiveSessionResponse> {
  const qs = new URLSearchParams()
  qs.set("org_id", payload.org_id)
  const res = await fetchWithAuth(`/api/v1/sb/live-sessions?${qs}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      connector_instance_id: payload.connector_instance_id,
      signal_ids: payload.signal_ids,
      threat_type_ids: payload.threat_type_ids,
      duration_minutes: payload.duration_minutes,
      workspace_id: payload.workspace_id,
    }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to start live session")
  return data as LiveSessionResponse
}

export async function listLiveSessions(params?: {
  org_id?: string
  session_status?: string
  connector_instance_id?: string
}): Promise<LiveSessionListResponse> {
  const qs = new URLSearchParams()
  if (params?.org_id) qs.set("org_id", params.org_id)
  if (params?.session_status) qs.set("session_status", params.session_status)
  if (params?.connector_instance_id) qs.set("connector_instance_id", params.connector_instance_id)
  const query = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/live-sessions${query ? `?${query}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list live sessions")
  return data as LiveSessionListResponse
}

export async function getLiveSession(id: string): Promise<LiveSessionResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/live-sessions/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get live session")
  return data as LiveSessionResponse
}

export async function getLiveStream(
  id: string,
  params?: { after_sequence?: number; limit?: number },
): Promise<LiveStreamResponse> {
  const qs = new URLSearchParams()
  if (params?.after_sequence !== undefined) qs.set("after_sequence", String(params.after_sequence))
  if (params?.limit !== undefined) qs.set("limit", String(params.limit))
  const query = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/live-sessions/${id}/stream${query ? `?${query}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get live stream")
  return data as LiveStreamResponse
}

export async function pauseSession(org_id: string, id: string): Promise<void> {
  const qs = new URLSearchParams({ org_id })
  const res = await fetchWithAuth(`/api/v1/sb/live-sessions/${id}/pause?${qs}`, { method: "POST" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to pause session")
  }
}

export async function resumeSession(org_id: string, id: string): Promise<void> {
  const qs = new URLSearchParams({ org_id })
  const res = await fetchWithAuth(`/api/v1/sb/live-sessions/${id}/resume?${qs}`, { method: "POST" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to resume session")
  }
}

export async function stopSession(org_id: string, id: string): Promise<void> {
  const qs = new URLSearchParams({ org_id })
  const res = await fetchWithAuth(`/api/v1/sb/live-sessions/${id}/stop?${qs}`, { method: "POST" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to stop session")
  }
}

export async function saveSessionDataset(
  id: string,
  payload: { dataset_code: string; properties?: Record<string, string> },
): Promise<DatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/live-sessions/${id}/save-dataset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to save session dataset")
  return data as DatasetResponse
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Stats ──────────────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface SandboxStats {
  connector_count: number
  dataset_count: number
  signal_count: number
  threat_type_count: number
  policy_count: number
  library_count: number
  active_policy_count: number
  recent_run_count_24h: number
  active_session_count: number
}

export async function getSandboxStats(orgId: string, workspaceId?: string): Promise<SandboxStats> {
  const params = new URLSearchParams({ org_id: orgId })
  if (workspaceId) params.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`/api/v1/sb/dimensions/stats?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to load stats")
  return data as SandboxStats
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Provider Definitions (/api/v1/sb/providers) ─────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface ProviderDefinitionResponse {
  code: string
  name: string
  description: string | null
  current_api_version: string | null
  supports_log_collection: boolean
  supports_steampipe: boolean
  config_schema: Record<string, unknown>
  is_active: boolean
}

export interface ProviderListResponse {
  items: ProviderDefinitionResponse[]
  total: number
}

export async function listProviders(params?: { is_active?: boolean }): Promise<ProviderListResponse> {
  const qs = new URLSearchParams()
  if (params?.is_active !== undefined) qs.set("is_active", String(params.is_active))
  const query = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/providers${query ? `?${query}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list providers")
  return data as ProviderListResponse
}

export async function getProvider(providerCode: string): Promise<ProviderDefinitionResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/providers/${providerCode}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get provider")
  return data as ProviderDefinitionResponse
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Asset Connectors (/api/v1/sb/asset-connectors) ──────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface AssetConnectorResponse {
  id: string
  tenant_key: string
  org_id: string
  instance_code: string
  provider_definition_code: string
  provider_version_code: string | null
  collection_schedule: string
  last_collected_at: string | null
  health_status: string
  consecutive_failures: number
  is_active: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
}

export interface AssetConnectorListResponse {
  items: AssetConnectorResponse[]
  total: number
}

export interface CreateAssetConnectorPayload {
  provider_code: string
  provider_version_code?: string
  connection_config: Record<string, string>
  credentials: Record<string, string>
  collection_schedule?: string
  name?: string
  description?: string
}

export interface UpdateAssetConnectorPayload {
  connection_config?: Record<string, string>
  credentials?: Record<string, string>
  collection_schedule?: string
  is_active?: boolean
  name?: string
  description?: string
}

export interface AssetConnectorTestResponse {
  success: boolean
  health_status: string
  message: string
  details: Record<string, unknown> | null
  tested_at: string
}

export async function listAssetConnectors(
  orgId: string,
  params?: { provider_code?: string; health_status?: string; offset?: number; limit?: number },
): Promise<AssetConnectorListResponse> {
  const qs = new URLSearchParams({ org_id: orgId })
  if (params?.provider_code) qs.set("provider_code", params.provider_code)
  if (params?.health_status) qs.set("health_status", params.health_status)
  if (params?.offset !== undefined) qs.set("offset", String(params.offset))
  if (params?.limit !== undefined) qs.set("limit", String(params.limit))
  const res = await fetchWithAuth(`/api/v1/sb/asset-connectors?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list asset connectors")
  return data as AssetConnectorListResponse
}

export async function createAssetConnector(
  orgId: string,
  payload: CreateAssetConnectorPayload,
): Promise<AssetConnectorResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/asset-connectors?org_id=${orgId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create asset connector")
  return data as AssetConnectorResponse
}

export async function getAssetConnector(orgId: string, connectorId: string): Promise<AssetConnectorResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/asset-connectors/${connectorId}?org_id=${orgId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get asset connector")
  return data as AssetConnectorResponse
}

export async function updateAssetConnector(
  orgId: string,
  connectorId: string,
  payload: UpdateAssetConnectorPayload,
): Promise<AssetConnectorResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/asset-connectors/${connectorId}?org_id=${orgId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update asset connector")
  return data as AssetConnectorResponse
}

export async function deleteAssetConnector(orgId: string, connectorId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/asset-connectors/${connectorId}?org_id=${orgId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete asset connector")
  }
}

export async function testAssetConnector(orgId: string, connectorId: string): Promise<AssetConnectorTestResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/asset-connectors/${connectorId}/test?org_id=${orgId}`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to test asset connector")
  return data as AssetConnectorTestResponse
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Assets (/api/v1/sb/assets) ──────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface AssetResponse {
  id: string
  tenant_key: string
  org_id: string
  workspace_id: string | null
  connector_instance_id: string
  provider_code: string
  asset_type_code: string
  asset_external_id: string
  parent_asset_id: string | null
  status_code: string
  current_snapshot_id: string | null
  last_collected_at: string | null
  consecutive_misses: number
  created_at: string
  updated_at: string
  is_deleted: boolean
  properties: Record<string, string> | null
}

export interface AssetListResponse {
  items: AssetResponse[]
  total: number
}

export interface AssetPropertyResponse {
  id: string
  asset_id: string
  property_key: string
  property_value: string
  value_type: string
  collected_at: string
}

export async function listAssets(orgId: string, params?: {
  connector_id?: string
  asset_type?: string
  status?: string
  limit?: number
  offset?: number
}): Promise<AssetListResponse> {
  const qs = new URLSearchParams({ org_id: orgId })
  if (params?.connector_id) qs.set("connector_id", params.connector_id)
  if (params?.asset_type) qs.set("asset_type", params.asset_type)
  if (params?.status) qs.set("status", params.status)
  if (params?.limit) qs.set("limit", String(params.limit))
  if (params?.offset) qs.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/sb/assets?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list assets")
  return data as AssetListResponse
}

export async function getAssetProperties(orgId: string, assetId: string): Promise<AssetPropertyResponse[]> {
  const res = await fetchWithAuth(`/api/v1/sb/assets/${assetId}/properties?org_id=${orgId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get asset properties")
  return data as AssetPropertyResponse[]
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Signal Test Suite & Live Execution ──────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface TestCaseResult {
  case_id: string | null
  scenario_name: string | null
  expected: string        // pass | fail | warning
  actual: string | null   // pass | fail | warning | error
  passed: boolean
  error: string | null
  execution_time_ms: number
  diff: Record<string, unknown>
}

export interface TestSuiteResponse {
  signal_id: string
  test_dataset_id: string | null
  total_cases: number
  passed: number
  failed: number
  errored: number
  pass_rate: number
  results: TestCaseResult[]
}

export interface ExecuteLiveResponse {
  signal_id: string
  status: string            // completed | failed | timeout
  result_code: string | null
  result_summary: string
  result_details: Array<Record<string, unknown>>
  metadata: Record<string, unknown>
  dataset_row_count: number
  execution_time_ms: number
}

export async function runSignalTestSuite(
  signalId: string,
  orgId: string,
  testDatasetId?: string,
): Promise<TestSuiteResponse> {
  const qs = new URLSearchParams({ org_id: orgId })
  if (testDatasetId) qs.set("test_dataset_id", testDatasetId)
  const res = await fetchWithAuth(`/api/v1/sb/signals/${signalId}/test-suite?${qs}`, {
    method: "POST",
  })
  const raw = await res.text()
  let data: unknown = null
  if (raw) {
    try {
      data = JSON.parse(raw)
    } catch {
      data = raw
    }
  }
  if (!res.ok) {
    if (typeof data === "object" && data !== null) {
      const errorPayload = data as { detail?: string; error?: { message?: string } }
      throw new Error(errorPayload.detail || errorPayload.error?.message || "Failed to run test suite")
    }
    throw new Error(typeof data === "string" && data ? data : "Failed to run test suite")
  }
  return (data ?? {}) as TestSuiteResponse
}

export async function executeSignalLive(
  signalId: string,
  orgId: string,
  payload: {
    configurable_args?: Record<string, unknown>
    connector_instance_id?: string
  },
): Promise<ExecuteLiveResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/signals/${signalId}/execute-live?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to execute live")
  return data as ExecuteLiveResponse
}

// ─── Dataset Compose & Schema Drift ─────────────────────────────────────────

export interface DatasetSourceRef {
  source_type: "asset_properties" | "asset_snapshot"
  connector_instance_id?: string
  asset_type_filter?: string
  asset_id?: string
  snapshot_id?: string
  limit?: number
}

export interface ComposeDatasetRequest {
  name: string
  description?: string
  workspace_id?: string
  sources: DatasetSourceRef[]
}

export interface ComposeDatasetResponse {
  dataset_id: string
  name: string
  source_count: number
  row_count: number
  schema_fingerprint: string
  asset_type_keys: string[]
}

export interface FieldChange {
  field: string
  change_type: "added" | "removed" | "type_changed"
  old_value?: unknown
  new_value?: unknown
}

export interface SchemaDriftResponse {
  has_drift: boolean
  old_fingerprint: string
  new_fingerprint: string
  changes: FieldChange[]
}

export async function composeDataset(orgId: string, payload: ComposeDatasetRequest): Promise<ComposeDatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/compose?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to compose dataset")
  return data as ComposeDatasetResponse
}

export interface SmartPreviewResponse {
  records: Array<Record<string, unknown>>
  total: number
  by_type: Record<string, number>
  composition_summary: string
  type_details: string[]
}

export async function smartPreviewDataset(orgId: string, payload: {
  connector_instance_id: string
  samples_per_type?: number
}): Promise<SmartPreviewResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/smart-preview?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, name: "preview" }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to preview")
  return data as SmartPreviewResponse
}

export async function smartComposeDataset(orgId: string, payload: {
  connector_instance_id: string
  name: string
  description?: string
  workspace_id?: string
  samples_per_type?: number
}): Promise<ComposeDatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/smart-compose?org_id=${encodeURIComponent(orgId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to smart-compose dataset")
  return data as ComposeDatasetResponse
}

export async function checkSchemaDrift(orgId: string, datasetId: string): Promise<SchemaDriftResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/datasets/${datasetId}/schema-drift?org_id=${encodeURIComponent(orgId)}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to check schema drift")
  return data as SchemaDriftResponse
}

// ─── Asset Type Discovery + Sample Preview ──────────────────────────────────

export interface AssetTypeInfo {
  asset_type_code: string
  asset_count: number
  sample_property_keys: string[]
}

export interface ConnectorAssetTypesResponse {
  connector_instance_id: string
  connector_name: string | null
  provider_code: string | null
  asset_types: AssetTypeInfo[]
}

export interface AssetSampleRecord {
  asset_id: string
  asset_external_id: string | null
  properties: Record<string, unknown>
}

export interface AssetSamplesResponse {
  connector_instance_id: string
  asset_type_code: string
  total_count: number
  property_keys: string[]
  samples: AssetSampleRecord[]
}

export async function getConnectorAssetTypes(
  orgId: string,
  connectorInstanceId: string,
): Promise<ConnectorAssetTypesResponse> {
  const qs = new URLSearchParams({ org_id: orgId, connector_instance_id: connectorInstanceId })
  const res = await fetchWithAuth(`/api/v1/sb/datasets/asset-types?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to get asset types")
  return data as ConnectorAssetTypesResponse
}

export async function getAssetSamples(
  orgId: string,
  connectorInstanceId: string,
  assetTypeCode: string,
  limit = 5,
): Promise<AssetSamplesResponse> {
  const qs = new URLSearchParams({
    org_id: orgId,
    connector_instance_id: connectorInstanceId,
    asset_type_code: assetTypeCode,
    limit: String(limit),
  })
  const res = await fetchWithAuth(`/api/v1/sb/datasets/asset-samples?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to get samples")
  return data as AssetSamplesResponse
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── AI Dataset Agent (/api/v1/ai/dataset-agent) ─────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface FieldExplanation {
  field_name: string
  data_type: string
  description: string
  compliance_relevance: "high" | "medium" | "low" | "none"
  example_signal_uses: string[]
  anomaly_indicators: string[]
}

export interface RecommendedSignal {
  signal_name: string
  description: string
  fields_used: string[]
  expected_result: string
}

export interface ExplainRecordResponse {
  asset_type: string
  record_summary: string
  total_fields: number
  fields: FieldExplanation[]
  recommended_signals: RecommendedSignal[]
}

export interface ExplainDatasetResponse {
  dataset_summary: string
  asset_type: string
  schema_fields: Array<{
    field_name: string
    data_type: string
    description: string
    compliance_relevance: string
    value_distribution: string
  }>
  record_explanations: Array<{
    record_index: number
    summary: string
    compliance_status: string
    key_observations: string[]
  }>
  overall_quality: string
  improvement_suggestions: string[]
}

export interface ComposeTestDataResponse {
  asset_type: string
  schema_summary: string
  generated_records: Array<Record<string, unknown>>
  coverage_notes: string
}

export interface DatasetGap {
  gap: string
  severity: string
  suggestion: string
}

export interface EnhanceDatasetResponse {
  quality_score: number
  strengths: string[]
  gaps: DatasetGap[]
  missing_scenarios: Array<{
    scenario_name: string
    description: string
    expected_result: string
    example_record: Record<string, unknown>
  }>
  field_coverage: Record<string, { unique_values_seen: number; coverage: string; suggestion: string }>
}

export async function aiExplainRecord(payload: {
  record_data: Record<string, unknown>
  asset_type_hint?: string
  connector_type?: string
}): Promise<ExplainRecordResponse> {
  const res = await fetchWithAuth("/api/v1/ai/dataset-agent/explain-record", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to explain record")
  return data as ExplainRecordResponse
}

export async function aiExplainDataset(payload: {
  records: Array<Record<string, unknown>>
  asset_type?: string
  connector_type?: string
}): Promise<ExplainDatasetResponse> {
  const res = await fetchWithAuth("/api/v1/ai/dataset-agent/explain-dataset", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to explain dataset")
  return data as ExplainDatasetResponse
}

export async function aiComposeTestData(payload: {
  property_keys: string[]
  sample_records: Array<Record<string, unknown>>
  asset_type: string
  connector_type?: string
  record_count?: number
}): Promise<ComposeTestDataResponse> {
  const res = await fetchWithAuth("/api/v1/ai/dataset-agent/compose-test-data", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to compose test data")
  return data as ComposeTestDataResponse
}

export async function aiEnhanceDataset(payload: {
  records: Array<Record<string, unknown>>
  asset_type?: string
  connector_type?: string
}): Promise<EnhanceDatasetResponse> {
  const res = await fetchWithAuth("/api/v1/ai/dataset-agent/enhance-dataset", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to enhance dataset")
  return data as EnhanceDatasetResponse
}


// ═══════════════════════════════════════════════════════════════════════════════
// Global Dataset Library
// ═══════════════════════════════════════════════════════════════════════════════

export interface GlobalDatasetResponse {
  id: string
  global_code: string
  connector_type_code: string
  connector_type_name: string | null
  version_number: number
  json_schema: Record<string, unknown>
  sample_payload: Record<string, unknown>[]
  record_count: number
  publish_status: string
  is_featured: boolean
  download_count: number
  source_dataset_id: string | null
  source_org_id: string | null
  published_by: string | null
  published_at: string | null
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  tags: string | null
  category: string | null
  collection_query: string | null
  compatible_asset_types: string | null
  changelog: string | null
}

export interface GlobalDatasetListResponse {
  items: GlobalDatasetResponse[]
  total: number
}

export interface GlobalDatasetStatsResponse {
  total: number
  by_connector_type: Record<string, number>
  by_category: Record<string, number>
  featured_count: number
}

export interface PullResultResponse {
  local_dataset_id: string
  dataset_code: string
  version_number: number
  global_source_code: string
  global_source_version: number
}

export async function publishGlobalDataset(orgId: string, payload: {
  source_dataset_id: string
  global_code: string
  properties: Record<string, string>
}): Promise<GlobalDatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-datasets/publish?org_id=${orgId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to publish dataset")
  return data as GlobalDatasetResponse
}

export async function listGlobalDatasets(params?: {
  connector_type_code?: string
  category?: string
  search?: string
  publish_status?: string
  is_featured?: boolean
  sort_by?: string
  sort_dir?: string
  limit?: number
  offset?: number
}): Promise<GlobalDatasetListResponse> {
  const qs = new URLSearchParams()
  if (params?.connector_type_code) qs.set("connector_type_code", params.connector_type_code)
  if (params?.category) qs.set("category", params.category)
  if (params?.search) qs.set("search", params.search)
  if (params?.publish_status) qs.set("publish_status", params.publish_status)
  if (params?.is_featured !== undefined) qs.set("is_featured", String(params.is_featured))
  if (params?.sort_by) qs.set("sort_by", params.sort_by)
  if (params?.sort_dir) qs.set("sort_dir", params.sort_dir)
  if (params?.limit !== undefined) qs.set("limit", String(params.limit))
  if (params?.offset !== undefined) qs.set("offset", String(params.offset))
  const query = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/global-datasets${query ? `?${query}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list global datasets")
  return data as GlobalDatasetListResponse
}

export async function getGlobalDataset(id: string): Promise<GlobalDatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-datasets/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get global dataset")
  return data as GlobalDatasetResponse
}

export async function getGlobalDatasetStats(): Promise<GlobalDatasetStatsResponse> {
  const res = await fetchWithAuth("/api/v1/sb/global-datasets/stats")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get global dataset stats")
  return data as GlobalDatasetStatsResponse
}

export async function updateGlobalDataset(id: string, orgId: string, payload: {
  properties?: Record<string, string>
  is_featured?: boolean
}): Promise<GlobalDatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-datasets/${id}?org_id=${orgId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update global dataset")
  return data as GlobalDatasetResponse
}

export async function deprecateGlobalDataset(id: string, orgId: string): Promise<GlobalDatasetResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-datasets/${id}/deprecate?org_id=${orgId}`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to deprecate global dataset")
  return data as GlobalDatasetResponse
}

export async function pullGlobalDataset(id: string, payload: {
  org_id: string
  workspace_id?: string
  connector_instance_id?: string
  custom_dataset_code?: string
}): Promise<PullResultResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-datasets/${id}/pull`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to pull global dataset")
  return data as PullResultResponse
}


// ═══════════════════════════════════════════════════════════════════════════════
// Global Control Test Library
// ═══════════════════════════════════════════════════════════════════════════════

export interface SignalBundle {
  signal_code: string
  name: string
  description: string
  python_source: string
  connector_type_codes: string[]
  timeout_ms: number
  max_memory_mb: number
  source_prompt: string | null
}

export interface ThreatTypeBundle {
  threat_code: string
  name: string
  description: string
  severity_code: string
  expression_tree: Record<string, unknown>
  mitigation_guidance: string | null
}

export interface PolicyBundle {
  policy_code: string
  name: string
  description: string
  actions: Record<string, unknown>[]
  cooldown_minutes: number
}

export interface TestDatasetRecord {
  record_name: string | null
  description: string | null
  record_data: Record<string, unknown>
  expected_result: string | null
  scenario_name: string | null
}

export interface TestDatasetBundle {
  dataset_code: string
  name: string
  description: string
  record_count: number
  records: TestDatasetRecord[]
  json_schema: Record<string, unknown> | null
}

export interface DatasetTemplateBundle {
  connector_type_code: string
  json_schema: Record<string, unknown>
  sample_records: Record<string, unknown>[]
  field_count: number
}

export interface ControlTestBundle {
  signals: SignalBundle[]
  threat_type: ThreatTypeBundle | null
  policy: PolicyBundle | null
  test_dataset: TestDatasetBundle | null
  dataset_template: DatasetTemplateBundle | null
}

export interface GlobalControlTestResponse {
  id: string
  global_code: string
  connector_type_code: string
  connector_type_name: string | null
  version_number: number
  bundle: ControlTestBundle
  source_signal_id: string | null
  source_policy_id: string | null
  source_library_id: string | null
  source_org_id: string | null
  linked_dataset_code: string | null
  publish_status: string
  is_featured: boolean
  download_count: number
  signal_count: number
  published_by: string | null
  published_at: string | null
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  tags: string | null
  category: string | null
  changelog: string | null
  compliance_references: string | null
}

export interface GlobalControlTestListResponse {
  items: GlobalControlTestResponse[]
  total: number
}

export interface GlobalControlTestStatsResponse {
  total: number
  by_connector_type: Record<string, number>
  by_category: Record<string, number>
  featured_count: number
}

export interface DeployResultResponse {
  created_signal_ids: string[]
  created_threat_type_id: string | null
  created_policy_id: string | null
  created_test_dataset_id: string | null
  created_dataset_template_id: string | null
  signal_count: number
  global_source_code: string
  global_source_version: number
}

export async function publishGlobalControlTest(orgId: string, payload: {
  source_signal_id: string
  global_code: string
  linked_dataset_code?: string
  properties: Record<string, string>
}): Promise<GlobalControlTestResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-tests/publish?org_id=${orgId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to publish control test")
  return data as GlobalControlTestResponse
}

export async function listGlobalControlTests(params?: {
  connector_type_code?: string
  category?: string
  search?: string
  linked_dataset_code?: string
  publish_status?: string
  limit?: number
  offset?: number
}): Promise<GlobalControlTestListResponse> {
  const qs = new URLSearchParams()
  if (params?.connector_type_code) qs.set("connector_type_code", params.connector_type_code)
  if (params?.category) qs.set("category", params.category)
  if (params?.search) qs.set("search", params.search)
  if (params?.linked_dataset_code) qs.set("linked_dataset_code", params.linked_dataset_code)
  if (params?.publish_status) qs.set("publish_status", params.publish_status)
  if (params?.limit !== undefined) qs.set("limit", String(params.limit))
  if (params?.offset !== undefined) qs.set("offset", String(params.offset))
  const query = qs.toString()
  const res = await fetchWithAuth(`/api/v1/sb/global-tests${query ? `?${query}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list global control tests")
  return data as GlobalControlTestListResponse
}

export async function getGlobalControlTest(id: string): Promise<GlobalControlTestResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-tests/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get global control test")
  return data as GlobalControlTestResponse
}

export async function getGlobalControlTestStats(): Promise<GlobalControlTestStatsResponse> {
  const res = await fetchWithAuth("/api/v1/sb/global-tests/stats")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get control test stats")
  return data as GlobalControlTestStatsResponse
}

export async function updateGlobalControlTest(id: string, orgId: string, payload: {
  properties?: Record<string, string>
  is_featured?: boolean
}): Promise<GlobalControlTestResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-tests/${id}?org_id=${orgId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update control test")
  return data as GlobalControlTestResponse
}

export async function deprecateGlobalControlTest(id: string, orgId: string): Promise<GlobalControlTestResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-tests/${id}/deprecate?org_id=${orgId}`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to deprecate control test")
  return data as GlobalControlTestResponse
}

export async function deployGlobalControlTest(id: string, payload: {
  org_id: string
  workspace_id: string
  connector_instance_id?: string
}): Promise<DeployResultResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/global-tests/${id}/deploy`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to deploy control test")
  return data as DeployResultResponse
}

export async function listDeployedGlobalTestIds(orgId: string, workspaceId?: string): Promise<string[]> {
  const q = new URLSearchParams({ org_id: orgId })
  if (workspaceId) q.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`/api/v1/sb/global-tests/deployed-ids?${q}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get deployed IDs")
  return data as string[]
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Live Test (/api/v1/sb/live-test) ─────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface LiveTestResultItem {
  asset_id: string
  asset_external_id: string
  asset_type: string
  signal_id: string
  signal_code: string
  signal_name: string | null
  result: string
  summary: string
  details: Record<string, unknown>[]
  execution_time_ms: number
}

export interface LiveTestResponse {
  connector_id: string
  total_assets: number
  total_signals: number
  total_tests: number
  passed: number
  failed: number
  warnings: number
  errors: number
  results: LiveTestResultItem[]
}

export async function runLiveTest(
  orgId: string,
  workspaceId: string,
  payload: { connector_id: string; signal_ids: string[] },
): Promise<LiveTestResponse> {
  const qs = new URLSearchParams()
  qs.set("org_id", orgId)
  qs.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`/api/v1/sb/live-test?${qs.toString()}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to run live test")
  return data as LiveTestResponse
}
