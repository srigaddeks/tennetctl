"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import {
  Button,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  ArrowLeft,
  Github,
  Cloud,
  Database as DatabaseIcon,
  Server,
  Plug,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Activity,
  Layers,
  FileJson,
  Copy,
  ExternalLink,
  Plus,
} from "lucide-react"
import {
  getConnector,
  listCollectionRuns,
  listCollectionRunSnapshots,
  testConnector,
  triggerCollection,
  createDataset,
  addDatasetRecords,
} from "@/lib/api/sandbox"
import type {
  ConnectorInstanceResponse,
  CollectionRunResponse,
  CollectionSnapshotItem,
} from "@/lib/api/sandbox"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"

// ── Helpers ──────────────────────────────────────────────────────────────────

function ConnectorIcon({ typeCode, className = "h-5 w-5" }: { typeCode: string; className?: string }) {
  const t = typeCode.toLowerCase()
  if (t.includes("github")) return <Github className={className} />
  if (t.includes("aws")) return <Cloud className={className} />
  if (t.includes("azure")) return <Cloud className={className} />
  if (t.includes("postgres") || t.includes("mysql") || t.includes("db")) return <DatabaseIcon className={className} />
  if (t.includes("kubernetes") || t.includes("k8s")) return <Server className={className} />
  return <Plug className={className} />
}

function HealthBadge({ status }: { status: string }) {
  const s = status.toLowerCase()
  if (s === "healthy") return <Badge className="bg-green-500/10 text-green-500 border-green-500/30 text-xs gap-1"><CheckCircle2 className="h-3 w-3" />Healthy</Badge>
  if (s === "degraded") return <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/30 text-xs gap-1"><AlertCircle className="h-3 w-3" />Degraded</Badge>
  if (s === "error" || s === "unhealthy") return <Badge className="bg-red-500/10 text-red-500 border-red-500/30 text-xs gap-1"><AlertCircle className="h-3 w-3" />Error</Badge>
  return <Badge variant="outline" className="text-xs gap-1"><Clock className="h-3 w-3" />Unchecked</Badge>
}

function StatusBadge({ status }: { status: string }) {
  const s = status?.toLowerCase() || ""
  if (s === "completed") return <Badge className="bg-green-500/10 text-green-500 border-green-500/30 text-[10px]">completed</Badge>
  if (s === "running") return <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/30 text-[10px] animate-pulse">running</Badge>
  if (s === "failed" || s === "error") return <Badge className="bg-red-500/10 text-red-500 border-red-500/30 text-[10px]">failed</Badge>
  if (s === "cancelled") return <Badge className="bg-muted text-muted-foreground border-border text-[10px]">cancelled</Badge>
  return <Badge variant="outline" className="text-[10px]">{status || "queued"}</Badge>
}

function formatDuration(start: string | null, end: string | null): string {
  if (!start) return "-"
  const s = new Date(start).getTime()
  const e = end ? new Date(end).getTime() : Date.now()
  const diff = Math.round((e - s) / 1000)
  if (diff < 60) return `${diff}s`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`
  return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`
}

