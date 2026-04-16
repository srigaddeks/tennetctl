"use client"

import { useEffect, useState, useCallback } from "react"
import { Button, Input } from "@kcontrol/ui"
import {
  Mail, Search, X, AlertCircle, ChevronLeft, ChevronRight,
  CheckCircle2, XCircle, Clock, AlertTriangle, RefreshCw, Ban,
  Send, MailCheck, MailX, Hourglass,
} from "lucide-react"
import { listInvitations, revokeInvitation, getInvitationStats } from "@/lib/api/admin"
import type { InvitationResponse, InvitationStatsResponse } from "@/lib/types/admin"
import Link from "next/link"

const PAGE_SIZE = 50

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-amber-500/10 border-amber-500/20 text-amber-500",
    accepted: "bg-emerald-500/10 border-emerald-500/20 text-emerald-500",
    expired: "bg-muted/40 border-border text-muted-foreground",
    revoked: "bg-red-500/10 border-red-500/20 text-red-500",
    declined: "bg-muted/40 border-border text-muted-foreground",
  }
  const icons: Record<string, React.ReactNode> = {
    pending: <Clock className="h-3 w-3" />,
    accepted: <CheckCircle2 className="h-3 w-3" />,
    expired: <AlertTriangle className="h-3 w-3" />,
    revoked: <XCircle className="h-3 w-3" />,
    declined: <XCircle className="h-3 w-3" />,
  }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border ${styles[status] || styles.pending}`}>
      {icons[status]}
      {status}
    </span>
  )
}

function ScopeBadge({ scope }: { scope: string }) {
  const styles: Record<string, string> = {
    platform: "bg-primary/10 border-primary/20 text-primary",
    organization: "bg-purple-500/10 border-purple-500/20 text-purple-500",
    workspace: "bg-cyan-500/10 border-cyan-500/20 text-cyan-500",
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium border ${styles[scope] || "bg-muted border-border text-muted-foreground"}`}>
      {scope}
    </span>
  )
}

function rowBorderCls(status: string) {
  switch (status) {
    case "pending":  return "border-l-amber-500"
    case "accepted": return "border-l-green-500"
    case "expired":
    case "revoked":
    case "declined": return "border-l-red-500"
    default:         return "border-l-primary"
  }
}

// KPI stat card data
const kpiCards = (stats: InvitationStatsResponse) => [
  {
    label: "Total Sent",
    value: stats.total,
    icon: <Send className="h-4 w-4 text-primary" />,
    numCls: "text-foreground",
    borderCls: "border-l-primary",
    filterKey: "",
  },
  {
    label: "Pending",
    value: stats.pending,
    icon: <Hourglass className="h-4 w-4 text-amber-500" />,
    numCls: "text-amber-500",
    borderCls: "border-l-amber-500",
    filterKey: "pending",
  },
  {
    label: "Accepted",
    value: stats.accepted,
    icon: <MailCheck className="h-4 w-4 text-green-500" />,
    numCls: "text-green-500",
    borderCls: "border-l-green-500",
    filterKey: "accepted",
  },
  {
    label: "Expired",
    value: stats.expired,
    icon: <AlertTriangle className="h-4 w-4 text-muted-foreground" />,
    numCls: "text-muted-foreground",
    borderCls: "border-l-red-500",
    filterKey: "expired",
  },
  {
    label: "Revoked",
    value: stats.revoked,
    icon: <MailX className="h-4 w-4 text-red-500" />,
    numCls: "text-red-500",
    borderCls: "border-l-red-500",
    filterKey: "revoked",
  },
  {
    label: "Declined",
    value: stats.declined,
    icon: <XCircle className="h-4 w-4 text-muted-foreground" />,
    numCls: "text-muted-foreground",
    borderCls: "border-l-red-500",
    filterKey: "declined",
  },
]

