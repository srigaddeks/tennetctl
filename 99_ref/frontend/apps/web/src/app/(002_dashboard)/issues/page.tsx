"use client"

import { useEffect, useState, useCallback } from "react"
import { Badge, Button, Input, Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, Tooltip, TooltipTrigger, TooltipContent } from "@kcontrol/ui"
import { Textarea } from "@/components/ui/textarea"
import {
  AlertCircle,
  Search,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Shield,
  Eye,
  ArrowRight,
  AlertTriangle,
  Github,
  Cloud,
  Server,
  Database,
  Plug,
  ChevronDown,
  ChevronUp,
  ListChecks,
  ArrowUpRight,
} from "lucide-react"
import { listIssues, getIssueStats, updateIssue, createTask } from "@/lib/api/grc"
import type { IssueResponse, IssueStatsResponse } from "@/lib/api/grc"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import Link from "next/link"

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high: "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium: "bg-amber-500/10 text-amber-500 border-amber-500/30",
  low: "bg-blue-500/10 text-blue-500 border-blue-500/30",
  info: "bg-muted text-muted-foreground border-border",
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: typeof CheckCircle2 }> = {
  open: { label: "Open", color: "text-red-500", icon: AlertCircle },
  investigating: { label: "Investigating", color: "text-amber-500", icon: Eye },
  remediated: { label: "Remediated", color: "text-blue-500", icon: Shield },
  verified: { label: "Verified", color: "text-emerald-500", icon: CheckCircle2 },
  closed: { label: "Closed", color: "text-muted-foreground", icon: CheckCircle2 },
  accepted: { label: "Risk Accepted", color: "text-purple-500", icon: Shield },
}

const TYPE_ICONS: Record<string, typeof Cloud> = {
  github: Github,
  aws: Cloud,
  azure: Cloud,
  postgres: Database,
  kubernetes: Server,
}

