"use client"

import { useEffect, useState, useCallback, useMemo, useRef } from "react"
import { useRouter, useSearchParams, usePathname } from "next/navigation"
import {
  Button,
  Input,
  Label,
  Badge,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  Plug,
  Search,
  Plus,
  Trash2,
  AlertTriangle,
  RefreshCw,
  Play,
  Pencil,
  X,
  Cloud,
  Database,
  Server,
  Shield,
  Globe,
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  MinusCircle,
  ArrowLeft,
  Loader2,
  Copy,
  ChevronDown,
  ChevronUp,
  History,
  Eye,
  ExternalLink,
} from "lucide-react"
import { copyToClipboard } from "@/lib/utils/sandbox-helpers"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"
import { useAccess } from "@/components/providers/AccessProvider"
import Link from "next/link"
import {
  listConnectors,
  listConnectorCategories,
  listConnectorTypes,
  getConnectorConfigSchema,
  getConnectorProperties,
  updateConnector,
  updateConnectorCredentials,
  deleteConnector,
  testConnector,
  triggerCollection,
  listCollectionRuns,
  listAssets,
  createDataset,
  addDatasetRecords,
} from "@/lib/api/sandbox"
import type {
  ConnectorInstanceResponse,
  DimensionResponse,
  ConnectorTestResult,
  ConnectorConfigField,
  CollectionRunResponse,
  AssetResponse,
} from "@/lib/api/sandbox"
import { CreateConnectorDialog } from "@/components/connectors/CreateConnectorDialog"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function formatDatetime(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  })
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}


const CATEGORY_ICONS: Record<string, typeof Cloud> = {
  cloud_provider: Cloud,
  saas: Globe,
  database: Database,
  infrastructure: Server,
  security: Shield,
  monitoring: Activity,
}

function getCategoryIcon(categoryCode: string) {
  return CATEGORY_ICONS[categoryCode] || Plug
}

const HEALTH_CONFIG: Record<string, { label: string; color: string; icon: typeof CheckCircle2 }> = {
  healthy: { label: "Healthy", color: "text-green-500 border-green-500/30 bg-green-500/5", icon: CheckCircle2 },
  degraded: { label: "Degraded", color: "text-yellow-500 border-yellow-500/30 bg-yellow-500/5", icon: AlertCircle },
  error: { label: "Error", color: "text-red-500 border-red-500/30 bg-red-500/5", icon: XCircle },
  unchecked: { label: "Unchecked", color: "text-muted-foreground border-border bg-muted/30", icon: MinusCircle },
}

function getHealthConfig(status: string) {
  return HEALTH_CONFIG[status] || HEALTH_CONFIG.unchecked
}

const SCHEDULE_OPTIONS = [
  { value: "manual", label: "Manual" },
]

