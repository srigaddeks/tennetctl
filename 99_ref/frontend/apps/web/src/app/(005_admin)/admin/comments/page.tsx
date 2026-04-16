"use client"

import { useCallback, useEffect, useState } from "react"
import { Button, Input, Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@kcontrol/ui"
import {
  MessageSquare,
  AlertCircle,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Trash2,
  RotateCcw,
  Pin,
  CheckCircle2,
  Search,
  X,
  Shield,
  Loader2,
  Eye,
  Globe,
  Lock,
  Bot,
} from "lucide-react"
import { fetchWithAuth } from "@/lib/api/apiClient"
import {
  gdprPreviewUserComments,
  gdprDeleteUserComments,
} from "@/lib/api/comments"
import type { GdprUserCommentsPreview, GdprCommentDeleteResult } from "@/lib/api/comments"
import type { CommentRecord } from "@/lib/types/comments"

// ── Constants ─────────────────────────────────────────────────────────────────

const PAGE_SIZE = 50

const ENTITY_TYPES = [
  "task",
  "risk",
  "control",
  "framework",
  "test",
  "evidence_template",
  "requirement",
  "feedback_ticket",
] as const

// ── Helpers ───────────────────────────────────────────────────────────────────

function entityTypeBadgeClass(type: string): string {
  switch (type) {
    case "task":      return "bg-cyan-500/10 text-cyan-600 border-cyan-500/20"
    case "risk":      return "bg-red-500/10 text-red-600 border-red-500/20"
    case "control":   return "bg-blue-500/10 text-blue-600 border-blue-500/20"
    case "framework": return "bg-purple-500/10 text-purple-600 border-purple-500/20"
    case "workspace": return "bg-teal-500/10 text-teal-600 border-teal-500/20"
    case "org":       return "bg-green-500/10 text-green-600 border-green-500/20"
    default:          return "bg-muted text-muted-foreground border-border"
  }
}

/** Derive a comment "type" for display purposes.
 *  - system: locked (platform-generated lock action) or no author display name + no email
 *  - internal: visibility === 'internal'
 *  - external: visibility === 'external'
 */
function commentType(comment: CommentRecord): "internal" | "external" | "system" {
  if (comment.is_locked) return "system"
  if (comment.visibility === "external") return "external"
  return "internal"
}

function rowBorderClsByType(type: "internal" | "external" | "system"): string {
  switch (type) {
    case "internal": return "border-l-blue-500"
    case "external": return "border-l-green-500"
    case "system":   return "border-l-slate-400"
  }
}

// ── Admin API calls ───────────────────────────────────────────────────────────

interface AdminCommentListResponse {
  items: CommentRecord[]
  total: number
  page: number
  per_page: number
  has_next: boolean
}

interface CommentStatsResponse {
  total: number
  today: number
  deleted: number
  pinned: number
  top_mentioned: Array<{ user_id: string; display_name: string | null; mention_count: number }>
}

async function adminListComments(opts: {
  page: number
  per_page: number
  q?: string
  entity_type?: string
  is_deleted?: boolean
  is_pinned?: boolean
  resolved?: boolean
  date_from?: string
  date_to?: string
}): Promise<AdminCommentListResponse> {
  const params = new URLSearchParams()
  params.set("page", String(opts.page))
  params.set("per_page", String(opts.per_page))
  if (opts.q)           params.set("q", opts.q)
  if (opts.entity_type) params.set("entity_type", opts.entity_type)
  if (opts.is_deleted !== undefined) params.set("is_deleted", String(opts.is_deleted))
  if (opts.is_pinned  !== undefined) params.set("is_pinned",  String(opts.is_pinned))
  if (opts.resolved   !== undefined) params.set("resolved",   String(opts.resolved))
  if (opts.date_from)  params.set("date_from", opts.date_from)
  if (opts.date_to)    params.set("date_to",   opts.date_to)

  const res = await fetchWithAuth(`/api/v1/cm/admin/comments?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to list comments")
  return data as AdminCommentListResponse
}

async function adminGetStats(): Promise<CommentStatsResponse> {
  const res = await fetchWithAuth("/api/v1/cm/admin/comments/stats")
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to load stats")
  return data as CommentStatsResponse
}

async function adminHardDeleteComment(commentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/cm/admin/comments/${commentId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || data.error?.message || "Failed to hard-delete comment")
  }
}

async function adminUndeleteComment(commentId: string): Promise<CommentRecord> {
  const res = await fetchWithAuth(`/api/v1/cm/admin/comments/${commentId}/undelete`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to undelete comment")
  return data as CommentRecord
}

async function adminSoftDeleteComment(commentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/cm/admin/comments/${commentId}/soft-delete`, { method: "POST" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || data.error?.message || "Failed to soft-delete comment")
  }
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SkeletonRow({ cols }: { cols: number }) {
  return (
    <tr className="border-b border-border">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-3.5 rounded bg-muted animate-pulse" style={{ width: `${40 + (i * 19) % 45}%` }} />
        </td>
      ))}
    </tr>
  )
}

