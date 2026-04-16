"use client"

import { useEffect, useState, useCallback } from "react"
import { MessageSquare, Clock, CheckCircle, XCircle, Loader2, RefreshCw, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@kcontrol/ui"
import { listAllApprovals, approveAction, rejectApproval, type ApprovalResponse } from "@/lib/api/ai"

type StatusTab = "pending" | "approved" | "rejected" | "all"

const STATUS_CONFIG = {
  pending: { label: "Pending", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20", icon: Clock },
  approved: { label: "Approved", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", icon: CheckCircle },
  rejected: { label: "Rejected", color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20", icon: XCircle },
  executed: { label: "Executed", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20", icon: CheckCircle },
}

const OP_COLORS: Record<string, string> = {
  create: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  update: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  delete: "bg-red-500/10 text-red-400 border-red-500/20",
}

function ApprovalRow({ approval, onApprove, onReject }: {
  approval: ApprovalResponse
  onApprove: (id: string) => Promise<void>
  onReject: (id: string, reason: string) => Promise<void>
}) {
  const [expanded, setExpanded] = useState(false)
  const [acting, setActing] = useState(false)
  const [rejectReason, setRejectReason] = useState("")
  const [showReject, setShowReject] = useState(false)

  const status = approval.status_code as keyof typeof STATUS_CONFIG
  const statusMeta = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending
  const StatusIcon = statusMeta.icon
  const isPending = approval.status_code === "pending"

  const diffAfter = (approval.diff_json as { after?: Record<string, unknown> } | null)?.after
  const allKeys = diffAfter ? Object.keys(diffAfter).filter(k => !["id", "tenant_key", "created_at", "updated_at"].includes(k)) : []

  async function handleApprove() {
    setActing(true)
    try { await onApprove(approval.id) } catch { /* ignore */ }
    finally { setActing(false) }
  }

  async function handleReject() {
    if (!rejectReason.trim()) return
    setActing(true)
    try { await onReject(approval.id, rejectReason); setShowReject(false) } catch { /* ignore */ }
    finally { setActing(false) }
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <div className="flex items-start gap-3 px-4 py-3 cursor-pointer" onClick={() => setExpanded(e => !e)}>
        <StatusIcon className={`w-4 h-4 shrink-0 mt-0.5 ${statusMeta.color}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-mono font-medium">{approval.tool_name}</span>
            {approval.operation && (
              <span className={`text-[11px] px-1.5 py-0.5 rounded border ${OP_COLORS[approval.operation] ?? "bg-muted text-muted-foreground border-border"}`}>
                {approval.operation}
              </span>
            )}
            {approval.entity_type && (
              <span className="text-xs text-muted-foreground capitalize">{approval.entity_type.replace(/_/g, " ")}</span>
            )}
            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${statusMeta.bg} ${statusMeta.color} ${statusMeta.border}`}>
              {statusMeta.label}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            {new Date(approval.created_at).toLocaleString()}
            {approval.requester_id && ` · by ${approval.requester_id.slice(0, 8)}…`}
          </p>
        </div>
        <button className="p-1 rounded text-muted-foreground" onClick={e => { e.stopPropagation(); setExpanded(v => !v) }}>
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {expanded && (
        <div className="border-t border-border bg-muted/10 px-4 py-3 space-y-3">
          {allKeys.length > 0 && (
            <div className="rounded-lg bg-background border border-border overflow-hidden">
              <div className="grid grid-cols-[140px_1fr_1fr] text-[10px] font-bold uppercase tracking-wider text-muted-foreground border-b border-border">
                <div className="px-3 py-1.5 bg-muted/30 border-r border-border">Field</div>
                <div className="px-3 py-1.5 bg-red-500/5 border-r border-border">Before</div>
                <div className="px-3 py-1.5 bg-emerald-500/5">After</div>
              </div>
              {allKeys.map(key => {
                const before = (approval.diff_json as { before?: Record<string, unknown> } | null)?.before?.[key]
                const after = diffAfter![key]
                return (
                  <div key={key} className="grid grid-cols-[140px_1fr_1fr] text-xs border-b border-border/40 last:border-0">
                    <div className="px-3 py-2 text-muted-foreground font-mono bg-muted/20 border-r border-border/40 truncate">{key}</div>
                    <div className={`px-3 py-2 font-mono border-r border-border/40 ${before !== undefined ? "bg-red-500/10" : "bg-muted/10"}`}>
                      {before !== undefined ? <span className="text-red-400 line-through">{String(before)}</span> : <span className="text-muted-foreground/40 italic">—</span>}
                    </div>
                    <div className="px-3 py-2 font-mono bg-emerald-500/10">
                      <span className="text-emerald-400">{String(after)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {approval.rejection_reason && (
            <div className="rounded-lg bg-red-500/5 border border-red-500/20 px-3 py-2">
              <p className="text-[11px] font-semibold text-red-400 mb-0.5">Rejection reason</p>
              <p className="text-xs text-muted-foreground">{approval.rejection_reason}</p>
            </div>
          )}

          {isPending && (
            showReject ? (
              <div className="space-y-2">
                <input
                  value={rejectReason}
                  onChange={e => setRejectReason(e.target.value)}
                  placeholder="Reason for rejection…"
                  className="w-full h-8 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring"
                  autoFocus
                />
                <div className="flex gap-2">
                  <Button size="sm" variant="destructive" disabled={acting || !rejectReason.trim()} onClick={handleReject}>
                    {acting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
                    Confirm Reject
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowReject(false)}>Cancel</Button>
                </div>
              </div>
            ) : (
              <div className="flex gap-2">
                <Button size="sm" className="gap-1.5 bg-emerald-500 hover:bg-emerald-600" disabled={acting} onClick={handleApprove}>
                  {acting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                  Approve
                </Button>
                <Button size="sm" variant="outline" className="gap-1.5 text-red-400 border-red-500/30 hover:bg-red-500/10" disabled={acting} onClick={() => setShowReject(true)}>
                  <XCircle className="w-3.5 h-3.5" /> Reject
                </Button>
              </div>
            )
          )}
        </div>
      )}
    </div>
  )
}

export default function AIApprovalsPage() {
  const [tab, setTab] = useState<StatusTab>("pending")
  const [approvals, setApprovals] = useState<ApprovalResponse[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listAllApprovals(tab === "all" ? {} : { status_code: tab })
      setApprovals(res.items ?? [])
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [tab])

  useEffect(() => { load() }, [load])

  async function handleApprove(id: string) {
    await approveAction(id)
    setApprovals(prev => prev.map(a => a.id === id ? { ...a, status_code: "approved" } : a))
  }

  async function handleReject(id: string, reason: string) {
    await rejectApproval(id, reason)
    setApprovals(prev => prev.map(a => a.id === id ? { ...a, status_code: "rejected", rejection_reason: reason } : a))
  }

  const tabs: { id: StatusTab; label: string }[] = [
    { id: "pending", label: "Pending" },
    { id: "approved", label: "Approved" },
    { id: "rejected", label: "Rejected" },
    { id: "all", label: "All" },
  ]

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/15 flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold">AI Approvals</h1>
            <p className="text-sm text-muted-foreground">Review write operations requested by AI agents across all users.</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={load} className="gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-muted/40 p-1 w-fit">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${tab === t.id ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-16 rounded-xl bg-muted animate-pulse" />)}
        </div>
      ) : approvals.length === 0 ? (
        <div className="flex flex-col items-center py-16 gap-3 text-center">
          <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
            <MessageSquare className="w-6 h-6 text-muted-foreground/40" />
          </div>
          <p className="text-sm text-muted-foreground">No {tab === "all" ? "" : tab} approvals found.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {approvals.map(a => (
            <ApprovalRow key={a.id} approval={a} onApprove={handleApprove} onReject={handleReject} />
          ))}
        </div>
      )}
    </div>
  )
}
