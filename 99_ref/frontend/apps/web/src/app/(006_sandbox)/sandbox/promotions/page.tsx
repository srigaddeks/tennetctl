"use client"

import { useEffect, useState, useCallback } from "react"
import {
  Button,
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
  ArrowUpFromLine,
  Zap,
  FileCheck,
  Library,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  Eye,
  Filter,
  X,
} from "lucide-react"
import { listPromotions, getPromotion } from "@/lib/api/sandbox"
import type { PromotionResponse } from "@/lib/api/sandbox"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; border: string; icon: typeof Clock }> = {
  pending_review: { label: "Pending Review", bg: "bg-yellow-500/10", text: "text-yellow-500", border: "border-yellow-500/30", icon: Clock },
  approved:       { label: "Approved",       bg: "bg-blue-500/10",   text: "text-blue-500",   border: "border-blue-500/30",   icon: CheckCircle2 },
  promoted:       { label: "Promoted",       bg: "bg-green-500/10",  text: "text-green-500",  border: "border-green-500/30",  icon: CheckCircle2 },
  rejected:       { label: "Rejected",       bg: "bg-red-500/10",    text: "text-red-500",    border: "border-red-500/30",    icon: XCircle },
}

function statusConfig(status: string) {
  return STATUS_CONFIG[status] ?? { label: status.replace(/_/g, " "), bg: "bg-muted", text: "text-muted-foreground", border: "border-border", icon: AlertCircle }
}

function promotionBorderCls(status: string) {
  if (status === "promoted" || status === "approved") return "border-l-green-500"
  if (status === "pending_review") return "border-l-amber-500"
  if (status === "rejected") return "border-l-red-500"
  return "border-l-primary"
}