function getTypeIcon(code: string | null) {
  if (!code) return Plug
  return TYPE_ICONS[code.toLowerCase()] || Plug
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export default function IssuesPage() {
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace()
  const [issues, setIssues] = useState<IssueResponse[]>([])
  const [stats, setStats] = useState<IssueStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState("")
  const [filterSeverity, setFilterSeverity] = useState("")
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // UX Enhancements State
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set())
  const [remediateIssueId, setRemediateIssueId] = useState<string | null>(null)
  const [remediationNotes, setRemediationNotes] = useState("")
  const [fulfillmentMsg, setFulfillmentMsg] = useState<{ id: string; text: string; isError: boolean } | null>(null)
  const [trackedTasks, setTrackedTasks] = useState<Set<string>>(new Set())

  const toggleExpand = (id: string) => {
    const next = new Set(expandedIssues)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setExpandedIssues(next)
  }

  // Load search from URL parameters on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search)
      const q = urlParams.get('search')
      if (q) setSearch(q)
    }
  }, [])

  const load = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true)
    try {
      const [issuesRes, statsRes] = await Promise.all([
        listIssues({
          orgId: selectedOrgId,
          status_code: filterStatus || undefined,
          severity_code: filterSeverity || undefined,
          search: search.trim() || undefined,
          limit: 100,
        }),
        getIssueStats(selectedOrgId),
      ])
      setIssues(issuesRes.items)
      setStats(statsRes)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load issues")
    } finally {
      setLoading(false)
    }
  }, [selectedOrgId, filterStatus, filterSeverity, search])

  useEffect(() => {
    if (ready) load()
  }, [ready, load])

  async function handleStatusChange(issueId: string, newStatus: string) {
    if (newStatus === "remediated") {
      setRemediateIssueId(issueId)
      return
    }

    setActionLoading(issueId)
    try {
      await updateIssue(issueId, { status_code: newStatus })
      await load()
    } catch { /* ignore */ }
    finally { setActionLoading(null) }
  }

  async function handleMarkRemediatedSubmit() {
    if (!remediateIssueId) return
    setActionLoading(remediateIssueId)
    try {
      await updateIssue(remediateIssueId, {
        status_code: "remediated",
        remediation_notes: remediationNotes
      })
      setRemediateIssueId(null)
      setRemediationNotes("")
      await load()
    } catch { /* ignore */ }
    finally { setActionLoading(null) }
  }

  async function handleSendToFulfillment(issue: IssueResponse) {
    if (!selectedOrgId) return
    setActionLoading(`fill-${issue.id}`)
    try {
      await createTask({
        org_id: selectedOrgId,
        workspace_id: selectedWorkspaceId || undefined,
        title: `Remediate: ${issue.test_name || issue.test_code || issue.issue_code}`,
        description: `Automated remediation task generated from issue ${issue.issue_code}.\n\nSummary: ${issue.result_summary || ""}`,
        task_type_code: "control_remediation",
        priority_code: issue.severity_code === "info" ? "low" : issue.severity_code,
        entity_type: "issue",
        entity_id: issue.id,
      })
      setFulfillmentMsg({ id: issue.id, text: "Created! Head to Tasks to assign.", isError: false })
      setTrackedTasks(prev => new Set(prev).add(issue.id))
      if (issue.status_code === "open") {
        await updateIssue(issue.id, { status_code: "investigating" })
        await load()
      }
    } catch (e) {
      setFulfillmentMsg({ id: issue.id, text: "Failed to create task", isError: true })
      setTimeout(() => setFulfillmentMsg(null), 3000)
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-border">
        <div className="flex items-start gap-4">
          <div className="h-9 w-9 rounded-lg bg-red-500/10 flex items-center justify-center shrink-0 mt-0.5">
            <AlertCircle className="h-5 w-5 text-red-500" />
          </div>
          <div>
            <h1 className="text-xl font-semibold leading-tight">Issues</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Findings from failed control tests. Track investigation, remediation, and verification.
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={load} className="gap-1.5">
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 px-6 py-4 border-b border-border">
          <div
            onClick={() => setFilterStatus(filterStatus === "open" ? "" : "open")}
            className={`flex items-center gap-3 rounded-xl border border-l-[3px] border-l-red-500 bg-card px-4 py-3 cursor-pointer hover:bg-muted/50 transition-colors ${filterStatus === "open" ? "ring-2 ring-red-500/50 shadow-md transform -translate-y-0.5" : ""}`}
          >
            <AlertCircle className="h-4 w-4 text-red-500" />
            <div>
              <span className="text-2xl font-bold text-red-500">{stats.open}</span>
              <span className="text-[10px] text-muted-foreground block">Open</span>
            </div>
          </div>
          <div
            onClick={() => setFilterStatus(filterStatus === "investigating" ? "" : "investigating")}
            className={`flex items-center gap-3 rounded-xl border border-l-[3px] border-l-amber-500 bg-card px-4 py-3 cursor-pointer hover:bg-muted/50 transition-colors ${filterStatus === "investigating" ? "ring-2 ring-amber-500/50 shadow-md transform -translate-y-0.5" : ""}`}
          >
            <Eye className="h-4 w-4 text-amber-500" />
            <div>
              <span className="text-2xl font-bold text-amber-500">{stats.investigating}</span>
              <span className="text-[10px] text-muted-foreground block">Investigating</span>
            </div>
          </div>
          <div
            onClick={() => setFilterStatus(filterStatus === "remediated" ? "" : "remediated")}
            className={`flex items-center gap-3 rounded-xl border border-l-[3px] border-l-blue-500 bg-card px-4 py-3 cursor-pointer hover:bg-muted/50 transition-colors ${filterStatus === "remediated" ? "ring-2 ring-blue-500/50 shadow-md transform -translate-y-0.5" : ""}`}
          >
            <Shield className="h-4 w-4 text-blue-500" />
            <div>
              <span className="text-2xl font-bold text-blue-500">{stats.remediated}</span>
              <span className="text-[10px] text-muted-foreground block">Remediated</span>
            </div>
          </div>
          <div
            onClick={() => setFilterStatus(filterStatus === "closed" ? "" : "closed")}
            className={`flex items-center gap-3 rounded-xl border border-l-[3px] border-l-emerald-500 bg-card px-4 py-3 cursor-pointer hover:bg-muted/50 transition-colors ${filterStatus === "closed" ? "ring-2 ring-emerald-500/50 shadow-md transform -translate-y-0.5" : ""}`}
          >
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <div>
              <span className="text-2xl font-bold text-emerald-500">{stats.closed}</span>
              <span className="text-[10px] text-muted-foreground block">Closed</span>
            </div>
          </div>
          <div
            onClick={() => setFilterStatus("")}
            className={`flex items-center gap-3 rounded-xl border border-l-[3px] border-l-foreground bg-card px-4 py-3 cursor-pointer hover:bg-muted/50 transition-colors ${filterStatus === "" ? "ring-2 ring-foreground/30 shadow-md transform -translate-y-0.5" : ""}`}
          >
            <AlertTriangle className="h-4 w-4 text-foreground" />
            <div>
              <span className="text-2xl font-bold text-foreground">{stats.total}</span>
              <span className="text-[10px] text-muted-foreground block">Total</span>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-border">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search issues..." className="pl-8 h-8 text-sm" />
        </div>
        <select className="h-8 rounded-md border border-border bg-background px-2.5 text-sm" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="remediated">Remediated</option>
          <option value="verified">Verified</option>
          <option value="closed">Closed</option>
        </select>
        <select className="h-8 rounded-md border border-border bg-background px-2.5 text-sm" value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}>
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="h-20 rounded-lg bg-muted/30 animate-pulse" />)}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-16">
            <XCircle className="h-8 w-8 text-destructive mb-3" />
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        ) : issues.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <CheckCircle2 className="h-10 w-10 text-emerald-500/30 mb-3" />
            <h3 className="text-lg font-semibold mb-2">No issues found</h3>
            <p className="text-sm text-muted-foreground">All control tests are passing. No findings to report.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {issues.map((issue) => {
              const statusCfg = STATUS_CONFIG[issue.status_code] || STATUS_CONFIG.open
              const StatusIcon = statusCfg.icon
              const TypeIcon = getTypeIcon(issue.connector_type_code)
              const isActing = actionLoading === issue.id
              return (
                <div key={issue.id} className="rounded-xl border bg-card hover:bg-muted/20 transition-colors">
                  <div className="flex items-start gap-4 px-4 py-3">
                    {/* Status icon */}
                    <div className="mt-1">
                      <StatusIcon className={`h-5 w-5 ${statusCfg.color}`} />
                    </div>

                    {/* Main content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <code className="text-xs font-mono text-primary">{issue.issue_code}</code>
                        <Badge variant="outline" className={`text-[9px] ${SEVERITY_COLORS[issue.severity_code] || ""}`}>
                          {issue.severity_code}
                        </Badge>
                        <Badge variant="outline" className={`text-[9px] ${statusCfg.color}`}>
                          {statusCfg.label}
                        </Badge>
                        {issue.connector_type_code && (
                          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                            <TypeIcon className="h-3 w-3" />
                            {issue.connector_type_code}
                          </div>
                        )}
                      </div>
                      <h3 className="text-sm font-semibold mt-1 hover:text-primary transition-colors inline-block cursor-pointer">
                        {issue.promoted_test_id ? (
                          <Link href={`/tests/${issue.promoted_test_id}/live`} className="flex items-center gap-1.5 group">
                            {issue.test_name || issue.test_code || "Untitled Issue"}
                            <ArrowUpRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </Link>
                        ) : (
                          issue.test_name || issue.test_code || "Untitled Issue"
                        )}
                      </h3>
                      {issue.result_summary && (
                        <p className="text-xs text-muted-foreground mt-0.5">{issue.result_summary}</p>
                      )}
                      {issue.remediation_notes && (
                        <div className="mt-2 text-xs border-l-2 border-primary/40 pl-3 py-0.5 text-muted-foreground italic bg-muted/20 rounded-r-md">
                          "{issue.remediation_notes}"
                        </div>
                      )}
                      <div className="flex items-center gap-3 mt-2 text-[10px] text-muted-foreground">
                        <span><Clock className="h-3 w-3 inline mr-1" />{timeAgo(issue.created_at)}</span>
                        {issue.test_code && <span className="font-mono">{issue.test_code}</span>}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 shrink-0">
                      {fulfillmentMsg?.id === issue.id || trackedTasks.has(issue.id) ? (
                        <span className={`text-[10px] px-2 py-1 flex items-center font-bold ${fulfillmentMsg?.isError ? "text-red-500" : "text-emerald-500"}`}>
                          {fulfillmentMsg?.isError ? <XCircle className="h-3 w-3 mr-1" /> : <CheckCircle2 className="h-3 w-3 mr-1" />}
                          {fulfillmentMsg?.id === issue.id ? fulfillmentMsg.text : "Created! Head to Tasks to assign."}
                        </span>
                      ) : (
                        (issue.status_code === "open" || issue.status_code === "investigating") && (
                          <Tooltip delayDuration={0}>
                            <TooltipTrigger asChild>
                              <button
                                onClick={() => handleSendToFulfillment(issue)}
                                disabled={isActing || actionLoading === `fill-${issue.id}`}
                                className="text-[10px] px-2.5 py-1.5 flex items-center gap-1.5 rounded-md border border-border bg-card hover:bg-muted/50 transition-colors disabled:opacity-50 font-medium"
                              >
                                <ListChecks className="h-3.5 w-3.5 text-blue-500" /> Fulfillment Queue
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">
                              Generate a remediation Task for the engineering team
                            </TooltipContent>
                          </Tooltip>
                        )
                      )}

                      <div className="flex flex-col gap-1.5 items-end ml-2 border-l border-border/50 pl-4">
                        {issue.status_code === "open" && (
                          <Tooltip delayDuration={0}>
                            <TooltipTrigger asChild>
                              <button
                                onClick={() => handleStatusChange(issue.id, "investigating")}
                                disabled={isActing}
                                className="text-[10px] px-3 py-1.5 rounded-md bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 transition-colors disabled:opacity-50 font-semibold"
                              >
                                Investigate
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="left" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[200px]">
                              Acknowledge finding and begin looking for a fix
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {issue.status_code === "investigating" && (
                          <Tooltip delayDuration={0}>
                            <TooltipTrigger asChild>
                              <button
                                onClick={() => handleStatusChange(issue.id, "remediated")}
                                disabled={isActing}
                                className="text-[10px] px-3 py-1.5 rounded-md bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 transition-colors disabled:opacity-50 font-semibold"
                              >
                                Mark Remediated
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="left" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[200px]">
                              Provide notes on how this was fixed in your environment
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {issue.status_code === "remediated" && (
                          <Tooltip delayDuration={0}>
                            <TooltipTrigger asChild>
                              <button
                                onClick={() => handleStatusChange(issue.id, "verified")}
                                disabled={isActing}
                                className="text-[10px] px-3 py-1.5 rounded-md bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 transition-colors disabled:opacity-50 font-semibold"
                              >
                                Verify fix
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="left" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[200px]">
                              Confirm the fix worked in the newest Control Test run
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {issue.status_code === "verified" && (
                          <Tooltip delayDuration={0}>
                            <TooltipTrigger asChild>
                              <button
                                onClick={() => handleStatusChange(issue.id, "closed")}
                                disabled={isActing}
                                className="text-[10px] px-3 py-1.5 rounded-md bg-muted text-muted-foreground hover:bg-muted/80 transition-colors disabled:opacity-50 font-semibold"
                              >
                                Close Issue
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="left" className="text-xs bg-zinc-900 text-slate-100 border-none">
                              Archive this finding as fully resolved
                            </TooltipContent>
                          </Tooltip>
                        )}
                      </div>
                    </div>

                    {/* Details expansion */}
                    {issue.result_details && Array.isArray(issue.result_details) && issue.result_details.length > 0 && (
                      <div className="border-t border-border/30 bg-muted/5">
                        <button
                          onClick={() => toggleExpand(issue.id)}
                          className="w-full flex items-center justify-between px-4 py-2 hover:bg-muted/10 transition-colors text-xs text-muted-foreground font-medium"
                        >
                          <span className="flex items-center gap-2">
                            <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
                            {issue.result_details.length} failed asset{issue.result_details.length !== 1 ? 's' : ''} reported
                          </span>
                          {expandedIssues.has(issue.id) ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                        </button>

                        {expandedIssues.has(issue.id) && (
                          <div className="px-4 pb-3 pt-1">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                              {issue.result_details.map((detail: any, idx) => {
                                const check = detail.check || detail.asset_id || `Asset ${idx + 1}`
                                const msg = detail.message || detail.summary || "No specific details provided."
                                return (
                                  <div key={idx} className="bg-red-500/5 border border-red-500/10 rounded-md p-2 hover:bg-red-500/10 transition-colors group">
                                    <div className="text-[11px] font-semibold text-red-500 dark:text-red-400 mb-1 truncate" title={check as string}>
                                      {check}
                                    </div>
                                    <div className="text-[10px] text-muted-foreground leading-snug line-clamp-2 group-hover:line-clamp-none transition-all">
                                      {msg}
                                    </div>
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Mark Remediated Dialog */}
      <Dialog open={!!remediateIssueId} onOpenChange={(open) => !open && setRemediateIssueId(null)}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Mark Issue as Remediated</DialogTitle>
            <DialogDescription>
              Provide notes on how this failing control was resolved. This establishes an audit trail allowing the compliance team to easily verify the fix.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <label htmlFor="notes" className="text-sm font-medium">Remediation Notes</label>
              <Textarea
                id="notes"
                placeholder="e.g. Enabled 'Require Enforced Checks' in Github repository settings across all affected repos."
                value={remediationNotes}
                onChange={(e) => setRemediationNotes(e.target.value)}
                className="min-h-[100px]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRemediateIssueId(null)} disabled={!!actionLoading}>
              Cancel
            </Button>
            <Button onClick={handleMarkRemediatedSubmit} disabled={!remediationNotes.trim() || !!actionLoading}>
              Confirm Remediation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div >
  )
}