function scheduleLabel(cron: string): string {
  const found = SCHEDULE_OPTIONS.find((o) => o.value === cron)
  return found ? found.label : cron
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit Connector Dialog
// ─────────────────────────────────────────────────────────────────────────────

function EditConnectorDialog({
  connector,
  orgId,
  onSaved,
  onClose,
}: {
  connector: ConnectorInstanceResponse | null
  orgId: string
  onSaved: () => void
  onClose: () => void
}) {
  const [schedule, setSchedule] = useState("manual")
  const [isActive, setIsActive] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Config schema fields
  const [configFields, setConfigFields] = useState<ConnectorConfigField[]>([])
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [loadingFields, setLoadingFields] = useState(false)

  // Test connection state
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ health_status: string; message: string } | null>(null)

  useEffect(() => {
    if (connector) {
      setSchedule(connector.collection_schedule)
      setIsActive(connector.is_active)
      setSaving(false)
      setError(null)
      setSuccessMsg(null)
      setTestResult(null)
      setFieldValues({})
      setLoadingFields(true)

      // Load schema + current properties in parallel
      Promise.all([
        getConnectorConfigSchema(connector.connector_type_code).catch(() => null),
        getConnectorProperties(connector.id).catch((): Record<string, string> => ({})),
      ]).then(([schema, props]) => {
        if (schema) {
          setConfigFields(schema.fields)
          // Pre-populate non-credential fields with current values
          const initial: Record<string, string> = {}
          for (const f of schema.fields) {
            if (!f.credential && props[f.key]) {
              initial[f.key] = props[f.key]
            }
            // Credential fields stay blank — user must re-enter
          }
          setFieldValues(initial)
        }
      }).finally(() => setLoadingFields(false))
    }
  }, [connector])

  if (!connector) return null

  const propFields = configFields.filter((f) => !f.credential)
  const credFields = configFields.filter((f) => f.credential)

  function setField(key: string, value: string) {
    setFieldValues((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    setSuccessMsg(null)
    setTestResult(null)
    try {
      // 1. Update connector settings (schedule, active)
      const propUpdates: Record<string, string> = {}
      for (const f of propFields) {
        const val = fieldValues[f.key]?.trim()
        if (val !== undefined) propUpdates[f.key] = val
      }
      await updateConnector(orgId, connector!.id, {
        collection_schedule: schedule,
        is_active: isActive,
        properties: Object.keys(propUpdates).length > 0 ? propUpdates : undefined,
      })

      // 2. Update credentials if any were filled in
      const credUpdates: Record<string, string> = {}
      for (const f of credFields) {
        const val = fieldValues[f.key]?.trim()
        if (val) credUpdates[f.key] = val
      }
      if (Object.keys(credUpdates).length > 0) {
        await updateConnectorCredentials(orgId, connector!.id, credUpdates)
      }

      onSaved()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save")
    } finally {
      setSaving(false)
    }
  }

  async function handleTest() {
    setTesting(true)
    setTestResult(null)
    setError(null)
    try {
      const result = await testConnector(connector!.id)
      setTestResult(result)
      onSaved() // Reload connectors list to reflect health change
    } catch (e) {
      setTestResult({ health_status: "error", message: e instanceof Error ? e.message : "Test failed" })
    } finally {
      setTesting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Pencil className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>Edit Connector</DialogTitle>
              <DialogDescription>
                <code className="text-xs font-mono text-foreground/60">{connector.instance_code}</code>
                <span className="mx-2 text-foreground/30">·</span>
                <span className="text-xs text-foreground/50">{connector.connector_type_name}</span>
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        {loadingFields ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-5">
            {/* Connection Config — non-credential fields */}
            {propFields.length > 0 && (
              <div className="space-y-3">
                <p className="text-xs font-semibold text-foreground/70 uppercase tracking-wider">Connection Config</p>
                {propFields.map((field) => (
                  <div key={field.key} className="space-y-1">
                    <Label className="text-xs">{field.label}{field.required && <span className="text-red-500 ml-0.5">*</span>}</Label>
                    <Input
                      type={field.type === "password" ? "password" : "text"}
                      placeholder={field.placeholder ?? ""}
                      value={fieldValues[field.key] ?? ""}
                      onChange={(e) => setField(field.key, e.target.value)}
                      className="h-8 text-xs"
                    />
                    {field.hint && <p className="text-[10px] text-foreground/40">{field.hint}</p>}
                  </div>
                ))}
              </div>
            )}

            {/* Credentials — always show as password, blank = keep existing */}
            {credFields.length > 0 && (
              <div className="space-y-3">
                <p className="text-xs font-semibold text-foreground/70 uppercase tracking-wider">Credentials</p>
                <p className="text-[10px] text-foreground/40">Leave blank to keep existing values.</p>
                {credFields.map((field) => (
                  <div key={field.key} className="space-y-1">
                    <Label className="text-xs">{field.label}{field.required && <span className="text-red-500 ml-0.5">*</span>}</Label>
                    <Input
                      type="password"
                      placeholder={field.placeholder ?? `Enter ${field.label.toLowerCase()}…`}
                      value={fieldValues[field.key] ?? ""}
                      onChange={(e) => setField(field.key, e.target.value)}
                      className="h-8 text-xs font-mono"
                    />
                    {field.hint && <p className="text-[10px] text-foreground/40">{field.hint}</p>}
                  </div>
                ))}
              </div>
            )}

            <Separator />

            {/* Settings */}
            <div className="space-y-3">
              <p className="text-xs font-semibold text-foreground/70 uppercase tracking-wider">Settings</p>
              <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                <Clock className="h-3.5 w-3.5 shrink-0" />
                <span>Collection: <strong className="text-foreground">Manual</strong></span>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="edit-is-active"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="h-4 w-4 rounded border-input"
                />
                <Label htmlFor="edit-is-active" className="text-xs cursor-pointer">Active</Label>
              </div>
            </div>
          </div>
        )}

        {/* Status messages */}
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        {successMsg && <p className="rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-xs text-green-600 mt-2">{successMsg}</p>}
        {testResult && (
          <div className={`rounded-lg border px-3 py-2 text-xs mt-2 ${testResult.health_status === "healthy" ? "border-green-500/30 bg-green-500/10 text-green-600" : "border-red-500/30 bg-red-500/10 text-red-500"}`}>
            <span className="font-medium">{testResult.health_status === "healthy" ? "Connected" : "Failed"}</span> — {testResult.message}
          </div>
        )}

        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving || testing}>Cancel</Button>
          <Button variant="outline" size="sm" onClick={handleTest} disabled={saving || testing}>
            {testing ? (
              <span className="flex items-center gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin" />
                Testing…
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <Activity className="h-3 w-3" />
                Test Connection
              </span>
            )}
          </Button>
          <Button size="sm" onClick={handleSave} disabled={saving || testing}>
            {saving ? (
              <span className="flex items-center gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin" />
                Saving…
              </span>
            ) : "Save All"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Delete Confirmation Dialog
// ─────────────────────────────────────────────────────────────────────────────

function DeleteConnectorDialog({
  connector,
  onConfirm,
  onClose,
}: {
  connector: ConnectorInstanceResponse | null
  onConfirm: (id: string) => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!connector) return null

  async function confirm() {
    setDeleting(true)
    setError(null)
    try {
      await onConfirm(connector!.id)
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete")
      setDeleting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-red-500/10 p-2.5"><AlertTriangle className="h-4 w-4 text-red-500" /></div>
            <div>
              <DialogTitle>Delete Connector</DialogTitle>
              <DialogDescription>This action cannot be undone. All associated datasets will be orphaned.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <p className="text-sm">
          Are you sure you want to delete <strong>{connector.name || connector.instance_code}</strong>{" "}
          (<code className="text-xs font-mono">{connector.connector_type_name}</code>)?
        </p>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={deleting}>Cancel</Button>
          <Button variant="destructive" size="sm" onClick={confirm} disabled={deleting}>
            {deleting ? (
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Deleting...
              </span>
            ) : "Delete Connector"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Test Result Toast
// ─────────────────────────────────────────────────────────────────────────────

function TestResultBanner({ result, onDismiss }: { result: ConnectorTestResult; onDismiss: () => void }) {
  const health = getHealthConfig(result.health_status)
  const Icon = health.icon

  return (
    <div className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${health.color}`}>
      <Icon className="h-4 w-4 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{health.label}</p>
        <p className="text-xs opacity-80">{result.message}</p>
      </div>
      <button onClick={onDismiss} className="shrink-0 rounded-lg p-1 hover:bg-black/10 dark:hover:bg-white/10 transition-colors">
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Collection History Panel
// ─────────────────────────────────────────────────────────────────────────────

function CollectionRunRow({
  run,
  orgId,
  connectorId,
  statusConfig,
  formatDuration,
}: {
  run: CollectionRunResponse
  orgId: string
  connectorId: string
  statusConfig: Record<string, { color: string; icon: typeof CheckCircle2 }>
  formatDuration: (seconds: number | null) => string
}) {
  const router = useRouter()
  const [expanded, setExpanded] = useState(false)
  const [assets, setAssets] = useState<AssetResponse[]>([])
  const [assetsLoading, setAssetsLoading] = useState(false)
  const [assetsError, setAssetsError] = useState<string | null>(null)
  const [expandedAssetId, setExpandedAssetId] = useState<string | null>(null)
  const [sendingToDataset, setSendingToDataset] = useState(false)
  const [datasetSuccess, setDatasetSuccess] = useState<string | null>(null)

  // "Send to Dataset" picker state
  const [pickerOpen, setPickerOpen] = useState(false)
  const [pickerLoading, setPickerLoading] = useState(false)
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set())
  const [datasetName, setDatasetName] = useState("")

  const canShowActions = run.status === "completed" || run.status === "partial"
  const cfg = statusConfig[run.status] ?? statusConfig.queued
  const StatusIcon = cfg.icon

  const loadAssets = useCallback(async () => {
    if (assets.length > 0) return
    setAssetsLoading(true)
    setAssetsError(null)
    try {
      const data = await listAssets(orgId, { connector_id: connectorId, limit: 500 })
      setAssets(data.items)
    } catch (e) {
      setAssetsError(e instanceof Error ? e.message : "Failed to load assets")
    } finally {
      setAssetsLoading(false)
    }
  }, [orgId, connectorId, assets.length])

  const handleToggleAssets = useCallback(() => {
    if (!expanded) loadAssets()
    setExpanded((v) => !v)
  }, [expanded, loadAssets])

  // Group assets by type for the picker
  const assetsByType = useMemo(() => {
    const grouped: Record<string, AssetResponse[]> = {}
    for (const a of assets) {
      if (!grouped[a.asset_type_code]) grouped[a.asset_type_code] = []
      grouped[a.asset_type_code].push(a)
    }
    return grouped
  }, [assets])

  const handleOpenPicker = useCallback(async () => {
    setPickerOpen(true)
    setPickerLoading(true)
    setDatasetSuccess(null)
    setAssetsError(null)
    const dateStr = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    setDatasetName(`GitHub Collection - ${dateStr}`)
    try {
      let assetList = assets
      if (assetList.length === 0) {
        const data = await listAssets(orgId, { connector_id: connectorId, limit: 500 })
        assetList = data.items
        setAssets(assetList)
      }
      // Default: select all types
      const types = new Set(assetList.map((a) => a.asset_type_code))
      setSelectedTypes(types)
    } catch (e) {
      setAssetsError(e instanceof Error ? e.message : "Failed to load assets")
    } finally {
      setPickerLoading(false)
    }
  }, [orgId, connectorId, assets])

  const selectedAssetCount = useMemo(() => {
    return assets.filter((a) => selectedTypes.has(a.asset_type_code)).length
  }, [assets, selectedTypes])

  const handleConfirmSendToDataset = useCallback(async () => {
    setSendingToDataset(true)
    try {
      const filtered = assets.filter((a) => selectedTypes.has(a.asset_type_code))
      if (filtered.length === 0) {
        setDatasetSuccess("No assets selected")
        setSendingToDataset(false)
        return
      }
      const ds = await createDataset(orgId, {
        dataset_source_code: "connector_pull",
        connector_instance_id: connectorId,
        properties: {
          name: datasetName.trim() || `Collection ${run.id.slice(0, 8)}`,
          description: `From collection run ${run.id.slice(0, 8)} — ${selectedTypes.size} asset type(s), ${filtered.length} record(s)`,
        },
      })
      await addDatasetRecords(orgId, ds.id, {
        records: filtered.map((a) => ({
          ...(a.properties ?? {}),
          _asset_type: a.asset_type_code,
          _external_id: a.asset_external_id,
        })),
        connector_instance_id: connectorId,
      })
      setPickerOpen(false)
      setDatasetSuccess(ds.id)
      setTimeout(() => router.push("/sandbox/datasets"), 1200)
    } catch (e) {
      setAssetsError(e instanceof Error ? e.message : "Failed to create dataset")
    } finally {
      setSendingToDataset(false)
    }
  }, [orgId, connectorId, run.id, assets, selectedTypes, datasetName, router])

  return (
    <div>
      <div className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-[11px] hover:bg-muted/10 transition-colors">
        <Badge variant="outline" className={`text-[10px] gap-1 shrink-0 ${cfg.color}`}>
          <StatusIcon className={`h-2.5 w-2.5 ${run.status === "running" ? "animate-spin" : ""}`} />
          {run.status}
        </Badge>
        <Badge variant="outline" className="text-[10px] text-muted-foreground shrink-0">
          {run.trigger_type}
        </Badge>
        <span className="text-muted-foreground shrink-0">
          {run.started_at ? timeAgo(run.started_at) : "pending"}
        </span>
        <span className="text-muted-foreground shrink-0">
          {formatDuration(run.duration_seconds)}
        </span>
        <span className="text-foreground shrink-0" title="Assets discovered / updated">
          {run.assets_discovered}↑ {run.assets_updated}↻
        </span>
        {run.error_message && (
          <span className="text-red-500 truncate min-w-0" title={run.error_message}>
            {run.error_message.length > 40 ? run.error_message.slice(0, 40) + "…" : run.error_message}
          </span>
        )}
        {canShowActions && (
          <div className="flex items-center gap-1 ml-auto shrink-0">
            <button
              onClick={handleToggleAssets}
              title="View Assets"
              className="rounded p-0.5 hover:bg-muted/20 transition-colors"
            >
              <Eye className="h-3 w-3 text-muted-foreground hover:text-foreground" />
            </button>
            <button
              onClick={handleOpenPicker}
              disabled={sendingToDataset}
              title="Send to Dataset"
              className="rounded p-0.5 hover:bg-muted/20 transition-colors disabled:opacity-40"
            >
              {sendingToDataset ? (
                <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
              ) : (
                <Database className="h-3 w-3 text-muted-foreground hover:text-foreground" />
              )}
            </button>
          </div>
        )}
      </div>

      {datasetSuccess && datasetSuccess !== "No assets to send" && (
        <div className="mx-2 mb-1 flex items-center gap-1.5 rounded-md bg-green-500/10 border border-green-500/20 px-2 py-1 text-[10px] text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-2.5 w-2.5" />
          Dataset created — redirecting to datasets...
        </div>
      )}
      {datasetSuccess === "No assets to send" && (
        <div className="mx-2 mb-1 flex items-center gap-1.5 rounded-md bg-yellow-500/10 border border-yellow-500/20 px-2 py-1 text-[10px] text-yellow-600 dark:text-yellow-400">
          <AlertCircle className="h-2.5 w-2.5" />
          No assets found for this connector
        </div>
      )}

      {expanded && (
        <div className="mx-2 mb-1 rounded-lg border border-border bg-background/50 p-2">
          {assetsLoading ? (
            <div className="flex items-center justify-center py-3">
              <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
            </div>
          ) : assetsError ? (
            <p className="text-[10px] text-red-500 py-1">{assetsError}</p>
          ) : assets.length === 0 ? (
            <p className="text-[10px] text-muted-foreground py-1 text-center">No assets found</p>
          ) : (
            <div>
              <div className="grid grid-cols-[1fr_1.5fr_0.5fr] gap-1 px-1 pb-1 text-[9px] font-medium text-muted-foreground uppercase tracking-wider border-b border-border mb-1">
                <span>Type</span>
                <span>External ID</span>
                <span className="text-right">Props</span>
              </div>
              <div className="max-h-48 overflow-y-auto space-y-px">
                {assets.map((asset) => {
                  const propCount = asset.properties ? Object.keys(asset.properties).length : 0
                  const isExpanded = expandedAssetId === asset.id
                  return (
                    <div key={asset.id}>
                      <button
                        onClick={() => setExpandedAssetId(isExpanded ? null : asset.id)}
                        className="w-full grid grid-cols-[1fr_1.5fr_0.5fr] gap-1 px-1 py-1 text-[10px] rounded hover:bg-muted/10 transition-colors text-left"
                      >
                        <span className="truncate font-medium">{asset.asset_type_code}</span>
                        <span className="truncate text-muted-foreground">{asset.asset_external_id}</span>
                        <span className="text-right text-muted-foreground">{propCount}</span>
                      </button>
                      {isExpanded && asset.properties && propCount > 0 && (
                        <div className="ml-2 mb-1 rounded border border-border/50 bg-muted/5 p-1.5">
                          {Object.entries(asset.properties).map(([k, v]) => (
                            <div key={k} className="flex gap-2 text-[9px] py-0.5">
                              <span className="text-muted-foreground font-mono shrink-0">{k}</span>
                              <span className="truncate">{v}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
              <div className="text-[9px] text-muted-foreground text-right pt-1 border-t border-border mt-1">
                {assets.length} asset{assets.length !== 1 ? "s" : ""}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Send to Dataset picker dialog */}
      {pickerOpen && (
        <Dialog open onOpenChange={(o) => { if (!o) setPickerOpen(false) }}>
          <DialogContent className="sm:max-w-md max-h-[70vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Send to Dataset</DialogTitle>
              <DialogDescription>
                Select which asset types to include. Each selected type becomes records in the dataset.
              </DialogDescription>
            </DialogHeader>
            <Separator className="my-2" />
            {pickerLoading ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label className="text-xs">Dataset Name</Label>
                  <Input
                    value={datasetName}
                    onChange={(e) => setDatasetName(e.target.value)}
                    placeholder="e.g. GitHub Repos - March 2026"
                    className="h-8 text-xs"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">Asset Types</Label>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setSelectedTypes(new Set(Object.keys(assetsByType)))}
                        className="text-[10px] text-blue-500 hover:underline"
                      >Select all</button>
                      <button
                        onClick={() => setSelectedTypes(new Set())}
                        className="text-[10px] text-muted-foreground hover:underline"
                      >Clear</button>
                    </div>
                  </div>
                  <div className="space-y-1 rounded-lg border border-border p-2">
                    {Object.entries(assetsByType).sort((a, b) => b[1].length - a[1].length).map(([type, items]) => (
                      <label key={type} className="flex items-center gap-2 rounded px-1.5 py-1 hover:bg-muted/10 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedTypes.has(type)}
                          onChange={(e) => {
                            const next = new Set(selectedTypes)
                            if (e.target.checked) next.add(type)
                            else next.delete(type)
                            setSelectedTypes(next)
                          }}
                          className="h-3.5 w-3.5 rounded border-input"
                        />
                        <span className="text-xs flex-1">{type.replace("github_", "").replace(/_/g, " ")}</span>
                        <Badge variant="outline" className="text-[10px] text-muted-foreground">{items.length}</Badge>
                      </label>
                    ))}
                  </div>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  {selectedAssetCount} record{selectedAssetCount !== 1 ? "s" : ""} from {selectedTypes.size} type{selectedTypes.size !== 1 ? "s" : ""} will be added to the dataset.
                </p>
                {assetsError && <p className="text-xs text-red-500">{assetsError}</p>}
              </div>
            )}
            <DialogFooter className="mt-3 gap-2 sm:gap-2">
              <Button variant="outline" size="sm" onClick={() => setPickerOpen(false)} disabled={sendingToDataset}>Cancel</Button>
              <Button size="sm" onClick={handleConfirmSendToDataset} disabled={sendingToDataset || selectedAssetCount === 0}>
                {sendingToDataset ? (
                  <span className="flex items-center gap-1.5">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Creating…
                  </span>
                ) : `Create Dataset (${selectedAssetCount} records)`}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}

function CollectionHistoryPanel({
  orgId,
  connectorId,
}: {
  orgId: string
  connectorId: string
}) {
  const [runs, setRuns] = useState<CollectionRunResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadRuns = useCallback(async () => {
    try {
      const data = await listCollectionRuns(orgId, connectorId)
      setRuns(data.items)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load runs")
    } finally {
      setLoading(false)
    }
  }, [orgId, connectorId])

  useEffect(() => {
    loadRuns()
  }, [loadRuns])

  // Auto-refresh when there are active runs
  const hasActiveRun = runs.some((r) => r.status === "running" || r.status === "queued")
  useEffect(() => {
    if (!hasActiveRun) return
    const interval = setInterval(loadRuns, 5000)
    return () => clearInterval(interval)
  }, [hasActiveRun, loadRuns])

  const statusConfig: Record<string, { color: string; icon: typeof CheckCircle2 }> = {
    completed: { color: "text-green-500 border-green-500/30 bg-green-500/5", icon: CheckCircle2 },
    running:   { color: "text-blue-500 border-blue-500/30 bg-blue-500/5", icon: Loader2 },
    queued:    { color: "text-muted-foreground border-border bg-muted/5", icon: Clock },
    partial:   { color: "text-yellow-500 border-yellow-500/30 bg-yellow-500/5", icon: AlertCircle },
    failed:    { color: "text-red-500 border-red-500/30 bg-red-500/5", icon: XCircle },
    cancelled: { color: "text-muted-foreground border-border bg-muted/5", icon: MinusCircle },
  }

  function formatDuration(seconds: number | null): string {
    if (seconds === null) return "—"
    if (seconds < 60) return `${seconds}s`
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`
  }

  return (
    <div className="rounded-xl border border-border bg-muted/5 p-3 mt-2">
      <div className="flex items-center gap-2 mb-2">
        <History className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground">Collection History</span>
        {hasActiveRun && (
          <span className="flex items-center gap-1 text-[10px] text-blue-500">
            <Loader2 className="h-2.5 w-2.5 animate-spin" />
            live
          </span>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <p className="text-xs text-red-500 py-2">{error}</p>
      ) : runs.length === 0 ? (
        <p className="text-xs text-muted-foreground py-2 text-center">No collection runs yet</p>
      ) : (
        <div className="space-y-1">
          {runs.slice(0, 10).map((run) => (
            <CollectionRunRow
              key={run.id}
              run={run}
              orgId={orgId}
              connectorId={connectorId}
              statusConfig={statusConfig}
              formatDuration={formatDuration}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Connector Card
// ─────────────────────────────────────────────────────────────────────────────

function ConnectorCard({
  connector,
  onTest,
  onCollect,
  onEdit,
  onDelete,
  expanded,
  onToggleExpand,
}: {
  connector: ConnectorInstanceResponse
  onTest: (id: string) => void
  onCollect: (id: string) => void
  onEdit?: (c: ConnectorInstanceResponse) => void
  onDelete?: (c: ConnectorInstanceResponse) => void
  expanded?: boolean
  onToggleExpand?: () => void
}) {
  const health = getHealthConfig(connector.health_status)
  const HealthIcon = health.icon
  const CategoryIcon = getCategoryIcon(connector.connector_category_code)
  const displayName = connector.name || connector.instance_code

  return (
    <div className="group flex flex-col rounded-2xl border border-border/60 bg-card/80 hover:bg-card hover:shadow-lg hover:shadow-black/5 transition-all duration-200 overflow-hidden">
      {/* Colored top accent bar */}
      <div className={`h-1 ${
        connector.health_status === "healthy" ? "bg-gradient-to-r from-green-500 to-emerald-500" :
        connector.health_status === "degraded" ? "bg-gradient-to-r from-yellow-500 to-amber-500" :
        connector.health_status === "error" ? "bg-gradient-to-r from-red-500 to-rose-500" :
        "bg-gradient-to-r from-muted to-muted/50"
      }`} />
      <div className="flex flex-col gap-4 p-5 flex-1">
        {/* Top row: icon + name + health */}
        <div className="flex items-start gap-3.5 cursor-pointer" onClick={onToggleExpand}>
          <div className="rounded-xl bg-gradient-to-br from-blue-500/10 to-indigo-500/10 p-2.5 shrink-0 border border-blue-500/10">
            <CategoryIcon className="h-5 w-5 text-blue-500" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <Link href={`/sandbox/connectors/${connector.id}`} onClick={(e) => e.stopPropagation()} className="text-sm font-semibold text-foreground truncate hover:text-blue-500 transition-colors">{displayName}</Link>
              {connector.is_draft && (
                <Badge variant="outline" className="text-[10px] text-orange-500 border-orange-500/30 bg-orange-500/5">draft</Badge>
              )}
              {!connector.is_active && !connector.is_draft && (
                <Badge variant="outline" className="text-[10px] text-red-500 border-red-500/30">inactive</Badge>
              )}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <code className="text-[11px] font-mono text-muted-foreground">{connector.instance_code}</code>
              <button onClick={(e) => { e.stopPropagation(); copyToClipboard(connector.instance_code) }} className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground" title="Copy code">
                <Copy className="h-3 w-3" />
              </button>
            </div>
          </div>
          <div className="shrink-0 flex items-center gap-2">
            <Badge variant="outline" className={`text-[10px] font-semibold gap-1 ${health.color}`}>
              <HealthIcon className="h-3 w-3" />
              {health.label}
            </Badge>
            {expanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>

        {/* Type + Category badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="secondary" className="text-[10px] font-medium">
            {connector.connector_type_name}
          </Badge>
          <span className="text-xs text-muted-foreground">·</span>
          <span className="text-xs text-muted-foreground">{connector.connector_category_name}</span>
        </div>

        {/* Description */}
        {connector.description && (
          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">{connector.description}</p>
        )}

        {/* Meta row */}
        <div className="flex items-center gap-4 text-[11px] text-muted-foreground mt-auto pt-3 border-t border-border/50">
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>{scheduleLabel(connector.collection_schedule)}</span>
          </div>
          {connector.last_collected_at && (
            <div className="flex items-center gap-1.5">
              <RefreshCw className="h-3.5 w-3.5" />
              <span>{timeAgo(connector.last_collected_at)}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1.5 pt-2 border-t border-border/50">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs gap-1.5 text-muted-foreground hover:text-blue-500 hover:bg-blue-500/5"
            onClick={() => onTest(connector.id)}
          >
            <Activity className="h-3.5 w-3.5" />
            Test
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs gap-1.5 text-muted-foreground hover:text-green-500 hover:bg-green-500/5"
            onClick={() => onCollect(connector.id)}
          >
            <Play className="h-3.5 w-3.5" />
            Collect
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs gap-1.5 text-muted-foreground hover:text-primary hover:bg-primary/5"
            asChild
          >
            <Link href={`/sandbox/connectors/${connector.id}`}>
              <ExternalLink className="h-3.5 w-3.5" />
              Details
            </Link>
          </Button>
          <div className="flex-1" />
          {onEdit && (
            <button
              onClick={() => onEdit(connector)}
              className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Edit"
            >
              <Pencil className="h-4 w-4" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(connector)}
              className="rounded-lg p-2 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors"
              title="Delete"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function ConnectorsPage() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { selectedOrgId, selectedWorkspaceId, ready: orgReady } = useSandboxOrgWorkspace()
  const { canWrite } = useAccess()
  const canModify = canWrite("sandbox")

  const [connectors, setConnectors] = useState<ConnectorInstanceResponse[]>([])
  const [categories, setCategories] = useState<DimensionResponse[]>([])
  const [allTypes, setAllTypes] = useState<DimensionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Success feedback
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const showSuccess = (msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 3000)
}

  // Filters — persisted in URL so they survive navigation
  const [searchInput, setSearchInput] = useState(() => searchParams.get("q") ?? "")
  const [search, setSearch] = useState(() => searchParams.get("q") ?? "")
  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const [filterCategory, setFilterCategory] = useState(() => searchParams.get("category") ?? "")
  const [filterType, setFilterType] = useState(() => searchParams.get("type") ?? "")
  const [filterHealth, setFilterHealth] = useState(() => searchParams.get("health") ?? "")

  // Sync filters → URL
  useEffect(() => {
    const params = new URLSearchParams()
    if (search) params.set("q", search)
    if (filterCategory) params.set("category", filterCategory)
    if (filterType) params.set("type", filterType)
    if (filterHealth) params.set("health", filterHealth)
    const qs = params.toString()
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
  }, [search, filterCategory, filterType, filterHealth, pathname, router])

  // Dialogs
  const [createOpen, setCreateOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<ConnectorInstanceResponse | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ConnectorInstanceResponse | null>(null)

  // Test/collect feedback
  const [testResult, setTestResult] = useState<ConnectorTestResult | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [collectMessage, setCollectMessage] = useState<string | null>(null)

  // Collection history panel
  const [selectedConnectorId, setSelectedConnectorId] = useState<string | null>(null)

  const loadConnectors = useCallback(async () => {
    if (!selectedOrgId) return
    try {
      const params: { org_id?: string; workspace_id?: string; category_code?: string; connector_type_code?: string; health_status?: string } = { org_id: selectedOrgId }
      if (selectedWorkspaceId) params.workspace_id = selectedWorkspaceId
      if (filterCategory) params.category_code = filterCategory
      if (filterType) params.connector_type_code = filterType
      if (filterHealth) params.health_status = filterHealth
      const data = await listConnectors(params)
      setConnectors(data.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load connectors")
    }
  }, [selectedOrgId, selectedWorkspaceId, filterCategory, filterType, filterHealth])

  const loadDimensions = useCallback(async () => {
    try {
      const [cats, types] = await Promise.all([
        listConnectorCategories(),
        listConnectorTypes(),
      ])
      setCategories(cats)
      setAllTypes(types)
    } catch {
      // Non-critical — filters will be empty
    }
  }, [])

  useEffect(() => {
    if (!orgReady) return
    Promise.all([loadConnectors(), loadDimensions()]).finally(() => setLoading(false))
  }, [orgReady, loadConnectors, loadDimensions])

  // Re-load connectors when filters change
  useEffect(() => {
    if (!loading) loadConnectors()
  }, [filterCategory, filterType, filterHealth]) // eslint-disable-line react-hooks/exhaustive-deps

  const filteredConnectors = useMemo(() => {
    if (!search.trim()) return connectors
    const q = search.toLowerCase()
    return connectors.filter((c) =>
      (c.name?.toLowerCase().includes(q)) ||
      c.instance_code.toLowerCase().includes(q) ||
      c.connector_type_name.toLowerCase().includes(q) ||
      c.connector_category_name.toLowerCase().includes(q)
    )
  }, [connectors, search])

  async function handleTest(id: string) {
    setActionLoading(id)
    setTestResult(null)
    setCollectMessage(null)
    try {
      const result = await testConnector(id)
      setTestResult(result)
      // Reload to pick up health status change
      await loadConnectors()
    } catch (e) {
      setTestResult({ health_status: "error", message: e instanceof Error ? e.message : "Test failed", tested_at: new Date().toISOString() })
    } finally {
      setActionLoading(null)
    }
  }

  async function handleCollect(id: string) {
    setActionLoading(id)
    setTestResult(null)
    setCollectMessage(null)
    try {
      const result = await triggerCollection(selectedOrgId!, id)
      setCollectMessage(`Collection started (run ${result.id.slice(0, 8)}…). Status: ${result.status}`)
      await loadConnectors()
    } catch (e) {
      setCollectMessage(e instanceof Error ? e.message : "Collection failed")
    } finally {
      setActionLoading(null)
    }
  }

  async function handleDelete(id: string) {
    await deleteConnector(selectedOrgId!, id)
    setDeleteTarget(null)
    showSuccess("Connector deleted")
    await loadConnectors()
  }

  const healthyCount = connectors.filter((c) => c.health_status === "healthy").length
  const degradedCount = connectors.filter((c) => c.health_status === "degraded").length
  const errorCount = connectors.filter((c) => c.health_status === "error").length
  const uncheckedCount = connectors.filter((c) => c.health_status === "unchecked").length
  const activeRuns = connectors.filter((c) => c.last_collected_at && (Date.now() - new Date(c.last_collected_at).getTime()) < 300000).length

  // Loading skeleton
  if (loading) {
    return (
      <div className="w-full space-y-8">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-500/10 via-indigo-500/5 to-purple-500/10 p-8">
          <div className="flex items-start gap-6">
            <div className="h-16 w-16 rounded-2xl bg-muted/50 animate-pulse" />
            <div className="space-y-3 flex-1">
              <div className="h-9 w-56 bg-muted/50 rounded animate-pulse" />
              <div className="h-5 w-96 bg-muted/30 rounded animate-pulse" />
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-28 bg-muted/30 rounded-xl animate-pulse" />)}
        </div>
        <div className="h-12 bg-muted/20 rounded-xl animate-pulse" />
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[1, 2, 3, 4, 5, 6].map((i) => <div key={i} className="h-56 bg-muted/30 rounded-2xl animate-pulse" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="w-full space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-blue-500/10 p-3 shrink-0">
            <Plug className="h-6 w-6 text-blue-500" />
          </div>
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-semibold text-foreground">Data Connectors</h2>
            <p className="text-sm text-muted-foreground">
              Integrate with cloud providers, SaaS platforms, and infrastructure services to collect compliance data.
            </p>
          </div>
        </div>
        {canModify && (
          <Button size="sm" onClick={() => setCreateOpen(true)} className="gap-1.5 shrink-0">
            <Plus className="h-3.5 w-3.5" />
            Add Connector
          </Button>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-xl border border-border/60 bg-card/50 p-5 hover:border-border transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Total</p>
              <p className="text-2xl font-semibold text-foreground mt-1">{connectors.length}</p>
            </div>
            <div className="rounded-lg bg-blue-500/10 p-2">
              <Plug className="h-4 w-4 text-blue-500" />
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-green-600 dark:text-green-400 uppercase tracking-wide">Healthy</p>
              <p className="text-2xl font-semibold text-green-600 dark:text-green-400 mt-1">{healthyCount}</p>
            </div>
            <div className="rounded-lg bg-green-500/10 p-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-yellow-600 dark:text-yellow-400 uppercase tracking-wide">Degraded</p>
              <p className="text-2xl font-semibold text-yellow-600 dark:text-yellow-400 mt-1">{degradedCount}</p>
            </div>
            <div className="rounded-lg bg-yellow-500/10 p-2">
              <AlertCircle className="h-4 w-4 text-yellow-500" />
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-red-600 dark:text-red-400 uppercase tracking-wide">Errors</p>
              <p className="text-2xl font-semibold text-red-600 dark:text-red-400 mt-1">{errorCount}</p>
            </div>
            <div className="rounded-lg bg-red-500/10 p-2">
              <XCircle className="h-4 w-4 text-red-500" />
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border/60 bg-card/50 p-5 hover:border-border transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Unchecked</p>
              <p className="text-2xl font-semibold text-foreground mt-1">{uncheckedCount}</p>
            </div>
            <div className="rounded-lg bg-muted/30 p-2">
              <MinusCircle className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border/60 bg-card/50 p-5 hover:border-border transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Categories</p>
              <p className="text-2xl font-semibold text-foreground mt-1">{categories.length}</p>
            </div>
            <div className="rounded-lg bg-purple-500/10 p-2">
              <Globe className="h-4 w-4 text-purple-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Success feedback */}
      {successMessage && (
        <div className="rounded-xl border border-green-500/30 bg-green-500/10 px-5 py-3 text-sm text-green-600 dark:text-green-400">
          {successMessage}
        </div>
      )}

      {/* Feedback banners */}
      {testResult && <TestResultBanner result={testResult} onDismiss={() => setTestResult(null)} />}
      {collectMessage && (
        <div className="flex items-center gap-3 rounded-xl border border-blue-500/30 bg-blue-500/5 px-5 py-3 text-blue-500">
          <Play className="h-4 w-4 shrink-0" />
          <p className="text-sm flex-1">{collectMessage}</p>
          <button onClick={() => setCollectMessage(null)} className="shrink-0 rounded-lg p-1 hover:bg-blue-500/10 transition-colors">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Filter bar */}
      <div className="rounded-xl border border-border/60 bg-card/50 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[240px]">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search connectors by name, code, or type..."
              className="pl-10 text-sm h-10 bg-background/80"
            />
          </div>
          <select
            className="h-10 rounded-lg border border-input bg-background/80 px-4 text-sm text-foreground hover:border-border transition-colors"
            value={filterCategory}
            onChange={(e) => { setFilterCategory(e.target.value); setFilterType("") }}
          >
            <option value="">All Categories</option>
            {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
          </select>
          <select
            className="h-10 rounded-lg border border-input bg-background/80 px-4 text-sm text-foreground hover:border-border transition-colors"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All Types</option>
            {(filterCategory ? allTypes.filter((t) => t.code.startsWith(filterCategory)) : allTypes).map((t) => (
              <option key={t.code} value={t.code}>{t.name}</option>
            ))}
          </select>
          <select
            className="h-10 rounded-lg border border-input bg-background/80 px-4 text-sm text-foreground hover:border-border transition-colors"
            value={filterHealth}
            onChange={(e) => setFilterHealth(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="healthy">Healthy</option>
            <option value="degraded">Degraded</option>
            <option value="error">Error</option>
            <option value="unchecked">Unchecked</option>
          </select>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 px-5 py-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-600 dark:text-red-400">Failed to load connectors</p>
              <p className="text-sm text-red-500 mt-0.5">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Connector grid */}
      {filteredConnectors.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-border/50 bg-muted/5 px-8 py-20 text-center">
          <div className="mx-auto w-20 h-20 rounded-2xl bg-muted/30 flex items-center justify-center mb-5">
            <Plug className="h-10 w-10 text-muted-foreground/40" />
          </div>
          <p className="text-lg font-medium text-foreground mb-2">
            {connectors.length === 0 ? "No connectors configured" : "No matching connectors"}
          </p>
          <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
            {connectors.length === 0
              ? "Create your first connector to start ingesting compliance data from external sources."
              : "Try adjusting your search or filter criteria."}
          </p>
          {connectors.length === 0 && canModify && (
            <Button size="sm" onClick={() => setCreateOpen(true)} className="gap-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 border-0">
              <Plus className="h-4 w-4" />
              Add Your First Connector
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredConnectors.map((c) => (
            <div key={c.id} className={`relative ${selectedConnectorId === c.id ? "md:col-span-2 lg:col-span-3 xl:col-span-4" : ""}`}>
              {actionLoading === c.id && (
                <div className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl bg-background/60 backdrop-blur-sm">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                </div>
              )}
              <ConnectorCard
                connector={c}
                onTest={handleTest}
                onCollect={handleCollect}
                onEdit={canModify ? setEditTarget : undefined}
                onDelete={canModify ? setDeleteTarget : undefined}
                expanded={selectedConnectorId === c.id}
                onToggleExpand={() => setSelectedConnectorId(selectedConnectorId === c.id ? null : c.id)}
              />
              {selectedConnectorId === c.id && selectedOrgId && (
                <CollectionHistoryPanel orgId={selectedOrgId} connectorId={c.id} />
              )}
            </div>
          ))}
        </div>
      )}

      {/* Dialogs */}
      <CreateConnectorDialog
        open={createOpen}
        orgId={selectedOrgId ?? ""}
        workspaceId={selectedWorkspaceId ?? undefined}
        onCreated={() => { showSuccess("Connector created successfully"); loadConnectors() }}
        onClose={() => setCreateOpen(false)}
      />
      <EditConnectorDialog
        connector={editTarget}
        orgId={selectedOrgId ?? ""}
        onSaved={() => { showSuccess("Connector updated"); loadConnectors() }}
        onClose={() => setEditTarget(null)}
      />
      <DeleteConnectorDialog
        connector={deleteTarget}
        onConfirm={handleDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  )
}
