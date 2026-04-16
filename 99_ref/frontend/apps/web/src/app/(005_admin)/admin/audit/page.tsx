"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
} from "@kcontrol/ui"
import { ScrollText, ChevronLeft, ChevronRight, RefreshCw, AlertCircle, ChevronDown, ChevronUp, Download, X } from "lucide-react"
import { listAuditEvents, listAdminUsers } from "@/lib/api/admin"
import type { AuditEventResponse, AuditEventListResponse } from "@/lib/types/admin"

// ── Constants ──────────────────────────────────────────────────────────────

const PAGE_SIZE = 50

// ── Entity type badge colors ───────────────────────────────────────────────

function entityBadgeClass(entityType: string): string {
  switch (entityType.toLowerCase()) {
    case "user":
      return "bg-blue-500/10 text-blue-500 border-blue-500/20"
    case "session":
      return "bg-purple-500/10 text-purple-500 border-purple-500/20"
    case "org":
      return "bg-green-500/10 text-green-500 border-green-500/20"
    case "workspace":
      return "bg-teal-500/10 text-teal-500 border-teal-500/20"
    case "role":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20"
    case "group":
      return "bg-orange-500/10 text-orange-500 border-orange-500/20"
    case "login_attempt":
      return "bg-red-500/10 text-red-500 border-red-500/20"
    case "challenge":
      return "bg-pink-500/10 text-pink-500 border-pink-500/20"
    case "feature_flag":
    case "feature":
      return "bg-cyan-500/10 text-cyan-500 border-cyan-500/20"
    case "api_key":
      return "bg-indigo-500/10 text-indigo-500 border-indigo-500/20"
    case "invitation":
    case "invite_campaign":
      return "bg-sky-500/10 text-sky-500 border-sky-500/20"
    case "notification_queue":
    case "notification_preference":
    case "broadcast":
      return "bg-violet-500/10 text-violet-500 border-violet-500/20"
    case "template":
      return "bg-fuchsia-500/10 text-fuchsia-500 border-fuchsia-500/20"
    case "license_profile":
      return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
    case "incident":
    case "release":
      return "bg-rose-500/10 text-rose-500 border-rose-500/20"
    default:
      return "bg-muted text-muted-foreground border-border"
  }
}

// ── Entity type accent (left border indicator) ─────────────────────────────

function entityAccentClass(entityType: string): string {
  switch (entityType.toLowerCase()) {
    case "user":
      return "bg-blue-500"
    case "session":
      return "bg-purple-500"
    case "org":
      return "bg-green-500"
    case "workspace":
      return "bg-teal-500"
    case "role":
      return "bg-amber-500"
    case "group":
      return "bg-orange-500"
    case "login_attempt":
      return "bg-red-500"
    case "challenge":
      return "bg-pink-500"
    case "feature_flag":
    case "feature":
      return "bg-cyan-500"
    case "api_key":
      return "bg-indigo-500"
    case "invitation":
    case "invite_campaign":
      return "bg-sky-500"
    case "notification_queue":
    case "notification_preference":
    case "broadcast":
      return "bg-violet-500"
    case "template":
      return "bg-fuchsia-500"
    case "license_profile":
      return "bg-emerald-500"
    case "incident":
    case "release":
      return "bg-rose-500"
    default:
      return "bg-muted-foreground/30"
  }
}

// ── Sub-components ─────────────────────────────────────────────────────────

function SkeletonRow() {
  return (
    <tr className="border-b border-border">
      <td className="w-0.5 p-0" />
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-3.5 rounded bg-muted animate-pulse" style={{ width: `${40 + (i * 17) % 45}%` }} />
        </td>
      ))}
    </tr>
  )
}

function PropertiesGrid({ properties }: { properties: Record<string, string | null> }) {
  const entries = Object.entries(properties).filter(([, v]) => v !== null && v !== undefined)
  if (entries.length === 0) {
    return <span className="text-xs text-muted-foreground italic">No additional properties</span>
  }
  return (
    <div className="flex flex-wrap gap-2 py-1">
      {entries.map(([key, value]) => (
        <span
          key={key}
          className="inline-flex items-center gap-1 rounded-md border border-border bg-muted px-2 py-1 text-xs font-mono"
        >
          <span className="text-muted-foreground">{key}:</span>
          <span className="text-foreground">{value}</span>
        </span>
      ))}
    </div>
  )
}