export default function InvitationsPage() {
  const [invitations, setInvitations] = useState<InvitationResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("")
  const [scopeFilter, setScopeFilter] = useState<string>("")
  const [stats, setStats] = useState<InvitationStatsResponse | null>(null)
  const [revoking, setRevoking] = useState<string | null>(null)

  useEffect(() => {
    const t = setTimeout(() => { setDebouncedSearch(search); setPage(1) }, 350)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => { setPage(1) }, [statusFilter, scopeFilter])

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const res = await listInvitations({
        page,
        page_size: PAGE_SIZE,
        email: debouncedSearch || undefined,
        status: statusFilter || undefined,
        scope: scopeFilter || undefined,
      })
      setInvitations(res.items); setTotal(res.total)
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to load invitations") }
    finally { setLoading(false) }
  }, [page, debouncedSearch, statusFilter, scopeFilter])

  useEffect(() => { load() }, [load])
  useEffect(() => { getInvitationStats().then(setStats).catch(() => null) }, [])

  async function revoke(id: string) {
    setRevoking(id)
    try {
      await revokeInvitation(id)
      setInvitations((prev) => prev.map((inv) => inv.id === id ? { ...inv, status: "revoked" } : inv))
      if (stats) setStats({ ...stats, pending: Math.max(0, stats.pending - 1), revoked: stats.revoked + 1 })
    } catch { /* ignore */ }
    finally { setRevoking(null) }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)
  const from = (page - 1) * PAGE_SIZE + 1
  const to = Math.min(page * PAGE_SIZE, total)
  const hasFilters = !!(statusFilter || scopeFilter || debouncedSearch)

  function clearFilters() { setSearch(""); setStatusFilter(""); setScopeFilter("") }

  return (
    <div className="max-w-5xl space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-primary/10 p-3.5 shrink-0">
            <Mail className="h-6 w-6 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <Link href="/admin/users" className="text-xs text-muted-foreground/50 hover:text-foreground transition-colors flex items-center gap-1">
                <ChevronLeft className="h-3 w-3" />Users
              </Link>
              <span className="text-xs text-muted-foreground/30">/</span>
              <span className="text-xs text-muted-foreground">Invitations</span>
            </div>
            <h2 className="text-2xl font-bold text-foreground tracking-tight mt-0.5">Invitations</h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              All platform invitations — pending, accepted, expired, and revoked.{" "}
              <Link href="/admin/campaigns" className="text-primary/70 hover:text-primary transition-colors">View Campaigns →</Link>
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading} className="h-7 text-xs gap-1.5 mt-1 shrink-0">
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />Refresh
        </Button>
      </div>

      {/* KPI stat cards */}
      {stats && (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
          {kpiCards(stats).map((card) => {
            const active = card.filterKey && statusFilter === card.filterKey
            return (
              <button
                key={card.label}
                type="button"
                onClick={() =>
                  card.filterKey
                    ? setStatusFilter(active ? "" : card.filterKey)
                    : clearFilters()
                }
                className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${card.borderCls} bg-card px-4 py-3 text-left transition-colors hover:bg-accent/10 ${active ? "ring-1 ring-primary/30" : ""}`}
              >
                <div className="shrink-0 rounded-lg p-2 bg-muted">
                  {card.icon}
                </div>
                <div className="min-w-0">
                  <span className={`text-2xl font-bold tabular-nums leading-none ${card.numCls}`}>{card.value}</span>
                  <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{card.label}</span>
                </div>
              </button>
            )
          })}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          <AlertCircle className="h-4 w-4 shrink-0" />{error}
        </div>
      )}

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-center gap-2 flex-wrap">
        {/* Search */}
        <div className="relative w-56">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40 pointer-events-none" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by email…"
            className="h-7 pl-8 text-xs"
          />
          {search && (
            <button type="button" onClick={() => setSearch("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Status filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-7 rounded-lg border border-border bg-background px-2.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="expired">Expired</option>
          <option value="revoked">Revoked</option>
          <option value="declined">Declined</option>
        </select>

        {/* Scope filter */}
        <select
          value={scopeFilter}
          onChange={(e) => setScopeFilter(e.target.value)}
          className="h-7 rounded-lg border border-border bg-background px-2.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
        >
          <option value="">All scopes</option>
          <option value="platform">Platform</option>
          <option value="organization">Organization</option>
          <option value="workspace">Workspace</option>
        </select>

        {/* Active filter chips */}
        {statusFilter && (
          <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] text-amber-500">
            {statusFilter}
            <button type="button" onClick={() => setStatusFilter("")} className="hover:text-foreground">
              <X className="h-2.5 w-2.5" />
            </button>
          </span>
        )}
        {scopeFilter && (
          <span className="inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[11px] text-primary">
            {scopeFilter}
            <button type="button" onClick={() => setScopeFilter("")} className="hover:text-foreground">
              <X className="h-2.5 w-2.5" />
            </button>
          </span>
        )}
        {debouncedSearch && (
          <span className="inline-flex items-center gap-1 rounded-full border border-border bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
            "{debouncedSearch}"
            <button type="button" onClick={() => setSearch("")} className="hover:text-foreground">
              <X className="h-2.5 w-2.5" />
            </button>
          </span>
        )}

        {hasFilters && (
          <button type="button" onClick={clearFilters}
            className="text-[11px] text-muted-foreground/50 hover:text-red-500 transition-colors flex items-center gap-1">
            <X className="h-3 w-3" />Clear all
          </button>
        )}

        <span className="ml-auto text-xs text-muted-foreground/60">
          <span className="font-semibold text-foreground">{total}</span> results
        </span>
      </div>

      {/* Invitation list */}
      <div className="rounded-xl border border-border overflow-hidden">
        {/* Column header */}
        <div className="grid grid-cols-[1fr_100px_80px_140px_100px_80px] gap-3 px-4 py-1.5 border-b border-border/30 bg-muted/20 text-[10px] font-medium text-muted-foreground/40 uppercase tracking-wider">
          <div>Email</div>
          <div>Status</div>
          <div>Scope</div>
          <div>Expires / Resolved</div>
          <div>Invited</div>
          <div />
        </div>

        {/* Skeleton loading */}
        {loading && (
          <div className="divide-y divide-border/20">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="grid grid-cols-[1fr_100px_80px_140px_100px_80px] gap-3 border-l-[3px] border-l-border/20 px-4 py-3 items-center">
                <div className="h-3 bg-muted rounded animate-pulse w-48" />
                <div className="h-5 bg-muted rounded-full animate-pulse w-16" />
                <div className="h-4 bg-muted rounded-full animate-pulse w-14" />
                <div className="h-3 bg-muted rounded animate-pulse w-28" />
                <div className="h-3 bg-muted rounded animate-pulse w-20" />
              </div>
            ))}
          </div>
        )}

        {/* Rows */}
        {!loading && invitations.map((inv) => (
          <div
            key={inv.id}
            className={`grid grid-cols-[1fr_100px_80px_140px_100px_80px] gap-3 border-b border-border/20 border-l-[3px] ${rowBorderCls(inv.status)} last:border-b-0 px-4 py-2.5 hover:bg-accent/10 transition-colors items-center group`}
          >
            <div className="min-w-0">
              <div className="text-xs font-medium text-foreground truncate">{inv.email}</div>
              <div className="flex items-center gap-2 mt-0.5">
                {inv.role && <span className="text-[11px] text-muted-foreground/40">role: {inv.role}</span>}
                {inv.source_tag && (
                  <span className="inline-flex items-center gap-0.5 text-[10px] text-violet-400/70 font-mono">
                    #{inv.source_tag}
                  </span>
                )}
              </div>
            </div>
            <div><StatusBadge status={inv.status} /></div>
            <div><ScopeBadge scope={inv.scope} /></div>
            <div className="text-[11px] text-muted-foreground/60">
              {inv.accepted_at
                ? <span className="text-green-500">Accepted {fmtDate(inv.accepted_at)}</span>
                : inv.revoked_at
                ? <span className="text-red-500/70">Revoked {fmtDate(inv.revoked_at)}</span>
                : <span className={new Date(inv.expires_at) < new Date() ? "text-muted-foreground/40" : ""}>
                    {fmtDateTime(inv.expires_at)}
                  </span>
              }
            </div>
            <div className="text-[11px] text-muted-foreground/50">{fmtDate(inv.created_at)}</div>
            <div className="flex items-center justify-end">
              {inv.status === "pending" && (
                <button
                  type="button"
                  onClick={() => revoke(inv.id)}
                  disabled={revoking === inv.id}
                  title="Revoke invitation"
                  className="opacity-0 group-hover:opacity-100 rounded-lg p-1.5 text-muted-foreground/40 hover:text-red-500 hover:bg-red-500/10 transition-all disabled:opacity-50"
                >
                  {revoking === inv.id
                    ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    : <Ban className="h-3.5 w-3.5" />
                  }
                </button>
              )}
            </div>
          </div>
        ))}

        {/* Empty state */}
        {!loading && invitations.length === 0 && (
          <div className="px-4 py-12 text-center">
            <Mail className="h-8 w-8 text-muted-foreground/20 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground/50">
              No invitations found{hasFilters ? " matching the current filters" : ""}.
            </p>
          </div>
        )}

        {/* Pagination */}
        {total > PAGE_SIZE && (
          <div className="flex items-center justify-between border-t border-border/30 px-4 py-2.5 bg-muted/10">
            <p className="text-xs text-muted-foreground/50">{from}–{to} of {total}</p>
            <div className="flex items-center gap-1.5">
              <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="h-7 text-xs gap-1">
                <ChevronLeft className="h-3 w-3" />Prev
              </Button>
              <span className="text-xs text-muted-foreground/50 tabular-nums">{page}/{totalPages}</span>
              <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} className="h-7 text-xs gap-1">
                Next<ChevronRight className="h-3 w-3" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