function TypeBadge({ type }: { type: "internal" | "external" | "system" }) {
  if (type === "internal") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-blue-500/20 bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-600">
        <Lock className="h-2.5 w-2.5" />
        Internal
      </span>
    )
  }
  if (type === "external") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-green-500/20 bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600">
        <Globe className="h-2.5 w-2.5" />
        External
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-border bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
      <Bot className="h-2.5 w-2.5" />
      System
    </span>
  )
}

function StatusBadge({ comment }: { comment: CommentRecord }) {
  const badges: React.ReactNode[] = []

  if (comment.is_deleted) {
    badges.push(
      <span key="del" className="inline-flex items-center rounded-md border border-red-500/20 bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-600">
        Deleted
      </span>
    )
  }
  if (comment.pinned) {
    badges.push(
      <span key="pin" className="inline-flex items-center gap-1 rounded-md border border-amber-500/20 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600">
        <Pin className="h-2.5 w-2.5" />
        Pinned
      </span>
    )
  }
  if (comment.resolved) {
    badges.push(
      <span key="res" className="inline-flex items-center gap-1 rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600">
        <CheckCircle2 className="h-2.5 w-2.5" />
        Resolved
      </span>
    )
  }
  if (badges.length === 0) {
    badges.push(
      <span key="active" className="inline-flex items-center rounded-md border border-border bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
        Active
      </span>
    )
  }

  return <div className="flex flex-wrap gap-1">{badges}</div>
}

interface CommentRowProps {
  comment: CommentRecord
  onDelete: (id: string) => void
  onHardDelete: (id: string) => void
  onUndelete: (id: string) => void
  actionInFlight: string | null
}