function sourceIcon(p: PromotionResponse) {
  if (p.signal_id) return { icon: Zap, color: "text-amber-500", bg: "bg-amber-500/10", label: "Signal" }
  if (p.policy_id) return { icon: FileCheck, color: "text-green-500", bg: "bg-green-500/10", label: "Control Test" }
  if (p.library_id) return { icon: Library, color: "text-teal-500", bg: "bg-teal-500/10", label: "Library" }
  return { icon: AlertCircle, color: "text-muted-foreground", bg: "bg-muted", label: "Unknown" }
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// Detail Dialog
// ─────────────────────────────────────────────────────────────────────────────

function PromotionDetailDialog({
  promotionId, onClose,
}: {
  promotionId: string | null
  onClose: () => void
}) {
  const [promo, setPromo] = useState<PromotionResponse | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!promotionId) { setPromo(null); return }
    setLoading(true)
    getPromotion(promotionId)
      .then(setPromo)
      .catch(() => { /* graceful */ })
      .finally(() => setLoading(false))
  }, [promotionId])

  if (!promotionId) return null

  const sc = promo ? statusConfig(promo.promotion_status) : null
  const si = promo ? sourceIcon(promo) : null
  const SourceIcon = si?.icon ?? AlertCircle
  const handleOpenChange = (o: boolean) => { if (!o) onClose() }

  return (
    <Dialog open onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-cyan-500/10 p-2.5"><Eye className="h-4 w-4 text-cyan-500" /></div>
            <div>
              <DialogTitle>Promotion Detail</DialogTitle>
              <DialogDescription>Full promotion record and review history.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        {loading ? (
          <div className="space-y-3 py-4">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-4 rounded bg-muted animate-pulse" />)}
          </div>
        ) : promo ? (
          <div className="space-y-4">
            {/* Source info */}
            <div className="flex items-center gap-3">
              <div className={`rounded-lg p-2 ${si?.bg}`}>
                <SourceIcon className={`h-4 w-4 ${si?.color}`} />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">{promo.source_name || promo.source_code || "Unnamed"}</p>
                <p className="text-xs text-muted-foreground">{si?.label} promotion</p>
              </div>
              <Badge variant="outline" className={`ml-auto text-[10px] font-semibold ${sc?.bg} ${sc?.text} ${sc?.border}`}>
                {sc?.label}
              </Badge>
            </div>

            {/* Detail rows */}
            <div className="rounded-lg border border-border bg-muted/20 divide-y divide-border text-sm">
              <div className="flex items-center justify-between px-4 py-2.5">
                <span className="text-xs text-muted-foreground">Promotion ID</span>
                <code className="text-xs font-mono text-foreground">{promo.id.slice(0, 8)}...</code>
              </div>
              {promo.source_code && (
                <div className="flex items-center justify-between px-4 py-2.5">
                  <span className="text-xs text-muted-foreground">Source Code</span>
                  <code className="text-xs font-mono text-foreground">{promo.source_code}</code>
                </div>
              )}
              {promo.target_test_code && (
                <div className="flex items-center justify-between px-4 py-2.5">
                  <span className="text-xs text-muted-foreground">Target GRC Test</span>
                  <code className="text-xs font-mono text-foreground">{promo.target_test_code}</code>
                </div>
              )}
              <div className="flex items-center justify-between px-4 py-2.5">
                <span className="text-xs text-muted-foreground">Created</span>
                <span className="text-xs text-foreground">{fmtDateTime(promo.created_at)}</span>
              </div>
              {promo.promoted_at && (
                <div className="flex items-center justify-between px-4 py-2.5">
                  <span className="text-xs text-muted-foreground">Promoted At</span>
                  <span className="text-xs text-foreground">{fmtDateTime(promo.promoted_at)}</span>
                </div>
              )}
              {promo.promoted_by && (
                <div className="flex items-center justify-between px-4 py-2.5">
                  <span className="text-xs text-muted-foreground">Promoted By</span>
                  <code className="text-xs font-mono text-foreground">{promo.promoted_by.slice(0, 8)}...</code>
                </div>
              )}
            </div>

            {/* Review notes */}
            {promo.review_notes && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Review Notes</p>
                <div className="rounded-lg border border-border bg-muted/20 px-4 py-3 text-sm text-foreground leading-relaxed">
                  {promo.review_notes}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground py-4">Failed to load promotion details.</p>
        )}
        <DialogFooter className="mt-3">
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function PromotionsPage() {
  const { selectedOrgId, ready } = useSandboxOrgWorkspace()
  const [promotions, setPromotions] = useState<PromotionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState("")
  const [detailId, setDetailId] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    if (!selectedOrgId) {
      setPromotions([])
      setLoading(false)
      setError(null)
      return
    }
    setLoading(true); setError(null)
    try {
      const res = await listPromotions({
        org_id: selectedOrgId,
        promotion_status: filterStatus || undefined,
      })
      setPromotions(res.items ?? [])
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to load promotions") }
    finally { setLoading(false) }
  }, [filterStatus, selectedOrgId])

  useEffect(() => {
    if (ready) void loadData()
  }, [loadData, ready])

  // Counts for flow visualization
  const pendingCount = promotions.filter((p) => p.promotion_status === "pending_review").length
  const approvedCount = promotions.filter((p) => p.promotion_status === "approved").length
  const promotedCount = promotions.filter((p) => p.promotion_status === "promoted").length
  const rejectedCount = promotions.filter((p) => p.promotion_status === "rejected").length

  // Active filter chips
  const activeFilters: { key: string; label: string; onRemove: () => void }[] = []
  if (filterStatus) {
    const sc = statusConfig(filterStatus)
    activeFilters.push({ key: "status", label: `Status: ${sc.label}`, onRemove: () => setFilterStatus("") })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="rounded-xl bg-cyan-500/10 p-3 shrink-0">
          <ArrowUpFromLine className="h-6 w-6 text-cyan-500" />
        </div>
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">Promotions</h2>
          <p className="text-sm text-muted-foreground">
            Track sandbox to production promotion history for signals, control tests, and libraries.
          </p>
        </div>
      </div>

      {/* Promotion flow visualization */}
      <div className="rounded-xl border border-border bg-muted/20 px-5 py-4 space-y-3">
        <h3 className="text-sm font-semibold text-foreground">Promotion Pipeline</h3>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2">
            <div className="rounded-md bg-amber-500/10 p-1.5">
              <Zap className="h-3.5 w-3.5 text-amber-500" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">Sandbox</span>
              <span className="text-[10px] text-muted-foreground">Build & test</span>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
          <div className="flex items-center gap-2 rounded-lg border border-yellow-500/30 bg-yellow-500/5 px-3 py-2">
            <div className="rounded-md bg-yellow-500/10 p-1.5">
              <Clock className="h-3.5 w-3.5 text-yellow-500" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">Review</span>
              <span className="text-[10px] text-yellow-500 font-semibold">{pendingCount} pending</span>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
          <div className="flex items-center gap-2 rounded-lg border border-blue-500/30 bg-blue-500/5 px-3 py-2">
            <div className="rounded-md bg-blue-500/10 p-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-blue-500" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">Approved</span>
              <span className="text-[10px] text-blue-500 font-semibold">{approvedCount} ready</span>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
          <div className="flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/5 px-3 py-2">
            <div className="rounded-md bg-green-500/10 p-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">Production</span>
              <span className="text-[10px] text-green-500 font-semibold">{promotedCount} deployed</span>
            </div>
          </div>
          {rejectedCount > 0 && (
            <>
              <span className="text-muted-foreground text-xs px-2">|</span>
              <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2">
                <div className="rounded-md bg-red-500/10 p-1.5">
                  <XCircle className="h-3.5 w-3.5 text-red-500" />
                </div>
                <div className="flex flex-col">
                  <span className="text-xs font-medium text-foreground">Rejected</span>
                  <span className="text-[10px] text-red-500 font-semibold">{rejectedCount}</span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* KPI stat cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          { label: "Total",          value: promotions.length, icon: ArrowUpFromLine, iconBg: "bg-cyan-500/10",   iconColor: "text-cyan-500",   numCls: "text-foreground",   borderCls: "border-l-primary" },
          { label: "Pending Review", value: pendingCount,       icon: Clock,          iconBg: "bg-yellow-500/10", iconColor: "text-yellow-500", numCls: "text-yellow-500",  borderCls: "border-l-amber-500" },
          { label: "Approved",       value: approvedCount,      icon: CheckCircle2,   iconBg: "bg-blue-500/10",   iconColor: "text-blue-500",   numCls: "text-blue-500",    borderCls: "border-l-blue-500" },
          { label: "Promoted",       value: promotedCount,      icon: CheckCircle2,   iconBg: "bg-green-500/10",  iconColor: "text-green-500",  numCls: "text-green-500",   borderCls: "border-l-green-500" },
        ].map((s) => (
          <div key={s.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}>
            <div className={`shrink-0 rounded-lg p-2 ${s.iconBg}`}>
              <s.icon className={`h-4 w-4 ${s.iconColor}`} />
            </div>
            <div className="flex flex-col min-w-0">
              <span className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5 text-muted-foreground" />
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="pending_review">Pending Review</option>
              <option value="approved">Approved</option>
              <option value="promoted">Promoted</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <Button size="sm" variant="ghost" className="h-9 gap-1" onClick={loadData}>
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </Button>
        </div>
        {/* Active filter chips */}
        {activeFilters.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] text-muted-foreground">Active filters:</span>
            {activeFilters.map((f) => (
              <span key={f.key} className="inline-flex items-center gap-1 rounded-md border border-border bg-muted/50 px-2 py-0.5 text-[11px] font-medium text-foreground">
                {f.label}
                <button onClick={f.onRemove} className="text-muted-foreground hover:text-foreground transition-colors">
                  <X className="h-2.5 w-2.5" />
                </button>
              </span>
            ))}
            <button
              onClick={() => setFilterStatus("")}
              className="text-[11px] text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="rounded-xl border border-l-[3px] border-l-primary border-border bg-card p-4 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-muted" />
                <div className="space-y-1 flex-1">
                  <div className="h-4 w-1/3 rounded bg-muted" />
                  <div className="h-3 w-1/4 rounded bg-muted" />
                </div>
                <div className="h-5 w-20 rounded bg-muted" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Promotions list */}
      {!loading && promotions.length > 0 && (
        <div className="space-y-2">
          {/* Table header */}
          <div className="grid grid-cols-[40px_1fr_1fr_120px_140px_80px] gap-3 px-4 py-2 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            <span>Type</span>
            <span>Source</span>
            <span>Target</span>
            <span>Status</span>
            <span>Date</span>
            <span className="text-right">Action</span>
          </div>

          {promotions.map((p) => {
            const si = sourceIcon(p)
            const sc = statusConfig(p.promotion_status)
            const StatusIcon = sc.icon
            const borderCls = promotionBorderCls(p.promotion_status)

            return (
              <div
                key={p.id}
                className={`relative grid grid-cols-[40px_1fr_1fr_120px_140px_80px] gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3 hover:bg-muted/10 transition-colors items-center`}
              >
                {/* Type icon */}
                <div className={`rounded-md p-1.5 w-7 h-7 flex items-center justify-center ${si.bg}`}>
                  <si.icon className={`h-3.5 w-3.5 ${si.color}`} />
                </div>

                {/* Source */}
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{p.source_name || p.source_code || "Unnamed"}</p>
                  <p className="text-[10px] text-muted-foreground font-mono truncate">{p.source_code || si.label}</p>
                </div>

                {/* Target */}
                <div className="min-w-0">
                  {p.target_test_code ? (
                    <code className="text-xs font-mono text-foreground">{p.target_test_code}</code>
                  ) : (
                    <span className="text-xs text-muted-foreground">Pending assignment</span>
                  )}
                </div>

                {/* Status */}
                <div>
                  <Badge variant="outline" className={`text-[10px] font-semibold gap-1 ${sc.bg} ${sc.text} ${sc.border}`}>
                    <StatusIcon className="h-2.5 w-2.5" />
                    {sc.label}
                  </Badge>
                </div>

                {/* Date */}
                <div className="text-xs text-muted-foreground">
                  {p.promoted_at ? fmtDate(p.promoted_at) : fmtDate(p.created_at)}
                </div>

                {/* Action */}
                <div className="text-right">
                  <Button size="sm" variant="ghost" className="h-6 text-xs gap-1" onClick={() => setDetailId(p.id)}>
                    <Eye className="h-3 w-3" /> View
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Review notes preview for pending items */}
      {!loading && promotions.filter((p) => p.promotion_status === "pending_review").length > 0 && (
        <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 px-5 py-4 space-y-2">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-yellow-500" />
            <h3 className="text-sm font-semibold text-foreground">Awaiting Review</h3>
          </div>
          <p className="text-xs text-muted-foreground">
            {promotions.filter((p) => p.promotion_status === "pending_review").length} promotion(s) require review
            before they can be deployed to production GRC tests.
          </p>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && promotions.length === 0 && (
        <div className="rounded-xl border border-dashed border-border bg-muted/10 px-5 py-12 text-center space-y-3">
          <ArrowUpFromLine className="h-8 w-8 text-muted-foreground mx-auto" />
          <p className="text-sm font-medium text-foreground">No promotions yet</p>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Promotions appear here when you promote signals, control tests, or libraries from the sandbox to production.
            Start by validating your controls in the sandbox environment.
          </p>
        </div>
      )}

      {/* Detail dialog */}
      <PromotionDetailDialog promotionId={detailId} onClose={() => setDetailId(null)} />
    </div>
  )
}
