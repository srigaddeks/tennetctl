"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import Link from "next/link"
import { Button, Input, Label } from "@kcontrol/ui"
import {
  Users, UserCog, Monitor, Clock, ChevronLeft, ChevronRight,
  X, AlertCircle, Search, Eye, EyeOff, Zap, CheckCircle2,
  XCircle, AlertTriangle, Shield, Mail, Plus, Upload, Tag,
  Send, Loader2, ArrowLeft, Building2, Layers, Key, UserCheck,
  Filter, ChevronDown, ChevronsUpDown, RefreshCw, Trash2, Ban,
  UserX, Activity,
} from "lucide-react"
import {
  listAdminUsers, listUserSessions, revokeUserSession,
  startImpersonation, listImpersonationHistory,
  bulkCreateInvitations, listCampaigns, createCampaign,
  bulkInviteCampaign, getInvitationStats, getAdminUserDetail,
  disableUser, enableUser, getUserAuditEvents, deleteUser,
  listGroups, addGroupMember, removeGroupMember,
} from "@/lib/api/admin"
import { listOrgs, addOrgMember, removeOrgMember } from "@/lib/api/orgs"
import { setAccessToken } from "@/lib/api/apiClient"
import type {
  UserSummaryResponse, SessionResponse, ImpersonationSessionResponse,
  CampaignResponse, BulkInviteResultEntry, InvitationStatsResponse,
  CreateCampaignRequest, UserDetailResponse, AuditEventResponse,
  GroupResponse,
} from "@/lib/types/admin"
import type { OrgResponse } from "@/lib/types/orgs"

const PAGE_SIZE = 20