function CommentRow({ comment, onDelete, onHardDelete, onUndelete, actionInFlight }: CommentRowProps) {
  const excerpt = comment.content.length > 120 ? comment.content.slice(0, 120) + "…" : comment.content
  const isActing = actionInFlight === comment.id
  const type = commentType(comment)
  const borderCls = rowBorderClsByType(type)

  return (
    <tr className={`border-b border-border border-l-[3px] ${borderCls} hover:bg-muted/20 transition-colors`}>
      {/* Excerpt */}
      <td className="px-4 py-3 max-w-[280px]">
        <p className="text-xs text-foreground leading-snug line-clamp-2" title={comment.content}>
          {comment.is_deleted ? (
            <span className="italic text-muted-foreground">[deleted content]</span>
          ) : (
            excerpt
          )}
        </p>
        {comment.is_edited && (
          <span className="text-[10px] text-muted-foreground italic">edited</span>
        )}
      </td>

      {/* Author */}
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex flex-col">
          <span className="text-xs font-medium text-foreground">
            {comment.author_display_name || comment.author_email || "Unknown"}
          </span>
          <span className="font-mono text-[10px] text-muted-foreground">
            {comment.author_user_id.slice(0, 8)}…
          </span>
        </div>
      </td>

      {/* Entity */}
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex flex-col gap-0.5">
          <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium w-fit ${entityTypeBadgeClass(comment.entity_type)}`}>
            {comment.entity_type}
          </span>
          <span className="font-mono text-[10px] text-muted-foreground" title={comment.entity_id}>
            {comment.entity_id.slice(0, 8)}…
          </span>
        </div>
      </td>

      {/* Type */}
      <td className="px-4 py-3 whitespace-nowrap">
        <TypeBadge type={type} />
      </td>

      {/* Status */}
      <td className="px-4 py-3 whitespace-nowrap">
        <StatusBadge comment={comment} />
      </td>

      {/* Replies */}
      <td className="px-4 py-3 whitespace-nowrap text-center">
        <div className="flex flex-col items-center gap-0.5">
          <span className="text-xs text-foreground font-medium">{comment.reply_count}</span>
          <span className="text-[10px] text-muted-foreground">replies</span>
        </div>
      </td>

      {/* Created */}
      <td className="px-4 py-3 whitespace-nowrap">
        <span className="text-xs text-muted-foreground">
          {new Date(comment.created_at).toLocaleDateString()}{" "}
          <span className="text-[10px]">{new Date(comment.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
        </span>
      </td>

      {/* Actions */}
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex items-center gap-1.5">
          {comment.is_deleted ? (
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1 text-xs"
              disabled={isActing}
              onClick={() => onUndelete(comment.id)}
            >
              <RotateCcw className="h-3 w-3" />
              Undelete
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1 text-xs text-amber-600 hover:bg-amber-500/10 hover:text-amber-600"
              disabled={isActing}
              onClick={() => onDelete(comment.id)}
            >
              <X className="h-3 w-3" />
              Soft Delete
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive"
            disabled={isActing}
            onClick={() => onHardDelete(comment.id)}
          >
            <Trash2 className="h-3 w-3" />
            Hard Delete
          </Button>
        </div>
      </td>
    </tr>
  )
}

// ── Stats bar ─────────────────────────────────────────────────────────────────

interface StatsBarProps {
  stats: CommentStatsResponse | null
  loading: boolean
  comments: CommentRecord[]
}

function StatsBar({ stats, loading, comments }: StatsBarProps) {
  if (loading) {
    return (
      <div className="flex gap-3 flex-wrap">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="relative flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 animate-pulse">
            <div className="shrink-0 rounded-lg p-2 bg-muted h-8 w-8" />
            <div className="flex flex-col gap-1">
              <div className="h-5 w-10 rounded bg-muted" />
              <div className="h-2.5 w-16 rounded bg-muted" />
            </div>
          </div>
        ))}
      </div>
    )
  }
  if (!stats) return null

  const internalCount = comments.filter(c => commentType(c) === "internal").length
  const externalCount = comments.filter(c => commentType(c) === "external").length
  const systemCount   = comments.filter(c => commentType(c) === "system").length

  const statItems: Array<{ label: string; value: string; borderCls: string; numCls: string; icon: React.ReactNode }> = [
    {
      label: "Total Comments",
      value: stats.total.toLocaleString(),
      borderCls: "border-l-violet-500",
      numCls: "text-foreground",
      icon: <MessageSquare className="h-4 w-4 text-violet-500" />,
    },
    {
      label: "Internal (page)",
      value: internalCount.toLocaleString(),
      borderCls: "border-l-blue-500",
      numCls: "text-blue-600",
      icon: <Lock className="h-4 w-4 text-blue-500" />,
    },
    {
      label: "External (page)",
      value: externalCount.toLocaleString(),
      borderCls: "border-l-green-500",
      numCls: "text-green-600",
      icon: <Globe className="h-4 w-4 text-green-500" />,
    },
    {
      label: "System (page)",
      value: systemCount.toLocaleString(),
      borderCls: "border-l-slate-400",
      numCls: "text-muted-foreground",
      icon: <Bot className="h-4 w-4 text-slate-400" />,
    },
  ]

  return (
    <div className="flex gap-3 flex-wrap">
      {statItems.map((s) => (
        <div key={s.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}>
          <div className="shrink-0 rounded-lg p-2 bg-muted">
            {s.icon}
          </div>
          <div className="flex flex-col">
            <span className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</span>
            <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
          </div>
        </div>
      ))}

      {stats.top_mentioned.length > 0 && (
        <div className="rounded-xl border border-border bg-card px-4 py-3">
          <p className="text-[11px] text-muted-foreground mb-1.5">Top Mentioned</p>
          <div className="flex flex-wrap gap-1.5">
            {stats.top_mentioned.slice(0, 5).map((u) => (
              <span
                key={u.user_id}
                className="inline-flex items-center gap-1 rounded-md border border-border bg-muted px-2 py-0.5 text-xs"
                title={u.user_id}
              >
                <span className="font-medium text-foreground">{u.display_name ?? u.user_id.slice(0, 8)}</span>
                <span className="text-muted-foreground">×{u.mention_count}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── GDPR Compliance Panel ─────────────────────────────────────────────────────

function GdprCompliancePanel() {
  const [userId, setUserId] = useState("")
  const [preview, setPreview] = useState<GdprUserCommentsPreview | null>(null)
  const [result, setResult] = useState<GdprCommentDeleteResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)

  async function handlePreview() {
    if (!userId.trim()) return
    setLoading(true)
    setError(null)
    setPreview(null)
    setResult(null)
    setConfirmDelete(false)
    try {
      const data = await gdprPreviewUserComments(userId.trim())
      setPreview(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to preview user data")
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete() {
    if (!userId.trim()) return
    setDeleting(true)
    setError(null)
    setConfirmDelete(false)
    try {
      const data = await gdprDeleteUserComments(userId.trim())
      setResult(data)
      setPreview(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete user data")
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
      <div className="flex items-center gap-2">
        <Shield className="h-4 w-4 text-amber-500 shrink-0" />
        <span className="text-sm font-semibold text-foreground">GDPR Compliance</span>
      </div>
      <p className="text-xs text-muted-foreground">
        Preview and delete all comment data for a specific user (Article 17 — Right to Erasure).
      </p>

      <div className="flex items-end gap-2">
        <div className="flex-1">
          <label className="text-xs font-medium text-muted-foreground mb-1 block">User ID</label>
          <Input
            placeholder="Enter user UUID..."
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handlePreview()}
            className="h-9 text-sm font-mono"
          />
        </div>
        <Button
          size="sm"
          variant="outline"
          className="h-9 gap-1.5 text-xs"
          onClick={handlePreview}
          disabled={loading || !userId.trim()}
        >
          {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Eye className="h-3 w-3" />}
          Preview
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
          <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
          <p className="text-xs text-red-500">{error}</p>
        </div>
      )}

      {preview && (
        <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-foreground">
              Found {preview.total} comment{preview.total !== 1 ? "s" : ""} for user {preview.user_id.slice(0, 8)}...
            </p>
            {preview.total > 0 && !confirmDelete && (
              <Button
                size="sm"
                variant="destructive"
                className="h-7 gap-1 text-xs"
                onClick={() => setConfirmDelete(true)}
                disabled={deleting}
              >
                <Trash2 className="h-3 w-3" />
                Delete All User Data
              </Button>
            )}
          </div>
          {preview.items.length > 0 && (
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {preview.items.slice(0, 10).map((item) => (
                <div key={item.id} className="flex items-center gap-2 text-[10px] text-muted-foreground">
                  <span className="inline-flex items-center rounded border border-border px-1 py-0.5 font-medium">
                    {item.entity_type}
                  </span>
                  <span className="truncate flex-1">{item.content}</span>
                  <span className="shrink-0">{new Date(item.created_at).toLocaleDateString()}</span>
                </div>
              ))}
              {preview.total > 10 && (
                <p className="text-[10px] text-muted-foreground italic">
                  ...and {preview.total - 10} more
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {confirmDelete && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2 flex items-center gap-3">
          <AlertCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
          <p className="text-xs text-red-700 dark:text-red-400 flex-1">
            This will anonymize all comments and delete all reactions for this user. This action cannot be undone.
          </p>
          <div className="flex gap-1.5">
            <Button
              size="sm"
              variant="destructive"
              className="h-7 text-xs"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? <Loader2 className="h-3 w-3 animate-spin" /> : "Confirm Delete"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={() => setConfirmDelete(false)}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {result && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
          <p className="text-xs text-emerald-600">
            Anonymized {result.comments_anonymized} comment{result.comments_anonymized !== 1 ? "s" : ""}, deleted {result.reactions_deleted} reaction{result.reactions_deleted !== 1 ? "s" : ""}.
          </p>
        </div>
      )}
    </div>
  )
}

// ── Active filter chips ───────────────────────────────────────────────────────

interface ActiveChip {
  label: string
  color: "blue" | "green" | "amber" | "violet" | "default"
  onDismiss: () => void
}

function ActiveFilterChips({ chips, onClearAll }: { chips: ActiveChip[]; onClearAll: () => void }) {
  if (chips.length === 0) return null

  const colorMap: Record<ActiveChip["color"], string> = {
    blue:    "border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-400",
    green:   "border-green-500/30 bg-green-500/10 text-green-700 dark:text-green-400",
    amber:   "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400",
    violet:  "border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-400",
    default: "border-border bg-muted text-foreground",
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {chips.map((chip) => (
        <span
          key={chip.label}
          className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${colorMap[chip.color]}`}
        >
          {chip.label}
          <button onClick={chip.onDismiss} className="opacity-60 hover:opacity-100 transition-opacity">
            <X className="h-2.5 w-2.5" />
          </button>
        </span>
      ))}
      {chips.length > 1 && (
        <button
          onClick={onClearAll}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors underline underline-offset-2"
        >
          Clear all
        </button>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminCommentsPage() {
  // Filters (controlled inputs)
  const [searchInput, setSearchInput]           = useState("")
  const [entityTypeInput, setEntityTypeInput]   = useState("")
  const [isDeletedInput, setIsDeletedInput]     = useState<"" | "true" | "false">("")
  const [isPinnedInput, setIsPinnedInput]       = useState<"" | "true" | "false">("")
  const [resolvedInput, setResolvedInput]       = useState<"" | "true" | "false">("")
  const [dateFromInput, setDateFromInput]       = useState("")
  const [dateToInput, setDateToInput]           = useState("")

  // Applied filters
  const [appliedFilters, setAppliedFilters] = useState({
    q: "",
    entity_type: "",
    is_deleted: undefined as boolean | undefined,
    is_pinned: undefined as boolean | undefined,
    resolved: undefined as boolean | undefined,
    date_from: "",
    date_to: "",
  })

  // Data
  const [comments, setComments] = useState<CommentRecord[]>([])
  const [total, setTotal]       = useState(0)
  const [page, setPage]         = useState(1)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState<string | null>(null)

  // Stats
  const [stats, setStats]               = useState<CommentStatsResponse | null>(null)
  const [statsLoading, setStatsLoading] = useState(true)

  // Action state
  const [actionInFlight, setActionInFlight] = useState<string | null>(null)
  const [actionError, setActionError]       = useState<string | null>(null)

  // Confirm hard-delete
  const [pendingHardDelete, setPendingHardDelete] = useState<string | null>(null)

  // Load stats once on mount
  useEffect(() => {
    adminGetStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setStatsLoading(false))
  }, [])

  const fetchComments = useCallback(
    async (pageIndex: number, filters: typeof appliedFilters) => {
      setLoading(true)
      setError(null)
      try {
        const result = await adminListComments({
          page: pageIndex,
          per_page: PAGE_SIZE,
          q:           filters.q           || undefined,
          entity_type: filters.entity_type || undefined,
          is_deleted:  filters.is_deleted,
          is_pinned:   filters.is_pinned,
          resolved:    filters.resolved,
          date_from:   filters.date_from   || undefined,
          date_to:     filters.date_to     || undefined,
        })
        setComments(result.items)
        setTotal(result.total)
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load comments")
      } finally {
        setLoading(false)
      }
    },
    []
  )

  useEffect(() => {
    fetchComments(page, appliedFilters)
  }, [page, appliedFilters, fetchComments])

  function parseBoolFilter(v: "" | "true" | "false"): boolean | undefined {
    if (v === "true")  return true
    if (v === "false") return false
    return undefined
  }

  function handleApplyFilters() {
    setPage(1)
    setAppliedFilters({
      q:           searchInput.trim(),
      entity_type: entityTypeInput,
      is_deleted:  parseBoolFilter(isDeletedInput),
      is_pinned:   parseBoolFilter(isPinnedInput),
      resolved:    parseBoolFilter(resolvedInput),
      date_from:   dateFromInput,
      date_to:     dateToInput,
    })
  }

  function handleClearFilters() {
    setSearchInput("")
    setEntityTypeInput("")
    setIsDeletedInput("")
    setIsPinnedInput("")
    setResolvedInput("")
    setDateFromInput("")
    setDateToInput("")
    setPage(1)
    setAppliedFilters({
      q: "", entity_type: "",
      is_deleted: undefined, is_pinned: undefined, resolved: undefined,
      date_from: "", date_to: "",
    })
  }

  async function handleHardDelete(id: string) {
    setActionInFlight(id)
    setActionError(null)
    setPendingHardDelete(null)
    try {
      await adminHardDeleteComment(id)
      setComments((prev) => prev.filter((c) => c.id !== id))
      setTotal((t) => t - 1)
      adminGetStats().then(setStats).catch(() => {})
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to delete comment")
    } finally {
      setActionInFlight(null)
    }
  }

  async function handleSoftDelete(id: string) {
    setActionInFlight(id)
    setActionError(null)
    try {
      await adminSoftDeleteComment(id)
      setComments((prev) => prev.map((c) => (c.id === id ? { ...c, is_deleted: true } : c)))
      adminGetStats().then(setStats).catch(() => {})
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to soft-delete comment")
    } finally {
      setActionInFlight(null)
    }
  }

  async function handleUndelete(id: string) {
    setActionInFlight(id)
    setActionError(null)
    try {
      const updated = await adminUndeleteComment(id)
      setComments((prev) => prev.map((c) => (c.id === id ? updated : c)))
      adminGetStats().then(setStats).catch(() => {})
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to undelete comment")
    } finally {
      setActionInFlight(null)
    }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)
  const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const rangeEnd   = Math.min(page * PAGE_SIZE, total)

  // Active filter chips
  const activeChips: ActiveChip[] = []
  if (appliedFilters.q) activeChips.push({ label: `Search: "${appliedFilters.q}"`, color: "violet", onDismiss: () => { setSearchInput(""); setAppliedFilters(f => ({ ...f, q: "" })); setPage(1) } })
  if (appliedFilters.entity_type) activeChips.push({ label: `Entity: ${appliedFilters.entity_type}`, color: "blue", onDismiss: () => { setEntityTypeInput(""); setAppliedFilters(f => ({ ...f, entity_type: "" })); setPage(1) } })
  if (appliedFilters.is_deleted !== undefined) activeChips.push({ label: appliedFilters.is_deleted ? "Deleted only" : "Not deleted", color: "amber", onDismiss: () => { setIsDeletedInput(""); setAppliedFilters(f => ({ ...f, is_deleted: undefined })); setPage(1) } })
  if (appliedFilters.is_pinned !== undefined) activeChips.push({ label: appliedFilters.is_pinned ? "Pinned only" : "Not pinned", color: "amber", onDismiss: () => { setIsPinnedInput(""); setAppliedFilters(f => ({ ...f, is_pinned: undefined })); setPage(1) } })
  if (appliedFilters.resolved !== undefined) activeChips.push({ label: appliedFilters.resolved ? "Resolved" : "Unresolved", color: "green", onDismiss: () => { setResolvedInput(""); setAppliedFilters(f => ({ ...f, resolved: undefined })); setPage(1) } })
  if (appliedFilters.date_from) activeChips.push({ label: `From: ${appliedFilters.date_from}`, color: "default", onDismiss: () => { setDateFromInput(""); setAppliedFilters(f => ({ ...f, date_from: "" })); setPage(1) } })
  if (appliedFilters.date_to) activeChips.push({ label: `To: ${appliedFilters.date_to}`, color: "default", onDismiss: () => { setDateToInput(""); setAppliedFilters(f => ({ ...f, date_to: "" })); setPage(1) } })

  const hasActiveFilters = activeChips.length > 0

  return (
    <div className="space-y-6">
      {/* ── Header ────────────────────────────────────────────────────── */}
      <div className="flex items-start gap-4">
        <div className="rounded-xl bg-violet-500/10 p-3 shrink-0">
          <MessageSquare className="h-6 w-6 text-violet-500" />
        </div>
        <div className="flex flex-col gap-1 flex-1">
          <h2 className="text-2xl font-semibold text-foreground">Comments</h2>
          <p className="text-sm text-muted-foreground">
            Monitor and moderate comments across all entities on the platform.
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 rounded-lg shrink-0"
          onClick={() => fetchComments(page, appliedFilters)}
          title="Refresh"
        >
          <RefreshCw className="h-4 w-4 text-muted-foreground" />
        </Button>
      </div>

      {/* ── Stats ─────────────────────────────────────────────────────── */}
      <StatsBar stats={stats} loading={statsLoading} comments={comments} />

      {/* ── GDPR Compliance ───────────────────────────────────────────── */}
      <GdprCompliancePanel />

      {/* ── Filter bar ────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
            <Input
              placeholder="Search comment content…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleApplyFilters()}
              className="h-9 pl-8 text-sm"
            />
          </div>

          {/* Entity type */}
          <div className="min-w-[160px]">
            <select
              value={entityTypeInput}
              onChange={(e) => setEntityTypeInput(e.target.value)}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All entity types</option>
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>

          {/* is_deleted */}
          <div className="min-w-[130px]">
            <select
              value={isDeletedInput}
              onChange={(e) => setIsDeletedInput(e.target.value as "" | "true" | "false")}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All statuses</option>
              <option value="false">Not deleted</option>
              <option value="true">Deleted only</option>
            </select>
          </div>

          {/* is_pinned */}
          <div className="min-w-[120px]">
            <select
              value={isPinnedInput}
              onChange={(e) => setIsPinnedInput(e.target.value as "" | "true" | "false")}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Any pinned</option>
              <option value="true">Pinned only</option>
              <option value="false">Not pinned</option>
            </select>
          </div>

          {/* resolved */}
          <div className="min-w-[130px]">
            <select
              value={resolvedInput}
              onChange={(e) => setResolvedInput(e.target.value as "" | "true" | "false")}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Any resolved</option>
              <option value="true">Resolved only</option>
              <option value="false">Unresolved only</option>
            </select>
          </div>

          {/* Date range */}
          <div className="flex items-center gap-1.5 min-w-[260px]">
            <Input
              type="date"
              value={dateFromInput}
              onChange={(e) => setDateFromInput(e.target.value)}
              className="h-9 text-sm"
              title="From date"
            />
            <span className="text-xs text-muted-foreground">–</span>
            <Input
              type="date"
              value={dateToInput}
              onChange={(e) => setDateToInput(e.target.value)}
              className="h-9 text-sm"
              title="To date"
            />
          </div>

          <Button size="sm" className="h-9 shrink-0" onClick={handleApplyFilters}>
            Apply
          </Button>
          {hasActiveFilters && (
            <Button
              size="sm"
              variant="ghost"
              className="h-9 shrink-0 gap-1 text-muted-foreground"
              onClick={handleClearFilters}
            >
              <X className="h-3.5 w-3.5" />
              Clear all
            </Button>
          )}
        </div>

        <ActiveFilterChips chips={activeChips} onClearAll={handleClearFilters} />
      </div>

      {/* ── Error banners ─────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}
      {actionError && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          <p className="text-sm text-red-500">{actionError}</p>
          <button className="ml-auto text-xs text-red-500 underline" onClick={() => setActionError(null)}>Dismiss</button>
        </div>
      )}

      {/* ── Dialogs ─────────────────────────────────────────────────────── */}
      <Dialog open={!!pendingHardDelete} onOpenChange={(o) => !o && setPendingHardDelete(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              Confirm Permanent Deletion
            </DialogTitle>
            <DialogDescription className="pt-2">
              Are you sure you want to permanently delete this comment?
              <br />
              <b>This action cannot be undone.</b>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4 gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPendingHardDelete(null)}
              disabled={actionInFlight !== null}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              className="gap-1"
              onClick={() => pendingHardDelete && handleHardDelete(pendingHardDelete)}
              disabled={actionInFlight !== null}
            >
              {actionInFlight ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
              Delete Permanently
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Table ─────────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <div>
            <p className="text-base font-semibold text-foreground">Comments</p>
            {!loading && !error && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {total === 0
                  ? "No comments found"
                  : `Showing ${rangeStart}–${rangeEnd} of ${total.toLocaleString()}`}
              </p>
            )}
          </div>
          {/* Legend */}
          <div className="hidden sm:flex items-center gap-3 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1"><span className="inline-block h-3 w-0.5 rounded bg-blue-500" />Internal</span>
            <span className="flex items-center gap-1"><span className="inline-block h-3 w-0.5 rounded bg-green-500" />External</span>
            <span className="flex items-center gap-1"><span className="inline-block h-3 w-0.5 rounded bg-slate-400" />System</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                {["Content", "Author", "Entity", "Type", "Status", "Replies", "Created", "Actions"].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 10 }).map((_, i) => <SkeletonRow key={i} cols={8} />)
              ) : comments.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-16 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                        <MessageSquare className="h-6 w-6 text-muted-foreground" />
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-foreground">No comments found</p>
                        <p className="text-xs text-muted-foreground">
                          Try adjusting your filters.
                        </p>
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                comments.map((comment) => (
                  <CommentRow
                    key={comment.id}
                    comment={comment}
                    onDelete={handleSoftDelete}
                    onHardDelete={(id) => setPendingHardDelete(id)}
                    onUndelete={handleUndelete}
                    actionInFlight={actionInFlight}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && total > 0 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3">
            <p className="text-xs text-muted-foreground">
              Showing {rangeStart}–{rangeEnd} of {total.toLocaleString()} comments
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Prev
              </Button>
              <span className="text-xs text-muted-foreground px-1">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
