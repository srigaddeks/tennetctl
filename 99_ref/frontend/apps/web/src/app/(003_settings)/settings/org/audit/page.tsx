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
import {
  ScrollText,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Download,
  Calendar,
  X,
} from "lucide-react"
import { listAuditEvents } from "@/lib/api/admin"
import { fetchAccessContext } from "@/lib/api/access"
import { listOrgMembers } from "@/lib/api/orgs"
import type { AuditEventResponse, AuditEventListResponse } from "@/lib/types/admin"
import type { OrgMemberResponse } from "@/lib/types/orgs"

// ── Constants ──────────────────────────────────────────────────────────────

const PAGE_SIZE = 50

// ── Helpers ────────────────────────────────────────────────────────────────

function entityBadgeClass(entityType: string): string {
  switch (entityType.toLowerCase()) {
    case "user": return "bg-blue-500/10 text-blue-500 border-blue-500/20"
    case "session": return "bg-purple-500/10 text-purple-500 border-purple-500/20"
    case "org": return "bg-green-500/10 text-green-500 border-green-500/20"
    case "workspace": return "bg-teal-500/10 text-teal-500 border-teal-500/20"
    case "role": return "bg-amber-500/10 text-amber-500 border-amber-500/20"
    case "group": return "bg-orange-500/10 text-orange-500 border-orange-500/20"
    case "login_attempt": return "bg-red-500/10 text-red-500 border-red-500/20"
    case "challenge": return "bg-pink-500/10 text-pink-500 border-pink-500/20"
    case "feature_flag":
    case "feature": return "bg-cyan-500/10 text-cyan-500 border-cyan-500/20"
    case "api_key": return "bg-indigo-500/10 text-indigo-500 border-indigo-500/20"
    case "invitation":
    case "invite_campaign": return "bg-sky-500/10 text-sky-500 border-sky-500/20"
    case "notification_queue":
    case "notification_preference":
    case "broadcast": return "bg-violet-500/10 text-violet-500 border-violet-500/20"
    case "template": return "bg-fuchsia-500/10 text-fuchsia-500 border-fuchsia-500/20"
    case "license_profile": return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
    case "incident":
    case "release": return "bg-rose-500/10 text-rose-500 border-rose-500/20"
    default: return "bg-muted text-muted-foreground border-border"
  }
}

const ENTITY_TYPES = [
  "user", "session", "org", "workspace", "role", "group", "feature_flag",
  "api_key", "invitation", "login_attempt", "challenge", "broadcast",
  "template", "license_profile", "incident", "release",
] as const

function SkeletonRow() {
  return (
    <tr className="border-b border-border">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-3.5 rounded bg-muted animate-pulse" style={{ width: `${40 + (i * 17) % 45}%` }} />
        </td>
      ))}
    </tr>
  )
}

