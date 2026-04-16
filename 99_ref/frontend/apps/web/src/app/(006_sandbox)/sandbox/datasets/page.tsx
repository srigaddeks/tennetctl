"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import { useSearchParams } from "next/navigation"
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
  Database,
  Search,
  Plus,
  Trash2,
  Lock,
  Copy,
  Eye,
  X,
  ArrowLeft,
  FileJson,
  Loader2,
  ClipboardCopy,
  CheckCircle2,
  RefreshCw,
  Layers,
  ChevronDown,
  ChevronRight,
  Rows3,
  LayoutGrid,
  GitMerge,
  AlertTriangle,
  ScanLine,
  Sparkles,
  Globe,
  Download,
  Link2,
} from "lucide-react"
import Link from "next/link"
import {
  listDatasets,
  listConnectors,
  createDataset,
  addDatasetRecords,
  getDatasetRecords,
  lockDataset,
  cloneDataset,
  deleteDataset,
  listAssets,
  getAssetProperties,
  composeDataset,
  checkSchemaDrift,
  updateDataset,
} from "@/lib/api/sandbox"
import { DatasetBuilder } from "@/components/sandbox/DatasetBuilder"
import { DatasetQualityDialog, ExplainRecordDialog } from "@/components/sandbox/DatasetAIPanel"
import { DatasetRecordsView } from "@/components/sandbox/DatasetRecordsView"
import { PublishDatasetDialog } from "@/components/sandbox/PublishDatasetDialog"
import { PullGlobalDatasetDialog } from "@/components/sandbox/PullGlobalDatasetDialog"
import type {
  DatasetResponse,
  DatasetDataRecord,
  ConnectorInstanceResponse,
  AssetResponse,
  DatasetSourceRef,
  SchemaDriftResponse,
} from "@/lib/api/sandbox"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function formatBytes(bytes: number | null): string {
  if (!bytes) return "0 B"
  const units = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

function slugify(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .substring(0, 64)
}

// Source type → border-l color + badge style + label
const SOURCE_META: Record<string, { label: string; borderCls: string; badgeCls: string; iconCls: string }> = {
  manual_json:    { label: "Manual JSON",    borderCls: "border-l-blue-500",   badgeCls: "text-blue-500 border-blue-500/30 bg-blue-500/5",    iconCls: "text-blue-500 bg-blue-500/10"   },
  connector_pull: { label: "Connector Pull", borderCls: "border-l-green-500",  badgeCls: "text-green-500 border-green-500/30 bg-green-500/5",  iconCls: "text-green-500 bg-green-500/10"  },
  file_upload:    { label: "File Upload",    borderCls: "border-l-amber-500",  badgeCls: "text-amber-500 border-amber-500/30 bg-amber-500/5",  iconCls: "text-amber-500 bg-amber-500/10"  },
  api_push:       { label: "API Push",       borderCls: "border-l-cyan-500",   badgeCls: "text-cyan-500 border-cyan-500/30 bg-cyan-500/5",    iconCls: "text-cyan-500 bg-cyan-500/10"   },
  clone:          { label: "Clone",          borderCls: "border-l-purple-500", badgeCls: "text-purple-500 border-purple-500/30 bg-purple-500/5", iconCls: "text-purple-500 bg-purple-500/10" },
  template:       { label: "Template",       borderCls: "border-l-amber-500",  badgeCls: "text-amber-500 border-amber-500/30 bg-amber-500/5",  iconCls: "text-amber-500 bg-amber-500/10"  },
}

function getSourceMeta(code: string) {
  return SOURCE_META[code] ?? {
    label: code.replace(/_/g, " "),
    borderCls: "border-l-primary",
    badgeCls: "text-muted-foreground border-border",
    iconCls: "text-muted-foreground bg-muted",
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Create Dataset Dialog — auto-generates code/slug from name
// ─────────────────────────────────────────────────────────────────────────────

function CreateDatasetDialog({
  open,
  orgId,
  connectors,
  onCreated,
  onClose,
}: {
  open: boolean
  orgId: string
  connectors: ConnectorInstanceResponse[]
  onCreated: (dataset: DatasetResponse) => void
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [source, setSource] = useState("manual_json")
  const [connectorId, setConnectorId] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const autoSlug = useMemo(() => slugify(name), [name])

  useEffect(() => {
    if (open) {
      setName(""); setSource("manual_json")
      setConnectorId(""); setSaving(false); setError(null)
    }
  }, [open])

  async function handleCreate() {
    if (!name.trim()) { setError("Name is required."); return }
    setSaving(true); setError(null)
    try {
      const ds = await createDataset(orgId, {
        dataset_source_code: source,
        connector_instance_id: connectorId || undefined,
        properties: { name: name.trim() },
      })
      onCreated(ds)
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create dataset")
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-indigo-500/10 p-2.5"><Plus className="h-4 w-4 text-indigo-500" /></div>
            <div>
              <DialogTitle>New Dataset</DialogTitle>
              <DialogDescription>Create a named collection. Add records after.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. GitHub Users Mar 2026"
              className="h-9 text-sm"
              autoFocus
            />
            {name.trim() && (
              <p className="text-[11px] text-muted-foreground font-mono">
                slug: <span className="text-foreground">{autoSlug}</span>
              </p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Source</Label>
            <select
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={source}
              onChange={(e) => setSource(e.target.value)}
            >
              <option value="manual_json">Manual JSON</option>
              <option value="connector_pull">Connector Pull</option>
              <option value="file_upload">File Upload</option>
              <option value="api_push">API Push</option>
            </select>
          </div>
          {source === "connector_pull" && (
            <div className="space-y-1.5">
              <Label className="text-xs">Connector <span className="text-muted-foreground">(optional)</span></Label>
              <select
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={connectorId}
                onChange={(e) => setConnectorId(e.target.value)}
              >
                <option value="">None</option>
                {connectors.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name || c.instance_code} ({c.connector_type_name})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>
        )}
        <DialogFooter className="mt-3 gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={handleCreate} disabled={saving || !name.trim()}>
            {saving ? <><Loader2 className="h-3 w-3 animate-spin mr-1" />Creating...</> : "Create Dataset"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Add Records Dialog — paste JSON or import from assets
// ─────────────────────────────────────────────────────────────────────────────

function AddRecordsDialog({
  dataset,
  orgId,
  connectors,
  onAdded,
  onClose,
}: {
  dataset: DatasetResponse | null
  orgId: string
  connectors: ConnectorInstanceResponse[]
  onAdded: () => void
  onClose: () => void
}) {
  const [tab, setTab] = useState<"paste" | "assets">("paste")
  const [jsonText, setJsonText] = useState("")
  const [jsonError, setJsonError] = useState<string | null>(null)

  const [assets, setAssets] = useState<AssetResponse[]>([])
  const [selectedAssetIds, setSelectedAssetIds] = useState<Set<string>>(new Set())
  const [assetsLoading, setAssetsLoading] = useState(false)
  const [assetConnectorFilter, setAssetConnectorFilter] = useState("")
  const [assetTypeFilter, setAssetTypeFilter] = useState<string | null>(null)
  const [importProgress, setImportProgress] = useState<string | null>(null)
  const [expandedAssetId, setExpandedAssetId] = useState<string | null>(null)
  const [assetJsonCache, setAssetJsonCache] = useState<Record<string, Record<string, unknown>>>({})
  const [assetJsonLoading, setAssetJsonLoading] = useState<string | null>(null)

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (dataset) {
      setTab("paste"); setJsonText(""); setJsonError(null)
      setAssets([]); setSelectedAssetIds(new Set())
      setAssetConnectorFilter(dataset?.connector_instance_id || ""); setAssetTypeFilter(null)
      setImportProgress(null)
      setExpandedAssetId(null); setAssetJsonCache({}); setAssetJsonLoading(null)
      setSaving(false); setError(null)
    }
  }, [dataset?.id])

  async function toggleAssetPreview(asset: AssetResponse) {
    if (expandedAssetId === asset.id) { setExpandedAssetId(null); return }
    setExpandedAssetId(asset.id)
    if (assetJsonCache[asset.id]) return
    setAssetJsonLoading(asset.id)
    try {
      const props = await getAssetProperties(orgId, asset.id)
      const json: Record<string, unknown> = {
        _asset_type: asset.asset_type_code,
        _external_id: asset.asset_external_id,
        _provider: asset.provider_code,
      }
      for (const p of props) { json[p.property_key] = p.property_value }
      setAssetJsonCache((prev) => ({ ...prev, [asset.id]: json }))
    } catch {
      setAssetJsonCache((prev) => ({ ...prev, [asset.id]: { error: "Failed to load properties" } }))
    } finally {
      setAssetJsonLoading(null)
    }
  }

  // If dataset is linked to a connector, lock the filter
  const datasetConnectorId = dataset?.connector_instance_id ?? null
  const effectiveConnectorFilter = datasetConnectorId || assetConnectorFilter

  useEffect(() => {
    if (tab !== "assets" || !orgId) return
    setAssetsLoading(true)
    listAssets(orgId, { connector_id: effectiveConnectorFilter || undefined, limit: 500 })
      .then((r) => setAssets(r.items))
      .catch(() => setAssets([]))
      .finally(() => setAssetsLoading(false))
  }, [tab, orgId, effectiveConnectorFilter])

  // Compute unique asset types with counts for filter tags
  const assetTypeCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const a of assets) {
      counts.set(a.asset_type_code, (counts.get(a.asset_type_code) || 0) + 1)
    }
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1])
  }, [assets])

  // Filter assets by selected type
  const filteredAssets = useMemo(() => {
    if (!assetTypeFilter) return assets
    return assets.filter((a) => a.asset_type_code === assetTypeFilter)
  }, [assets, assetTypeFilter])

  function handleJsonChange(val: string) {
    setJsonText(val)
    if (!val.trim()) { setJsonError(null); return }
    try { JSON.parse(val); setJsonError(null) }
    catch (e) { setJsonError(e instanceof Error ? e.message : "Invalid JSON") }
  }

  const parsedRecordCount = useMemo(() => {
    if (!jsonText.trim()) return 0
    try {
      const p = JSON.parse(jsonText)
      return Array.isArray(p) ? p.length : 1
    } catch { return null }
  }, [jsonText])

  function toggleAsset(id: string) {
    setSelectedAssetIds((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  async function handleAddFromPaste() {
    if (!dataset || !jsonText.trim() || jsonError) return
    let records: Record<string, unknown>[]
    try {
      const parsed = JSON.parse(jsonText)
      records = Array.isArray(parsed) ? parsed : [parsed]
    } catch {
      setError("Invalid JSON"); return
    }
    setSaving(true); setError(null)
    try {
      await addDatasetRecords(orgId, dataset.id, { records })
      onAdded(); onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add records")
      setSaving(false)
    }
  }

  async function handleAddFromAssets() {
    if (!dataset || selectedAssetIds.size === 0) return
    setSaving(true); setError(null)
    const assetArr = assets.filter((a) => selectedAssetIds.has(a.id))
    let done = 0
    try {
      for (const asset of assetArr) {
        setImportProgress(`Fetching ${asset.asset_external_id} (${done + 1}/${assetArr.length})...`)
        const props = await getAssetProperties(orgId, asset.id)
        const record: Record<string, unknown> = {
          _asset_id: asset.id,
          _asset_type: asset.asset_type_code,
          _external_id: asset.asset_external_id,
          _provider: asset.provider_code,
          _collected_at: asset.last_collected_at,
        }
        for (const p of props) {
          record[p.property_key] = p.property_value
        }
        await addDatasetRecords(orgId, dataset.id, {
          records: [record],
          source_asset_id: asset.id,
          connector_instance_id: asset.connector_instance_id,
        })
        done++
      }
      setImportProgress(null)
      onAdded(); onClose()
    } catch (e) {
      setImportProgress(null)
      setError(e instanceof Error ? e.message : "Failed to import assets")
      setSaving(false)
    }
  }

  const open = !!dataset

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-indigo-500/10 p-2.5"><Layers className="h-4 w-4 text-indigo-500" /></div>
            <div>
              <DialogTitle>Add Records</DialogTitle>
              <DialogDescription className="font-mono text-xs truncate">
                {dataset?.name || dataset?.dataset_code} · {dataset?.row_count ?? 0} records so far
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        {/* Tabs */}
        <div className="flex gap-1 rounded-lg bg-muted/30 p-1 w-fit">
          {(["paste", "assets"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                tab === t ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t === "paste" ? "Paste JSON" : "From Assets"}
            </button>
          ))}
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto space-y-3 pr-1">
          {tab === "paste" ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  Paste a JSON array (multiple records) or a single JSON object.
                </p>
                {parsedRecordCount !== null && parsedRecordCount > 0 && (
                  <span className="text-xs text-indigo-500 font-medium">{parsedRecordCount} record{parsedRecordCount !== 1 ? "s" : ""}</span>
                )}
              </div>
              <textarea
                value={jsonText}
                onChange={(e) => handleJsonChange(e.target.value)}
                rows={16}
                className={`w-full rounded-md border bg-muted/20 px-3 py-2 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-ring resize-y ${
                  jsonError ? "border-red-500/50" : "border-input"
                }`}
                placeholder={`[\n  { "id": "r001", "user": "alice", "status": "active" },\n  { "id": "r002", "user": "bob", "status": "inactive" }\n]`}
                spellCheck={false}
              />
              {jsonError && (
                <p className="text-[11px] text-red-500 font-mono truncate">{jsonError}</p>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {/* Connector selector — locked if dataset is linked */}
              <div className="flex items-center gap-2">
                <select
                  className={`h-8 rounded-md border border-input bg-background px-2 text-xs flex-1 ${
                    datasetConnectorId ? "opacity-60 cursor-not-allowed" : ""
                  }`}
                  value={effectiveConnectorFilter}
                  onChange={(e) => { if (!datasetConnectorId) setAssetConnectorFilter(e.target.value) }}
                  disabled={!!datasetConnectorId}
                >
                  <option value="">All connectors</option>
                  {connectors.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name || c.instance_code}
                    </option>
                  ))}
                </select>
                {selectedAssetIds.size > 0 && (
                  <span className="text-xs text-indigo-500 font-medium shrink-0">
                    {selectedAssetIds.size} selected
                  </span>
                )}
              </div>

              {/* Asset type filter tags */}
              {assetTypeCounts.length > 1 && (
                <div className="flex flex-wrap gap-1.5">
                  <button
                    onClick={() => setAssetTypeFilter(null)}
                    className={`rounded-full px-2.5 py-0.5 text-[10px] font-medium border transition-colors ${
                      !assetTypeFilter
                        ? "bg-indigo-500/20 border-indigo-500/40 text-indigo-400"
                        : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/30"
                    }`}
                  >
                    All ({assets.length})
                  </button>
                  {assetTypeCounts.map(([type, count]) => (
                    <button
                      key={type}
                      onClick={() => setAssetTypeFilter(assetTypeFilter === type ? null : type)}
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-medium border transition-colors ${
                        assetTypeFilter === type
                          ? "bg-indigo-500/20 border-indigo-500/40 text-indigo-400"
                          : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/30"
                      }`}
                    >
                      {type.replace(/_/g, " ")} ({count})
                    </button>
                  ))}
                </div>
              )}

              {assetsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : filteredAssets.length === 0 ? (
                <div className="rounded-lg border border-dashed px-4 py-8 text-center text-xs text-muted-foreground">
                  {assets.length === 0 ? "No assets found. Connect a data source first." : "No assets match this filter."}
                </div>
              ) : (
                <div className="space-y-1 max-h-80 overflow-y-auto">
                  <div className="flex items-center gap-2 px-1 pb-1">
                    <button
                      onClick={() => setSelectedAssetIds(new Set(filteredAssets.map((a) => a.id)))}
                      className="text-[11px] text-indigo-500 hover:underline"
                    >
                      Select all{assetTypeFilter ? ` ${assetTypeFilter.replace(/_/g, " ")}` : ""}
                    </button>
                    <span className="text-muted-foreground/30">·</span>
                    <button
                      onClick={() => setSelectedAssetIds(new Set())}
                      className="text-[11px] text-muted-foreground hover:underline"
                    >
                      Clear
                    </button>
                  </div>
                  {filteredAssets.map((asset) => (
                    <div key={asset.id} className="rounded-lg border border-border overflow-hidden">
                      <div className="flex items-center gap-3 px-3 py-2 hover:bg-muted/20 transition-colors">
                        <input
                          type="checkbox"
                          checked={selectedAssetIds.has(asset.id)}
                          onChange={() => toggleAsset(asset.id)}
                          className="h-3.5 w-3.5 rounded cursor-pointer"
                        />
                        <button
                          onClick={() => toggleAssetPreview(asset)}
                          className="flex-1 min-w-0 text-left"
                        >
                          <p className="text-xs font-medium truncate">{asset.asset_external_id}</p>
                          <p className="text-[10px] text-muted-foreground">
                            {asset.asset_type_code} · {asset.provider_code}
                            {asset.last_collected_at ? ` · ${formatDate(asset.last_collected_at)}` : ""}
                          </p>
                        </button>
                        <Badge variant="outline" className={`text-[9px] shrink-0 ${
                          asset.status_code === "active" ? "text-green-500 border-green-500/30" : "text-muted-foreground"
                        }`}>
                          {asset.status_code}
                        </Badge>
                        <button
                          onClick={() => toggleAssetPreview(asset)}
                          className="text-muted-foreground hover:text-foreground p-0.5"
                          title="Preview JSON"
                        >
                          {expandedAssetId === asset.id ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                        </button>
                      </div>
                      {expandedAssetId === asset.id && (
                        <div className="border-t border-border bg-muted/10 px-3 py-2">
                          {assetJsonLoading === asset.id ? (
                            <div className="flex items-center gap-2 py-2 text-xs text-muted-foreground">
                              <Loader2 className="h-3 w-3 animate-spin" /> Loading properties...
                            </div>
                          ) : assetJsonCache[asset.id] ? (
                            <pre className="text-[10px] font-mono text-muted-foreground overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                              {JSON.stringify(assetJsonCache[asset.id], null, 2)}
                            </pre>
                          ) : null}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <p className="text-[11px] text-muted-foreground">
                Each selected asset's properties will be fetched from its latest snapshot and added as one JSON record.
              </p>
            </div>
          )}
        </div>

        {importProgress && (
          <div className="flex items-center gap-2 rounded-lg bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin shrink-0" />
            {importProgress}
          </div>
        )}
        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">{error}</p>
        )}

        <DialogFooter className="gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          {tab === "paste" ? (
            <Button
              size="sm"
              onClick={handleAddFromPaste}
              disabled={saving || !!jsonError || !jsonText.trim()}
            >
              {saving ? <><Loader2 className="h-3 w-3 animate-spin mr-1" />Adding...</> : `Add ${parsedRecordCount || ""} Record${parsedRecordCount !== 1 ? "s" : ""}`}
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handleAddFromAssets}
              disabled={saving || selectedAssetIds.size === 0}
            >
              {saving ? <><Loader2 className="h-3 w-3 animate-spin mr-1" />Importing...</> : `Import ${selectedAssetIds.size} Asset${selectedAssetIds.size !== 1 ? "s" : ""}`}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// View Records Dialog
// ─────────────────────────────────────────────────────────────────────────────

function ViewRecordsDialog({
  dataset,
  onClose,
}: {
  dataset: DatasetResponse | null
  onClose: () => void
}) {
  const [records, setRecords] = useState<DatasetDataRecord[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)

  useEffect(() => {
    if (!dataset) { setRecords([]); setError(null); return }
    setLoading(true)
    getDatasetRecords(dataset.id, { limit: 200 })
      .then((r) => { setRecords(r.records); setTotal(r.total) })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load records"))
      .finally(() => setLoading(false))
  }, [dataset?.id])

  function handleCopyAll() {
    navigator.clipboard.writeText(JSON.stringify(records.map((r) => r.record_data), null, 2))
    setCopied("all")
    setTimeout(() => setCopied(null), 2000)
  }

  function handleCopyRecord(r: DatasetDataRecord) {
    navigator.clipboard.writeText(JSON.stringify(r.record_data, null, 2))
    setCopied(r.id)
    setTimeout(() => setCopied(null), 2000)
  }

  const open = !!dataset

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-indigo-500/10 p-2.5"><Eye className="h-4 w-4 text-indigo-500" /></div>
            <div className="flex-1 min-w-0">
              <DialogTitle>Dataset Records</DialogTitle>
              <DialogDescription className="font-mono text-xs truncate">
                {dataset?.name || dataset?.dataset_code} · {total} record{total !== 1 ? "s" : ""}
              </DialogDescription>
            </div>
            {records.length > 0 && (
              <Button variant="ghost" size="sm" onClick={handleCopyAll} className="h-7 text-xs gap-1.5 shrink-0">
                {copied === "all" ? <><CheckCircle2 className="h-3 w-3 text-green-500" />Copied</> : <><ClipboardCopy className="h-3 w-3" />Copy all</>}
              </Button>
            )}
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3">
            <p className="text-sm text-red-500">{error}</p>
          </div>
        ) : records.length === 0 ? (
          <div className="py-10 text-center text-xs text-muted-foreground">No records yet.</div>
        ) : (
          <div className="flex-1 min-h-0 overflow-y-auto space-y-1 pr-1">
            {records.map((r) => {
              const isExpanded = expandedId === r.id
              const keys = Object.keys(r.record_data)
              const preview = keys.slice(0, 3).map((k) => `${k}: ${String(r.record_data[k]).substring(0, 30)}`).join("  ·  ")
              return (
                <div key={r.id} className="rounded-lg border border-border bg-card">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : r.id)}
                    className="flex items-center gap-3 w-full px-3 py-2 text-left hover:bg-muted/10 rounded-lg transition-colors"
                  >
                    <span className="text-[10px] text-muted-foreground font-mono w-6 shrink-0">#{r.record_seq}</span>
                    {isExpanded ? (
                      <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
                    ) : (
                      <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
                    )}
                    <span className="text-xs text-muted-foreground truncate flex-1">{preview}</span>
                    <span className="text-[10px] text-muted-foreground/50 shrink-0">{keys.length} keys</span>
                  </button>
                  {isExpanded && (
                    <div className="border-t border-border px-3 pb-3 pt-2">
                      <div className="flex items-center justify-end mb-1.5">
                        <Button variant="ghost" size="sm" onClick={() => handleCopyRecord(r)} className="h-6 text-[10px] gap-1">
                          {copied === r.id ? <><CheckCircle2 className="h-2.5 w-2.5 text-green-500" />Copied</> : <><ClipboardCopy className="h-2.5 w-2.5" />Copy</>}
                        </Button>
                      </div>
                      <pre className="rounded-md border border-border bg-muted/20 p-3 text-[11px] font-mono text-foreground overflow-x-auto whitespace-pre-wrap break-all max-h-72">
                        {JSON.stringify(r.record_data, null, 2)}
                      </pre>
                      {r.source_asset_id && (
                        <p className="text-[10px] text-muted-foreground mt-1.5">Asset: <code className="font-mono">{r.source_asset_id}</code></p>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
            {total > records.length && (
              <p className="text-center text-xs text-muted-foreground py-2">
                Showing {records.length} of {total} records
              </p>
            )}
          </div>
        )}

        <DialogFooter className="mt-3">
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Delete Dialog
// ─────────────────────────────────────────────────────────────────────────────

function DeleteDatasetDialog({
  dataset,
  orgId,
  onConfirm,
  onClose,
}: {
  dataset: DatasetResponse | null
  orgId: string
  onConfirm: () => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!dataset) return null

  async function confirm() {
    setDeleting(true); setError(null)
    try { await onConfirm(); onClose() }
    catch (e) { setError(e instanceof Error ? e.message : "Failed to delete"); setDeleting(false) }
  }

  return (
    <Dialog open onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-red-500/10 p-2.5"><Trash2 className="h-4 w-4 text-red-500" /></div>
            <div>
              <DialogTitle>Delete Dataset</DialogTitle>
              <DialogDescription>This action cannot be undone.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <p className="text-sm">
          Delete <strong>{dataset.name || dataset.dataset_code}</strong>{" "}
          <span className="text-muted-foreground text-xs font-mono">({dataset.row_count ?? 0} records)</span>?
        </p>
        {dataset.is_locked && (
          <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-amber-600 mt-2">
            <Lock className="h-3.5 w-3.5 shrink-0" />
            This dataset is locked and cannot be deleted.
          </div>
        )}
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={deleting}>Cancel</Button>
          <Button variant="destructive" size="sm" onClick={confirm} disabled={deleting || dataset.is_locked}>
            {deleting ? <><Loader2 className="h-3 w-3 animate-spin mr-1" />Deleting...</> : "Delete Dataset"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Change Connector Dialog
// ─────────────────────────────────────────────────────────────────────────────

function ChangeConnectorDialog({
  dataset,
  connectors,
  orgId,
  onConfirm,
  onClose,
}: {
  dataset: DatasetResponse | null
  connectors: ConnectorInstanceResponse[]
  orgId: string
  onConfirm: (connectorId: string | null) => Promise<void>
  onClose: () => void
}) {
  const [selected, setSelected] = useState<string>(dataset?.connector_instance_id || "")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!dataset) return null

  async function confirm() {
    setSaving(true); setError(null)
    try {
      await onConfirm(selected || null)
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to update"); setSaving(false) }
  }

  return (
    <Dialog open onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-500/10 p-2.5"><Link2 className="h-4 w-4 text-blue-500" /></div>
            <div>
              <DialogTitle>Change Connector</DialogTitle>
              <DialogDescription>Link this dataset to a different connector or remove the link.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-3">
          <Label>Connector</Label>
          <select
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">No connector (unlinked)</option>
            {connectors.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name || c.instance_code} ({c.connector_type_name || c.connector_type_code})
              </option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground">
            Current: {dataset.connector_instance_id
              ? connectors.find(c => c.id === dataset.connector_instance_id)?.name || dataset.connector_instance_id.slice(0, 8)
              : "None"}
          </p>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={confirm} disabled={saving}>
            {saving ? <><Loader2 className="h-3 w-3 animate-spin mr-1" />Saving...</> : "Update Connector"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Dataset Row — border-l-[3px] colored by source type
// ─────────────────────────────────────────────────────────────────────────────

function DatasetRow({
  dataset,
  actionLoading,
  onView,
  onAddRecords,
  onClone,
  onLock,
  onDelete,
  onDrift,
  onAI,
  onPublish,
  onChangeConnector,
}: {
  dataset: DatasetResponse
  actionLoading: string | null
  onView: (d: DatasetResponse) => void
  onAddRecords: (d: DatasetResponse) => void
  onClone: (d: DatasetResponse) => void
  onLock: (d: DatasetResponse) => void
  onDelete: (d: DatasetResponse) => void
  onDrift?: (d: DatasetResponse) => void
  onAI?: (d: DatasetResponse) => void
  onPublish?: (d: DatasetResponse) => void
  onChangeConnector?: (d: DatasetResponse) => void
}) {
  const src = getSourceMeta(dataset.dataset_source_code)
  const isActing = actionLoading === dataset.id
  const displayName = dataset.name || dataset.dataset_code
  const rowCount = dataset.row_count ?? 0

  return (
    <div className={`group relative flex items-center gap-4 rounded-xl border border-l-[3px] ${src.borderCls} bg-card px-4 py-3 hover:bg-muted/20 transition-colors`}>
      {isActing && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-background/60 backdrop-blur-sm">
          <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />
        </div>
      )}
      <div className={`rounded-lg p-2 shrink-0 ${src.iconCls}`}>
        <FileJson className="h-3.5 w-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-medium text-foreground truncate">{displayName}</p>
          {dataset.is_locked && <Lock className="h-3 w-3 text-amber-500 shrink-0" />}
          <Badge variant="outline" className={`text-[10px] ${src.badgeCls}`}>{src.label}</Badge>
        </div>
        <div className="flex items-center gap-2 mt-0.5 text-[11px] text-muted-foreground">
          <code className="font-mono">{dataset.dataset_code}</code>
          <span className="text-muted-foreground/30">·</span>
          <span className="font-medium text-foreground">{rowCount.toLocaleString()} record{rowCount !== 1 ? "s" : ""}</span>
          {dataset.byte_size ? (
            <>
              <span className="text-muted-foreground/30">·</span>
              <span>{formatBytes(dataset.byte_size)}</span>
            </>
          ) : null}
          <span className="text-muted-foreground/30">·</span>
          <span>{formatDate(dataset.created_at)}</span>
        </div>
      </div>
      <div className="shrink-0 text-center w-10">
        <span className="text-[9px] uppercase text-muted-foreground tracking-widest block">ver</span>
        <span className="text-sm font-semibold text-foreground">{dataset.version_number}</span>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <button
          onClick={() => onView(dataset)}
          className="rounded-lg p-1.5 text-muted-foreground hover:bg-indigo-500/10 hover:text-indigo-500 transition-colors"
          title="View records"
        >
          <Eye className="h-3.5 w-3.5" />
        </button>
        {!dataset.is_locked && (
          <button
            onClick={() => onAddRecords(dataset)}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-green-500/10 hover:text-green-500 transition-colors"
            title="Add records"
          >
            <Plus className="h-3.5 w-3.5" />
          </button>
        )}
        {onAI && (
          <button
            onClick={() => onAI(dataset)}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-purple-500/10 hover:text-purple-500 transition-colors"
            title="AI Dataset Assistant"
          >
            <Sparkles className="h-3.5 w-3.5" />
          </button>
        )}
        {onDrift && (
          <button
            onClick={() => onDrift(dataset)}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-amber-500/10 hover:text-amber-500 transition-colors"
            title="Check schema drift"
          >
            <ScanLine className="h-3.5 w-3.5" />
          </button>
        )}
        {onChangeConnector && (
          <button
            onClick={() => onChangeConnector(dataset)}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-blue-500/10 hover:text-blue-500 transition-colors"
            title="Change Connector"
          >
            <Link2 className="h-3.5 w-3.5" />
          </button>
        )}
        <button
          onClick={() => onClone(dataset)}
          className="rounded-lg p-1.5 text-muted-foreground hover:bg-purple-500/10 hover:text-purple-500 transition-colors"
          title="Clone"
        >
          <Copy className="h-3.5 w-3.5" />
        </button>
        {!dataset.is_locked && (
          <button
            onClick={() => onLock(dataset)}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-amber-500/10 hover:text-amber-500 transition-colors"
            title="Lock (make immutable)"
          >
            <Lock className="h-3.5 w-3.5" />
          </button>
        )}
        {onPublish && (dataset.row_count ?? 0) > 0 && (
          <button
            onClick={() => onPublish(dataset)}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-emerald-500/10 hover:text-emerald-500 transition-colors"
            title="Publish to Global Library"
          >
            <Globe className="h-3.5 w-3.5" />
          </button>
        )}
        <button
          onClick={() => onDelete(dataset)}
          className="rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors"
          title="Delete"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

const SOURCE_FILTER_OPTIONS = [
  { value: "", label: "All Sources" },
  { value: "manual_json", label: "Manual JSON" },
  { value: "connector_pull", label: "Connector Pull" },
  { value: "file_upload", label: "File Upload" },
  { value: "api_push", label: "API Push" },
  { value: "clone", label: "Clone" },
  { value: "template", label: "Template" },
]

// ─────────────────────────────────────────────────────────────────────────────
// Compose Dataset Dialog — builds a dataset from collected asset properties
// ─────────────────────────────────────────────────────────────────────────────

function ComposeDatasetDialog({
  open,
  orgId,
  connectors,
  onCreated,
  onClose,
}: {
  open: boolean
  orgId: string
  connectors: ConnectorInstanceResponse[]
  onCreated: (name: string) => void
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [sources, setSources] = useState<DatasetSourceRef[]>([
    { source_type: "asset_properties", connector_instance_id: "", asset_type_filter: "" },
  ])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function addSource() {
    setSources((prev) => [...prev, { source_type: "asset_properties", connector_instance_id: "", asset_type_filter: "" }])
  }

  function removeSource(i: number) {
    setSources((prev) => prev.filter((_, idx) => idx !== i))
  }

  function updateSource(i: number, patch: Partial<DatasetSourceRef>) {
    setSources((prev) => prev.map((s, idx) => idx === i ? { ...s, ...patch } : s))
  }

  async function handleSubmit() {
    if (!name.trim()) { setError("Dataset name is required"); return }
    if (sources.length === 0) { setError("Add at least one source"); return }
    setLoading(true)
    setError(null)
    try {
      await composeDataset(orgId, {
        name: name.trim(),
        description: description.trim() || undefined,
        sources: sources.filter((s) => s.connector_instance_id || s.asset_id),
      })
      onCreated(name.trim())
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to compose dataset")
    } finally {
      setLoading(false)
    }
  }

  const ASSET_TYPE_OPTIONS = [
    "github_org", "github_repo", "github_team", "github_org_member", "github_workflow",
    "azure_storage_account", "azure_blob_container",
    "postgres_role", "postgres_database", "postgres_schema", "postgres_table",
    "postgres_stat_activity", "postgres_stat_statements",
  ]

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <GitMerge className="h-4 w-4 text-indigo-500" />
            <DialogTitle>Compose Dataset from Assets</DialogTitle>
          </div>
          <DialogDescription>
            Pull current asset properties from one or more connectors into a single dataset.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Dataset Name</Label>
            <Input
              className="h-8 text-sm"
              placeholder="e.g. github_assets_2026"
              value={name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs font-medium text-muted-foreground">Description (optional)</Label>
            <Input
              className="h-8 text-sm"
              placeholder="What this dataset contains..."
              value={description}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDescription(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-medium">Asset Sources</Label>
              <button
                onClick={addSource}
                className="text-xs text-indigo-500 hover:text-indigo-600 flex items-center gap-1"
                disabled={loading}
              >
                <Plus className="h-3 w-3" /> Add Source
              </button>
            </div>

            {sources.map((src, i) => (
              <div key={i} className="rounded-lg border border-border bg-muted/20 p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground">Source {i + 1}</span>
                  {sources.length > 1 && (
                    <button onClick={() => removeSource(i)} disabled={loading} className="text-red-400 hover:text-red-500">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-[10px] text-muted-foreground">Connector</label>
                    <select
                      className="w-full h-7 rounded border border-input bg-background px-2 text-xs"
                      value={src.connector_instance_id ?? ""}
                      onChange={(e) => updateSource(i, { connector_instance_id: e.target.value })}
                      disabled={loading}
                    >
                      <option value="">Select connector…</option>
                      {connectors.map((c) => (
                        <option key={c.id} value={c.id}>{c.name || c.id}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] text-muted-foreground">Asset Type Filter</label>
                    <select
                      className="w-full h-7 rounded border border-input bg-background px-2 text-xs"
                      value={src.asset_type_filter ?? ""}
                      onChange={(e) => updateSource(i, { asset_type_filter: e.target.value || undefined })}
                      disabled={loading}
                    >
                      <option value="">All types</option>
                      {ASSET_TYPE_OPTIONS.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button size="sm" onClick={handleSubmit} disabled={loading} className="gap-1.5">
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <GitMerge className="h-3.5 w-3.5" />}
            Compose Dataset
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Schema Drift Dialog
// ─────────────────────────────────────────────────────────────────────────────

function SchemaDriftDialog({
  dataset,
  orgId,
  onClose,
}: {
  dataset: DatasetResponse
  orgId: string
  onClose: () => void
}) {
  const [loading, setLoading] = useState(true)
  const [result, setResult] = useState<SchemaDriftResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const r = await checkSchemaDrift(orgId, dataset.id)
        setResult(r)
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to check drift")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [dataset.id, orgId])

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <ScanLine className="h-4 w-4 text-amber-500" />
            <DialogTitle>Schema Drift — {dataset.name}</DialogTitle>
          </div>
          <DialogDescription>
            Compare the stored schema fingerprint against current asset properties.
          </DialogDescription>
        </DialogHeader>

        <div className="py-2 space-y-3">
          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />Checking schema…
            </div>
          )}
          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500">
              {error}
            </div>
          )}
          {result && !loading && (
            <>
              <div className={`rounded-lg border px-4 py-3 flex items-center gap-3 ${result.has_drift ? "border-amber-500/30 bg-amber-500/10" : "border-green-500/30 bg-green-500/10"}`}>
                {result.has_drift
                  ? <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0" />
                  : <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
                }
                <div>
                  <p className={`font-medium text-sm ${result.has_drift ? "text-amber-600 dark:text-amber-400" : "text-green-600 dark:text-green-400"}`}>
                    {result.has_drift ? `${result.changes.length} schema change${result.changes.length !== 1 ? "s" : ""} detected` : "No schema drift detected"}
                  </p>
                  <p className="text-xs text-muted-foreground font-mono mt-0.5">
                    {result.old_fingerprint.slice(0, 16)}… → {result.new_fingerprint.slice(0, 16)}…
                  </p>
                </div>
              </div>

              {result.changes.length > 0 && (
                <div className="space-y-1.5 max-h-64 overflow-y-auto">
                  {result.changes.map((c, i) => (
                    <div key={i} className="flex items-center gap-2 rounded border border-border bg-muted/30 px-3 py-2 text-xs">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${c.change_type === "added" ? "bg-green-500/20 text-green-600" : c.change_type === "removed" ? "bg-red-500/20 text-red-500" : "bg-amber-500/20 text-amber-600"}`}>
                        {c.change_type}
                      </span>
                      <code className="font-mono">{c.field}</code>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function DatasetsPage() {
  const { selectedOrgId, ready: orgReady } = useSandboxOrgWorkspace()
  const searchParams = useSearchParams()

  const [datasets, setDatasets] = useState<DatasetResponse[]>([])
  const [connectors, setConnectors] = useState<ConnectorInstanceResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterSource, setFilterSource] = useState("")

  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  function showSuccess(msg: string) {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 3500)
  }

  const [createOpen, setCreateOpen] = useState(false)
  const [composeOpen, setComposeOpen] = useState(false)
  const [driftTarget, setDriftTarget] = useState<DatasetResponse | null>(null)
  const [aiTarget, setAiTarget] = useState<DatasetResponse | null>(null)
  const [aiRecords, setAiRecords] = useState<Array<Record<string, unknown>>>([])
  const [aiLoading, setAiLoading] = useState(false)
  const [viewTarget, setViewTarget] = useState<DatasetResponse | null>(null)
  const [addRecordsTarget, setAddRecordsTarget] = useState<DatasetResponse | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<DatasetResponse | null>(null)
  const [connectorChangeTarget, setConnectorChangeTarget] = useState<DatasetResponse | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [publishTarget, setPublishTarget] = useState<DatasetResponse | null>(null)
  const [pullLibraryOpen, setPullLibraryOpen] = useState(false)

  // Auto-open compose dialog when navigating from connector detail page
  const composeFromUrl = searchParams.get("compose") === "true"
  const connectorIdFromUrl = searchParams.get("connector_id")
  useEffect(() => {
    if (composeFromUrl && orgReady) {
      setComposeOpen(true)
    }
  }, [composeFromUrl, orgReady])

  const loadDatasets = useCallback(async () => {
    if (!selectedOrgId) return
    setError(null)
    try {
      const params: { dataset_source_code?: string } = {}
      if (filterSource) params.dataset_source_code = filterSource
      const data = await listDatasets(selectedOrgId, params)
      setDatasets(data.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to list datasets")
    }
  }, [selectedOrgId, filterSource])

  const loadConnectors = useCallback(async () => {
    if (!selectedOrgId) return
    try {
      const data = await listConnectors({ org_id: selectedOrgId })
      setConnectors(data.items)
    } catch { /* non-critical */ }
  }, [selectedOrgId])

  useEffect(() => {
    if (!orgReady) return
    Promise.all([loadDatasets(), loadConnectors()]).finally(() => setLoading(false))
  }, [orgReady, loadDatasets, loadConnectors])

  const filteredDatasets = useMemo(() => {
    if (!search.trim()) return datasets
    const q = search.toLowerCase()
    return datasets.filter((d) =>
      d.name?.toLowerCase().includes(q) ||
      d.dataset_code.toLowerCase().includes(q) ||
      d.dataset_source_code.toLowerCase().includes(q)
    )
  }, [datasets, search])

  async function handleClone(d: DatasetResponse) {
    if (!selectedOrgId) return
    setActionLoading(d.id)
    try {
      const cloned = await cloneDataset(selectedOrgId, d.id)
      showSuccess(`Cloned → v${cloned.version_number}`)
      await loadDatasets()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Clone failed")
    } finally {
      setActionLoading(null)
    }
  }

  async function handleLock(d: DatasetResponse) {
    if (!selectedOrgId) return
    setActionLoading(d.id)
    try {
      await lockDataset(selectedOrgId, d.id)
      showSuccess("Dataset locked — records are now immutable")
      await loadDatasets()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lock failed")
    } finally {
      setActionLoading(null)
    }
  }

  async function handleDelete(d: DatasetResponse) {
    if (!selectedOrgId) return
    await deleteDataset(selectedOrgId, d.id)
    showSuccess("Dataset deleted")
    await loadDatasets()
  }

  // KPI data
  const totalRows = datasets.reduce((a, d) => a + (d.row_count ?? 0), 0)
  const lockedCount = datasets.filter((d) => d.is_locked).length
  const sourceBreakdown = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const d of datasets) {
      counts[d.dataset_source_code] = (counts[d.dataset_source_code] ?? 0) + 1
    }
    return counts
  }, [datasets])
  const topSource = Object.entries(sourceBreakdown).sort((a, b) => b[1] - a[1])[0]

  // Active filter chips
  const activeFilters: { key: string; label: string; onRemove: () => void }[] = []
  if (search.trim()) {
    activeFilters.push({ key: "search", label: `"${search}"`, onRemove: () => setSearch("") })
  }
  if (filterSource) {
    const opt = SOURCE_FILTER_OPTIONS.find((o) => o.value === filterSource)
    activeFilters.push({ key: "source", label: opt?.label ?? filterSource, onRemove: () => setFilterSource("") })
  }

  // ─── Loading skeleton ────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="w-full space-y-6">
        <div className="flex items-start gap-4">
          <div className="h-12 w-12 rounded-xl bg-muted animate-pulse" />
          <div className="space-y-2 flex-1">
            <div className="h-7 w-40 bg-muted rounded animate-pulse" />
            <div className="h-4 w-64 bg-muted rounded animate-pulse" />
          </div>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />)}
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="w-full space-y-6">
      {/* Back nav */}
      <Button variant="ghost" size="sm" asChild className="gap-1.5 -ml-2 text-muted-foreground hover:text-foreground">
        <Link href="/sandbox"><ArrowLeft className="h-4 w-4" />Sandbox</Link>
      </Button>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-indigo-500/10 p-3 shrink-0">
            <Database className="h-6 w-6 text-indigo-500" />
          </div>
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-semibold text-foreground">Datasets</h2>
            <p className="text-sm text-muted-foreground">
              Collections of individual JSON records — sourced from connectors, assets, or manual input.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={() => setPullLibraryOpen(true)} className="gap-1.5">
            <Download className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Pull from Library</span>
            <span className="sm:hidden">Pull</span>
          </Button>
          <Button variant="outline" size="sm" onClick={() => setComposeOpen(true)} className="gap-1.5">
            <GitMerge className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Compose from Assets</span>
            <span className="sm:hidden">Compose</span>
          </Button>
          <Button size="sm" onClick={() => setCreateOpen(true)} className="gap-1.5">
            <Plus className="h-3.5 w-3.5" />
            New Dataset
          </Button>
        </div>
      </div>

      {/* KPI stat cards */}
      {datasets.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Total datasets */}
          <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-indigo-500 bg-card px-4 py-3">
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <Database className="h-4 w-4 text-indigo-500" />
            </div>
            <div className="min-w-0">
              <span className="text-2xl font-bold tabular-nums leading-none text-indigo-500">{datasets.length}</span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Datasets</span>
            </div>
          </div>

          {/* Total records */}
          <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-blue-500 bg-card px-4 py-3">
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <Rows3 className="h-4 w-4 text-blue-500" />
            </div>
            <div className="min-w-0">
              <span className="text-2xl font-bold tabular-nums leading-none text-blue-500">{totalRows.toLocaleString()}</span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Total Records</span>
            </div>
          </div>

          {/* Locked */}
          <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-amber-500 bg-card px-4 py-3">
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <Lock className="h-4 w-4 text-amber-500" />
            </div>
            <div className="min-w-0">
              <span className="text-2xl font-bold tabular-nums leading-none text-amber-500">{lockedCount}</span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Locked</span>
            </div>
          </div>

          {/* Top source */}
          <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-green-500 bg-card px-4 py-3">
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <LayoutGrid className="h-4 w-4 text-green-500" />
            </div>
            <div className="min-w-0">
              <span className="text-2xl font-bold tabular-nums leading-none text-green-500">{topSource ? topSource[1] : 0}</span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">
                {topSource ? getSourceMeta(topSource[0]).label : "No sources"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Feedback banners */}
      {successMessage && (
        <div className="flex items-center gap-3 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {successMessage}
        </div>
      )}
      {error && (
        <div className="flex items-center justify-between rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3">
          <p className="text-sm text-red-500">{error}</p>
          <button onClick={() => setError(null)}><X className="h-4 w-4 text-red-500" /></button>
        </div>
      )}

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex flex-wrap items-center gap-2 flex-1">
            <div className="relative flex-1 min-w-[180px] max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search datasets..."
                className="pl-8 text-sm h-9"
              />
            </div>
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground"
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
            >
              {SOURCE_FILTER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <button
              onClick={loadDatasets}
              className="rounded-md border border-input bg-background p-2 text-muted-foreground hover:text-foreground transition-colors"
              title="Refresh"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          {/* Active filter chips */}
          {activeFilters.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {activeFilters.map((f) => (
                <span
                  key={f.key}
                  className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/40 px-2.5 py-1 text-[11px] text-foreground"
                >
                  {f.label}
                  <button
                    onClick={f.onRemove}
                    className="ml-0.5 rounded-full hover:bg-muted transition-colors"
                    aria-label={`Remove ${f.label} filter`}
                  >
                    <X className="h-2.5 w-2.5 text-muted-foreground" />
                  </button>
                </span>
              ))}
              <button
                onClick={() => { setSearch(""); setFilterSource("") }}
                className="text-[11px] text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear all
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Dataset list */}
      {filteredDatasets.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed px-6 py-16 text-center">
          <Database className="h-10 w-10 text-muted-foreground/30" />
          <div>
            <p className="text-sm font-medium text-foreground mb-1">
              {datasets.length === 0 ? "No datasets yet" : "No datasets match your filters"}
            </p>
            <p className="text-xs text-muted-foreground">
              {datasets.length === 0
                ? "Create a dataset, then add records — paste JSON or import from connected assets."
                : "Try adjusting your search or filter."}
            </p>
          </div>
          {datasets.length === 0 && (
            <Button size="sm" onClick={() => setCreateOpen(true)} className="gap-1.5 mt-2">
              <Plus className="h-3.5 w-3.5" />
              New Dataset
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredDatasets.map((d) => (
            <DatasetRow
              key={d.id}
              dataset={d}
              actionLoading={actionLoading}
              onView={setViewTarget}
              onAddRecords={setAddRecordsTarget}
              onClone={handleClone}
              onLock={handleLock}
              onDelete={setDeleteTarget}
              onPublish={setPublishTarget}
              onChangeConnector={setConnectorChangeTarget}
              onDrift={d.dataset_source_code === "asset_properties" ? () => setDriftTarget(d) : undefined}
              onAI={(d.row_count ?? 0) > 0 ? () => {
                setAiTarget(d)
                setAiLoading(true)
                getDatasetRecords(d.id, { limit: 100 }).then((res) => {
                  setAiRecords(res.records?.map((r: DatasetDataRecord) => r.record_data) ?? [])
                }).catch(() => setAiRecords([])).finally(() => setAiLoading(false))
              } : undefined}
            />
          ))}
        </div>
      )}

      {/* Dialogs */}
      {/* AI Dataset Assistant */}
      {aiTarget && selectedOrgId && !aiLoading && aiRecords.length > 0 && (
        <DatasetQualityDialog
          records={aiRecords}
          datasetId={aiTarget.id}
          orgId={selectedOrgId}
          assetType={aiTarget.dataset_source_code}
          onRecordsAdded={() => { showSuccess("AI records added"); loadDatasets() }}
          onClose={() => { setAiTarget(null); setAiRecords([]) }}
        />
      )}

      <DatasetBuilder
        open={composeOpen}
        orgId={selectedOrgId ?? ""}
        defaultConnectorId={connectorIdFromUrl || undefined}
        onCreated={(_id, name) => { showSuccess(`Dataset "${name}" created`); loadDatasets(); setComposeOpen(false) }}
        onClose={() => setComposeOpen(false)}
      />
      {driftTarget && selectedOrgId && (
        <SchemaDriftDialog
          dataset={driftTarget}
          orgId={selectedOrgId}
          onClose={() => setDriftTarget(null)}
        />
      )}
      <CreateDatasetDialog
        open={createOpen}
        orgId={selectedOrgId ?? ""}
        connectors={connectors}
        onCreated={(ds) => {
          showSuccess(`Dataset "${ds.name || ds.dataset_code}" created`)
          loadDatasets()
          setAddRecordsTarget(ds)
        }}
        onClose={() => setCreateOpen(false)}
      />
      <AddRecordsDialog
        dataset={addRecordsTarget}
        orgId={selectedOrgId ?? ""}
        connectors={connectors}
        onAdded={() => { showSuccess("Records added"); loadDatasets() }}
        onClose={() => setAddRecordsTarget(null)}
      />
      {/* New AI-powered records view */}
      {viewTarget && selectedOrgId && (
        <DatasetRecordsView
          dataset={viewTarget}
          orgId={selectedOrgId}
          onClose={() => setViewTarget(null)}
        />
      )}
      {/* Legacy view (kept for fallback) */}
      {!selectedOrgId && viewTarget && (
        <ViewRecordsDialog
          dataset={viewTarget}
          onClose={() => setViewTarget(null)}
        />
      )}
      <DeleteDatasetDialog
        dataset={deleteTarget}
        orgId={selectedOrgId ?? ""}
        onConfirm={() => handleDelete(deleteTarget!)}
        onClose={() => setDeleteTarget(null)}
      />

      <ChangeConnectorDialog
        dataset={connectorChangeTarget}
        connectors={connectors}
        orgId={selectedOrgId ?? ""}
        onConfirm={async (connectorId) => {
          if (!selectedOrgId || !connectorChangeTarget) return
          await updateDataset(selectedOrgId, connectorChangeTarget.id, {
            connector_instance_id: connectorId ?? "",
          })
          showSuccess("Connector updated")
          loadDatasets()
        }}
        onClose={() => setConnectorChangeTarget(null)}
      />

      {/* Global Library Dialogs */}
      {publishTarget && selectedOrgId && (
        <PublishDatasetDialog
          dataset={publishTarget}
          orgId={selectedOrgId}
          onPublished={() => { showSuccess("Dataset published to global library"); loadDatasets() }}
          onClose={() => setPublishTarget(null)}
        />
      )}
      <PullGlobalDatasetDialog
        open={pullLibraryOpen}
        orgId={selectedOrgId ?? ""}
        onPulled={(code) => { showSuccess(`Pulled "${code}" from library`); loadDatasets(); setPullLibraryOpen(false) }}
        onClose={() => setPullLibraryOpen(false)}
      />
    </div>
  )
}
