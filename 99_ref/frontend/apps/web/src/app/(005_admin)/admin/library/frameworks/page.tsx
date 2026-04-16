"use client"

import { useEffect, useState, useCallback, useMemo, useRef } from "react"
import Link from "next/link"
import {
  Button,
  Input,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@kcontrol/ui"
import { useRouter } from "next/navigation"
import {
  Library,
  Search,
  RefreshCw,
  AlertCircle,
  ChevronRight,
  Clock,
  CheckCircle2,
  XCircle,
  FileText,
  Eye,
  Ban,
  X,
  Sparkles,
} from "lucide-react"
import { listFrameworks, rejectFramework } from "@/lib/api/grc"
import { createBuilderSession } from "@/lib/api/ai"
import { getSessionOrg, getSessionWorkspace } from "@/lib/api/apiClient"
import { useAccess } from "@/components/providers/AccessProvider"
import type { FrameworkResponse } from "@/lib/types/grc"

// ── Types ─────────────────────────────────────────────────────────────────────

type ApprovalStatusFilter = "all" | "draft" | "pending_review" | "approved" | "rejected"

// ── Toast ─────────────────────────────────────────────────────────────────────

type ToastMsg = { id: number; message: string; type: "success" | "error" }

function ToastContainer({ toasts, onDismiss }: { toasts: ToastMsg[]; onDismiss: (id: number) => void }) {
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-72">
      {toasts.map(t => (
        <div key={t.id} className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg border text-sm font-medium animate-in slide-in-from-bottom-2 ${
          t.type === "success"
            ? "bg-green-50 border-green-500/30 text-green-800"
            : "bg-red-50 border-red-500/30 text-red-800"
        }`}>
          {t.type === "success"
            ? <CheckCircle2 className="h-4 w-4 shrink-0 text-green-600" />
            : <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />}
          <span className="flex-1">{t.message}</span>
          <button onClick={() => onDismiss(t.id)} className="shrink-0 opacity-60 hover:opacity-100">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function approvalStatusBadge(status: string) {
  switch (status) {
    case "draft":
      return (
        <Badge variant="outline" className="text-[10px] font-medium bg-muted text-muted-foreground border-border">
          <FileText className="h-3 w-3 mr-1" />
          Draft
        </Badge>
      )
    case "pending_review":
      return (
        <Badge variant="outline" className="text-[10px] font-medium bg-amber-500/10 text-amber-600 border-amber-500/20">
          <Clock className="h-3 w-3 mr-1" />
          Pending Review
        </Badge>
      )
    case "approved":
      return (
        <Badge variant="outline" className="text-[10px] font-medium bg-green-500/10 text-green-600 border-green-500/20">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          Approved
        </Badge>
      )
    case "rejected":
      return (
        <Badge variant="outline" className="text-[10px] font-medium bg-red-500/10 text-red-600 border-red-500/20">
          <XCircle className="h-3 w-3 mr-1" />
          Rejected
        </Badge>
      )
    default:
      return (
        <Badge variant="outline" className="text-[10px] text-muted-foreground">
          {status}
        </Badge>
      )
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

// ── Status filter tabs ────────────────────────────────────────────────────────

const STATUS_FILTERS: Array<{ label: string; value: ApprovalStatusFilter }> = [
  { label: "All", value: "all" },
  { label: "Pending Review", value: "pending_review" },
  { label: "Approved", value: "approved" },
  { label: "Draft", value: "draft" },
  { label: "Rejected", value: "rejected" },
]

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminLibraryFrameworksPage() {
  const router = useRouter()
  const { isSuperAdmin } = useAccess()
  const [frameworks, setFrameworks] = useState<FrameworkResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<ApprovalStatusFilter>("all")
  const [revokingId, setRevokingId] = useState<string | null>(null)
  const [revokeTarget, setRevokeTarget] = useState<FrameworkResponse | null>(null)
  const [enhancingId, setEnhancingId] = useState<string | null>(null)

  // ── Toast ────────────────────────────────────────────────────────────────
  const [toasts, setToasts] = useState<ToastMsg[]>([])
  const toastIdRef = useRef(0)
  const addToast = useCallback((message: string, type: "success" | "error" = "success") => {
    const id = ++toastIdRef.current
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])
  const dismissToast = useCallback((id: number) => setToasts(prev => prev.filter(t => t.id !== id)), [])

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true)
    setError(null)
    try {
      const res = await listFrameworks()
      // Library = global templates (no org scope) + marketplace-visible + pending review
      const library = (res.items ?? []).filter(f => !f.scope_org_id || f.is_marketplace_visible || f.approval_status === "pending_review")
      setFrameworks(library)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load frameworks")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const counts = useMemo(() => {
    const result: Record<ApprovalStatusFilter, number> = {
      all: frameworks.length,
      draft: 0,
      pending_review: 0,
      approved: 0,
      rejected: 0,
    }
    for (const fw of frameworks) {
      if (fw.approval_status in result) {
        result[fw.approval_status as keyof typeof result]++
      }
    }
    return result
  }, [frameworks])

  const filtered = useMemo(() => {
    return frameworks.filter((fw) => {
      if (statusFilter !== "all" && fw.approval_status !== statusFilter) return false
      if (
        search &&
        !fw.name?.toLowerCase().includes(search.toLowerCase()) &&
        !fw.framework_code.toLowerCase().includes(search.toLowerCase()) &&
        !fw.publisher_name?.toLowerCase().includes(search.toLowerCase())
      )
        return false
      return true
    })
  }, [frameworks, search, statusFilter])

  const confirmRevoke = async () => {
    if (!revokeTarget) return
    const fw = revokeTarget
    setRevokeTarget(null)
    setRevokingId(fw.id)
    try {
      await rejectFramework(fw.id, "Approval revoked by admin")
      await load(true)
      addToast(`"${fw.name}" has been revoked from the marketplace`)
    } catch (e) {
      addToast(e instanceof Error ? e.message : "Failed to revoke", "error")
    } finally {
      setRevokingId(null)
    }
  }

  async function handleEnhanceWithAI(fw: FrameworkResponse) {
    setEnhancingId(fw.id)
    try {
      const session = await createBuilderSession({
        session_type: "enhance",
        framework_id: fw.id,
        framework_name: fw.name,
        framework_type_code: fw.framework_type_code,
        framework_category_code: fw.framework_category_code,
        scope_org_id: getSessionOrg(),
        scope_workspace_id: getSessionWorkspace(),
      })
      router.push(`/admin/library/frameworks/builder?session=${session.id}&tab=enhance`)
    } catch (e) {
      addToast(e instanceof Error ? e.message : "Failed to start enhance session", "error")
    } finally {
      setEnhancingId(null)
    }
  }

  // ── Loading skeleton ────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 rounded-md bg-muted animate-pulse" />
        <div className="h-9 w-80 rounded-md bg-muted animate-pulse" />
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-14 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight font-secondary">
            Framework Library Review
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Review and approve frameworks submitted for the marketplace
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/admin/library/frameworks/builder">
            <Button size="sm" className="h-8 gap-1.5 text-xs">
              <Sparkles className="h-3.5 w-3.5" />
              Create with AI
            </Button>
          </Link>
          {counts.pending_review > 0 && (
            <Badge className="bg-amber-500/15 text-amber-700 border-amber-500/30 font-medium gap-1">
              <Clock className="h-3 w-3" />
              {counts.pending_review} awaiting review
            </Badge>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => load(true)}
            disabled={refreshing}
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 flex items-center gap-3">
          <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
          <p className="text-sm text-destructive flex-1">{error}</p>
          <button className="text-xs underline text-destructive" onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search by name, code, or publisher..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 pr-7 h-8 text-sm"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-1 border-b border-border">
        {STATUS_FILTERS.map((sf) => (
          <button
            key={sf.value}
            type="button"
            onClick={() => setStatusFilter(sf.value)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
              statusFilter === sf.value
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {sf.label}
            {counts[sf.value] > 0 && (
              <span
                className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                  sf.value === "pending_review"
                    ? statusFilter === sf.value
                      ? "bg-amber-500/15 text-amber-700"
                      : "bg-amber-500/10 text-amber-600"
                    : statusFilter === sf.value
                      ? "bg-primary/15 text-primary"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {counts[sf.value]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
          <Library className="h-12 w-12 text-muted-foreground/40" />
          <p className="text-base font-medium text-muted-foreground">
            {search ? "No frameworks match your search" : "No frameworks in this status"}
          </p>
          {search && (
            <Button variant="ghost" size="sm" onClick={() => setSearch("")}>
              Clear search
            </Button>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-border overflow-hidden">
          {/* Table header */}
          <div className="grid grid-cols-[1fr_1.5fr_auto_auto_auto_auto] gap-x-4 px-4 py-2.5 bg-muted/50 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border">
            <span>Code</span>
            <span>Name</span>
            <span>Category</span>
            <span>Status</span>
            <span>Created</span>
            <span className="text-right">Actions</span>
          </div>

          {/* Rows */}
          <div className="divide-y divide-border">
            {filtered.map((fw) => (
              <div
                key={fw.id}
                className="grid grid-cols-[1fr_1.5fr_auto_auto_auto_auto] gap-x-4 px-4 py-3 items-center hover:bg-muted/30 transition-colors"
              >
                {/* Code */}
                <span className="text-xs font-mono text-muted-foreground truncate">
                  {fw.framework_code}
                </span>

                {/* Name — clickable to review/hierarchy */}
                <Link href={`/admin/library/frameworks/${fw.id}/review`} className="min-w-0 hover:text-primary transition-colors">
                  <p className="text-sm font-medium truncate hover:underline" title={fw.name ?? undefined}>{fw.name}</p>
                  {fw.publisher_name && (
                    <p className="text-[11px] text-muted-foreground truncate">
                      by {fw.publisher_name}
                    </p>
                  )}
                </Link>

                {/* Category */}
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {fw.category_name || fw.framework_category_code}
                </span>

                {/* Status badge */}
                <span>{approvalStatusBadge(fw.approval_status)}</span>

                {/* Created at */}
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {formatDate(fw.created_at)}
                </span>

                {/* Actions */}
                <div className="flex items-center gap-1.5 justify-end">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-xs gap-1 text-violet-600 hover:text-violet-700 hover:bg-violet-50"
                    onClick={() => handleEnhanceWithAI(fw)}
                    disabled={enhancingId === fw.id}
                    title="Enhance with AI"
                  >
                    {enhancingId === fw.id ? (
                      <RefreshCw className="h-3 w-3 animate-spin" />
                    ) : (
                      <Sparkles className="h-3 w-3" />
                    )}
                    Enhance
                  </Button>
                  {(fw.approval_status === "pending_review" || (fw.approval_status === "approved" && fw.has_pending_changes)) && (
                    <Link href={`/admin/library/frameworks/${fw.id}/review`}>
                      <Button size="sm" variant="outline" className="h-7 text-xs gap-1">
                        <Eye className="h-3 w-3" />
                        Review
                      </Button>
                    </Link>
                  )}
                  {fw.approval_status === "approved" && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs gap-1 text-destructive hover:text-destructive hover:bg-destructive/10 border-destructive/30"
                      onClick={() => setRevokeTarget(fw)}
                      disabled={revokingId === fw.id}
                    >
                      {revokingId === fw.id ? (
                        <RefreshCw className="h-3 w-3 animate-spin" />
                      ) : (
                        <Ban className="h-3 w-3" />
                      )}
                      Revoke
                    </Button>
                  )}
                  {(fw.approval_status === "draft" || fw.approval_status === "rejected") && (
                    <Link href={`/admin/library/frameworks/${fw.id}/review`}>
                      <Button size="sm" variant="ghost" className="h-7 text-xs gap-1">
                        <ChevronRight className="h-3 w-3" />
                        View
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer count */}
      {filtered.length > 0 && (
        <p className="text-xs text-muted-foreground">
          Showing {filtered.length} of {frameworks.length} frameworks
        </p>
      )}

      {/* Revoke confirmation dialog */}
      <Dialog open={!!revokeTarget} onOpenChange={open => { if (!open) setRevokeTarget(null) }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Revoke marketplace approval?</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">&ldquo;{revokeTarget?.name}&rdquo;</span> will be removed from the marketplace and unavailable for deployment.
            </p>
            <p className="text-xs text-muted-foreground">
              Existing deployments in organizations will not be affected.
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="ghost" size="sm" onClick={() => setRevokeTarget(null)}>Cancel</Button>
            <Button variant="destructive" size="sm" onClick={confirmRevoke}>
              <Ban className="h-3.5 w-3.5 mr-1.5" />
              Revoke Approval
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  )
}
