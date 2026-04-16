"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import { 
  Badge, 
  Button, 
  Card, 
  CardContent,
} from "@kcontrol/ui"
import {
  Activity,
  Shield,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Plug,
  Github,
  Cloud,
  Database,
  Server,
  AlertCircle,
  Zap,
  Signal,
  ArrowRight,
} from "lucide-react"
import { getMonitoringDashboard } from "@/lib/api/grc"
import type { MonitoringDashboardData } from "@/lib/api/grc"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"

// ── Helpers ───────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", { 
    hour: "2-digit", 
    minute: "2-digit", 
    second: "2-digit", 
    hour12: false 
  })
}

const TYPE_ICONS: Record<string, typeof Cloud> = {
  github: Github, aws: Cloud, azure: Cloud, gcp: Cloud, postgres: Database, kubernetes: Server,
}
function getTypeIcon(code: string) { return TYPE_ICONS[code?.toLowerCase()] || Plug }

// ── Components ────────────────────────────────────────────────────────────────

function KPIOverviewCard({
  label,
  value,
  accentClass,
  borderCls,
  description,
  icon: Icon,
}: {
  label: string;
  value: string;
  accentClass: string;
  borderCls: string;
  description: string;
  icon: typeof Activity;
}) {
  return (
    <Card className={`rounded-xl border bg-card border-l-[3px] ${borderCls} shadow-sm`}>
      <CardContent className="px-5 py-4 text-left">
        <div className="flex items-center justify-between mb-3 text-left">
          <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 text-left">
            {label}
          </p>
          <Icon className={`h-3.5 w-3.5 ${accentClass} opacity-60`} />
        </div>
        <div className="flex items-baseline gap-2 text-left">
          <span className={`text-2xl font-bold tabular-nums tracking-tight ${accentClass} text-left`}>
            {value}
          </span>
        </div>
        <p className="mt-1 text-[11px] text-muted-foreground font-medium text-left">{description}</p>
      </CardContent>
    </Card>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function MonitoringPage() {
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace()
  const [data, setData] = useState<MonitoringDashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [filterConnector, setFilterConnector] = useState("")
  const [filterAsset, setFilterAsset] = useState("")
  const [expandedExecId, setExpandedExecId] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!selectedOrgId || !selectedWorkspaceId) return
    try {
      const result = await getMonitoringDashboard(selectedOrgId, selectedWorkspaceId)
      setData(result)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [selectedOrgId, selectedWorkspaceId])

  useEffect(() => { if (ready && selectedOrgId && selectedWorkspaceId) load() }, [ready, selectedOrgId, selectedWorkspaceId, load])

  const d = data
  const passRate = d?.execution_summary.pass_rate ?? 0
  const passRateColor = passRate >= 90 ? "text-emerald-500" : passRate >= 70 ? "text-amber-500" : "text-red-500"

  const filteredExecutions = useMemo(() => {
    if (!d) return []
    return d.recent_executions.filter(e => {
      // Normalize comparison to prevent filter mismatch
      if (filterConnector && e.connector_type?.toLowerCase() !== filterConnector.toLowerCase()) return false
      if (filterAsset && e.connector_id !== filterAsset) return false
      return true
    })
  }, [d, filterConnector, filterAsset])

  const connectorTypes = useMemo(() => {
    if (!d) return []
    return [...new Set(d.connector_health.map(c => c.connector_type_code))]
  }, [d])

  if (loading && !data) {
    return <div className="flex items-center justify-center h-full"><RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" /></div>
  }
  if (!d) return null

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-background overflow-y-auto">
      
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-20">
        <div className="flex items-start gap-4 text-left">
          <div className="h-10 w-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0 mt-0.5 shadow-sm border border-emerald-500/20">
            <Activity className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2 text-left">
              <h1 className="text-xl font-bold tracking-tight text-left">Live Monitoring</h1>
            </div>
            <p className="text-xs text-muted-foreground mt-1 max-w-md text-left leading-relaxed">
              Real-time signal feed and drift detection across your connected infrastructure.
              {d.execution_summary.last_execution_at && ` Last signal ${timeAgo(d.execution_summary.last_execution_at)}.`}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={load} className="h-8 w-8 p-0">
            <RefreshCw className={`h-3.5 w-3.5 text-muted-foreground ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* ── KPI Stats Row ───────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 px-6 py-5 border-b border-border">
        <KPIOverviewCard 
          label="Signals / Session" 
          value={String(d.execution_summary.total_executions)} 
          borderCls={passRate >= 90 ? "border-l-emerald-500" : passRate >= 70 ? "border-l-amber-500" : "border-l-red-500"} 
          accentClass={passRateColor} 
          icon={Activity}
          description={`${Math.round(passRate)}% pass rate across sessions`}
        />
        <KPIOverviewCard 
          label="Controls Checked" 
          value={String(d.total_promoted_tests)} 
          borderCls="border-l-violet-500" 
          accentClass="text-violet-500" 
          icon={Shield}
          description={d.execution_summary.last_execution_at ? `Last scan ${timeAgo(d.execution_summary.last_execution_at)}` : "No scans recorded"}
        />
        <KPIOverviewCard 
          label="Drift Events" 
          value={String(d.execution_summary.fail_count)} 
          borderCls="border-l-amber-500" 
          accentClass="text-amber-500" 
          icon={AlertTriangle}
          description={`${d.open_issues.length} open finding${d.open_issues.length !== 1 ? "s" : ""} detected`}
        />
        <KPIOverviewCard 
          label="Sources Live" 
          value={String(d.total_connectors)} 
          borderCls="border-l-blue-500" 
          accentClass="text-blue-500" 
          icon={Server}
          description={`${d.connector_health.filter(c => c.health_status === "healthy" || c.health_status === "connected").length} sources reporting healthy`}
        />
      </div>

      {/* ── Filter bar ──────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-border bg-muted/20">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="h-6 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 border-none bg-transparent">
            Filters
          </Badge>
          <select
            className="h-8 rounded-md border border-border bg-background px-2.5 text-xs font-semibold"
            value={filterConnector}
            onChange={(e) => { setFilterConnector(e.target.value); setFilterAsset("") }}
          >
            <option value="">All Sources</option>
            {connectorTypes.map(ct => <option key={ct} value={ct}>{ct.replace(/_/g, " ").toUpperCase()}</option>)}
          </select>
          <select
            className="h-8 rounded-md border border-border bg-background px-2.5 text-xs font-semibold min-w-[160px]"
            value={filterAsset}
            onChange={(e) => setFilterAsset(e.target.value)}
          >
            <option value="">All Instances</option>
            {d.connector_health
              .filter(c => !filterConnector || c.connector_type_code === filterConnector)
              .map(c => (
                <option key={c.connector_id} value={c.connector_id}>
                  {c.connector_name || c.connector_id.slice(0, 12)}
                </option>
              ))
            }
          </select>
        </div>
        <div className="flex-1" />
        <span className="text-[11px] text-muted-foreground font-medium">
          Showing {filteredExecutions.length} recent signals
        </span>
      </div>

      <div className="px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 items-start">

          {/* ── Signal Feed ───────────────────────────────────────────────────── */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 px-1 text-left">
              <Zap className="h-4 w-4 text-emerald-500" />
              <h2 className="text-sm font-bold tracking-tight uppercase text-left">Recent Signal Activity</h2>
            </div>
            
            <div className="space-y-2">
              {filteredExecutions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 bg-muted/10 rounded-xl border border-dashed text-center">
                  <Signal className="h-10 w-10 text-muted-foreground/20 mb-3" />
                  <p className="text-sm text-muted-foreground text-center">No signals detected for current filters</p>
                </div>
              ) : (
                filteredExecutions.slice(0, 30).map((exec, idx) => {
                  const testName = exec.test_name || exec.test_code || "Untitled Probe"
                  const connType = exec.connector_type || "internal"
                  const isExpanded = expandedExecId === exec.execution_id
                  const StatusIcon = exec.result_status === "pass" ? CheckCircle2 : exec.result_status === "fail" ? XCircle : AlertCircle
                  const statusColor = exec.result_status === "pass" ? "text-emerald-500" : exec.result_status === "fail" ? "text-red-500 shadow-[0_0_8px_rgba(239,68,68,0.2)]" : "text-amber-500"
                  
                  return (
                    <div 
                      key={exec.execution_id || idx} 
                      className={`overflow-hidden rounded-xl border bg-card transition-all duration-200 ${isExpanded ? "ring-1 ring-primary/50 translate-x-0.5" : "hover:shadow-md hover:border-primary/20"}`}
                    >
                      <button
                        onClick={() => setExpandedExecId(isExpanded ? null : exec.execution_id)}
                        className="w-full text-left px-4 py-3 flex items-center gap-4 group"
                      >
                        <div className={`shrink-0 rounded-lg p-1.5 bg-background border border-border/10 ${statusColor}`}>
                          <StatusIcon className="h-4 w-4" />
                        </div>
                        
                        <div className="flex-1 min-w-0 text-left">
                          <div className="flex items-center gap-2 mb-0.5 text-left">
                            <span className="text-[10px] font-mono text-muted-foreground text-left">
                              {formatTime(exec.executed_at)}
                            </span>
                            <Badge variant="outline" className="text-[8px] font-bold uppercase tracking-tighter h-3.5 py-0">
                              {connType}
                            </Badge>
                            {exec.connector_name && (
                              <span className="text-[10px] text-muted-foreground bg-muted/50 px-1.5 rounded truncate max-w-[120px]">
                                {exec.connector_name}
                              </span>
                            )}
                          </div>
                          <h3 className="text-sm font-semibold text-foreground truncate text-left">{testName}</h3>
                        </div>

                        <div className="shrink-0 flex items-center gap-3">
                          <div className={`text-[10px] font-bold uppercase tracking-widest ${statusColor}`}>
                            {exec.result_status}
                          </div>
                          <div className="h-6 w-6 rounded-full group-hover:bg-muted flex items-center justify-center text-muted-foreground transition-colors">
                            <ArrowRight className={`h-3.5 w-3.5 transition-transform duration-300 ${isExpanded ? "rotate-90" : ""}`} />
                          </div>
                        </div>
                      </button>

                      {isExpanded && (
                        <div className="px-4 py-4 bg-muted/20 border-t border-border/50 animate-in slide-in-from-top-1 duration-200 text-left">
                          <div className="grid grid-cols-[80px_1fr] gap-x-4 gap-y-2 text-left">
                            <span className="text-[10px] font-bold text-muted-foreground uppercase text-left">Signal</span>
                            <span className="text-xs font-medium text-foreground text-left leading-relaxed">{exec.result_summary || "No summary provided"}</span>
                            
                            <span className="text-[10px] font-bold text-muted-foreground uppercase text-left">Source ID</span>
                            <code className="text-[10px] font-mono text-primary/70 text-left">{exec.connector_id}</code>
                            
                            {exec.test_code && (
                              <>
                                <span className="text-[10px] font-bold text-muted-foreground uppercase text-left">Control</span>
                                <code className="text-[10px] font-mono text-foreground/80 text-left">{exec.test_code}</code>
                              </>
                            )}
                          </div>
                          <div className="mt-4 flex justify-end">
                            <Button variant="outline" size="sm" className="text-[10px] h-7 font-bold" onClick={(e) => { e.stopPropagation(); window.location.href = `/issues?search=${exec.test_code || ""}` }}>
                              View History
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          </div>

          {/* ── Side Panels ───────────────────────────────────────────────────── */}
          <div className="space-y-6">
            
            {/* Health Panel */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 px-1 text-left">
                <Activity className="h-4 w-4 text-primary" />
                <h2 className="text-[11px] font-bold tracking-widest uppercase text-muted-foreground text-left semi-bold">Infrastructure</h2>
              </div>
              <Card className="rounded-xl shadow-sm overflow-hidden border">
                <div className="divide-y divide-border/40">
                  {d.connector_health.map((c) => {
                    const TypeIcon = getTypeIcon(c.connector_type_code)
                    const isHealthy = c.health_status === "healthy" || c.health_status === "connected"
                    return (
                      <div key={c.connector_id} className="flex items-center justify-between px-4 py-3 hover:bg-muted/20 transition-colors text-left">
                        <div className="flex items-center gap-3 text-left">
                          <div className="h-8 w-8 rounded-lg bg-muted/50 flex items-center justify-center shrink-0 border border-border/10 shadow-inner">
                            <TypeIcon className="h-4 w-4 text-foreground/70" />
                          </div>
                          <div className="text-left">
                            <p className="text-[11px] font-bold text-foreground leading-none mb-1 text-left">
                              {c.connector_name || "Source " + c.connector_id.slice(0, 6)}
                            </p>
                            <p className="text-[9px] font-mono text-muted-foreground uppercase tracking-tighter text-left">
                              {c.connector_type_code}
                            </p>
                          </div>
                        </div>
                        {isHealthy ? (
                          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                            <div className="h-1 w-1 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-[9px] font-bold uppercase tracking-wider">Live</span>
                          </div>
                        ) : (
                          <Badge variant="outline" className="text-[9px] font-bold bg-amber-500/5 text-amber-500 border-amber-500/20 py-0 h-4">
                            {c.health_status}
                          </Badge>
                        )}
                      </div>
                    )
                  })}
                </div>
              </Card>
            </div>

            {/* Findings Panel */}
            <div className="space-y-3">
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2 text-left">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <h2 className="text-[11px] font-bold tracking-widest uppercase text-muted-foreground text-left">Findings</h2>
                </div>
                {d.open_issues.length > 0 && (
                  <Badge className="bg-red-500 text-white border-none h-4 px-1 text-[9px] font-bold">
                    {d.open_issues.length}
                  </Badge>
                )}
              </div>
              <Card className="rounded-xl shadow-sm border-t-2 border-t-red-500/30 overflow-hidden">
                <div className="max-h-[300px] overflow-y-auto">
                  {d.open_issues.length === 0 ? (
                    <div className="px-4 py-10 text-center">
                      <CheckCircle2 className="h-8 w-8 text-emerald-500/10 mx-auto mb-3" />
                      <p className="text-xs font-semibold text-foreground">All Clear</p>
                      <p className="text-[10px] text-muted-foreground mt-1 px-4 text-center leading-relaxed">No active drifts or findings identified in the environment.</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-border/20">
                      {d.open_issues.map((issue) => (
                        <a 
                          href={`/issues?search=${issue.title || ""}`}
                          key={issue.task_id} 
                          className="block px-4 py-3 hover:bg-muted/30 transition-colors group"
                        >
                          <div className="flex items-start gap-3">
                            <div className={`mt-1.5 h-1.5 w-1.5 rounded-full shrink-0 ${
                              issue.priority_code === "critical" ? "bg-red-500 shadow-[0_0_4px_rgba(239,68,68,0.5)]" :
                              issue.priority_code === "high" ? "bg-red-400" : "bg-amber-500"
                            }`} />
                            <div className="min-w-0 flex-1 text-left">
                              <p className="text-[11px] font-bold text-foreground leading-snug group-hover:text-primary transition-colors text-left truncate">
                                {issue.title || "Untitled Finding"}
                              </p>
                              <div className="flex items-center justify-between mt-1 text-left">
                                <span className="text-[9px] text-muted-foreground font-medium text-left">
                                  {timeAgo(issue.created_at)}
                                </span>
                                <span className="text-[9px] font-mono text-primary/40 text-left">
                                  {issue.task_id.slice(0, 8)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </a>
                      ))}
                    </div>
                  )}
                </div>
                {d.open_issues.length > 0 && (
                  <div className="p-2 border-t border-border/20 bg-muted/10">
                    <Button variant="ghost" size="sm" className="w-full h-7 text-[10px] font-bold text-muted-foreground hover:text-primary" asChild>
                      <a href="/issues">View All Findings <ArrowRight className="h-3 w-3 ml-1.5" /></a>
                    </Button>
                  </div>
                )}
              </Card>
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}