function formatDate(d: string | null): string {
  if (!d) return "-"
  return new Date(d).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

function assetTypeLabel(code: string): string {
  return code.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
}

// ── Asset Type Icon ──────────────────────────────────────────────────────────

function AssetTypeIcon({ type, className = "h-3.5 w-3.5" }: { type: string; className?: string }) {
  if (type.includes("repo")) return <Layers className={className} />
  if (type.includes("workflow")) return <Activity className={className} />
  if (type.includes("member")) return <Server className={className} />
  if (type.includes("org")) return <Github className={className} />
  if (type.includes("team")) return <Server className={className} />
  return <FileJson className={className} />
}

// ── Collection Run Row (expandable) ──────────────────────────────────────────

function CollectionRunRow({
  run,
  orgId,
  connectorId,
  connectorName,
  onDatasetCreated,
}: {
  run: CollectionRunResponse
  orgId: string
  connectorId: string
  connectorName: string
  onDatasetCreated?: (msg: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [snapshots, setSnapshots] = useState<CollectionSnapshotItem[]>([])
  const [typeSummary, setTypeSummary] = useState<Record<string, number>>({})
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [typeFilter, setTypeFilter] = useState("")
  const [expandedAsset, setExpandedAsset] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<"list" | "json">("list")
  const [createDatasetOpen, setCreateDatasetOpen] = useState(false)
  const [datasetName, setDatasetName] = useState("")
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set())
  const [creatingDataset, setCreatingDataset] = useState(false)

  const loadSnapshots = useCallback(async (assetType?: string) => {
    setLoading(true)
    try {
      const data = await listCollectionRunSnapshots(orgId, run.id, {
        asset_type: assetType || undefined,
        limit: 200,
      })
      setSnapshots(data.items)
      setTotal(data.total)
      setTypeSummary(data.asset_type_summary)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [orgId, run.id])

  function handleExpand() {
    if (!expanded) loadSnapshots()
    setExpanded((v) => !v)
  }

  function handleTypeFilter(type: string) {
    setTypeFilter(type)
    loadSnapshots(type)
  }

  const duration = formatDuration(run.started_at, run.completed_at)
  const totalAssets = (run.assets_discovered || 0) + (run.assets_updated || 0)

  return (
    <div className="border border-border rounded-xl overflow-hidden">
      {/* Run header */}
      <button
        onClick={handleExpand}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/20 transition-colors text-left"
      >
        {expanded
          ? <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
          : <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
        }
        <StatusBadge status={run.status} />
        <Badge variant="outline" className="text-[10px]">{run.trigger_type || "manual"}</Badge>
        <span className="text-xs text-muted-foreground">{formatDate(run.started_at)}</span>
        <span className="text-xs text-muted-foreground/60">{duration}</span>
        <div className="flex-1" />
        <div className="flex items-center gap-3 text-xs">
          {run.assets_discovered > 0 && (
            <span className="text-green-500 font-medium">{run.assets_discovered} new</span>
          )}
          {run.assets_updated > 0 && (
            <span className="text-blue-500 font-medium">{run.assets_updated} updated</span>
          )}
          {run.assets_deleted > 0 && (
            <span className="text-red-500 font-medium">{run.assets_deleted} deleted</span>
          )}
          {totalAssets === 0 && <span className="text-muted-foreground">0 assets</span>}
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); copyToClipboard(run.id) }}
          className="p-1 text-muted-foreground hover:text-foreground transition-colors"
          title={`Copy run ID: ${run.id}`}
        >
          <Copy className="h-3 w-3" />
        </button>
      </button>

      {/* Run ID line + view toggle */}
      {expanded && (
        <div className="px-4 py-1.5 border-t border-border bg-muted/10 flex items-center gap-2 text-[10px] text-muted-foreground">
          <span className="font-mono">Run ID: {run.id}</span>
          {run.error_message && (
            <span className="text-red-500 ml-4">Error: {run.error_message}</span>
          )}
          <div className="flex-1" />
          <div className="flex items-center gap-0.5 rounded-md border border-border bg-background p-0.5">
            <button
              onClick={(e) => { e.stopPropagation(); setViewMode("list") }}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${viewMode === "list" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground"}`}
            >
              List
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setViewMode("json") }}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${viewMode === "json" ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground"}`}
            >
              JSON
            </button>
          </div>
          {snapshots.length > 0 && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  const jsonData = snapshots.map((s) => ({
                    _asset_type: s.asset_type_code,
                    _external_id: s.asset_external_id,
                    _status: s.status_code,
                    ...s.properties,
                  }))
                  copyToClipboard(JSON.stringify(jsonData, null, 2))
                }}
                className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors"
                title="Copy all as JSON"
              >
                <Copy className="h-3 w-3" />
                Copy JSON
              </button>
              <button
                onClick={async (e) => {
                  e.stopPropagation()
                  if (creatingDataset) return
                  setCreatingDataset(true)
                  try {
                    const records = snapshots.map((s) => ({
                      _asset_type: s.asset_type_code,
                      _external_id: s.asset_external_id,
                      _status: s.status_code,
                      ...s.properties,
                    }))
                    const ds = await createDataset(orgId, {
                      dataset_source_code: "connector_pull",
                      connector_instance_id: connectorId,
                      properties: {
                        name: `${connectorName} — ${formatDate(run.started_at)}`,
                        description: `Collection run ${run.id.slice(0, 8)} — ${Object.keys(typeSummary).length} asset types, ${snapshots.length} records`,
                        collection_run_id: run.id,
                      },
                    })
                    await addDatasetRecords(orgId, ds.id, { records })
                    onDatasetCreated?.(`Dataset created: ${ds.dataset_code} (${records.length} records)`)
                  } catch (err) {
                    onDatasetCreated?.(`Failed: ${err instanceof Error ? err.message : "Unknown error"}`)
                  } finally {
                    setCreatingDataset(false)
                  }
                }}
                className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium text-green-500 hover:bg-green-500/10 transition-colors"
                title="Create dataset from this collection"
              >
                {creatingDataset ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
                {creatingDataset ? "Creating..." : "Create Dataset"}
              </button>
            </>
          )}
        </div>
      )}

      {/* Expanded content — snapshots */}
      {expanded && (
        <div className="border-t border-border">
          {/* Type filter tabs */}
          {Object.keys(typeSummary).length > 0 && (
            <div className="flex items-center gap-1 px-4 py-2 border-b border-border bg-muted/5 flex-wrap">
              <button
                onClick={() => handleTypeFilter("")}
                className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-colors ${
                  !typeFilter ? "bg-primary/10 text-primary border border-primary/30" : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
                }`}
              >
                All ({Object.values(typeSummary).reduce((a, b) => a + b, 0)})
              </button>
              {Object.entries(typeSummary)
                .sort(([, a], [, b]) => b - a)
                .map(([type, count]) => (
                  <button
                    key={type}
                    onClick={() => handleTypeFilter(type)}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-medium transition-colors ${
                      typeFilter === type ? "bg-primary/10 text-primary border border-primary/30" : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
                    }`}
                  >
                    <AssetTypeIcon type={type} className="h-3 w-3" />
                    {assetTypeLabel(type)} ({count})
                  </button>
                ))}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Loading collection data...
            </div>
          ) : snapshots.length === 0 ? (
            <div className="px-4 py-6 text-center text-xs text-muted-foreground">
              No assets in this collection run
            </div>
          ) : viewMode === "json" ? (
            /* ── Full JSON view ─────────────────────────────────── */
            <div className="max-h-[600px] overflow-y-auto">
              <pre className="px-4 py-3 text-[11px] font-mono text-green-400 bg-[#0d1117] leading-relaxed whitespace-pre-wrap break-all">
                {JSON.stringify(
                  snapshots.map((s) => ({
                    _asset_type: s.asset_type_code,
                    _external_id: s.asset_external_id,
                    _status: s.status_code,
                    _snapshot_number: s.snapshot_number,
                    ...s.properties,
                  })),
                  null,
                  2,
                )}
              </pre>
            </div>
          ) : (
            /* ── List view ──────────────────────────────────────── */
            <div className="divide-y divide-border max-h-[600px] overflow-y-auto">
              {snapshots.map((snap) => (
                <div key={snap.snapshot_id}>
                  {/* Asset row */}
                  <button
                    onClick={() => setExpandedAsset(expandedAsset === snap.snapshot_id ? null : snap.snapshot_id)}
                    className="w-full flex items-center gap-3 px-4 py-2 hover:bg-muted/10 transition-colors text-left"
                  >
                    {expandedAsset === snap.snapshot_id
                      ? <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
                      : <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
                    }
                    <AssetTypeIcon type={snap.asset_type_code} className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    <Badge variant="outline" className="text-[9px] shrink-0">{assetTypeLabel(snap.asset_type_code)}</Badge>
                    <span className="text-xs font-mono text-foreground truncate">{snap.asset_external_id}</span>
                    <div className="flex-1" />
                    <span className="text-[10px] text-muted-foreground shrink-0">{snap.property_count} props</span>
                    <Badge variant="outline" className={`text-[9px] shrink-0 ${
                      snap.status_code === "active" ? "text-green-500 border-green-500/30" : ""
                    }`}>{snap.status_code}</Badge>
                  </button>

                  {/* Expanded: JSON per asset */}
                  {expandedAsset === snap.snapshot_id && (
                    <div className="px-4 pb-3 pt-1 bg-muted/5">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-mono text-muted-foreground">{snap.asset_external_id}</span>
                        <button
                          onClick={() => copyToClipboard(JSON.stringify({ _asset_type: snap.asset_type_code, _external_id: snap.asset_external_id, ...snap.properties }, null, 2))}
                          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <Copy className="h-3 w-3" />
                          Copy JSON
                        </button>
                      </div>
                      <div className="rounded-lg border border-border bg-[#0d1117] overflow-hidden">
                        <pre className="px-3 py-2 text-[11px] font-mono text-green-400 leading-relaxed whitespace-pre-wrap break-all max-h-[300px] overflow-y-auto">
                          {JSON.stringify(
                            { _asset_type: snap.asset_type_code, _external_id: snap.asset_external_id, _status: snap.status_code, ...snap.properties },
                            null,
                            2,
                          )}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {total > snapshots.length && (
                <div className="px-4 py-3 text-center text-xs text-muted-foreground">
                  Showing {snapshots.length} of {total} assets
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function ConnectorDetailPage() {
  const params = useParams()
  const connectorId = params.id as string
  const { selectedOrgId, ready } = useSandboxOrgWorkspace()

  const [connector, setConnector] = useState<ConnectorInstanceResponse | null>(null)
  const [runs, setRuns] = useState<CollectionRunResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)
  const [collecting, setCollecting] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true)
    setError(null)
    try {
      const [conn, runData] = await Promise.all([
        getConnector(connectorId),
        listCollectionRuns(selectedOrgId, connectorId),
      ])
      setConnector(conn)
      setRuns(runData.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load connector")
    } finally {
      setLoading(false)
    }
  }, [connectorId, selectedOrgId])

  useEffect(() => {
    if (ready && selectedOrgId) load()
  }, [ready, selectedOrgId, load])

  async function handleTest() {
    setTesting(true)
    setMessage(null)
    try {
      const result = await testConnector(connectorId)
      setMessage(`Test: ${result.health_status} — ${result.message}`)
      load()
    } catch (e) {
      setMessage(`Test failed: ${e instanceof Error ? e.message : "Unknown error"}`)
    } finally {
      setTesting(false)
    }
  }

  async function handleCollect() {
    if (!selectedOrgId) return
    setCollecting(true)
    setMessage(null)
    try {
      const run = await triggerCollection(selectedOrgId, connectorId)
      setMessage(`Collection started (run ${run.id.slice(0, 8)}…)`)
      // Refresh runs list
      setTimeout(() => load(), 2000)
    } catch (e) {
      setMessage(`Collection failed: ${e instanceof Error ? e.message : "Unknown error"}`)
    } finally {
      setCollecting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading connector...
      </div>
    )
  }

  if (error || !connector) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertCircle className="h-8 w-8 text-destructive mb-3 opacity-60" />
        <p className="text-sm text-muted-foreground mb-4">{error || "Connector not found"}</p>
        <Button variant="outline" size="sm" asChild>
          <Link href="/sandbox/connectors"><ArrowLeft className="h-3 w-3 mr-1" />Back to Connectors</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/sandbox/connectors"
        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-3 w-3" />
        Back to Connectors
      </Link>

      {/* Connector Header Card */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 rounded-xl bg-muted flex items-center justify-center shrink-0">
              <ConnectorIcon typeCode={connector.connector_type_code} className="h-6 w-6 text-foreground" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-lg font-semibold">{connector.name || connector.instance_code}</h1>
                <HealthBadge status={connector.health_status} />
              </div>
              <p className="text-xs font-mono text-muted-foreground mt-0.5">{connector.instance_code}</p>
              {connector.description && (
                <p className="text-sm text-muted-foreground mt-1">{connector.description}</p>
              )}
              <div className="flex items-center gap-3 mt-2 flex-wrap">
                <Badge variant="outline" className="text-xs">{connector.connector_type_name || connector.connector_type_code}</Badge>
                <Badge variant="outline" className="text-xs">{connector.connector_category_name || connector.connector_category_code}</Badge>
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {connector.collection_schedule || "Manual"}
                </span>
                {connector.last_collected_at && (
                  <span className="text-xs text-muted-foreground">
                    Last collected: {formatDate(connector.last_collected_at)}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={handleTest} disabled={testing}>
              {testing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Activity className="h-3 w-3" />}
              Test
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
              <Link href={`/sandbox/datasets?compose=true&connector_id=${connectorId}`}>
                <Layers className="h-3 w-3" />
                Compose Dataset
              </Link>
            </Button>
            <Button size="sm" className="gap-1.5 text-xs" onClick={handleCollect} disabled={collecting}>
              {collecting ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
              Collect Now
            </Button>
          </div>
        </div>
        {message && (
          <div className={`mt-3 rounded-lg border px-3 py-2 text-xs ${
            message.includes("failed") || message.includes("Error")
              ? "border-red-500/30 bg-red-500/5 text-red-500"
              : "border-green-500/30 bg-green-500/5 text-green-600 dark:text-green-400"
          }`}>
            {message}
          </div>
        )}
      </div>

      {/* Collection History */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            Collection History
            <Badge variant="outline" className="text-[10px]">{runs.length} runs</Badge>
          </h2>
          <Button variant="ghost" size="sm" className="text-xs gap-1" onClick={load}>
            <RefreshCw className="h-3 w-3" />
            Refresh
          </Button>
        </div>

        {runs.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border py-12 text-center">
            <RefreshCw className="h-8 w-8 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">No collections yet</p>
            <p className="text-xs text-muted-foreground/60 mt-1">Click &quot;Collect Now&quot; to trigger your first data collection</p>
          </div>
        ) : (
          <div className="space-y-2">
            {runs.map((run) => (
              <CollectionRunRow
                key={run.id}
                run={run}
                orgId={selectedOrgId!}
                connectorId={connectorId}
                connectorName={connector?.name || connector?.instance_code || ""}
                onDatasetCreated={(msg) => setMessage(msg)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