function initials(email: string | null, username: string | null) {
  const s = email || username || "?"
  const p = s.split(/[@._-]/)
  return p.length >= 2 ? (p[0][0] + p[1][0]).toUpperCase() : s.slice(0, 2).toUpperCase()
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

function parseEmails(raw: string): string[] {
  return [...new Set(
    raw.split(/[\n,;]+/)
      .map((e) => e.trim().toLowerCase())
      .filter((e) => e.includes("@") && e.length >= 5)
  )]
}

function slugify(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")
}

// ─────────────────────────────────────────────────────────────────────────────
// Status tag
// ─────────────────────────────────────────────────────────────────────────────

function UserCategoryTag({ category }: { category?: string }) {
  if (!category || category === "full") return null
  return (
    <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border bg-blue-500/10 border-blue-500/20 text-blue-500">
      <UserCheck className="h-3 w-3" />External
    </span>
  )
}

function StatusTag({ user }: { user: UserSummaryResponse }) {
  if (user.is_disabled) return (
    <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border bg-red-500/10 border-red-500/20 text-red-500">
      <XCircle className="h-3 w-3" />Disabled
    </span>
  )
  if (user.is_active) return (
    <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border bg-emerald-500/10 border-emerald-500/20 text-emerald-500">
      <CheckCircle2 className="h-3 w-3" />Active
    </span>
  )
  return (
    <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border bg-amber-500/10 border-amber-500/20 text-amber-500">
      <AlertTriangle className="h-3 w-3" />Inactive
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Sessions panel
// ─────────────────────────────────────────────────────────────────────────────

function SessionsPanel({ userId, onClose }: { userId: string; onClose: () => void }) {
  const [sessions, setSessions] = useState<SessionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [revoking, setRevoking] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { const r = await listUserSessions(userId, true); setSessions(r.sessions) }
    catch (e) { setError(e instanceof Error ? e.message : "Failed to load sessions") }
    finally { setLoading(false) }
  }, [userId])

  useEffect(() => { load() }, [load])

  async function revoke(sid: string) {
    setRevoking(sid); setError(null)
    try { await revokeUserSession(userId, sid); await load() }
    catch (e) { setError(e instanceof Error ? e.message : "Failed to revoke session") }
    finally { setRevoking(null) }
  }

  return (
    <div className="space-y-1.5">
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />{error}
        </div>
      )}
      {loading && <div className="space-y-1.5">{[1,2].map(i => <div key={i} className="h-9 animate-pulse rounded-lg bg-muted" />)}</div>}
      {!loading && sessions.length === 0 && <p className="text-xs text-muted-foreground/50 text-center py-2">No sessions.</p>}
      {!loading && sessions.map((s) => (
        <div key={s.session_id} className="flex items-center gap-3 rounded-lg border border-border/40 bg-card px-3 py-2">
          <div className="flex-1 min-w-0 space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground">{s.client_ip || "Unknown IP"}</span>
              {s.is_impersonation && <span className="text-[10px] rounded-full px-1.5 py-0.5 border bg-amber-500/10 border-amber-500/20 text-amber-500">impersonation</span>}
              {s.revoked_at
                ? <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                : <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              }
            </div>
            <p className="text-[11px] text-muted-foreground/50 truncate">{s.user_agent?.slice(0, 60) || "—"}</p>
            <p className="text-[11px] text-muted-foreground/40">{fmtDateTime(s.created_at)}</p>
          </div>
          {!s.revoked_at && (
            <Button variant="outline" size="sm" className="shrink-0 h-7 text-xs text-red-500 border-red-500/30 hover:bg-red-500/10"
              disabled={revoking === s.session_id} onClick={() => revoke(s.session_id)}>
              {revoking === s.session_id ? "…" : "Revoke"}
            </Button>
          )}
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Org memberships panel
// ─────────────────────────────────────────────────────────────────────────────

const ORG_ROLES = ["owner", "admin", "member", "viewer", "billing"]

function OrgMembershipsPanel({
  userId, memberships, onChanged,
}: {
  userId: string
  memberships: import("@/lib/types/admin").UserOrgMembership[]
  onChanged: () => void
}) {
  const [orgs, setOrgs] = useState<OrgResponse[]>([])
  const [selectedOrgId, setSelectedOrgId] = useState("")
  const [selectedRole, setSelectedRole] = useState("member")
  const [adding, setAdding] = useState(false)
  const [removing, setRemoving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [orgsOpen, setOrgsOpen] = useState(false)

  useEffect(() => {
    listOrgs().then(setOrgs).catch(() => {})
  }, [])

  const selectedOrg = orgs.find((o) => o.id === selectedOrgId)
  const alreadyMember = memberships.some((m) => m.org_id === selectedOrgId)

  async function doAdd() {
    if (!selectedOrgId) return
    setAdding(true); setError(null)
    try {
      await addOrgMember(selectedOrgId, userId, selectedRole)
      setSelectedOrgId(""); setSelectedRole("member")
      onChanged()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add to org")
    } finally {
      setAdding(false)
    }
  }

  async function doRemove(orgId: string) {
    setRemoving(orgId); setError(null)
    try {
      await removeOrgMember(orgId, userId)
      onChanged()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove from org")
    } finally {
      setRemoving(null)
    }
  }

  return (
    <div className="space-y-3">
      {/* Add to org */}
      <div className="rounded-lg border border-border/40 bg-card p-3 space-y-2">
        <p className="text-xs font-medium text-foreground">Add to org</p>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <button
              type="button"
              onClick={() => setOrgsOpen((v) => !v)}
              className="w-full flex items-center justify-between rounded-lg border border-border/60 bg-background px-3 py-2 text-xs text-foreground h-8"
            >
              <span className={selectedOrg ? "text-foreground" : "text-muted-foreground/40"}>
                {selectedOrg ? selectedOrg.name : "Select org…"}
              </span>
              <ChevronsUpDown className="h-3 w-3 text-muted-foreground/40" />
            </button>
            {orgsOpen && (
              <div className="absolute z-50 mt-1 w-full rounded-lg border border-border/60 bg-popover shadow-lg max-h-48 overflow-y-auto">
                {orgs.map((o) => (
                  <button
                    key={o.id}
                    type="button"
                    onClick={() => { setSelectedOrgId(o.id); setOrgsOpen(false) }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-left hover:bg-accent/30 transition-colors"
                  >
                    <Building2 className="h-3 w-3 text-muted-foreground/40 shrink-0" />
                    <span className="flex-1 truncate">{o.name}</span>
                    <span className="text-[10px] text-muted-foreground/40">{o.org_type_code}</span>
                  </button>
                ))}
                {orgs.length === 0 && <p className="px-3 py-2 text-xs text-muted-foreground/40">No orgs found.</p>}
              </div>
            )}
          </div>
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="rounded-lg border border-border/60 bg-background px-2 py-1 text-xs text-foreground h-8 focus:outline-none"
          >
            {ORG_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <Button
            size="sm"
            className="h-8 text-xs gap-1.5"
            disabled={!selectedOrgId || adding || alreadyMember}
            onClick={doAdd}
          >
            {adding ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
            {alreadyMember ? "Already member" : "Add"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />{error}
        </div>
      )}

      {/* Current memberships */}
      {memberships.length === 0 && <p className="text-xs text-muted-foreground/40 text-center py-2">Not a member of any org.</p>}
      {memberships.map((m) => (
        <div key={m.org_id} className="flex items-center gap-3 rounded-lg border border-border/40 bg-card px-3 py-2">
          <div className="h-6 w-6 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
            <Building2 className="h-3.5 w-3.5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-foreground truncate">{m.org_name}</div>
            <div className="text-[11px] text-muted-foreground/50">{m.org_type}</div>
          </div>
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium border ${
            m.role === "owner" ? "bg-amber-500/10 border-amber-500/20 text-amber-500" :
            m.role === "admin" ? "bg-primary/10 border-primary/20 text-primary" :
            "bg-muted border-border text-muted-foreground"
          }`}>{m.role}</span>
          <button
            type="button"
            onClick={() => doRemove(m.org_id)}
            disabled={removing === m.org_id}
            className="shrink-0 h-6 w-6 flex items-center justify-center rounded-md text-muted-foreground/30 hover:text-red-500 hover:bg-red-500/10 transition-colors disabled:opacity-50"
          >
            {removing === m.org_id ? <Loader2 className="h-3 w-3 animate-spin" /> : <X className="h-3 w-3" />}
          </button>
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Group memberships panel
// ─────────────────────────────────────────────────────────────────────────────

function GroupMembershipsPanel({
  userId, memberships, orgMemberships, onChanged,
}: {
  userId: string
  memberships: import("@/lib/types/admin").UserGroupMembership[]
  orgMemberships: import("@/lib/types/admin").UserOrgMembership[]
  onChanged: () => void
}) {
  const [groups, setGroups] = useState<GroupResponse[]>([])
  const [search, setSearch] = useState("")
  const [selectedGroupId, setSelectedGroupId] = useState("")
  const [adding, setAdding] = useState(false)
  const [removing, setRemoving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listGroups().then((r) => setGroups(r.groups)).catch(() => {})
  }, [])

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (!dropdownRef.current?.contains(e.target as Node)) setDropdownOpen(false) }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  // Org name lookup from user's org memberships
  const orgNameMap = Object.fromEntries(orgMemberships.map((m) => [m.org_id, m.org_name]))

  // Only show non-system groups in the picker — system groups are auto-managed
  const pickableGroups = groups.filter((g) => !g.is_system)
  const memberIds = new Set(memberships.map((m) => m.group_id))

  // Filter by search within pickable, non-already-member groups
  const filteredGroups = pickableGroups.filter((g) =>
    !memberIds.has(g.id) &&
    (!search || g.name.toLowerCase().includes(search.toLowerCase()) || g.code.toLowerCase().includes(search.toLowerCase()))
  )

  // Group picker results by scope
  const platformGroups = filteredGroups.filter((g) => !g.scope_org_id && !g.scope_workspace_id)
  const scopedGroups = filteredGroups.filter((g) => g.scope_org_id || g.scope_workspace_id)
  const scopedByOrg: Record<string, GroupResponse[]> = {}
  for (const g of scopedGroups) {
    const key = g.scope_org_id ?? g.scope_workspace_id ?? "other"
    ;(scopedByOrg[key] ??= []).push(g)
  }

  const selectedGroup = groups.find((g) => g.id === selectedGroupId)

  async function doAdd() {
    if (!selectedGroupId) return
    setAdding(true); setError(null)
    try {
      await addGroupMember(selectedGroupId, userId)
      setSelectedGroupId(""); setSearch("")
      onChanged()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add to group")
    } finally {
      setAdding(false)
    }
  }

  async function doRemove(groupId: string) {
    setRemoving(groupId); setError(null)
    try {
      await removeGroupMember(groupId, userId)
      onChanged()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove from group")
    } finally {
      setRemoving(null)
    }
  }

  // Partition current memberships
  const systemMemberships = memberships.filter((m) => m.is_system)
  const customMemberships = memberships.filter((m) => !m.is_system)

  return (
    <div className="space-y-3">
      {/* Add to group — only non-system groups */}
      <div className="rounded-lg border border-border/40 bg-card p-3 space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-foreground">Add to custom group</p>
          <span className="text-[10px] text-muted-foreground/50">System groups are auto-managed</span>
        </div>
        <div className="flex gap-2">
          <div ref={dropdownRef} className="relative flex-1">
            <div className="flex items-center rounded-lg border border-border/60 bg-background px-3 h-8 gap-2">
              <Search className="h-3 w-3 text-muted-foreground/40 shrink-0" />
              <input
                type="text"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setDropdownOpen(true); setSelectedGroupId("") }}
                onFocus={() => setDropdownOpen(true)}
                placeholder="Search custom groups…"
                className="flex-1 bg-transparent text-xs text-foreground placeholder:text-muted-foreground/40 focus:outline-none"
              />
              {selectedGroup && <span className="text-[10px] text-primary font-medium shrink-0 truncate max-w-[120px]">{selectedGroup.name}</span>}
            </div>
            {dropdownOpen && (platformGroups.length > 0 || Object.keys(scopedByOrg).length > 0) && (
              <div className="absolute z-50 mt-1 w-full rounded-lg border border-border/60 bg-popover shadow-lg max-h-64 overflow-y-auto">
                {platformGroups.length > 0 && (
                  <>
                    <div className="px-3 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border/40 bg-muted/30">
                      Platform Groups
                    </div>
                    {platformGroups.slice(0, 10).map((g) => (
                      <button key={g.id} type="button"
                        onClick={() => { setSelectedGroupId(g.id); setSearch(g.name); setDropdownOpen(false) }}
                        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-left hover:bg-accent/30 transition-colors"
                      >
                        <Shield className="h-3 w-3 text-violet-400 shrink-0" />
                        <span className="flex-1 truncate">{g.name}</span>
                        <span className="text-[10px] text-muted-foreground/40 font-mono shrink-0">{g.code}</span>
                      </button>
                    ))}
                  </>
                )}
                {Object.entries(scopedByOrg).map(([orgId, orgGroups]) => {
                  const orgName = orgNameMap[orgId] ?? orgId.slice(0, 8)
                  return (
                    <div key={orgId}>
                      <div className="px-3 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border/40 bg-muted/30 flex items-center gap-1">
                        <Building2 className="h-3 w-3 text-blue-400" />{orgName}
                      </div>
                      {orgGroups.slice(0, 10).map((g) => (
                        <button key={g.id} type="button"
                          onClick={() => { setSelectedGroupId(g.id); setSearch(g.name); setDropdownOpen(false) }}
                          className="w-full flex items-center gap-2 px-3 py-2 text-xs text-left hover:bg-accent/30 transition-colors"
                        >
                          <Layers className="h-3 w-3 text-blue-400 shrink-0" />
                          <span className="flex-1 truncate">{g.name}</span>
                          <span className="text-[10px] text-muted-foreground/40 font-mono shrink-0">{g.code}</span>
                        </button>
                      ))}
                    </div>
                  )
                })}
                {filteredGroups.length === 0 && search && (
                  <p className="px-3 py-2 text-xs text-muted-foreground/40">No groups match &quot;{search}&quot;</p>
                )}
              </div>
            )}
          </div>
          <Button size="sm" className="h-8 text-xs gap-1.5"
            disabled={!selectedGroupId || adding} onClick={doAdd}
          >
            {adding ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
            Add
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />{error}
        </div>
      )}

      {memberships.length === 0 && (
        <p className="text-xs text-muted-foreground/40 text-center py-2">Not a member of any group.</p>
      )}

      {/* System groups — read-only, auto-managed */}
      {systemMemberships.length > 0 && (
        <div className="space-y-1">
          <p className="text-[10px] font-semibold text-muted-foreground/50 uppercase tracking-wider flex items-center gap-1">
            <Ban className="h-2.5 w-2.5" /> System Groups (auto-managed)
          </p>
          {systemMemberships.map((m) => (
            <div key={m.group_id} className="flex items-center gap-3 rounded-lg border border-amber-500/15 bg-amber-500/5 px-3 py-2">
              <div className="h-6 w-6 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
                {m.scope_workspace_id
                  ? <Layers className="h-3.5 w-3.5 text-emerald-500" />
                  : m.scope_org_id
                  ? <Building2 className="h-3.5 w-3.5 text-blue-500" />
                  : <Shield className="h-3.5 w-3.5 text-amber-500" />
                }
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-foreground truncate">{m.group_name}</div>
                <div className="text-[11px] text-muted-foreground/50 font-mono flex items-center gap-1">
                  {m.scope_org_id && orgNameMap[m.scope_org_id] && (
                    <><Building2 className="h-2.5 w-2.5 text-blue-400" />{orgNameMap[m.scope_org_id]} · </>
                  )}
                  {m.group_code}
                </div>
              </div>
              <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium border bg-amber-500/10 border-amber-500/20 text-amber-600">
                <Ban className="h-2.5 w-2.5" /> system
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Custom groups — removable */}
      {customMemberships.length > 0 && (
        <div className="space-y-1">
          {systemMemberships.length > 0 && (
            <p className="text-[10px] font-semibold text-muted-foreground/50 uppercase tracking-wider">Custom Groups</p>
          )}
          {customMemberships.map((m) => (
            <div key={m.group_id} className="flex items-center gap-3 rounded-lg border border-border/40 bg-card px-3 py-2 group/gmrow">
              <div className="h-6 w-6 rounded-lg bg-purple-500/10 flex items-center justify-center shrink-0">
                {m.scope_workspace_id
                  ? <Layers className="h-3.5 w-3.5 text-emerald-500" />
                  : m.scope_org_id
                  ? <Building2 className="h-3.5 w-3.5 text-blue-500" />
                  : <Layers className="h-3.5 w-3.5 text-purple-500" />
                }
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-foreground truncate">{m.group_name}</div>
                <div className="text-[11px] text-muted-foreground/50 font-mono flex items-center gap-1">
                  {m.scope_org_id && orgNameMap[m.scope_org_id] && (
                    <><Building2 className="h-2.5 w-2.5 text-blue-400" />{orgNameMap[m.scope_org_id]} · </>
                  )}
                  {m.group_code}
                </div>
              </div>
              <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium border bg-muted border-border text-muted-foreground">
                {m.role_level_code}
              </span>
              <button type="button" onClick={() => doRemove(m.group_id)} disabled={removing === m.group_id}
                className="shrink-0 h-6 w-6 flex items-center justify-center rounded-md text-muted-foreground/30 hover:text-red-500 hover:bg-red-500/10 transition-colors disabled:opacity-50 opacity-0 group-hover/gmrow:opacity-100"
              >
                {removing === m.group_id ? <Loader2 className="h-3 w-3 animate-spin" /> : <X className="h-3 w-3" />}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// User detail expanded panel
// ─────────────────────────────────────────────────────────────────────────────

type DetailTab = "profile" | "orgs" | "workspaces" | "groups" | "sessions" | "audit" | "impersonate"

function AuditPanel({ userId }: { userId: string }) {
  const [events, setEvents] = useState<AuditEventResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getUserAuditEvents(userId, { limit: 20 })
      .then((r) => setEvents(r.events))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load audit events"))
      .finally(() => setLoading(false))
  }, [userId])

  if (loading) return <div className="space-y-1.5">{[1,2,3].map(i => <div key={i} className="h-9 animate-pulse rounded-lg bg-muted" />)}</div>
  if (error) return (
    <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
      <AlertCircle className="h-3.5 w-3.5 shrink-0" />{error}
    </div>
  )
  if (events.length === 0) return <p className="text-xs text-muted-foreground/50 text-center py-4">No audit events found.</p>

  return (
    <div className="space-y-1">
      {events.map((e) => (
        <div key={e.id} className="flex items-start gap-2.5 rounded-lg border border-border/30 bg-card px-3 py-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-medium text-foreground">{e.event_type.replace(/_/g, " ")}</span>
              <span className="inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] border bg-muted/50 border-border/40 text-muted-foreground">{e.entity_type}</span>
              <span className="text-[10px] text-muted-foreground/40">{e.event_category}</span>
            </div>
            <div className="flex items-center gap-2 mt-0.5 text-[11px] text-muted-foreground/50">
              <span>{fmtDateTime(e.occurred_at)}</span>
              {e.actor_id && <span>· by <code className="font-mono text-[10px]">{e.actor_id.slice(0, 8)}…</code></span>}
              {e.ip_address && <span>· {e.ip_address}</span>}
            </div>
          </div>
        </div>
      ))}
      <p className="text-[11px] text-muted-foreground/40 text-center pt-1">Showing last 20 events</p>
    </div>
  )
}

function UserDetailPanel({ user, onClose, onUserUpdated }: { user: UserSummaryResponse; onClose: () => void; onUserUpdated?: () => void }) {
  const [tab, setTab] = useState<DetailTab>("profile")
  const [detail, setDetail] = useState<UserDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [impersonateReason, setImpersonateReason] = useState("")
  const [impersonating, setImpersonating] = useState(false)
  const [impersonateError, setImpersonateError] = useState<string | null>(null)
  const [toggling, setToggling] = useState(false)
  const [toggleError, setToggleError] = useState<string | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    setDetailError(null)
    getAdminUserDetail(user.user_id)
      .then(setDetail)
      .catch((e) => setDetailError(e instanceof Error ? e.message : "Failed to load user details"))
      .finally(() => setLoading(false))
  }, [user.user_id])

  async function doToggleDisabled() {
    setToggling(true); setToggleError(null)
    try {
      if (user.is_disabled) {
        await enableUser(user.user_id)
      } else {
        await disableUser(user.user_id)
      }
      onUserUpdated?.()
    } catch (e) {
      setToggleError(e instanceof Error ? e.message : "Failed to update user")
    } finally {
      setToggling(false)
    }
  }

  async function doDelete() {
    setDeleting(true); setDeleteError(null)
    try {
      await deleteUser(user.user_id)
      onClose?.()
      onUserUpdated?.()
    } catch (e) {
      setDeleteError(e instanceof Error ? e.message : "Failed to delete user")
      setDeleteConfirm(false)
    } finally {
      setDeleting(false)
    }
  }

  async function doImpersonate() {
    if (impersonateReason.trim().length < 5) return
    setImpersonating(true); setImpersonateError(null)
    try {
      // Save admin's current refresh token to a separate httpOnly cookie before overwriting
      await fetch("/api/auth/save-admin-session", { method: "POST" })

      const res = await startImpersonation({ target_user_id: user.user_id, reason: impersonateReason.trim() })

      // Store the target user info so the banner can display it after page reload
      sessionStorage.setItem("kc_imp_target", JSON.stringify({
        email: res.target_user.email,
        username: res.target_user.username,
        user_id: res.target_user.user_id,
      }))

      // Swap the httpOnly cookie to the impersonation refresh token
      await fetch("/api/auth/set-refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: res.refresh_token }),
      })

      // Put impersonation access token in memory and navigate
      setAccessToken(res.access_token)
      window.location.href = "/dashboard"
    } catch (e) { setImpersonateError(e instanceof Error ? e.message : "Failed"); setImpersonating(false) }
  }

  const TABS: { key: DetailTab; label: string }[] = [
    { key: "profile", label: "Profile" },
    { key: "orgs", label: `Orgs${detail ? ` (${detail.org_memberships.length})` : ""}` },
    { key: "workspaces", label: `Workspaces${detail ? ` (${detail.workspace_memberships.length})` : ""}` },
    { key: "groups", label: `Groups${detail ? ` (${detail.group_memberships.length})` : ""}` },
    { key: "sessions", label: "Sessions" },
    { key: "audit", label: "Audit" },
    { key: "impersonate", label: "Impersonate" },
  ]

  return (
    <div className="mx-1 mb-1 rounded-xl border border-border/60 bg-muted/10">
      {/* Tab bar */}
      <div className="flex border-b border-border/40 overflow-x-auto">
        {TABS.map((t) => (
          <button key={t.key} type="button" onClick={() => setTab(t.key)}
            className={`shrink-0 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
              tab === t.key ? "border-primary text-primary" : "border-transparent text-muted-foreground/60 hover:text-foreground"
            }`}>
            {t.label}
          </button>
        ))}
        <div className="flex-1" />
        <button type="button" onClick={onClose} className="px-3 py-2 text-muted-foreground/40 hover:text-foreground transition-colors">
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="p-3">
        {loading && <div className="space-y-1.5">{[1,2,3].map(i => <div key={i} className="h-8 animate-pulse rounded-lg bg-muted" />)}</div>}
        {!loading && detailError && (
          <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />{detailError}
          </div>
        )}

        {/* Profile tab */}
        {!loading && detail && tab === "profile" && (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              {detail.properties.map((p) => {
                let displayValue: React.ReactNode = p.value || <span className="italic text-muted-foreground/40">—</span>
                if (p.key === "default_org_id" && p.value) {
                  const org = detail.org_memberships.find((m) => m.org_id === p.value)
                  if (org) displayValue = org.org_name
                }
                if (p.key === "default_workspace_id" && p.value) {
                  const ws = detail.workspace_memberships.find((m) => m.workspace_id === p.value)
                  if (ws) displayValue = ws.workspace_name
                }
                return (
                  <div key={p.key} className="rounded-lg border border-border/30 bg-card px-3 py-2">
                    <div className="text-[10px] text-muted-foreground/50 uppercase tracking-wider font-medium">{p.key.replace(/_/g, " ")}</div>
                    <div className="text-xs text-foreground font-medium mt-0.5 truncate">{displayValue}</div>
                  </div>
                )
              })}
              {detail.properties.length === 0 && (
                <p className="text-xs text-muted-foreground/40 col-span-2 py-2 text-center">No properties set.</p>
              )}
            </div>
            <div className="flex items-center gap-2 text-[11px] text-muted-foreground/50 pt-1">
              <Key className="h-3 w-3" />
              <code className="font-mono">{user.user_id}</code>
              <span>·</span>
              <span>{user.tenant_key}</span>
              {user.is_system && <span className="rounded-full px-1.5 py-0.5 border bg-amber-500/10 border-amber-500/20 text-amber-500 text-[10px]">system</span>}
              {user.is_test && <span className="rounded-full px-1.5 py-0.5 border bg-muted/40 border-border text-muted-foreground text-[10px]">test</span>}
              {user.is_locked && <span className="rounded-full px-1.5 py-0.5 border bg-red-500/10 border-red-500/20 text-red-500 text-[10px]">locked</span>}
            </div>
            {/* Admin actions */}
            {!user.is_system && (
              <div className="flex items-center gap-2 pt-1 border-t border-border/30 flex-wrap">
                {(toggleError || deleteError) && (
                  <p className="text-xs text-red-500 flex items-center gap-1 w-full">
                    <AlertCircle className="h-3 w-3" />{toggleError || deleteError}
                  </p>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  disabled={toggling}
                  onClick={doToggleDisabled}
                  className={`h-7 text-xs gap-1.5 ${user.is_disabled ? "text-emerald-500 border-emerald-500/30 hover:bg-emerald-500/10" : "text-amber-500 border-amber-500/30 hover:bg-amber-500/10"}`}
                >
                  {toggling
                    ? <Loader2 className="h-3 w-3 animate-spin" />
                    : user.is_disabled
                    ? <Eye className="h-3 w-3" />
                    : <EyeOff className="h-3 w-3" />
                  }
                  {toggling ? "Updating…" : user.is_disabled ? "Enable Account" : "Disable Account"}
                </Button>
                <div className="flex-1" />
                {!deleteConfirm ? (
                  <button
                    type="button"
                    onClick={() => setDeleteConfirm(true)}
                    className="h-7 inline-flex items-center gap-1.5 rounded-md border border-red-500/20 px-2.5 text-xs text-red-500/60 hover:text-red-500 hover:border-red-500/40 hover:bg-red-500/5 transition-all"
                  >
                    <Trash2 className="h-3 w-3" />Delete user
                  </button>
                ) : (
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-red-500">Permanently delete?</span>
                    <button
                      type="button"
                      onClick={doDelete}
                      disabled={deleting}
                      className="h-7 inline-flex items-center gap-1 rounded-md bg-red-500 px-2.5 text-xs text-white hover:bg-red-600 transition-colors disabled:opacity-50"
                    >
                      {deleting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                      {deleting ? "Deleting…" : "Confirm"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteConfirm(false)}
                      className="h-7 inline-flex items-center gap-1 rounded-md border border-border px-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <X className="h-3 w-3" />Cancel
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Orgs tab */}
        {!loading && detail && tab === "orgs" && (
          <OrgMembershipsPanel
            userId={user.user_id}
            memberships={detail.org_memberships}
            onChanged={() => getAdminUserDetail(user.user_id).then(setDetail).catch(() => {})}
          />
        )}

        {/* Workspaces tab */}
        {!loading && detail && tab === "workspaces" && (
          <div className="space-y-1.5">
            {detail.workspace_memberships.length === 0 && <p className="text-xs text-muted-foreground/40 py-2 text-center">Not a member of any workspace.</p>}
            {detail.workspace_memberships.map((m) => (
              <div key={m.workspace_id} className="flex items-center gap-3 rounded-lg border border-border/40 bg-card px-3 py-2">
                <div className="h-6 w-6 rounded-lg bg-emerald-500/10 flex items-center justify-center shrink-0">
                  <Layers className="h-3.5 w-3.5 text-emerald-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-foreground truncate">{m.workspace_name}</div>
                  <div className="text-[11px] text-muted-foreground/50">{m.org_name} · {m.workspace_type}</div>
                </div>
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium border ${
                  m.role === "owner" ? "bg-amber-500/10 border-amber-500/20 text-amber-500" :
                  m.role === "admin" ? "bg-primary/10 border-primary/20 text-primary" :
                  "bg-muted border-border text-muted-foreground"
                }`}>{m.role}</span>
                <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${m.is_active ? "bg-emerald-500" : "bg-muted-foreground/40"}`} />
              </div>
            ))}
          </div>
        )}

        {/* Groups tab */}
        {!loading && detail && tab === "groups" && (
          <GroupMembershipsPanel
            userId={user.user_id}
            memberships={detail.group_memberships}
            orgMemberships={detail.org_memberships}
            onChanged={() => getAdminUserDetail(user.user_id).then(setDetail).catch(() => {})}
          />
        )}

        {/* Sessions tab */}
        {tab === "sessions" && <SessionsPanel userId={user.user_id} onClose={onClose} />}

        {/* Audit tab */}
        {tab === "audit" && <AuditPanel userId={user.user_id} />}

        {/* Impersonate tab */}
        {tab === "impersonate" && (
          <div className="space-y-3 max-w-sm">
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2">
              <p className="text-xs text-amber-500/80">You will be logged in as this user. All actions will be recorded.</p>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Reason <span className="text-red-500">*</span></Label>
              <textarea rows={2} value={impersonateReason} onChange={(e) => setImpersonateReason(e.target.value)}
                placeholder="Why are you impersonating? (min 5 chars)"
                className="w-full rounded-lg border border-border bg-card px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-amber-500/40 resize-none" />
            </div>
            {impersonateError && <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" />{impersonateError}</p>}
            <Button size="sm" disabled={impersonating || impersonateReason.trim().length < 5} onClick={doImpersonate}
              className="h-7 text-xs bg-amber-500 hover:bg-amber-600 text-white gap-1.5">
              {impersonating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <UserCog className="h-3.5 w-3.5" />}
              {impersonating ? "Starting…" : "Start Impersonation"}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// User row — border-l-[3px] colored by role/type
// ─────────────────────────────────────────────────────────────────────────────

function userBorderCls(user: UserSummaryResponse): string {
  if (user.is_disabled) return "border-l-red-500/60"
  if (user.is_system) return "border-l-amber-500/60"
  if (user.user_category && user.user_category !== "full") return "border-l-blue-500/60"
  return "border-l-primary/40"
}

function UserRow({ user, expanded, onToggle, onUserUpdated }: {
  user: UserSummaryResponse
  expanded: boolean
  onToggle: () => void
  onUserUpdated?: () => void
}) {
  const init = initials(user.email, user.username)
  const colors = ["bg-primary/20 text-primary", "bg-purple-500/20 text-purple-500", "bg-emerald-500/20 text-emerald-500", "bg-amber-500/20 text-amber-500", "bg-cyan-500/20 text-cyan-500"]
  const avatarColor = colors[user.user_id.charCodeAt(0) % colors.length]
  const displayName = user.display_name || user.email || user.username
  const borderCls = userBorderCls(user)

  return (
    <>
      <button type="button" onClick={onToggle}
        className={`w-full flex items-center gap-3 px-4 py-2.5 border-b border-l-[3px] ${borderCls} border-border/20 last:border-b-0 hover:bg-accent/10 transition-colors group text-left`}>
        <div className={`shrink-0 h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold ${avatarColor}`}>
          {init}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground truncate">{displayName || <span className="italic text-muted-foreground/50">no email</span>}</span>
            {user.display_name && user.email && <code className="text-[10px] font-mono text-muted-foreground/30 hidden sm:inline">{user.email}</code>}
            {!user.display_name && user.username && <code className="text-[10px] font-mono text-muted-foreground/30 hidden sm:inline">{user.username}</code>}
          </div>
          <p className="text-[11px] text-muted-foreground/40 mt-0.5">{fmtDate(user.created_at)}</p>
        </div>
        <StatusTag user={user} />
        <UserCategoryTag category={user.user_category} />
        <span className="hidden sm:flex items-center gap-1 text-[11px] text-muted-foreground/50 shrink-0">
          <span className={`h-1.5 w-1.5 rounded-full ${
            user.account_status === "active" ? "bg-emerald-500" :
            user.account_status === "pending_verification" ? "bg-amber-500" : "bg-muted-foreground/40"
          }`} />
          {user.account_status.replace(/_/g, " ")}
        </span>
        <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground/30 shrink-0 transition-transform ${expanded ? "rotate-180" : ""}`} />
      </button>
      {expanded && <UserDetailPanel user={user} onClose={onToggle} onUserUpdated={onUserUpdated} />}
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Bulk invite result summary
// ─────────────────────────────────────────────────────────────────────────────

function BulkResultSummary({ results, sent, skipped, errors, onDone }: {
  results: BulkInviteResultEntry[]
  sent: number; skipped: number; errors: number
  onDone: () => void
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="flex-1 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2.5 text-center">
          <div className="text-lg font-bold text-emerald-500">{sent}</div>
          <div className="text-[11px] text-emerald-500/70 font-medium">Sent</div>
        </div>
        <div className="flex-1 rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-2.5 text-center">
          <div className="text-lg font-bold text-amber-500">{skipped}</div>
          <div className="text-[11px] text-amber-500/70 font-medium">Skipped</div>
        </div>
        <div className="flex-1 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-center">
          <div className="text-lg font-bold text-red-500">{errors}</div>
          <div className="text-[11px] text-red-500/70 font-medium">Errors</div>
        </div>
      </div>
      <div className="max-h-56 overflow-y-auto space-y-1 rounded-xl border border-border/40 bg-muted/20 p-2">
        {results.map((r, i) => (
          <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-muted/30 transition-colors">
            {r.status === "sent"
              ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
              : r.status === "skipped"
              ? <XCircle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
              : <XCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
            }
            <span className="text-xs font-medium text-foreground/80 flex-1 truncate">{r.email}</span>
            {r.reason && <span className="text-[11px] text-muted-foreground/50 truncate max-w-[140px]">{r.reason}</span>}
          </div>
        ))}
      </div>
      <Button size="sm" onClick={onDone} className="w-full h-8 text-xs">Done</Button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick invite tab
// ─────────────────────────────────────────────────────────────────────────────

const CSV_SAMPLE = `email,scope
alice@example.com,platform
bob@acme.com,platform
carol@corp.com,platform`

function QuickInviteTab() {
  const [emailsRaw, setEmailsRaw] = useState("")
  const [scope, setScope] = useState("platform")
  const [sourceTag, setSourceTag] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{ sent: number; skipped: number; errors: number; results: BulkInviteResultEntry[] } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const emails = parseEmails(emailsRaw)

  function downloadSampleCSV() {
    const blob = new Blob([CSV_SAMPLE], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url; a.download = "invite_template.csv"; a.click()
    URL.revokeObjectURL(url)
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const text = await file.text()
    // Extract emails from CSV: skip header row if it contains "email", parse each line
    const lines = text.split(/\n/).filter(Boolean)
    const emailLines = lines
      .filter((l) => !l.toLowerCase().startsWith("email"))
      .map((l) => l.split(",")[0].trim())
      .join("\n")
    setEmailsRaw((prev) => prev ? prev + "\n" + emailLines : emailLines)
    e.target.value = ""
  }

  async function send() {
    if (emails.length === 0) { setError("Enter at least one valid email."); return }
    setLoading(true); setError(null)
    try {
      const res = await bulkCreateInvitations({
        emails,
        scope,
        source_tag: sourceTag.trim() || undefined,
      })
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send invitations")
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return <BulkResultSummary {...result} onDone={() => { setResult(null); setEmailsRaw(""); setSourceTag("") }} />
  }

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <Label className="text-xs">Emails</Label>
          <button type="button" onClick={downloadSampleCSV}
            className="flex items-center gap-1 text-[11px] text-primary/70 hover:text-primary transition-colors">
            <Upload className="h-3 w-3" />Download CSV template
          </button>
        </div>
        <textarea rows={5} value={emailsRaw} onChange={(e) => setEmailsRaw(e.target.value)}
          placeholder="alice@example.com, bob@example.com&#10;(comma-separated, newlines, or CSV)"
          className="w-full rounded-lg border border-border bg-card px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none font-mono" />
        <div className="flex items-center justify-between">
          <button type="button" onClick={() => fileRef.current?.click()}
            className="flex items-center gap-1 text-[11px] text-muted-foreground/60 hover:text-foreground transition-colors">
            <Upload className="h-3 w-3" />Upload CSV
          </button>
          <input ref={fileRef} type="file" accept=".csv,.txt" className="hidden" onChange={handleFileUpload} />
          {emails.length > 0 && <span className="text-[11px] text-muted-foreground/50">{emails.length} email{emails.length !== 1 ? "s" : ""}</span>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs">Scope</Label>
          <select value={scope} onChange={(e) => setScope(e.target.value)}
            className="w-full rounded-lg border border-border bg-card px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30">
            <option value="platform">Platform</option>
            <option value="organization">Organization</option>
            <option value="workspace">Workspace</option>
          </select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Source tag <span className="text-muted-foreground/40">(optional)</span></Label>
          <Input value={sourceTag} onChange={(e) => setSourceTag(e.target.value)}
            placeholder="e.g. linkedin-2026-q1" className="h-7 text-xs" />
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />{error}
        </div>
      )}

      <Button size="sm" disabled={loading || emails.length === 0} onClick={send} className="w-full h-8 text-xs gap-1.5">
        {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
        {loading ? "Sending…" : `Send ${emails.length > 0 ? emails.length : ""} invite${emails.length !== 1 ? "s" : ""}`}
      </Button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Campaign card
// ─────────────────────────────────────────────────────────────────────────────

function CampaignCard({ campaign, onInvite }: { campaign: CampaignResponse; onInvite: (c: CampaignResponse) => void }) {
  const statusColor: Record<string, string> = {
    active: "bg-emerald-500/10 border-emerald-500/20 text-emerald-500",
    paused: "bg-amber-500/10 border-amber-500/20 text-amber-500",
    closed: "bg-muted/40 border-border text-muted-foreground",
    archived: "bg-muted/20 border-border/40 text-muted-foreground/50",
  }
  const typeIcon: Record<string, string> = { event: "🎪", referral: "🔗", form: "📋", import: "📥", other: "📌" }

  return (
    <div className="rounded-xl border border-border/40 bg-card/60 p-3 hover:border-border/70 transition-colors">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-base">{typeIcon[campaign.campaign_type] || "📌"}</span>
          <div>
            <div className="text-xs font-semibold text-foreground leading-tight">{campaign.name}</div>
            <code className="text-[10px] text-muted-foreground/40 font-mono">{campaign.code}</code>
          </div>
        </div>
        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium border shrink-0 ${statusColor[campaign.status] || statusColor.closed}`}>
          {campaign.status}
        </span>
      </div>
      {campaign.description && <p className="text-[11px] text-muted-foreground/60 mb-2 line-clamp-2">{campaign.description}</p>}
      <div className="flex items-center gap-3 text-[11px] text-muted-foreground/50 mb-2.5">
        <span className="flex items-center gap-1"><Send className="h-3 w-3" />{campaign.invite_count} sent</span>
        <span className="flex items-center gap-1"><CheckCircle2 className="h-3 w-3 text-emerald-500/60" />{campaign.accepted_count} accepted</span>
        {campaign.invite_count > 0 && <span>{Math.round((campaign.accepted_count / campaign.invite_count) * 100)}%</span>}
      </div>
      {campaign.status === "active" && (
        <Button size="sm" onClick={() => onInvite(campaign)} className="w-full h-7 text-xs gap-1">
          <Plus className="h-3 w-3" />Bulk Invite to this Campaign
        </Button>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Campaign invite form
// ─────────────────────────────────────────────────────────────────────────────

function CampaignInviteForm({ campaign, onBack, onDone }: {
  campaign: CampaignResponse; onBack: () => void; onDone: () => void
}) {
  const [emailsRaw, setEmailsRaw] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{ sent: number; skipped: number; errors: number; results: BulkInviteResultEntry[] } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const emails = parseEmails(emailsRaw)

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const text = await file.text()
    const lines = text.split(/\n/).filter(Boolean)
    const emailLines = lines.filter((l) => !l.toLowerCase().startsWith("email")).map((l) => l.split(",")[0].trim()).join("\n")
    setEmailsRaw((prev) => prev ? prev + "\n" + emailLines : emailLines)
    e.target.value = ""
  }

  async function send() {
    if (emails.length === 0) { setError("Enter at least one valid email."); return }
    setLoading(true); setError(null)
    try {
      const res = await bulkInviteCampaign(campaign.id, { emails })
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send invitations")
    } finally { setLoading(false) }
  }

  if (result) return <BulkResultSummary {...result} onDone={onDone} />

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <button type="button" onClick={onBack} className="text-muted-foreground/50 hover:text-foreground transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" />
        </button>
        <div className="flex-1 min-w-0">
          <span className="text-xs font-semibold text-foreground">Invite to: {campaign.name}</span>
          <div className="text-[11px] text-muted-foreground/50">{campaign.default_scope} scope · expires in {campaign.default_expires_hours}h</div>
        </div>
      </div>
      <div className="space-y-1.5">
        <Label className="text-xs">Emails</Label>
        <textarea rows={6} value={emailsRaw} onChange={(e) => setEmailsRaw(e.target.value)}
          placeholder="alice@example.com, bob@example.com&#10;(comma-separated, newlines, or CSV)"
          className="w-full rounded-lg border border-border bg-card px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none font-mono" />
        <div className="flex items-center justify-between">
          <button type="button" onClick={() => fileRef.current?.click()}
            className="flex items-center gap-1 text-[11px] text-muted-foreground/60 hover:text-foreground transition-colors">
            <Upload className="h-3 w-3" />Upload CSV / TXT
          </button>
          <input ref={fileRef} type="file" accept=".csv,.txt" className="hidden" onChange={handleFileUpload} />
          {emails.length > 0 && <span className="text-[11px] text-muted-foreground/50">{emails.length} email{emails.length !== 1 ? "s" : ""}</span>}
        </div>
      </div>
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />{error}
        </div>
      )}
      <Button size="sm" disabled={loading || emails.length === 0} onClick={send} className="w-full h-8 text-xs gap-1.5">
        {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
        {loading ? "Sending…" : `Send ${emails.length > 0 ? emails.length : ""} invite${emails.length !== 1 ? "s" : ""} to campaign`}
      </Button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Create campaign form — auto-slug from name
// ─────────────────────────────────────────────────────────────────────────────

function CreateCampaignForm({ onCreated, onCancel }: { onCreated: (c: CampaignResponse) => void; onCancel: () => void }) {
  const [form, setForm] = useState<CreateCampaignRequest>({
    code: "", name: "", description: "", campaign_type: "event", default_scope: "platform", default_expires_hours: 168,
  })
  const [codeManuallyEdited, setCodeManuallyEdited] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set<K extends keyof CreateCampaignRequest>(k: K, v: CreateCampaignRequest[K]) {
    setForm((f) => ({ ...f, [k]: v }))
  }

  function handleNameChange(name: string) {
    set("name", name)
    if (!codeManuallyEdited) {
      set("code", slugify(name))
    }
  }

  function handleCodeChange(raw: string) {
    const cleaned = raw.toLowerCase().replace(/[^a-z0-9_-]/g, "")
    set("code", cleaned)
    setCodeManuallyEdited(true)
  }

  async function submit() {
    if (!form.code || !form.name) { setError("Name and code are required."); return }
    setLoading(true); setError(null)
    try {
      const { createCampaign: apiCreateCampaign } = await import("@/lib/api/admin")
      const res = await apiCreateCampaign(form)
      onCreated(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create campaign")
    } finally { setLoading(false) }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <button type="button" onClick={onCancel} className="text-muted-foreground/50 hover:text-foreground transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" />
        </button>
        <span className="text-xs font-semibold text-foreground">New Campaign</span>
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Name <span className="text-red-500">*</span></Label>
        <Input value={form.name} onChange={(e) => handleNameChange(e.target.value)}
          placeholder="Q2 Partner Summit 2026" className="h-7 text-xs" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Code <span className="text-red-500">*</span></Label>
          <Input value={form.code} onChange={(e) => handleCodeChange(e.target.value)}
            placeholder="q2-partner-summit-2026" className="h-7 text-xs font-mono" />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Type</Label>
          <select value={form.campaign_type} onChange={(e) => set("campaign_type", e.target.value as CreateCampaignRequest["campaign_type"])}
            className="w-full rounded-lg border border-border bg-card px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-primary/30">
            <option value="event">Event</option>
            <option value="referral">Referral</option>
            <option value="form">Form</option>
            <option value="import">Import</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Description</Label>
        <textarea rows={2} value={form.description} onChange={(e) => set("description", e.target.value)}
          placeholder="Short description…"
          className="w-full rounded-lg border border-border bg-card px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Default scope</Label>
          <select value={form.default_scope} onChange={(e) => set("default_scope", e.target.value as CreateCampaignRequest["default_scope"])}
            className="w-full rounded-lg border border-border bg-card px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-primary/30">
            <option value="platform">Platform</option>
            <option value="organization">Organization</option>
            <option value="workspace">Workspace</option>
          </select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Invite expires (hours)</Label>
          <Input type="number" min={1} max={2160} value={form.default_expires_hours}
            onChange={(e) => set("default_expires_hours", parseInt(e.target.value) || 168)} className="h-7 text-xs" />
        </div>
      </div>
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />{error}
        </div>
      )}
      <div className="flex items-center gap-2">
        <Button size="sm" disabled={loading} onClick={submit} className="flex-1 h-8 text-xs gap-1">
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
          {loading ? "Creating…" : "Create Campaign"}
        </Button>
        <Button variant="outline" size="sm" onClick={onCancel} disabled={loading} className="h-8 text-xs">Cancel</Button>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Campaigns tab
// ─────────────────────────────────────────────────────────────────────────────

function CampaignsTab() {
  const [campaigns, setCampaigns] = useState<CampaignResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState<"list" | "create" | "invite">("list")
  const [activeCampaign, setActiveCampaign] = useState<CampaignResponse | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try { const res = await listCampaigns(); setCampaigns(res.campaigns) }
    catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  if (view === "create") {
    return <CreateCampaignForm onCreated={(c) => { setCampaigns((prev) => [c, ...prev]); setView("list") }} onCancel={() => setView("list")} />
  }

  if (view === "invite" && activeCampaign) {
    return <CampaignInviteForm campaign={activeCampaign} onBack={() => setView("list")} onDone={() => { load(); setView("list") }} />
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground/60">{campaigns.length} campaign{campaigns.length !== 1 ? "s" : ""}</span>
        <Button size="sm" onClick={() => setView("create")} className="h-7 text-xs gap-1">
          <Plus className="h-3 w-3" />New Campaign
        </Button>
      </div>
      {loading && <div className="space-y-2">{[1,2].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-muted" />)}</div>}
      {!loading && campaigns.length === 0 && (
        <div className="rounded-xl border border-dashed border-border/40 px-4 py-8 text-center">
          <Tag className="h-8 w-8 text-muted-foreground/20 mx-auto mb-2" />
          <p className="text-xs text-muted-foreground/40">No campaigns yet.</p>
          <p className="text-[11px] text-muted-foreground/30 mt-0.5">Create a campaign to track where users came from.</p>
        </div>
      )}
      {!loading && campaigns.map((c) => (
        <CampaignCard key={c.id} campaign={c} onInvite={(campaign) => { setActiveCampaign(campaign); setView("invite") }} />
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Invite slide-over
// ─────────────────────────────────────────────────────────────────────────────

function InviteSlideOver({ open, onClose, stats }: { open: boolean; onClose: () => void; stats: InvitationStatsResponse | null }) {
  const [tab, setTab] = useState<"quick" | "campaigns">("quick")
  if (!open) return null

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed right-0 top-0 h-full w-full max-w-sm bg-card border-l border-border/60 shadow-2xl z-50 flex flex-col">
        <div className="flex items-center justify-between px-4 py-3.5 border-b border-border/40">
          <div className="flex items-center gap-2">
            <div className="rounded-xl bg-primary/10 p-1.5">
              <Mail className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">Invite Users</h3>
              {stats && <p className="text-[11px] text-muted-foreground/50">{stats.pending} pending · {stats.accepted} accepted</p>}
            </div>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-1.5 text-muted-foreground/50 hover:text-foreground hover:bg-muted transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex border-b border-border/40">
          {(["quick", "campaigns"] as const).map((t) => (
            <button key={t} type="button" onClick={() => setTab(t)}
              className={`flex-1 py-2.5 text-xs font-medium transition-colors border-b-2 ${
                tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground/60 hover:text-foreground"
              }`}>
              {t === "quick" ? "Quick Invite" : "Campaigns"}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {tab === "quick" ? <QuickInviteTab /> : <CampaignsTab />}
        </div>
      </div>
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Filter bar — wrapped in card style, with inline active-filter chips
// ─────────────────────────────────────────────────────────────────────────────

interface Filters {
  is_active?: boolean
  is_disabled?: boolean
  account_status?: string
  org_id?: string
  group_id?: string
  user_category?: string
}

const FILTER_CHIP_LABELS: Record<string, (v: unknown) => string> = {
  is_active: (v) => v === true ? "Active" : "Inactive",
  is_disabled: () => "Disabled",
  account_status: (v) => `Status: ${String(v).replace(/_/g, " ")}`,
  org_id: (v) => `Org: ${String(v).slice(0, 8)}…`,
  group_id: (v) => `Group: ${String(v).slice(0, 8)}…`,
  user_category: (v) => `Category: ${String(v).replace(/_/g, " ")}`,
}

function FilterBar({ filters, onChange }: { filters: Filters; onChange: (f: Filters) => void }) {
  const [open, setOpen] = useState(false)
  const activeEntries = Object.entries(filters).filter(([, v]) => v !== undefined)
  const activeCount = activeEntries.length

  function removeFilter(key: string) {
    const next = { ...filters }
    delete (next as Record<string, unknown>)[key]
    onChange(next)
  }

  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        {/* Filter toggle button */}
        <div className="relative">
          <button type="button" onClick={() => setOpen((v) => !v)}
            className={`flex items-center gap-1.5 h-7 px-3 rounded-lg border text-xs transition-colors ${
              activeCount > 0
                ? "bg-primary/10 border-primary/30 text-primary"
                : "border-border bg-muted/30 text-muted-foreground/60 hover:text-foreground"
            }`}>
            <Filter className="h-3 w-3" />
            Filters
            {activeCount > 0 && <span className="rounded-full bg-primary text-white text-[10px] font-bold px-1.5 leading-none py-0.5">{activeCount}</span>}
            <ChevronDown className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
          </button>

          {open && (
            <div className="absolute left-0 top-9 z-20 w-72 rounded-xl border border-border bg-card shadow-xl p-3 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground">Filters</span>
                <button type="button" onClick={() => { onChange({}); setOpen(false) }}
                  className="text-[11px] text-muted-foreground/50 hover:text-red-500 transition-colors">
                  Clear all
                </button>
              </div>

              <div className="space-y-1">
                <Label className="text-[11px]">Status</Label>
                <div className="flex gap-2 flex-wrap">
                  {[
                    { label: "Active", key: "is_active", value: true },
                    { label: "Inactive", key: "is_active", value: false },
                    { label: "Disabled", key: "is_disabled", value: true },
                  ].map((opt) => {
                    const isOn = filters[opt.key as keyof Filters] === opt.value
                    return (
                      <button key={opt.label} type="button"
                        onClick={() => onChange(isOn
                          ? { ...filters, [opt.key]: undefined }
                          : { ...filters, [opt.key]: opt.value }
                        )}
                        className={`rounded-full px-2.5 py-0.5 text-[11px] border transition-colors ${
                          isOn ? "bg-primary/10 border-primary/30 text-primary" : "border-border text-muted-foreground hover:border-primary/30 hover:text-foreground"
                        }`}>
                        {opt.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="space-y-1">
                <Label className="text-[11px]">Account status</Label>
                <select
                  value={filters.account_status || ""}
                  onChange={(e) => onChange({ ...filters, account_status: e.target.value || undefined })}
                  className="w-full rounded-lg border border-border bg-muted px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-primary/30">
                  <option value="">Any</option>
                  <option value="active">Active</option>
                  <option value="pending_verification">Pending verification</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>

              <div className="space-y-1">
                <Label className="text-[11px]">Filter by Org ID</Label>
                <Input
                  value={filters.org_id || ""}
                  onChange={(e) => onChange({ ...filters, org_id: e.target.value || undefined })}
                  placeholder="Paste org UUID…"
                  className="h-7 text-xs font-mono"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-[11px]">Filter by Group ID</Label>
                <Input
                  value={filters.group_id || ""}
                  onChange={(e) => onChange({ ...filters, group_id: e.target.value || undefined })}
                  placeholder="Paste group UUID…"
                  className="h-7 text-xs font-mono"
                />
              </div>

              <Button size="sm" onClick={() => setOpen(false)} className="w-full h-7 text-xs">Apply</Button>
            </div>
          )}
        </div>

        {/* Active filter chips */}
        {activeEntries.map(([key, val]) => (
          <span key={key}
            className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium border bg-primary/10 border-primary/20 text-primary">
            {FILTER_CHIP_LABELS[key]?.(val) ?? key}
            <button type="button" onClick={() => removeFilter(key)}
              className="ml-0.5 hover:text-red-500 transition-colors">
              <X className="h-2.5 w-2.5" />
            </button>
          </span>
        ))}

        {activeCount > 0 && (
          <button type="button" onClick={() => onChange({})}
            className="text-[11px] text-muted-foreground/50 hover:text-red-500 transition-colors ml-auto">
            Clear all
          </button>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// KPI stat card
// ─────────────────────────────────────────────────────────────────────────────

function StatCard({
  icon, label, value, borderCls, numCls, bgCls,
}: {
  icon: React.ReactNode
  label: string
  value: number | null
  borderCls: string
  numCls: string
  bgCls: string
}) {
  return (
    <div className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3`}>
      <div className={`shrink-0 rounded-lg p-2 bg-muted ${bgCls}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>
          {value === null ? <span className="h-5 w-10 rounded bg-muted animate-pulse inline-block" /> : value.toLocaleString()}
        </div>
        <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{label}</span>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserSummaryResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [filters, setFilters] = useState<Filters>({})
  const [categoryTab, setCategoryTab] = useState<"all" | "full" | "external_collaborator">("all")
  const [fullCount, setFullCount] = useState<number | null>(null)
  const [externalCount, setExternalCount] = useState<number | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [history, setHistory] = useState<ImpersonationSessionResponse[]>([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [showHistory, setShowHistory] = useState(false)
  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteStats, setInviteStats] = useState<InvitationStatsResponse | null>(null)

  useEffect(() => {
    const t = setTimeout(() => { setDebouncedSearch(search); setPage(0) }, 350)
    return () => clearTimeout(t)
  }, [search])

  const fetchUsers = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const catFilter = categoryTab === "all" ? undefined : categoryTab
      const res = await listAdminUsers({
        limit: PAGE_SIZE, offset: page * PAGE_SIZE,
        search: debouncedSearch || undefined,
        ...filters,
        user_category: catFilter,
      })
      setUsers(res.users); setTotal(res.total)
    } catch (e) { setError(e instanceof Error ? e.message : "Failed") }
    finally { setLoading(false) }
  }, [page, debouncedSearch, filters, categoryTab])

  const fetchCounts = useCallback(async () => {
    try {
      const [full, ext] = await Promise.all([
        listAdminUsers({ limit: 1, user_category: "full" }),
        listAdminUsers({ limit: 1, user_category: "external_collaborator" }),
      ])
      setFullCount(full.total)
      setExternalCount(ext.total)
    } catch { /* non-critical */ }
  }, [])

  useEffect(() => { fetchUsers() }, [fetchUsers])
  useEffect(() => { fetchCounts() }, [fetchCounts])

  useEffect(() => {
    listImpersonationHistory({ limit: 20 }).then((r) => setHistory(r.sessions)).catch(() => setHistory([])).finally(() => setHistoryLoading(false))
  }, [])

  useEffect(() => { getInvitationStats().then(setInviteStats).catch(() => null) }, [])

  const totalPages = Math.ceil(total / PAGE_SIZE)
  const from = page * PAGE_SIZE + 1
  const to = Math.min((page + 1) * PAGE_SIZE, total)
  const activeCount = users.filter((u) => u.is_active).length
  const disabledCount = users.filter((u) => u.is_disabled).length

  function handleFiltersChange(f: Filters) {
    setFilters(f); setPage(0)
  }

  return (
    <div className="max-w-5xl space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-primary/10 p-3.5 shrink-0">
            <Users className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-foreground tracking-tight">Users</h2>
            <p className="text-sm text-muted-foreground mt-0.5">All registered platform users. Click a row to expand details.</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 mt-1 flex-wrap">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => fetchUsers()}
            disabled={loading}
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </Button>
          <button type="button" onClick={() => setShowHistory((v) => !v)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground/60 hover:text-foreground transition-colors">
            <Clock className="h-3.5 w-3.5" />Impersonation log
          </button>
          <Link href="/admin/users/invitations">
            <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5">
              <Mail className="h-3.5 w-3.5" />
              Invitations
              {inviteStats && inviteStats.pending > 0 && (
                <span className="rounded-full bg-amber-500/20 text-amber-500 px-1.5 py-0.5 text-[10px] font-bold leading-none">
                  {inviteStats.pending}
                </span>
              )}
            </Button>
          </Link>
          <Link href="/admin/campaigns">
            <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5">
              <Tag className="h-3.5 w-3.5" />
              Campaigns
            </Button>
          </Link>
          <Button size="sm" onClick={() => setInviteOpen(true)} className="h-7 text-xs gap-1.5">
            <Mail className="h-3.5 w-3.5" />Invite Users
          </Button>
        </div>
      </div>

      {/* KPI stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          icon={<Users className="h-4 w-4 text-primary" />}
          label="Total Users"
          value={fullCount !== null && externalCount !== null ? fullCount + externalCount : null}
          borderCls="border-primary/40"
          numCls="text-foreground"
          bgCls=""
        />
        <StatCard
          icon={<Activity className="h-4 w-4 text-emerald-500" />}
          label="Active (page)"
          value={loading ? null : activeCount}
          borderCls="border-emerald-500/40"
          numCls="text-emerald-500"
          bgCls=""
        />
        <StatCard
          icon={<UserCheck className="h-4 w-4 text-blue-500" />}
          label="External"
          value={externalCount}
          borderCls="border-blue-500/40"
          numCls="text-blue-500"
          bgCls=""
        />
        <StatCard
          icon={<UserX className="h-4 w-4 text-red-500" />}
          label="Disabled (page)"
          value={loading ? null : disabledCount}
          borderCls="border-red-500/40"
          numCls="text-red-500"
          bgCls=""
        />
      </div>

      {/* Category tabs */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1 rounded-xl border border-border/40 bg-card/50 p-1">
          {([
            { key: "all", label: "All Users", count: (fullCount ?? 0) + (externalCount ?? 0) },
            { key: "full", label: "Full Users", count: fullCount },
            { key: "external_collaborator", label: "External", count: externalCount },
          ] as const).map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => { setCategoryTab(tab.key); setPage(0) }}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                categoryTab === tab.key
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground/60 hover:text-foreground"
              }`}
            >
              {tab.label}
              {tab.count !== null && (
                <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold leading-none ${
                  categoryTab === tab.key ? "bg-white/20 text-white" : "bg-muted text-muted-foreground"
                }`}>{tab.count}</span>
              )}
            </button>
          ))}
        </div>
        {categoryTab === "external_collaborator" && (
          <span className="text-xs text-muted-foreground/50 flex items-center gap-1">
            <UserCheck className="h-3.5 w-3.5 text-blue-500" />
            External collaborators — passwordless only, task-scoped access
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          <AlertCircle className="h-4 w-4 shrink-0" />{error}
        </div>
      )}

      {/* Filter bar + search */}
      <div className="flex items-start gap-2 flex-wrap">
        <div className="flex-1 min-w-0">
          <FilterBar filters={filters} onChange={handleFiltersChange} />
        </div>
        <div className="relative w-56 shrink-0">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40 pointer-events-none" />
          <Input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search email or username…" className="h-9 pl-8 text-xs" />
          {search && (
            <button type="button" onClick={() => setSearch("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Inline count */}
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground/60 -mt-2">
        <span className="font-semibold text-foreground text-sm">{total}</span> users
        {!loading && <span>· <span className="text-emerald-500 font-medium">{activeCount}</span> active on this page</span>}
      </div>

      {/* User list — plain div, no Card */}
      <div className="rounded-xl border border-border/40 bg-card/50 overflow-hidden">
        <div className="flex items-center gap-3 px-4 py-1.5 border-b border-border/30 bg-muted/20">
          <div className="w-1 shrink-0" />
          <div className="w-8 shrink-0" />
          <div className="flex-1 text-[10px] font-medium text-muted-foreground/40 uppercase tracking-wider">User</div>
          <div className="text-[10px] font-medium text-muted-foreground/40 uppercase tracking-wider">Status</div>
          <div className="text-[10px] font-medium text-muted-foreground/40 uppercase tracking-wider hidden sm:block">Account</div>
          <div className="w-5 shrink-0" />
        </div>

        {loading && (
          <div className="divide-y divide-border/20">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-2.5 border-l-[3px] border-l-border/20">
                <div className="h-8 w-8 rounded-full bg-muted animate-pulse shrink-0" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3 bg-muted rounded animate-pulse w-48" />
                  <div className="h-2.5 bg-muted rounded animate-pulse w-24" />
                </div>
                <div className="h-5 w-16 bg-muted rounded-full animate-pulse" />
              </div>
            ))}
          </div>
        )}

        {!loading && users.map((user) => (
          <UserRow key={user.user_id} user={user}
            expanded={expandedId === user.user_id}
            onToggle={() => setExpandedId((prev) => prev === user.user_id ? null : user.user_id)}
            onUserUpdated={fetchUsers}
          />
        ))}

        {!loading && users.length === 0 && (
          <div className="px-4 py-12 text-center text-sm text-muted-foreground/50">
            No users found{Object.values(filters).filter((v) => v !== undefined).length > 0 ? " matching the current filters" : ""}.
          </div>
        )}

        {total > PAGE_SIZE && (
          <div className="flex items-center justify-between border-t border-border/30 px-4 py-2.5 bg-muted/10">
            <p className="text-xs text-muted-foreground/50">{from}–{to} of {total}</p>
            <div className="flex items-center gap-1.5">
              <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)} className="h-7 text-xs gap-1">
                <ChevronLeft className="h-3 w-3" />Prev
              </Button>
              <span className="text-xs text-muted-foreground/50 tabular-nums">{page + 1}/{totalPages}</span>
              <Button variant="outline" size="sm" disabled={page + 1 >= totalPages} onClick={() => setPage((p) => p + 1)} className="h-7 text-xs gap-1">
                Next<ChevronRight className="h-3 w-3" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Impersonation history — plain div, no Card */}
      {showHistory && (
        <div className="rounded-xl border border-border/40 bg-card/50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/30 bg-muted/20">
            <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-amber-500" />Impersonation Log
            </span>
            <button type="button" onClick={() => setShowHistory(false)} className="text-muted-foreground/40 hover:text-foreground transition-colors">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
          {historyLoading && <div className="p-4 space-y-2">{[1,2,3].map(i => <div key={i} className="h-9 animate-pulse rounded-lg bg-muted" />)}</div>}
          {!historyLoading && history.length === 0 && <p className="text-xs text-muted-foreground/40 text-center py-6">No impersonation history.</p>}
          {!historyLoading && history.map((entry) => (
            <div key={entry.session_id} className="flex items-center gap-3 px-4 py-2.5 border-b border-border/20 last:border-b-0">
              <Zap className="h-3.5 w-3.5 text-amber-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-foreground/70 truncate max-w-[160px]">{entry.target_email || entry.target_user_id.slice(0, 8) + "…"}</span>
                  <span className="text-muted-foreground/40">by</span>
                  <span className="text-foreground/70 truncate max-w-[160px]">{entry.impersonator_email || entry.impersonator_user_id.slice(0, 8) + "…"}</span>
                </div>
                {entry.reason && <p className="text-[11px] text-muted-foreground/40 truncate mt-0.5">{entry.reason}</p>}
              </div>
              <span className="text-[11px] text-muted-foreground/40 shrink-0">{fmtDateTime(entry.created_at)}</span>
              <span className={`inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-medium border ${
                entry.revoked_at ? "bg-red-500/10 border-red-500/20 text-red-500" : "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
              }`}>{entry.revoked_at ? "Ended" : "Active"}</span>
            </div>
          ))}
        </div>
      )}

      {/* Invite slide-over */}
      <InviteSlideOver open={inviteOpen} onClose={() => setInviteOpen(false)} stats={inviteStats} />
    </div>
  )
}
