"use client"

import { useState } from "react"
import { Check, XCircle, Loader2, AlertTriangle, ChevronRight } from "lucide-react"
import type { ApprovalResponse } from "@/lib/api/ai"

interface ApprovalModalProps {
  approval: ApprovalResponse
  queueLength: number          // total pending including this one
  onApprove: (id: string) => Promise<void>
  onReject: (id: string, reason: string) => Promise<void>
}

const OPERATION_META: Record<string, { label: string; color: string; bg: string; border: string }> = {
  create: { label: "Create", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/25" },
  update: { label: "Update", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/25" },
  delete: { label: "Delete", color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/25" },
}

function DiffRow({ field, before, after }: { field: string; before?: unknown; after?: unknown }) {
  const hasChanged = before !== undefined && String(before) !== String(after ?? "")
  const isNew = before === undefined

  return (
    <div className="grid grid-cols-[140px_1fr_1fr] gap-0 text-xs border-b border-border/40 last:border-0">
      <div className="px-3 py-2 text-muted-foreground font-mono font-medium bg-muted/20 border-r border-border/40 truncate">
        {field}
      </div>
      {/* Before */}
      <div className={`px-3 py-2 font-mono border-r border-border/40 ${isNew ? "bg-muted/10" : hasChanged ? "bg-red-500/10" : "bg-muted/10"}`}>
        {isNew ? (
          <span className="text-muted-foreground/40 italic">—</span>
        ) : (
          <span className={hasChanged ? "text-red-400 line-through" : "text-muted-foreground"}>
            {String(before ?? "")}
          </span>
        )}
      </div>
      {/* After */}
      <div className={`px-3 py-2 font-mono ${after !== undefined ? "bg-emerald-500/10" : "bg-muted/10"}`}>
        {after !== undefined ? (
          <span className="text-emerald-400">{String(after)}</span>
        ) : (
          <span className="text-muted-foreground/40 italic">—</span>
        )}
      </div>
    </div>
  )
}

export function ApprovalModal({ approval, queueLength, onApprove, onReject }: ApprovalModalProps) {
  const [acting, setActing] = useState(false)
  const [showReject, setShowReject] = useState(false)
  const [rejectReason, setRejectReason] = useState("")

  const op = approval.operation ?? "update"
  const meta = OPERATION_META[op] ?? OPERATION_META.update

  // Build diff entries
  const diffAfter = (approval.diff_json as { after?: Record<string, unknown> } | null)?.after ?? {}
  const diffBefore = (approval.diff_json as { before?: Record<string, unknown> } | null)?.before ?? {}
  const payload = approval.payload_json ?? {}

  // Collect all keys to display — prefer diff, fallback to payload
  const allKeys = Array.from(new Set([
    ...Object.keys(diffAfter),
    ...Object.keys(diffBefore),
    ...Object.keys(payload as Record<string, unknown>),
  ])).filter(k => !["id", "tenant_key", "created_at", "updated_at"].includes(k))

  async function handleApprove() {
    setActing(true)
    try { await onApprove(approval.id) } catch { /* ignore */ }
    finally { setActing(false) }
  }

  async function handleReject() {
    if (!rejectReason.trim()) return
    setActing(true)
    try { await onReject(approval.id, rejectReason) } catch { /* ignore */ }
    finally { setActing(false) }
  }

  return (
    // Full-screen backdrop
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Dialog */}
      <div className="relative w-full max-w-lg bg-background border border-border rounded-2xl shadow-2xl flex flex-col max-h-[90vh]">

        {/* Header */}
        <div className="flex items-start gap-3 px-5 py-4 border-b border-border shrink-0">
          <div className="w-9 h-9 rounded-xl bg-amber-500/15 flex items-center justify-center shrink-0 mt-0.5">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-bold text-foreground">Approval Required</span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold border ${meta.bg} ${meta.color} ${meta.border}`}>
                {meta.label}
              </span>
              {approval.entity_type && (
                <span className="text-xs text-muted-foreground capitalize">
                  {approval.entity_type.replace(/_/g, " ")}
                </span>
              )}
            </div>
            <p className="text-[11px] text-muted-foreground font-mono mt-0.5">{approval.tool_name}</p>
          </div>
          {queueLength > 1 && (
            <span className="shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 text-[11px] font-bold border border-amber-500/25">
              <ChevronRight className="w-3 h-3" />
              {queueLength - 1} more
            </span>
          )}
        </div>

        {/* Diff table */}
        {allKeys.length > 0 && (
          <div className="flex-1 overflow-auto min-h-0">
            {/* Column headers */}
            <div className="grid grid-cols-[140px_1fr_1fr] gap-0 text-[10px] font-bold uppercase tracking-wider text-muted-foreground border-b border-border/40 sticky top-0 bg-background z-10">
              <div className="px-3 py-1.5 bg-muted/30 border-r border-border/40">Field</div>
              <div className="px-3 py-1.5 bg-red-500/5 border-r border-border/40">Before</div>
              <div className="px-3 py-1.5 bg-emerald-500/5">After</div>
            </div>
            <div>
              {allKeys.map(key => (
                <DiffRow
                  key={key}
                  field={key}
                  before={diffBefore[key]}
                  after={diffAfter[key] ?? (payload as Record<string, unknown>)[key]}
                />
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="px-5 py-4 border-t border-border shrink-0 space-y-3">
          {showReject ? (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted-foreground">
                Reason for rejection
              </label>
              <textarea
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                placeholder="Explain why this change is being rejected…"
                rows={2}
                autoFocus
                className="w-full rounded-xl border border-input bg-muted/30 text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleReject}
                  disabled={acting || !rejectReason.trim()}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-500 text-white text-sm font-semibold disabled:opacity-50 hover:bg-red-600 transition-colors"
                >
                  {acting ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                  Confirm Reject
                </button>
                <button
                  onClick={() => { setShowReject(false); setRejectReason("") }}
                  className="px-4 py-2 rounded-xl text-sm text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 justify-end">
              <button
                onClick={() => setShowReject(true)}
                disabled={acting}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-red-500/30 text-red-400 text-sm font-semibold hover:bg-red-500/10 disabled:opacity-50 transition-colors"
              >
                <XCircle className="w-4 h-4" />
                Reject
              </button>
              <button
                onClick={handleApprove}
                disabled={acting}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 text-white text-sm font-semibold hover:bg-emerald-600 disabled:opacity-50 transition-colors"
              >
                {acting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Approve
              </button>
            </div>
          )}
          <p className="text-[10px] text-muted-foreground/50 text-center">
            This action will be executed immediately upon approval.
          </p>
        </div>
      </div>
    </div>
  )
}