function EventRow({ event, actorMap }: { event: AuditEventResponse; actorMap: Map<string, string> }) {
  const [expanded, setExpanded] = useState(false)
  const hasProperties = Object.keys(event.properties || {}).length > 0
  const actorName = event.actor_id ? actorMap.get(event.actor_id) : null

  return (
    <>
      <tr
        className={`border-b border-border transition-colors cursor-pointer hover:bg-muted/30 ${expanded ? "bg-muted/20" : ""}`}
        onClick={() => setExpanded((v) => !v)}
      >
        {/* Colored left border accent */}
        <td className="w-0.5 p-0">
          <div className={`h-full w-0.5 ${entityAccentClass(event.entity_type)}`} />
        </td>

        {/* Time */}
        <td className="px-4 py-3 whitespace-nowrap">
          <span className="text-xs text-muted-foreground">
            {new Date(event.occurred_at).toLocaleString()}
          </span>
        </td>

        {/* Entity Type */}
        <td className="px-4 py-3 whitespace-nowrap">
          <span
            className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${entityBadgeClass(event.entity_type)}`}
          >
            {event.entity_type}
          </span>
        </td>

        {/* Event Type */}
        <td className="px-4 py-3 whitespace-nowrap">
          <span className="font-mono text-xs text-foreground">{event.event_type}</span>
        </td>

        {/* Category */}
        <td className="px-4 py-3 whitespace-nowrap">
          <span className="text-xs text-muted-foreground capitalize">{event.event_category}</span>
        </td>

        {/* Actor */}
        <td className="px-4 py-3 whitespace-nowrap max-w-[160px]">
          {actorName ? (
            <span className="text-xs text-foreground font-medium truncate block" title={event.actor_id ?? ""}>
              {actorName}
            </span>
          ) : event.actor_id ? (
            <span className="font-mono text-xs text-foreground truncate block" title={event.actor_id}>
              {event.actor_id.slice(0, 8)}…
            </span>
          ) : (
            <span className="text-xs text-muted-foreground italic">System</span>
          )}
        </td>

        {/* Entity ID */}
        <td className="px-4 py-3 whitespace-nowrap">
          <span className="font-mono text-xs text-muted-foreground" title={event.entity_id}>
            {event.entity_id.slice(0, 8)}…
          </span>
        </td>

        {/* IP */}
        <td className="px-4 py-3 whitespace-nowrap">
          <span className="text-xs text-muted-foreground">
            {event.ip_address || "—"}
          </span>
        </td>

        {/* Details expand */}
        <td className="px-4 py-3 whitespace-nowrap">
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v) }}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            disabled={!hasProperties}
          >
            {hasProperties ? (
              <>
                {Object.keys(event.properties).length} props
                {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </>
            ) : (
              <span className="text-muted-foreground/50">—</span>
            )}
          </button>
        </td>
      </tr>

      {/* Expanded properties row */}
      {expanded && (
        <tr className="border-b border-border bg-muted/10">
          <td className="w-0.5 p-0">
            <div className={`h-full w-0.5 ${entityAccentClass(event.entity_type)}`} />
          </td>
          <td colSpan={8} className="px-4 py-3">
            <PropertiesGrid properties={event.properties || {}} />
          </td>
        </tr>
      )}
    </>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

const ENTITY_TYPES = [
  "user", "session", "org", "workspace", "role", "group", "feature_flag",
  "api_key", "invitation", "login_attempt", "challenge", "broadcast",
  "template", "notification_queue", "license_profile", "incident", "release",
] as const

const EVENT_CATEGORIES = ["auth", "access", "org", "workspace", "product", "system", "notification"] as const

export default function AuditLogPage() {
  // Filters
  const [entityTypeInput, setEntityTypeInput] = useState("")
  const [eventTypeInput, setEventTypeInput] = useState("")
  const [actorIdInput, setActorIdInput] = useState("")
  const [categoryInput, setCategoryInput] = useState("")

  // Applied filters (only updated on "Apply" for text inputs; immediately for select)
  const [appliedFilters, setAppliedFilters] = useState({
    entity_type: "",
    event_type: "",
    actor_id: "",
  })

  // Data
  const [events, setEvents] = useState<AuditEventResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Actor name resolution
  const [actorMap, setActorMap] = useState<Map<string, string>>(new Map())

  // Auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Build actor map on mount
  useEffect(() => {
    listAdminUsers({ limit: 200 })
      .then((res) => {
        const map = new Map<string, string>()
        for (const u of res.users) {
          map.set(u.user_id, u.display_name ?? u.email ?? u.username ?? u.user_id.slice(0, 8))
        }
        setActorMap(map)
      })
      .catch(() => {}) // non-critical
  }, [])

  const fetchEvents = useCallback(
    async (pageIndex: number, filters: typeof appliedFilters) => {
      setLoading(true)
      setError(null)
      try {
        const result: AuditEventListResponse = await listAuditEvents({
          entity_type: filters.entity_type || undefined,
          event_type: filters.event_type || undefined,
          actor_id: filters.actor_id || undefined,
          limit: PAGE_SIZE,
          offset: pageIndex * PAGE_SIZE,
        })
        setEvents(result.events)
        setTotal(result.total)
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load audit events")
      } finally {
        setLoading(false)
      }
    },
    []
  )

  // Initial fetch and on filter/page change
  useEffect(() => {
    fetchEvents(page, appliedFilters)
  }, [page, appliedFilters, fetchEvents])

  // Auto-refresh interval
  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        fetchEvents(page, appliedFilters)
      }, 30_000)
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [autoRefresh, page, appliedFilters, fetchEvents])

  function handleApplyFilters() {
    setPage(0)
    setAppliedFilters({
      entity_type: entityTypeInput.trim(),
      event_type: eventTypeInput.trim(),
      actor_id: actorIdInput.trim(),
    })
  }

  function handleClearFilters() {
    setEntityTypeInput("")
    setEventTypeInput("")
    setActorIdInput("")
    setPage(0)
    setAppliedFilters({ entity_type: "", event_type: "", actor_id: "" })
  }

  // Chip dismiss handlers — set state and apply immediately
  function handleDismissEntityType() {
    setEntityTypeInput("")
    setPage(0)
    setAppliedFilters((prev) => ({ ...prev, entity_type: "" }))
  }

  function handleDismissEventType() {
    setEventTypeInput("")
    setPage(0)
    setAppliedFilters((prev) => ({ ...prev, event_type: "" }))
  }

  function handleDismissActorId() {
    setActorIdInput("")
    setPage(0)
    setAppliedFilters((prev) => ({ ...prev, actor_id: "" }))
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)
  const rangeStart = total === 0 ? 0 : page * PAGE_SIZE + 1
  const rangeEnd = Math.min((page + 1) * PAGE_SIZE, total)

  const hasActiveFilters = !!(appliedFilters.entity_type || appliedFilters.event_type || appliedFilters.actor_id)

  return (
    <div className="space-y-6">
      {/* ── Header ────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight font-secondary">Audit Log</h1>
          <p className="text-sm text-muted-foreground mt-1">Full platform event trail across all tenants.</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Auto-refresh</span>
          <button
            role="switch"
            aria-checked={autoRefresh}
            onClick={() => setAutoRefresh((v) => !v)}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
              autoRefresh ? "bg-primary" : "bg-muted"
            }`}
          >
            <span
              className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
                autoRefresh ? "translate-x-4" : "translate-x-1"
              }`}
            />
          </button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 rounded-lg"
            onClick={() => fetchEvents(page, appliedFilters)}
            title="Refresh now"
          >
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </Button>
        </div>
      </div>

      {/* ── Filter bar ────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="min-w-[180px]">
            <select
              value={entityTypeInput}
              onChange={(e) => {
                const val = e.target.value
                setEntityTypeInput(val)
                setPage(0)
                setAppliedFilters((prev) => ({ ...prev, entity_type: val.trim() }))
              }}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All entity types</option>
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[180px]">
            <Input
              placeholder="Event type (e.g. login_succeeded)"
              value={eventTypeInput}
              onChange={(e) => setEventTypeInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleApplyFilters()}
              className="h-9 text-sm"
            />
          </div>
          <div className="flex-1 min-w-[140px]">
            <Input
              placeholder="Actor ID"
              value={actorIdInput}
              onChange={(e) => setActorIdInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleApplyFilters()}
              className="h-9 text-sm font-mono"
            />
          </div>
          <Button size="sm" className="h-9 shrink-0" onClick={handleApplyFilters}>
            Apply
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-9 shrink-0 text-muted-foreground"
            onClick={handleClearFilters}
          >
            Clear
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-9 shrink-0 gap-1.5"
            disabled={events.length === 0}
            onClick={() => {
              const headers = ["Time", "Entity Type", "Event Type", "Category", "Actor ID", "Actor Name", "Entity ID", "IP"]
              const rows = events.map((e) => [
                new Date(e.occurred_at).toISOString(), e.entity_type, e.event_type, e.event_category,
                e.actor_id ?? "", e.actor_id ? (actorMap.get(e.actor_id) ?? "") : "",
                e.entity_id, e.ip_address ?? "",
              ])
              const csv = [headers, ...rows].map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n")
              const blob = new Blob([csv], { type: "text/csv" })
              const url = URL.createObjectURL(blob)
              const a = document.createElement("a")
              a.href = url
              a.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`
              a.click()
              URL.revokeObjectURL(url)
            }}
          >
            <Download className="h-3.5 w-3.5" />
            CSV
          </Button>
        </div>

        {/* Active filter chips row */}
        {hasActiveFilters && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Active:</span>
            {appliedFilters.entity_type && (
              <span className="inline-flex items-center gap-1 rounded-full border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 text-[11px] font-medium text-blue-600 dark:text-blue-400">
                {appliedFilters.entity_type}
                <button onClick={handleDismissEntityType}>
                  <X className="w-2.5 h-2.5" />
                </button>
              </span>
            )}
            {appliedFilters.event_type && (
              <span className="inline-flex items-center gap-1 rounded-full border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-[11px] font-medium text-purple-600 dark:text-purple-400">
                {appliedFilters.event_type}
                <button onClick={handleDismissEventType}>
                  <X className="w-2.5 h-2.5" />
                </button>
              </span>
            )}
            {appliedFilters.actor_id && (
              <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-600 dark:text-amber-400 font-mono">
                actor:{appliedFilters.actor_id.slice(0, 8)}…
                <button onClick={handleDismissActorId}>
                  <X className="w-2.5 h-2.5" />
                </button>
              </span>
            )}
            <button
              onClick={handleClearFilters}
              className="text-[11px] text-muted-foreground hover:text-foreground underline-offset-2 hover:underline ml-1"
            >
              clear all
            </button>
          </div>
        )}
      </div>

      {/* ── Error banner ──────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}

      {/* ── Events table ──────────────────────────────────────────────── */}
      <Card className="rounded-2xl border-border bg-card overflow-hidden">
        <CardHeader className="pb-3 border-b border-border">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base font-semibold">Events</CardTitle>
              {!loading && !error && (
                <CardDescription className="text-xs mt-0.5">
                  {total === 0
                    ? "No events found"
                    : `Showing ${rangeStart}–${rangeEnd} of ${total.toLocaleString()} events`}
                </CardDescription>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th className="w-0.5 p-0" />
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Time
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Entity Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Event Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Category
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Actor
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Entity ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    IP
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 10 }).map((_, i) => <SkeletonRow key={i} />)
                ) : events.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-16 text-center">
                      <div className="flex flex-col items-center gap-3">
                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                          <ScrollText className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium text-foreground">No events found</p>
                          <p className="text-xs text-muted-foreground">
                            Try adjusting your filters or check back later.
                          </p>
                        </div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  events.map((event) => <EventRow key={event.id} event={event} actorMap={actorMap} />)
                )}
              </tbody>
            </table>
          </div>

          {/* ── Pagination ──────────────────────────────────────────── */}
          {!loading && total > 0 && (
            <div className="flex items-center justify-between border-t border-border px-4 py-3">
              <p className="text-xs text-muted-foreground">
                Showing {rangeStart}–{rangeEnd} of {total.toLocaleString()} events
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 gap-1"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  Prev
                </Button>
                <span className="text-xs text-muted-foreground px-1">
                  Page {page + 1} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 gap-1"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                  <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
