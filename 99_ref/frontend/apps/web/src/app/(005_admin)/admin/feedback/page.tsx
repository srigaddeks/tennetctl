"use client"

import { useEffect, useState, useCallback } from "react"
import { Button, Input, Label, Separator } from "@kcontrol/ui"
import {
  Search,
  RefreshCw,
  AlertTriangle,
  Loader2,
  X,
  MessageSquarePlus,
  Bug,
  Lightbulb,
  MessageSquare,
  ShieldAlert,
  Zap,
  Inbox,
  Clock,
  CheckCircle2,
  ChevronRight,
  XCircle,
} from "lucide-react"
import {
  listAdminTickets,
  adminUpdateTicketStatus,
  adminUpdateTicket,
  getFeedbackDimensions,
} from "@/lib/api/feedback"
import { CommentsSection } from "@/components/comments/CommentsSection"
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection"
import type {
  TicketResponse,
  TicketDimensionsResponse,
} from "@/lib/api/feedback"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function getJwtSubject(): string | null {
  try {
    const token = localStorage.getItem("access_token")
    if (!token) return null
    const payload = JSON.parse(atob(token.split(".")[1]))
    return payload.sub || null
  } catch {
    return null
  }
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

const TYPE_ICONS: Record<string, React.ElementType> = {
  bug_report:       Bug,
  feature_request:  Lightbulb,
  general_feedback: MessageSquare,
  service_issue:    ShieldAlert,
  security_concern: Zap,
}

// ── Status meta ───────────────────────────────────────────────────────────────

interface StatusMeta {
  badgeCls: string
  borderCls: string
  icon: React.ElementType
}

const STATUS_META: Record<string, StatusMeta> = {
  open:        { badgeCls: "bg-amber-500/10 text-amber-600 border-amber-500/20",       borderCls: "border-l-amber-500",  icon: Inbox },
  in_review:   { badgeCls: "bg-purple-500/10 text-purple-600 border-purple-500/20",    borderCls: "border-l-purple-500", icon: Clock },
  in_progress: { badgeCls: "bg-blue-500/10 text-blue-600 border-blue-500/20",          borderCls: "border-l-blue-500",   icon: Clock },
  resolved:    { badgeCls: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20", borderCls: "border-l-green-500",  icon: CheckCircle2 },
  closed:      { badgeCls: "bg-muted text-muted-foreground border-border",             borderCls: "border-l-slate-400",  icon: XCircle },
  wont_fix:    { badgeCls: "bg-red-500/10 text-red-600 border-red-500/20",             borderCls: "border-l-red-500",    icon: XCircle },
  duplicate:   { badgeCls: "bg-gray-500/10 text-gray-600 border-gray-500/20",          borderCls: "border-l-slate-400",  icon: XCircle },
}

function rowBorderCls(statusCode: string): string {
  return STATUS_META[statusCode]?.borderCls ?? "border-l-primary"
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: "text-red-600 font-semibold",
  high:     "text-orange-600",
  medium:   "text-amber-600",
  low:      "text-muted-foreground",
}

function StatusBadge({ code, label }: { code: string; label?: string }) {
  const m = STATUS_META[code]
  const Icon = m?.icon ?? Inbox
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${m?.badgeCls ?? "bg-muted text-muted-foreground border-border"}`}>
      <Icon className="h-2.5 w-2.5" />
      {label ?? code}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Ticket Detail Panel
// ─────────────────────────────────────────────────────────────────────────────

function AdminTicketPanel({
  ticket,
  dimensions,
  onClose,
  onUpdated,
}: {
  ticket: TicketResponse
  dimensions: TicketDimensionsResponse | null
  onClose: () => void
  onUpdated: (t: TicketResponse) => void
}) {
  const TypeIcon = TYPE_ICONS[ticket.ticket_type_code] ?? MessageSquare
  const typeDef = dimensions?.ticket_types.find((t) => t.code === ticket.ticket_type_code)
  const statusDef = dimensions?.ticket_statuses.find((s) => s.code === ticket.status_code)

  const [newStatus, setNewStatus] = useState(ticket.status_code)
  const [adminNote, setAdminNote] = useState(ticket.admin_note ?? "")
  const [statusNote, setStatusNote] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSaveNote() {
    setSaving(true)
    setError(null)
    try {
      const updated = await adminUpdateTicket(ticket.id, { admin_note: adminNote.trim() || null })
      onUpdated(updated)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save note")
    } finally {
      setSaving(false)
    }
  }

  async function handleChangeStatus() {
    if (newStatus === ticket.status_code) return
    setSaving(true)
    setError(null)
    try {
      const updated = await adminUpdateTicketStatus(ticket.id, {
        status_code: newStatus,
        note: statusNote.trim() || null,
      })
      onUpdated(updated)
      setStatusNote("")
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to change status")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 shrink-0 rounded-lg p-2 bg-muted">
            <TypeIcon className="h-5 w-5 text-primary" />
          </span>
          <div>
            <h2 className="text-xl font-semibold">{ticket.title}</h2>
            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              <StatusBadge code={ticket.status_code} label={statusDef?.name} />
              <span className={`text-xs ${PRIORITY_COLORS[ticket.priority_code] ?? ""}`}>
                {ticket.priority_code}
              </span>
              <span className="text-xs text-muted-foreground">{typeDef?.name ?? ticket.ticket_type_code}</span>
              <span className="text-xs text-muted-foreground">#{ticket.id.slice(0, 8)}</span>
            </div>
            <div className="mt-1 text-xs text-muted-foreground">
              Submitted by <span className="font-medium">{ticket.submitter_email ?? ticket.submitter_display_name ?? ticket.submitted_by.slice(0, 8)}</span>
              {" "} on {fmtDate(ticket.created_at)}
            </div>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Triage panel */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-4">
        <h3 className="text-sm font-semibold">Triage</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Change Status</Label>
            <div className="flex gap-2">
              <select
                className="flex-1 h-8 rounded-md border border-input bg-background px-3 text-sm"
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
              >
                {(dimensions?.ticket_statuses ?? []).sort((a, b) => a.sort_order - b.sort_order).map((s) => (
                  <option key={s.code} value={s.code}>{s.name}</option>
                ))}
              </select>
              <Button
                size="sm"
                variant="outline"
                disabled={saving || newStatus === ticket.status_code}
                onClick={handleChangeStatus}
              >
                Apply
              </Button>
            </div>
            <Input
              className="h-8 text-sm"
              placeholder="Optional status note..."
              value={statusNote}
              onChange={(e) => setStatusNote(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Internal Admin Note</Label>
            <div className="flex gap-2">
              <Input
                className="h-8 text-sm flex-1"
                placeholder="Visible only to admins..."
                value={adminNote}
                onChange={(e) => setAdminNote(e.target.value)}
              />
              <Button
                size="sm"
                variant="outline"
                disabled={saving}
                onClick={handleSaveNote}
              >
                {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : "Save"}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      {ticket.description && (
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Description</h3>
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{ticket.description}</p>
        </div>
      )}

      {ticket.steps_to_reproduce && (
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Steps to Reproduce</h3>
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{ticket.steps_to_reproduce}</p>
        </div>
      )}

      {ticket.context_url && (
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Related URL</h3>
          <a href={ticket.context_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline break-all">
            {ticket.context_url}
          </a>
        </div>
      )}

      <Separator />

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Attachments</h3>
        <AttachmentsSection entityType="feedback_ticket" entityId={ticket.id} currentUserId={getJwtSubject() ?? ""} />
      </div>

      <Separator />

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Comments</h3>
        <CommentsSection entityType="feedback_ticket" entityId={ticket.id} currentUserId={getJwtSubject() ?? ""} />
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Admin Page
// ─────────────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20

export default function AdminFeedbackPage() {
  const [tickets, setTickets] = useState<TicketResponse[]>([])
  const [total, setTotal] = useState(0)
  const [dimensions, setDimensions] = useState<TicketDimensionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState("")
  const [filterType, setFilterType] = useState("")
  const [filterPriority, setFilterPriority] = useState("")
  const [offset, setOffset] = useState(0)
  const [selectedTicket, setSelectedTicket] = useState<TicketResponse | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [dimRes, ticketRes] = await Promise.all([
        getFeedbackDimensions(),
        listAdminTickets({
          status_code: filterStatus || undefined,
          ticket_type_code: filterType || undefined,
          priority_code: filterPriority || undefined,
          limit: PAGE_SIZE,
          offset,
        }),
      ])
      setDimensions(dimRes)
      setTickets(ticketRes.items)
      setTotal(ticketRes.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load tickets")
    } finally {
      setLoading(false)
    }
  }, [filterStatus, filterType, filterPriority, offset])

  useEffect(() => {
    load()
  }, [load])

  function handleUpdated(updated: TicketResponse) {
    setTickets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)))
    setSelectedTicket(updated)
  }

  const filtered = tickets.filter((t) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      t.title?.toLowerCase().includes(q) ||
      t.description?.toLowerCase().includes(q) ||
      t.submitter_email?.toLowerCase().includes(q) ||
      t.ticket_type_code.includes(q)
    )
  })

  // KPI counts from loaded page
  const openCount     = tickets.filter((t) => t.status_code === "open").length
  const resolvedCount = tickets.filter((t) => t.status_code === "resolved").length
  const closedCount   = tickets.filter((t) => ["closed", "wont_fix", "duplicate"].includes(t.status_code)).length

  // Active filter chips
  const activeFilters: Array<{ key: string; label: string; clear: () => void }> = []
  if (filterStatus) {
    const def = dimensions?.ticket_statuses.find((s) => s.code === filterStatus)
    activeFilters.push({ key: "status", label: def?.name ?? filterStatus, clear: () => { setFilterStatus(""); setOffset(0) } })
  }
  if (filterType) {
    const def = dimensions?.ticket_types.find((t) => t.code === filterType)
    activeFilters.push({ key: "type", label: def?.name ?? filterType, clear: () => { setFilterType(""); setOffset(0) } })
  }
  if (filterPriority) {
    activeFilters.push({ key: "priority", label: filterPriority, clear: () => { setFilterPriority(""); setOffset(0) } })
  }
  if (search.trim()) {
    activeFilters.push({ key: "search", label: `"${search}"`, clear: () => setSearch("") })
  }

  const hasFilters = activeFilters.length > 0

  const kpis = [
    {
      label: "Total",
      value: total,
      icon: MessageSquarePlus,
      borderCls: "border-l-primary",
      numCls: "text-foreground",
      iconBg: "bg-muted",
      iconCls: "text-primary",
    },
    {
      label: "Open",
      value: openCount,
      icon: Inbox,
      borderCls: "border-l-amber-500",
      numCls: "text-amber-600",
      iconBg: "bg-amber-500/10",
      iconCls: "text-amber-600",
    },
    {
      label: "Resolved",
      value: resolvedCount,
      icon: CheckCircle2,
      borderCls: "border-l-green-500",
      numCls: "text-green-600",
      iconBg: "bg-emerald-500/10",
      iconCls: "text-emerald-600",
    },
    {
      label: "Closed",
      value: closedCount,
      icon: XCircle,
      borderCls: "border-l-slate-400",
      numCls: "text-muted-foreground",
      iconBg: "bg-muted",
      iconCls: "text-muted-foreground",
    },
  ]

  if (selectedTicket) {
    return (
      <div className="space-y-6 p-6 max-w-4xl">
        <Button variant="ghost" size="sm" className="gap-2" onClick={() => setSelectedTicket(null)}>
          <X className="h-4 w-4" />
          Back to all tickets
        </Button>
        <AdminTicketPanel
          ticket={selectedTicket}
          dimensions={dimensions}
          onClose={() => setSelectedTicket(null)}
          onUpdated={handleUpdated}
        />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Feedback & Support</h1>
          <p className="text-muted-foreground mt-0.5 text-sm">
            Triage and respond to user-submitted tickets.
          </p>
        </div>
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={load} title="Refresh">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {/* KPI stat cards */}
      <div className="grid grid-cols-4 gap-3">
        {kpis.map(({ label, value, icon: Icon, borderCls, numCls, iconBg, iconCls }) => (
          <div key={label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3`}>
            <div className={`shrink-0 rounded-lg p-2 ${iconBg}`}>
              <Icon className={`h-4 w-4 ${iconCls}`} />
            </div>
            <div className="min-w-0">
              <span className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>{value}</span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 flex flex-col gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9 h-9"
              placeholder="Search tickets..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
            value={filterStatus}
            onChange={(e) => { setFilterStatus(e.target.value); setOffset(0) }}
          >
            <option value="">All statuses</option>
            {(dimensions?.ticket_statuses ?? []).sort((a, b) => a.sort_order - b.sort_order).map((s) => (
              <option key={s.code} value={s.code}>{s.name}</option>
            ))}
          </select>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
            value={filterType}
            onChange={(e) => { setFilterType(e.target.value); setOffset(0) }}
          >
            <option value="">All types</option>
            {(dimensions?.ticket_types ?? []).filter((t) => t.is_active).sort((a, b) => a.sort_order - b.sort_order).map((t) => (
              <option key={t.code} value={t.code}>{t.name}</option>
            ))}
          </select>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
            value={filterPriority}
            onChange={(e) => { setFilterPriority(e.target.value); setOffset(0) }}
          >
            <option value="">All priorities</option>
            {(dimensions?.ticket_priorities ?? []).sort((a, b) => a.sort_order - b.sort_order).map((p) => (
              <option key={p.code} value={p.code}>{p.name}</option>
            ))}
          </select>
        </div>

        {/* Active filter chips */}
        {hasFilters && (
          <div className="flex items-center gap-2 flex-wrap">
            {activeFilters.map((f) => (
              <button
                key={f.key}
                onClick={f.clear}
                className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-0.5 text-[11px] font-medium text-primary hover:bg-primary/20 transition-colors"
              >
                {f.label}
                <X className="h-2.5 w-2.5" />
              </button>
            ))}
            <button
              onClick={() => { setSearch(""); setFilterStatus(""); setFilterType(""); setFilterPriority(""); setOffset(0) }}
              className="text-xs text-muted-foreground hover:text-foreground ml-auto"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Ticket list */}
      {loading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-[72px] rounded-xl border border-border bg-card animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3 rounded-xl border border-border bg-card">
          <Inbox className="h-10 w-10 text-muted-foreground/40" />
          <p className="text-muted-foreground text-sm">No tickets found.</p>
          {hasFilters && (
            <button
              onClick={() => { setSearch(""); setFilterStatus(""); setFilterType(""); setFilterPriority(""); setOffset(0) }}
              className="text-xs text-primary hover:underline"
            >
              Clear all filters
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((ticket) => {
            const TypeIcon = TYPE_ICONS[ticket.ticket_type_code] ?? MessageSquare
            const statusDef = dimensions?.ticket_statuses.find((s) => s.code === ticket.status_code)
            const typeDef = dimensions?.ticket_types.find((t) => t.code === ticket.ticket_type_code)
            const bCls = rowBorderCls(ticket.status_code)
            return (
              <div
                key={ticket.id}
                className={`group flex items-center gap-3 rounded-xl border border-l-[3px] ${bCls} border-border bg-card px-4 py-3 cursor-pointer hover:bg-muted/30 transition-colors`}
                onClick={() => setSelectedTicket(ticket)}
              >
                {/* Type icon */}
                <div className="shrink-0 rounded-lg p-2 bg-muted">
                  <TypeIcon className="h-4 w-4 text-muted-foreground" />
                </div>

                {/* Title + meta */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm truncate">{ticket.title}</span>
                    <span className="text-xs text-muted-foreground font-mono hidden sm:inline">#{ticket.id.slice(0, 8)}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                    <StatusBadge code={ticket.status_code} label={statusDef?.name} />
                    <span className={`text-xs ${PRIORITY_COLORS[ticket.priority_code] ?? ""}`}>{ticket.priority_code}</span>
                    <span className="text-xs text-muted-foreground">{typeDef?.name ?? ticket.ticket_type_code}</span>
                  </div>
                </div>

                {/* Submitter + date */}
                <div className="shrink-0 text-right hidden sm:block">
                  <p className="text-xs text-muted-foreground truncate max-w-[140px]">
                    {ticket.submitter_email ?? ticket.submitter_display_name ?? ticket.submitted_by.slice(0, 8)}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">{fmtDate(ticket.created_at)}</p>
                </div>

                {/* Chevron */}
                <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            )
          })}
        </div>
      )}

      {/* Pagination */}
      {total > PAGE_SIZE && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
