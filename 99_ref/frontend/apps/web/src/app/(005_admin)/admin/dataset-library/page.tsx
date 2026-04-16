"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import {
  Button,
  Input,
  Badge,
} from "@kcontrol/ui"
import {
  Database,
  Search,
  Star,
  Globe,
  Cloud,
  Server,
  Github,
  Plug,
  Tag,
  AlertTriangle,
  Archive,
  RefreshCw,
} from "lucide-react"
import {
  listGlobalDatasets,
  getGlobalDatasetStats,
  updateGlobalDataset,
  deprecateGlobalDataset,
} from "@/lib/api/sandbox"
import type { GlobalDatasetResponse, GlobalDatasetStatsResponse } from "@/lib/api/sandbox"
import { useAccess } from "@/components/providers/AccessProvider"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"

const TYPE_ICONS: Record<string, typeof Cloud> = {
  github: Github,
  aws: Cloud,
  azure: Cloud,
  gcp: Cloud,
  postgres: Database,
  mysql: Database,
  kubernetes: Server,
}

function getTypeIcon(code: string) {
  return TYPE_ICONS[code?.toLowerCase()] || Plug
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

export default function DatasetLibraryPage() {
  const { selectedOrgId } = useOrgWorkspace()
  const { isSuperAdmin } = useAccess()

  const [datasets, setDatasets] = useState<GlobalDatasetResponse[]>([])
  const [stats, setStats] = useState<GlobalDatasetStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterType, setFilterType] = useState("")
  const [filterCategory, setFilterCategory] = useState("")
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  function showSuccess(msg: string) {
    setSuccessMsg(msg)
    setTimeout(() => setSuccessMsg(null), 3500)
  }

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [dsRes, statsRes] = await Promise.all([
        listGlobalDatasets({
          search: search.trim() || undefined,
          connector_type_code: filterType || undefined,
          category: filterCategory || undefined,
          limit: 200,
        }),
        getGlobalDatasetStats(),
      ])
      setDatasets(dsRes.items)
      setStats(statsRes)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load datasets")
    } finally {
      setLoading(false)
    }
  }, [search, filterType, filterCategory])

  useEffect(() => { loadData() }, [loadData])

  const connectorTypes = useMemo(() => {
    return Object.keys(stats?.by_connector_type ?? {}).sort()
  }, [stats])

  const categories = useMemo(() => {
    return Object.keys(stats?.by_category ?? {}).sort()
  }, [stats])

  async function handleToggleFeatured(d: GlobalDatasetResponse) {
    if (!selectedOrgId) return
    setActionLoading(d.id)
    try {
      await updateGlobalDataset(d.id, selectedOrgId, { is_featured: !d.is_featured })
      showSuccess(d.is_featured ? "Removed from featured" : "Marked as featured")
      await loadData()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update")
    } finally {
      setActionLoading(null)
    }
  }

  async function handleDeprecate(d: GlobalDatasetResponse) {
    if (!selectedOrgId) return
    setActionLoading(d.id)
    try {
      await deprecateGlobalDataset(d.id, selectedOrgId)
      showSuccess("Dataset deprecated")
      await loadData()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to deprecate")
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-border">
        <div className="flex items-start gap-4">
          <div className="h-9 w-9 rounded-lg bg-emerald-500/10 flex items-center justify-center shrink-0 mt-0.5">
            <Globe className="h-5 w-5 text-emerald-500" />
          </div>
          <div>
            <h1 className="text-xl font-semibold leading-tight">Global Dataset Library</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Platform-managed dataset templates available to all organizations.
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={loadData} className="gap-1.5">
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-emerald-500 bg-card px-4 py-3">
            <Database className="h-4 w-4 text-emerald-500" />
            <div>
              <span className="text-2xl font-bold text-emerald-500">{stats.total}</span>
              <span className="text-[11px] text-muted-foreground block">Total Datasets</span>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-blue-500 bg-card px-4 py-3">
            <Plug className="h-4 w-4 text-blue-500" />
            <div>
              <span className="text-2xl font-bold text-blue-500">{Object.keys(stats.by_connector_type).length}</span>
              <span className="text-[11px] text-muted-foreground block">Connector Types</span>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-purple-500 bg-card px-4 py-3">
            <Tag className="h-4 w-4 text-purple-500" />
            <div>
              <span className="text-2xl font-bold text-purple-500">{Object.keys(stats.by_category).length}</span>
              <span className="text-[11px] text-muted-foreground block">Categories</span>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-amber-500 bg-card px-4 py-3">
            <Star className="h-4 w-4 text-amber-500" />
            <div>
              <span className="text-2xl font-bold text-amber-500">{stats.featured_count}</span>
              <span className="text-[11px] text-muted-foreground block">Featured</span>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-border">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search datasets..."
            className="pl-8 h-8 text-sm"
          />
        </div>
        <select
          className="h-8 rounded-md border border-border bg-background px-2.5 text-sm"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          <option value="">All Connector Types</option>
          {connectorTypes.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          className="h-8 rounded-md border border-border bg-background px-2.5 text-sm"
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Success message */}
      {successMsg && (
        <div className="mx-6 mt-3 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-xs text-green-600">
          {successMsg}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-lg bg-muted/30 animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <AlertTriangle className="h-8 w-8 text-destructive mb-3" />
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button variant="outline" size="sm" onClick={loadData} className="mt-3">Retry</Button>
          </div>
        ) : datasets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Database className="h-10 w-10 text-muted-foreground/30 mb-3" />
            <h3 className="text-lg font-semibold mb-2">No datasets in the global library</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Publish datasets from the Sandbox to make them available here.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {datasets.map((d) => {
              const TypeIcon = getTypeIcon(d.connector_type_code)
              const isDeprecated = d.publish_status === "deprecated"
              return (
                <div
                  key={d.id}
                  className={`group relative flex items-center gap-4 rounded-xl border border-l-[3px] bg-card px-4 py-3 transition-colors ${
                    isDeprecated
                      ? "border-l-muted opacity-60"
                      : d.is_featured
                        ? "border-l-amber-500 hover:bg-muted/20"
                        : "border-l-emerald-500 hover:bg-muted/20"
                  }`}
                >
                  {/* Icon */}
                  <div className="h-10 w-10 rounded-lg bg-muted/50 flex items-center justify-center shrink-0">
                    <TypeIcon className="h-5 w-5 text-muted-foreground" />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold truncate">{d.name || d.global_code}</h3>
                      {d.is_featured && <Star className="h-3 w-3 text-amber-500 fill-amber-500 shrink-0" />}
                      {isDeprecated && <Badge variant="outline" className="text-[9px] text-red-500 border-red-500/30">Deprecated</Badge>}
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge variant="secondary" className="text-[9px] font-mono">{d.connector_type_code}</Badge>
                      {d.category && <Badge variant="outline" className="text-[9px]">{d.category}</Badge>}
                      <code className="text-[10px] text-muted-foreground font-mono">{d.global_code}</code>
                      <span className="text-[10px] text-muted-foreground">v{d.version_number}</span>
                    </div>
                    {d.description && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{d.description}</p>
                    )}
                  </div>

                  {/* Metrics */}
                  <div className="hidden sm:flex items-center gap-4 shrink-0 text-center">
                    <div>
                      <span className="text-sm font-bold text-foreground">{d.record_count}</span>
                      <span className="text-[9px] text-muted-foreground block">Samples</span>
                    </div>
                    <div>
                      <span className="text-sm font-bold text-foreground">{d.download_count}</span>
                      <span className="text-[9px] text-muted-foreground block">Pulls</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-muted-foreground">{d.published_at ? formatDate(d.published_at) : "—"}</span>
                      <span className="text-[9px] text-muted-foreground block">Published</span>
                    </div>
                  </div>

                  {/* Actions */}
                  {isSuperAdmin && !isDeprecated && (
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={() => handleToggleFeatured(d)}
                        disabled={actionLoading === d.id}
                        className={`rounded-lg p-1.5 transition-colors ${
                          d.is_featured
                            ? "text-amber-500 hover:bg-amber-500/10"
                            : "text-muted-foreground hover:bg-amber-500/10 hover:text-amber-500"
                        }`}
                        title={d.is_featured ? "Remove from featured" : "Feature this dataset"}
                      >
                        <Star className={`h-3.5 w-3.5 ${d.is_featured ? "fill-current" : ""}`} />
                      </button>
                      <button
                        onClick={() => handleDeprecate(d)}
                        disabled={actionLoading === d.id}
                        className="rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors"
                        title="Deprecate"
                      >
                        <Archive className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