function EventDetailRow({
  event,
  actorMap,
}: {
  event: AuditEventResponse
  actorMap: Map<string, string>
}) {
  const [open, setOpen] = useState(false)
  const hasProps = event.properties && Object.keys(event.properties).length > 0
  const actorName = event.actor_id ? actorMap.get(event.actor_id) : null

  return (
    <>
      <tr
        className={`border-b border-border hover:bg-accent/20 transition-colors ${hasProps ? "cursor-pointer" : ""}`}
        onClick={() => hasProps && setOpen((v) => !v)}
      >
        <td className="px-4 py-2.5 text-xs text-muted-foreground whitespace-nowrap">
          {new Date(event.occurred_at).toLocaleString(undefined, {
            dateStyle: "short",
            timeStyle: "medium",
          })}
        </td>
        <td className="px-4 py-2.5">
          <span className={`inline-block rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${entityBadgeClass(event.entity_type)}`}>
            {event.entity_type.replace(/_/g, " ")}
          </span>
        </td>
        <td className="px-4 py-2.5 text-xs text-foreground font-medium">{event.event_type}</td>
        <td className="px-4 py-2.5 text-xs text-muted-foreground">{event.event_category}</td>
        <td className="px-4 py-2.5 text-xs font-mono text-muted-foreground truncate max-w-[120px]" title={event.entity_id}>
          {event.entity_id.slice(0, 8)}…
        </td>
        <td className="px-4 py-2.5 text-xs text-muted-foreground truncate max-w-[160px]" title={event.actor_id ?? ""}>
          {actorName ? (
            <span className="text-foreground font-medium">{actorName}</span>
          ) : event.actor_id ? (
            <span className="font-mono">{event.actor_id.slice(0, 8)}…</span>
          ) : (
            "—"
          )}
        </td>
        <td className="px-4 py-2.5 text-xs text-muted-foreground">
          {hasProps && (
            <span className="inline-flex items-center gap-0.5 text-muted-foreground">
              {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </span>
          )}
        </td>
      </tr>
      {open && hasProps && (
        <tr className="border-b border-border bg-muted/30">
          <td colSpan={7} className="px-6 py-3">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {Object.entries(event.properties ?? {}).map(([k, v]) => (
                <div key={k} className="flex flex-col gap-0.5">
                  <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">{k}</span>
                  <span className="text-xs text-foreground break-all">{String(v)}</span>
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ── Date presets ──────────────────────────────────────────────────────────

function getDatePreset(preset: string): { from: string; to: string } {
  const now = new Date()
  const to = now.toISOString().slice(0, 10)
  const from = new Date(now)
  switch (preset) {
    case "24h":
      from.setDate(from.getDate() - 1)
      break
    case "7d":
      from.setDate(from.getDate() - 7)
      break
    case "30d":
      from.setDate(from.getDate() - 30)
      break
    case "90d":
      from.setDate(from.getDate() - 90)
      break
  }
  return { from: from.toISOString().slice(0, 10), to }
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function OrgAuditPage() {
  const [orgId, setOrgId] = useState<string | null>(null)
  const [events, setEvents] = useState<AuditEventResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actorMap, setActorMap] = useState<Map<string, string>>(new Map())

  // Filters
  const [entityTypeFilter, setEntityTypeFilter] = useState("")
  const [eventTypeFilter, setEventTypeFilter] = useState("")
  const [actorIdFilter, setActorIdFilter] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [activePreset, setActivePreset] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)

  const orgIdRef = useRef<string | null>(null)

  useEffect(() => {
    fetchAccessContext()
      .then(async (access) => {
        const id = access.current_org?.org_id
        if (!id) {
          setError("No organization found. Complete onboarding first.")
          setIsLoading(false)
          return
        }
        setOrgId(id)
        orgIdRef.current = id

        // Build actor name map from org members
        try {
          const members = await listOrgMembers(id)
          const map = new Map<string, string>()
          for (const m of members) {
            if (m.user_id) {
              map.set(m.user_id, m.display_name || m.email || m.user_id.slice(0, 8))
            }
          }
          setActorMap(map)
        } catch {
          // Non-critical
        }
      })
      .catch(() => {
        setError("Failed to load organization.")
        setIsLoading(false)
      })
  }, [])

  const loadEvents = useCallback(async (currentPage: number, currentOrgId: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const params: Record<string, string | number | undefined> = {
        entity_type: entityTypeFilter.trim() || undefined,
        event_type: eventTypeFilter.trim() || undefined,
        actor_id: actorIdFilter.trim() || undefined,
        entity_id: currentOrgId,
        limit: PAGE_SIZE,
        offset: currentPage * PAGE_SIZE,
      }
      // Date range — pass as occurred_after / occurred_before if supported
      if (dateFrom) (params as Record<string, unknown>).occurred_after = `${dateFrom}T00:00:00Z`
      if (dateTo) (params as Record<string, unknown>).occurred_before = `${dateTo}T23:59:59Z`

      const data: AuditEventListResponse = await listAuditEvents(params as Parameters<typeof listAuditEvents>[0])
      setEvents(data.events ?? [])
      setTotal(data.total ?? 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit events")
    } finally {
      setIsLoading(false)
    }
  }, [entityTypeFilter, eventTypeFilter, actorIdFilter, dateFrom, dateTo])

  useEffect(() => {
    if (!orgId) return
    loadEvents(page, orgId)
  }, [orgId, page, loadEvents])

  function handleFilterSubmit(e: React.FormEvent) {
    e.preventDefault()
    setPage(0)
    if (orgId) loadEvents(0, orgId)
  }

  function handleDatePreset(preset: string) {
    const { from, to } = getDatePreset(preset)
    setDateFrom(from)
    setDateTo(to)
    setActivePreset(preset)
  }

  // Reset active preset if dates changed manually
  useEffect(() => {
    if (activePreset) {
      const { from, to } = getDatePreset(activePreset)
      if (dateFrom !== from || dateTo !== to) {
        setActivePreset(null)
      }
    }
  }, [dateFrom, dateTo, activePreset])

  function handleClearFilters() {
    setEntityTypeFilter("")
    setEventTypeFilter("")
    setActorIdFilter("")
    setDateFrom("")
    setDateTo("")
    setActivePreset(null)
    setPage(0)
    if (orgId) loadEvents(0, orgId)
  }

  function handleExportCsv() {
    if (events.length === 0) return
    const headers = ["Time", "Entity Type", "Event Type", "Category", "Entity ID", "Actor ID", "Actor Name"]
    const rows = events.map((e) => [
      new Date(e.occurred_at).toISOString(),
      e.entity_type,
      e.event_type,
      e.event_category,
      e.entity_id,
      e.actor_id ?? "",
      e.actor_id ? (actorMap.get(e.actor_id) ?? "") : "",
    ])
    const csv = [headers, ...rows].map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const hasActiveFilters = entityTypeFilter || eventTypeFilter || actorIdFilter || dateFrom || dateTo
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div className="w-full space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">Audit Log</h2>
          <p className="text-sm text-muted-foreground">
            Activity and change history for your organization.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={handleExportCsv}
            disabled={events.length === 0}
            className="hidden sm:flex gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90 font-semibold transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Mobile view Export CSV button */}
      <div className="flex justify-end p-1 sm:hidden">
        <Button
          size="sm"
          onClick={handleExportCsv}
          disabled={events.length === 0}
          className="gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90 font-semibold transition-colors"
        >
          <Download className="h-3.5 w-3.5" />
          Export CSV
        </Button>
      </div>

      {/* Search and Quick Filters Bar */}
      <div className="flex items-center gap-3 flex-wrap rounded-xl border border-border bg-muted/20 px-3 py-2">
        <div className="flex items-center gap-2 flex-wrap flex-1">
          <div className="flex items-center gap-1.5 mr-2 text-muted-foreground">
            <Calendar className="h-3.5 w-3.5" />
            <span className="text-xs font-semibold uppercase tracking-wider">Quick:</span>
          </div>
          <div className="flex items-center gap-1.5 flex-wrap">
            {[
              { label: "Last 24h", value: "24h" },
              { label: "Last 7 days", value: "7d" },
              { label: "Last 30 days", value: "30d" },
              { label: "Last 90 days", value: "90d" },
            ].map((p) => {
              const isActive = activePreset === p.value
              return (
                <Button
                  key={p.value}
                  variant="outline"
                  size="sm"
                  className={`h-7 px-2.5 text-[11px] font-medium transition-all shadow-none ${
                    isActive
                      ? "bg-primary/10 text-primary border-primary/20"
                      : "border-transparent bg-transparent hover:bg-primary/5 hover:text-primary hover:border-primary/20"
                  }`}
                  onClick={() => {
                    handleDatePreset(p.value)
                    setPage(0)
                  }}
                >
                  {p.label}
                </Button>
              )
            })}
          </div>
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2.5 text-[11px] text-muted-foreground hover:text-red-500 hover:bg-red-500/5 transition-colors gap-1 ml-1"
              onClick={handleClearFilters}
            >
              <X className="h-3 w-3" />
              Clear all
            </Button>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2.5 text-[11px] font-semibold text-primary hover:bg-primary/5 transition-colors"
          onClick={() => setShowFilters((v) => !v)}
        >
          {showFilters ? "Hide" : "More"} filters
        </Button>
      </div>

      {/* Advanced filters */}
      {showFilters && (
        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm">Filters</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <form onSubmit={handleFilterSubmit} className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Entity Type</label>
                  <select
                    value={entityTypeFilter}
                    onChange={(e) => setEntityTypeFilter(e.target.value)}
                    className="h-8 w-full rounded-md border border-input bg-background px-2 text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="">All</option>
                    {ENTITY_TYPES.map((t) => (
                      <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Event Type</label>
                  <Input
                    value={eventTypeFilter}
                    onChange={(e) => setEventTypeFilter(e.target.value)}
                    placeholder="e.g. member_added"
                    className="h-8 text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" /> From
                  </label>
                  <Input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="h-8 text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" /> To
                  </label>
                  <Input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="h-8 text-xs"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Actor ID</label>
                <Input
                  value={actorIdFilter}
                  onChange={(e) => setActorIdFilter(e.target.value)}
                  placeholder="User UUID"
                  className="h-8 text-xs w-full sm:w-1/2"
                />
              </div>
              <div className="flex items-center gap-2">
                <Button type="submit" size="sm" disabled={isLoading || !orgId} className="h-7 text-xs">
                  Apply
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleClearFilters}
                  className="h-7 text-xs"
                >
                  Reset
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Events table */}
      <Card>
        <CardHeader className="py-3 px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ScrollText className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm">
                {isLoading ? "Loading…" : `${total.toLocaleString()} event${total !== 1 ? "s" : ""}`}
              </CardTitle>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>Page {page + 1} of {totalPages}</span>
              <Button
                variant="outline"
                size="sm"
                className="h-7 w-7 p-0"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0 || isLoading}
              >
                <ChevronLeft className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-7 w-7 p-0"
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1 || isLoading}
              >
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {error ? (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 m-4">
              <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/40">
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Time</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Entity</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Event</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Category</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Entity ID</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Actor</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading
                    ? [...Array(10)].map((_, i) => <SkeletonRow key={i} />)
                    : events.length === 0
                    ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-sm text-muted-foreground">
                          No audit events found for this organization.
                        </td>
                      </tr>
                    )
                    : events.map((event) => (
                      <EventDetailRow key={event.id} event={event} actorMap={actorMap} />
                    ))
                  }
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
