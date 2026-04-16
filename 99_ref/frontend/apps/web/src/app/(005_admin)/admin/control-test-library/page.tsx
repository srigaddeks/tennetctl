"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import {
  Button,
  Input,
  Badge,
} from "@kcontrol/ui"
import {
  FlaskConical,
  Search,
  Star,
  Globe,
  Cloud,
  Server,
  Github,
  Plug,
  Database,
  Tag,
  AlertTriangle,
  Archive,
  RefreshCw,
  Shield,
  Zap,
  Link2,
  ChevronDown,
  ChevronUp,
  Code2,
  GitBranch,
  TestTubes,
  FileJson,
} from "lucide-react"
import {
  listGlobalControlTests,
  getGlobalControlTestStats,
  updateGlobalControlTest,
  deprecateGlobalControlTest,
} from "@/lib/api/sandbox"
import type { GlobalControlTestResponse, GlobalControlTestStatsResponse } from "@/lib/api/sandbox"
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

export default function ControlTestLibraryPage() {
  const { selectedOrgId } = useOrgWorkspace()
  const { isSuperAdmin } = useAccess()

  const [tests, setTests] = useState<GlobalControlTestResponse[]>([])
  const [stats, setStats] = useState<GlobalControlTestStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterType, setFilterType] = useState("")
  const [filterCategory, setFilterCategory] = useState("")
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  function showSuccess(msg: string) {
    setSuccessMsg(msg)
    setTimeout(() => setSuccessMsg(null), 3500)
  }

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [testsRes, statsRes] = await Promise.all([
        listGlobalControlTests({
          search: search.trim() || undefined,
          connector_type_code: filterType || undefined,
          category: filterCategory || undefined,
          limit: 200,
        }),
        getGlobalControlTestStats(),
      ])
      setTests(testsRes.items)
      setStats(statsRes)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load control tests")
    } finally {
      setLoading(false)
    }
  }, [search, filterType, filterCategory])

  useEffect(() => { loadData() }, [loadData])

  const connectorTypes = useMemo(() => Object.keys(stats?.by_connector_type ?? {}).sort(), [stats])
  const categories = useMemo(() => Object.keys(stats?.by_category ?? {}).sort(), [stats])

  async function handleToggleFeatured(t: GlobalControlTestResponse) {
    if (!selectedOrgId) return
    setActionLoading(t.id)
    try {
      await updateGlobalControlTest(t.id, selectedOrgId, { is_featured: !t.is_featured })
      showSuccess(t.is_featured ? "Removed from featured" : "Marked as featured")
      await loadData()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to update") }
    finally { setActionLoading(null) }
  }

  async function handleDeprecate(t: GlobalControlTestResponse) {
    if (!selectedOrgId) return
    setActionLoading(t.id)
    try {
      await deprecateGlobalControlTest(t.id, selectedOrgId)
      showSuccess("Control test deprecated")
      await loadData()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to deprecate") }
    finally { setActionLoading(null) }
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-border">
        <div className="flex items-start gap-4">
          <div className="h-9 w-9 rounded-lg bg-blue-500/10 flex items-center justify-center shrink-0 mt-0.5">
            <FlaskConical className="h-5 w-5 text-blue-500" />
          </div>
          <div>
            <h1 className="text-xl font-semibold leading-tight">Global Control Test Library</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Platform-managed control test bundles (signal + threat + control test + test dataset) for all organizations.
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
          <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-blue-500 bg-card px-4 py-3">
            <FlaskConical className="h-4 w-4 text-blue-500" />
            <div>
              <span className="text-2xl font-bold text-blue-500">{stats.total}</span>
              <span className="text-[11px] text-muted-foreground block">Control Tests</span>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-emerald-500 bg-card px-4 py-3">
            <Plug className="h-4 w-4 text-emerald-500" />
            <div>
              <span className="text-2xl font-bold text-emerald-500">{Object.keys(stats.by_connector_type).length}</span>
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
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search control tests..." className="pl-8 h-8 text-sm" />
        </div>
        <select className="h-8 rounded-md border border-border bg-background px-2.5 text-sm" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="">All Connector Types</option>
          {connectorTypes.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select className="h-8 rounded-md border border-border bg-background px-2.5 text-sm" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
          <option value="">All Categories</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {successMsg && (
        <div className="mx-6 mt-3 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-xs text-green-600">{successMsg}</div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="h-24 rounded-lg bg-muted/30 animate-pulse" />)}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <AlertTriangle className="h-8 w-8 text-destructive mb-3" />
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button variant="outline" size="sm" onClick={loadData} className="mt-3">Retry</Button>
          </div>
        ) : tests.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <FlaskConical className="h-10 w-10 text-muted-foreground/30 mb-3" />
            <h3 className="text-lg font-semibold mb-2">No control tests in the global library</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Publish signals from the Sandbox to create control test bundles.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {tests.map((t) => {
              const TypeIcon = getTypeIcon(t.connector_type_code)
              const isDeprecated = t.publish_status === "deprecated"
              const isExpanded = expandedId === t.id
              return (
                <div
                  key={t.id}
                  className={`relative rounded-xl border border-l-[3px] bg-card transition-colors ${
                    isDeprecated ? "border-l-muted opacity-60"
                      : t.is_featured ? "border-l-amber-500"
                        : "border-l-blue-500"
                  }`}
                >
                  {/* Header row — clickable to expand */}
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : t.id)}
                    className="w-full text-left flex items-center gap-4 px-4 py-3 hover:bg-muted/20 transition-colors rounded-xl"
                  >
                    <div className="h-10 w-10 rounded-lg bg-muted/50 flex items-center justify-center shrink-0">
                      <TypeIcon className="h-5 w-5 text-muted-foreground" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold truncate">{t.name || t.global_code}</h3>
                        {t.is_featured && <Star className="h-3 w-3 text-amber-500 fill-amber-500 shrink-0" />}
                        {isDeprecated && <Badge variant="outline" className="text-[9px] text-red-500 border-red-500/30">Deprecated</Badge>}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                        <Badge variant="secondary" className="text-[9px] font-mono">{t.connector_type_code}</Badge>
                        {t.category && <Badge variant="outline" className="text-[9px]">{t.category}</Badge>}
                        <code className="text-[10px] text-muted-foreground font-mono">{t.global_code}</code>
                        <span className="text-[10px] text-muted-foreground">v{t.version_number}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1.5">
                        <div className="flex items-center gap-1 text-[10px] text-blue-500">
                          <Zap className="h-3 w-3" />
                          {t.signal_count} signal{t.signal_count !== 1 ? "s" : ""}
                        </div>
                        {t.bundle.threat_type && (
                          <div className="flex items-center gap-1 text-[10px] text-amber-500">
                            <Shield className="h-3 w-3" />
                            threat: {t.bundle.threat_type.severity_code}
                          </div>
                        )}
                        {t.bundle.policy && (
                          <div className="flex items-center gap-1 text-[10px] text-purple-500">
                            <Globe className="h-3 w-3" />
                            control test: {t.bundle.policy.actions.length} action{t.bundle.policy.actions.length !== 1 ? "s" : ""}
                          </div>
                        )}
                        {t.bundle.test_dataset && (
                          <div className="flex items-center gap-1 text-[10px] text-teal-500">
                            <TestTubes className="h-3 w-3" />
                            {t.bundle.test_dataset.record_count} test records
                          </div>
                        )}
                        {t.bundle.dataset_template && (
                          <div className="flex items-center gap-1 text-[10px] text-emerald-500">
                            <FileJson className="h-3 w-3" />
                            {t.bundle.dataset_template.field_count} fields
                          </div>
                        )}
                        {t.linked_dataset_code && (
                          <div className="flex items-center gap-1 text-[10px] text-emerald-500">
                            <Link2 className="h-3 w-3" />
                            {t.linked_dataset_code}
                          </div>
                        )}
                      </div>
                      {!isExpanded && t.description && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{t.description}</p>
                      )}
                    </div>

                    <div className="hidden sm:flex items-center gap-4 shrink-0 text-center">
                      <div>
                        <span className="text-sm font-bold text-foreground">{t.download_count}</span>
                        <span className="text-[9px] text-muted-foreground block">Deploys</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-muted-foreground">{t.published_at ? formatDate(t.published_at) : "—"}</span>
                        <span className="text-[9px] text-muted-foreground block">Published</span>
                      </div>
                    </div>

                    {isSuperAdmin && !isDeprecated && (
                      <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => handleToggleFeatured(t)}
                          disabled={actionLoading === t.id}
                          className={`rounded-lg p-1.5 transition-colors ${t.is_featured ? "text-amber-500 hover:bg-amber-500/10" : "text-muted-foreground hover:bg-amber-500/10 hover:text-amber-500"}`}
                          title={t.is_featured ? "Remove from featured" : "Feature"}
                        >
                          <Star className={`h-3.5 w-3.5 ${t.is_featured ? "fill-current" : ""}`} />
                        </button>
                        <button
                          onClick={() => handleDeprecate(t)}
                          disabled={actionLoading === t.id}
                          className="rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors"
                          title="Deprecate"
                        >
                          <Archive className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    )}

                    {isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0" /> : <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />}
                  </button>

                  {/* Expanded bundle details */}
                  {isExpanded && (
                    <div className="px-4 pb-4 space-y-4 border-t border-border/30 pt-3">
                      {/* Description */}
                      {t.description && (
                        <p className="text-xs text-muted-foreground">{t.description}</p>
                      )}
                      {t.tags && (
                        <div className="flex items-center gap-1.5">
                          <Tag className="h-3 w-3 text-muted-foreground/50" />
                          <span className="text-[10px] text-muted-foreground">{t.tags}</span>
                        </div>
                      )}
                      {t.compliance_references && (
                        <p className="text-[10px] text-muted-foreground">Compliance: {t.compliance_references}</p>
                      )}

                      {/* Signals */}
                      {t.bundle.signals.length > 0 && (
                        <div className="rounded-lg border border-blue-500/20 bg-blue-500/[0.02] p-3 space-y-3">
                          <div className="flex items-center gap-2">
                            <Zap className="h-3.5 w-3.5 text-blue-500" />
                            <span className="text-xs font-medium text-blue-500 uppercase tracking-wide">
                              Signals ({t.bundle.signals.length})
                            </span>
                          </div>
                          {t.bundle.signals.map((sig, idx) => (
                            <div key={idx} className="rounded-md border border-border/30 bg-background/50 p-3 space-y-2">
                              <div className="flex items-center justify-between">
                                <div>
                                  <h4 className="text-xs font-semibold">{sig.name}</h4>
                                  <code className="text-[10px] text-muted-foreground font-mono">{sig.signal_code}</code>
                                </div>
                                <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                  {sig.connector_type_codes.map((ct) => (
                                    <Badge key={ct} variant="secondary" className="text-[9px]">{ct}</Badge>
                                  ))}
                                  <span>{sig.timeout_ms}ms</span>
                                  <span>{sig.max_memory_mb}MB</span>
                                </div>
                              </div>
                              {sig.description && <p className="text-[10px] text-muted-foreground">{sig.description}</p>}
                              <div className="rounded-md bg-muted/50 border border-border/20 p-2 max-h-48 overflow-y-auto">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <Code2 className="h-3 w-3 text-muted-foreground/60" />
                                  <span className="text-[9px] font-medium text-muted-foreground uppercase tracking-wide">Python Source</span>
                                </div>
                                <pre className="text-[10px] font-mono text-foreground/80 whitespace-pre-wrap break-all">{sig.python_source}</pre>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Threat Type */}
                      {t.bundle.threat_type && (
                        <div className="rounded-lg border border-amber-500/20 bg-amber-500/[0.02] p-3 space-y-2">
                          <div className="flex items-center gap-2">
                            <Shield className="h-3.5 w-3.5 text-amber-500" />
                            <span className="text-xs font-medium text-amber-500 uppercase tracking-wide">Threat Type</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="text-xs font-semibold">{t.bundle.threat_type.name}</h4>
                              <code className="text-[10px] text-muted-foreground font-mono">{t.bundle.threat_type.threat_code}</code>
                            </div>
                            <Badge variant="outline" className="text-[9px]">severity: {t.bundle.threat_type.severity_code}</Badge>
                          </div>
                          {t.bundle.threat_type.description && (
                            <p className="text-[10px] text-muted-foreground">{t.bundle.threat_type.description}</p>
                          )}
                          {t.bundle.threat_type.expression_tree && Object.keys(t.bundle.threat_type.expression_tree).length > 0 && (
                            <div className="rounded-md bg-muted/50 border border-border/20 p-2 max-h-32 overflow-y-auto">
                              <div className="flex items-center gap-1.5 mb-1">
                                <GitBranch className="h-3 w-3 text-muted-foreground/60" />
                                <span className="text-[9px] font-medium text-muted-foreground uppercase tracking-wide">Expression Tree</span>
                              </div>
                              <pre className="text-[10px] font-mono text-foreground/80 whitespace-pre-wrap">{JSON.stringify(t.bundle.threat_type.expression_tree, null, 2)}</pre>
                            </div>
                          )}
                          {t.bundle.threat_type.mitigation_guidance && (
                            <p className="text-[10px] text-muted-foreground"><strong>Mitigation:</strong> {t.bundle.threat_type.mitigation_guidance}</p>
                          )}
                        </div>
                      )}

                      {/* Control Test */}
                      {t.bundle.policy && (
                        <div className="rounded-lg border border-purple-500/20 bg-purple-500/[0.02] p-3 space-y-2">
                          <div className="flex items-center gap-2">
                            <Globe className="h-3.5 w-3.5 text-purple-500" />
                            <span className="text-xs font-medium text-purple-500 uppercase tracking-wide">Control Test</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="text-xs font-semibold">{t.bundle.policy.name}</h4>
                              <code className="text-[10px] text-muted-foreground font-mono">{t.bundle.policy.policy_code}</code>
                            </div>
                            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                              <span>{t.bundle.policy.actions.length} action{t.bundle.policy.actions.length !== 1 ? "s" : ""}</span>
                              {t.bundle.policy.cooldown_minutes > 0 && <span>cooldown: {t.bundle.policy.cooldown_minutes}min</span>}
                            </div>
                          </div>
                          {t.bundle.policy.description && (
                            <p className="text-[10px] text-muted-foreground">{t.bundle.policy.description}</p>
                          )}
                          {t.bundle.policy.actions.length > 0 && (
                            <div className="rounded-md bg-muted/50 border border-border/20 p-2 max-h-32 overflow-y-auto">
                              <span className="text-[9px] font-medium text-muted-foreground uppercase tracking-wide">Actions</span>
                              <pre className="text-[10px] font-mono text-foreground/80 whitespace-pre-wrap mt-1">{JSON.stringify(t.bundle.policy.actions, null, 2)}</pre>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Test Dataset */}
                      {t.bundle.test_dataset && (
                        <div className="rounded-lg border border-teal-500/20 bg-teal-500/[0.02] p-3 space-y-2">
                          <div className="flex items-center gap-2">
                            <TestTubes className="h-3.5 w-3.5 text-teal-500" />
                            <span className="text-xs font-medium text-teal-500 uppercase tracking-wide">
                              Test Dataset ({t.bundle.test_dataset.record_count} records)
                            </span>
                          </div>
                          <div>
                            <h4 className="text-xs font-semibold">{t.bundle.test_dataset.name || t.bundle.test_dataset.dataset_code}</h4>
                            {t.bundle.test_dataset.description && (
                              <p className="text-[10px] text-muted-foreground mt-0.5">{t.bundle.test_dataset.description}</p>
                            )}
                          </div>
                          {t.bundle.test_dataset.records.length > 0 && (
                            <div className="space-y-1.5 max-h-48 overflow-y-auto">
                              {t.bundle.test_dataset.records.slice(0, 5).map((rec, i) => (
                                <div key={i} className="rounded-md bg-muted/50 border border-border/20 p-2">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-[10px] font-medium">{rec.scenario_name || rec.record_name || `Record ${i + 1}`}</span>
                                    {rec.expected_result && (
                                      <Badge
                                        variant="outline"
                                        className={`text-[9px] ${
                                          rec.expected_result === "pass" ? "text-green-500 border-green-500/30"
                                            : rec.expected_result === "fail" ? "text-red-500 border-red-500/30"
                                              : "text-amber-500 border-amber-500/30"
                                        }`}
                                      >
                                        expects: {rec.expected_result}
                                      </Badge>
                                    )}
                                  </div>
                                  <pre className="text-[10px] font-mono text-foreground/80 whitespace-pre-wrap max-h-20 overflow-y-auto">
                                    {JSON.stringify(rec.record_data, null, 2)}
                                  </pre>
                                </div>
                              ))}
                              {t.bundle.test_dataset.records.length > 5 && (
                                <p className="text-[10px] text-muted-foreground text-center py-1">
                                  + {t.bundle.test_dataset.records.length - 5} more records
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Dataset Template */}
                      {t.bundle.dataset_template && (
                        <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/[0.02] p-3 space-y-2">
                          <div className="flex items-center gap-2">
                            <FileJson className="h-3.5 w-3.5 text-emerald-500" />
                            <span className="text-xs font-medium text-emerald-500 uppercase tracking-wide">
                              Dataset Template ({t.bundle.dataset_template.field_count} fields)
                            </span>
                          </div>
                          <p className="text-[10px] text-muted-foreground">
                            Expected data shape for <code className="font-mono">{t.bundle.dataset_template.connector_type_code}</code> connector
                          </p>
                          {Object.keys(t.bundle.dataset_template.json_schema).length > 0 && (
                            <div className="rounded-md bg-muted/50 border border-border/20 p-2 max-h-32 overflow-y-auto">
                              <span className="text-[9px] font-medium text-muted-foreground uppercase tracking-wide">Schema</span>
                              <pre className="text-[10px] font-mono text-foreground/80 whitespace-pre-wrap mt-1">
                                {JSON.stringify(t.bundle.dataset_template.json_schema, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}

                      {/* No dependencies indicator */}
                      {!t.bundle.threat_type && !t.bundle.policy && !t.bundle.test_dataset && (
                        <p className="text-xs text-muted-foreground italic">This bundle contains signal(s) only — no threat type, control test, or test dataset chain.</p>
                      )}
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
