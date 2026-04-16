"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Label,
  Badge,
} from "@kcontrol/ui";
import {
  Layers,
  Plus,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Pencil,
  X,
  Trash2,
  Users,
  ChevronDown,
  ChevronRight,
  UserPlus,
  UserMinus,
  Search,
  Mail,
  Shield,
} from "lucide-react";
import { fetchAccessContext } from "@/lib/api/access";
import {
  listWorkspaces,
  createWorkspace,
  updateWorkspace,
  listWorkspaceMembers,
  addWorkspaceMember,
  removeWorkspaceMember,
  updateWorkspaceMemberRole,
  updateWorkspaceMemberGrcRole,
} from "@/lib/api/workspaces";
import { createInvitation, listInvitations, revokeInvitation } from "@/lib/api/invitations";
import type { InvitationResponse } from "@/lib/api/invitations";
import type { WorkspaceResponse, WorkspaceMemberResponse } from "@/lib/types/orgs";
import { listAdminUsers } from "@/lib/api/admin";
import { fetchUserProperties } from "@/lib/api/auth";

const WS_ROLES = ["owner", "admin", "contributor", "viewer", "readonly"] as const;

const GRC_ROLES: { code: string; label: string; group: "internal" | "auditor" | "vendor" }[] = [
  { code: "grc_practitioner",  label: "GRC Practitioner", group: "internal" },
  { code: "grc_engineer",      label: "Engineer",         group: "internal" },
  { code: "grc_ciso",          label: "CISO / Exec",      group: "internal" },
  { code: "grc_lead_auditor",  label: "Lead Auditor",     group: "auditor"  },
  { code: "grc_staff_auditor", label: "Staff Auditor",    group: "auditor"  },
  { code: "grc_vendor",        label: "Vendor",           group: "vendor"   },
];

// What each GRC role can do — shown in the invite UI so admin knows what access they're granting
const GRC_ROLE_MATRIX: Record<string, { can: string[]; cannot: string[] }> = {
  grc_practitioner:  { can: ["Activate frameworks", "Approve evidence", "Manage tasks", "View live test results", "Respond to findings", "Contribute evidence", "Manage workspace members"], cannot: ["Raise audit findings"] },
  grc_engineer:      { can: ["Complete assigned tasks", "Submit evidence", "View own controls"], cannot: ["View live test results", "Approve evidence", "Manage workspace"] },
  grc_ciso:          { can: ["View posture dashboard", "View risk register (read-only)", "Use Kue AI (summary)"], cannot: ["Manage tasks", "View live test results", "Edit controls"] },
  grc_lead_auditor:  { can: ["Assign evidence tasks", "Raise findings", "Review published evidence", "Mark tasks complete", "Invite staff auditors"], cannot: ["View live test results", "View unpublished evidence"] },
  grc_staff_auditor: { can: ["View published evidence", "View controls & requirements", "Internal annotations"], cannot: ["Raise findings directly", "View live test results", "View unpublished evidence"] },
  grc_vendor:        { can: ["Complete vendor questionnaire"], cannot: ["View controls", "View evidence", "Access compliance program"] },
};

const WS_TYPE_OPTIONS = [
  { code: "grc",     label: "GRC (Compliance)" },
  { code: "sandbox", label: "Sandbox" },
] as const;

function grcRoleLabel(code: string | null | undefined): string {
  return GRC_ROLES.find(r => r.code === code)?.label ?? "";
}

function grcRoleBadgeClass(code: string | null | undefined): string {
  const role = GRC_ROLES.find(r => r.code === code);
  if (!role) return "bg-muted text-muted-foreground border-border";
  if (role.group === "auditor") return "bg-amber-500/10 text-amber-700 border-amber-500/20";
  if (role.group === "vendor")  return "bg-stone-500/10 text-stone-600 border-stone-500/20";
  switch (role.code) {
    case "grc_practitioner": return "bg-purple-500/10 text-purple-700 border-purple-500/20";
    case "grc_engineer": return "bg-green-500/10 text-green-600 border-green-500/20";
    case "grc_ciso":     return "bg-indigo-500/10 text-indigo-700 border-indigo-500/20";
    default:             return "bg-muted text-muted-foreground border-border";
  }
}

function wsTypeBadgeClass(code: string): string {
  switch (code) {
    case "grc":     return "bg-purple-500/10 text-purple-700 border-purple-500/20";
    case "sandbox": return "bg-orange-500/10 text-orange-700 border-orange-500/20";
    default:        return "bg-blue-500/10 text-blue-600 border-blue-500/20";
  }
}

function wsTypeLabel(code: string): string {
  const labels: Record<string, string> = { grc: "GRC (Compliance)", sandbox: "Sandbox", project: "GRC (Compliance)" };
  return labels[code] ?? code;
}

function roleBadgeClass(role: string) {
  switch (role) {
    case "owner":       return "bg-purple-500/10 text-purple-600 border-purple-500/20";
    case "admin":       return "bg-blue-500/10 text-blue-600 border-blue-500/20";
    case "contributor": return "bg-green-500/10 text-green-600 border-green-500/20";
    case "viewer":      return "bg-gray-500/10 text-gray-600 border-gray-500/20";
    case "readonly":    return "bg-stone-500/10 text-stone-600 border-stone-500/20";
    default:            return "bg-muted text-muted-foreground border-border";
  }
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

function SkeletonCard() {
  return (
    <div className="rounded-lg border border-border px-4 py-3 animate-pulse space-y-2">
      <div className="h-4 w-40 rounded bg-muted" />
      <div className="h-3 w-64 rounded bg-muted" />
    </div>
  );
}

// ── User search for adding members ──────────────────────────────────────────

interface UserResult { user_id: string; email: string | null; username: string | null; display_name?: string | null }

function UserSearchInput({ onSelect, orgId, disabled, placeholder }: { onSelect: (u: UserResult) => void; orgId: string; disabled?: boolean; placeholder?: string }) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<UserResult[]>([])
  const [open, setOpen] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!query.trim()) { setResults([]); setOpen(false); return }
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      const res = await listAdminUsers({ search: query, limit: 8, org_id: orgId }).catch(() => null)
      setResults(res?.users ?? [])
      setOpen(true)
    }, 250)
  }, [query, orgId])

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false) }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  return (
    <div ref={ref} className="relative">
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-muted-foreground" />
        <Input className="pl-8 h-8 text-sm" placeholder={placeholder ?? "Search users to add..."} value={query} onChange={e => setQuery(e.target.value)} disabled={disabled} />
      </div>
      {open && results.length > 0 && (
        <div className="absolute z-50 top-full mt-1 w-full rounded-lg border border-border bg-popover shadow-lg overflow-hidden">
          {results.map(u => (
            <button key={u.user_id} className="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors flex items-center gap-2"
              onClick={() => { onSelect(u); setQuery(""); setOpen(false) }}>
              <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium text-primary shrink-0">
                {(u.email ?? u.username ?? "?")[0].toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="font-medium truncate text-xs">{u.display_name ?? u.email ?? u.username}</div>
                {u.email && <div className="text-xs text-muted-foreground truncate">{u.email}</div>}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Workspace members panel ─────────────────────────────────────────────────

function GrcRolePermissionHint({ grcRoleCode }: { grcRoleCode: string }) {
  const matrix = GRC_ROLE_MATRIX[grcRoleCode]
  if (!matrix) return null
  return (
    <div className="mt-2 rounded-lg border border-border bg-muted/20 p-2.5 space-y-1.5 text-xs">
      <div className="space-y-0.5">
        {matrix.can.map(item => (
          <div key={item} className="flex items-start gap-1.5 text-green-700">
            <span className="shrink-0 mt-0.5">✓</span>
            <span>{item}</span>
          </div>
        ))}
        {matrix.cannot.map(item => (
          <div key={item} className="flex items-start gap-1.5 text-muted-foreground">
            <span className="shrink-0 mt-0.5">✗</span>
            <span>{item}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function WorkspaceMembersPanel({
  orgId,
  wsId,
  wsTypeCode,
  currentUserId,
}: {
  orgId: string;
  wsId: string;
  wsTypeCode: string;
  currentUserId: string | null;
}) {
  const isGrc = wsTypeCode === "grc"
  const [members, setMembers] = useState<WorkspaceMemberResponse[]>([])
  const [pendingInvites, setPendingInvites] = useState<InvitationResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [addRole, setAddRole] = useState<string>("contributor")
  const [addGrcRole, setAddGrcRole] = useState<string>("grc_practitioner")
  const [adding, setAdding] = useState(false)
  const [removingId, setRemovingId] = useState<string | null>(null)
  const [changingRoleId, setChangingRoleId] = useState<string | null>(null)
  const [confirmRemoveId, setConfirmRemoveId] = useState<string | null>(null)
  const [revokingId, setRevokingId] = useState<string | null>(null)

  // External invite state
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteGrcRole, setInviteGrcRole] = useState("grc_practitioner")
  const [inviting, setInviting] = useState(false)
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null)
  const [inviteError, setInviteError] = useState<string | null>(null)
  const [showMatrix, setShowMatrix] = useState(false)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [mems, invites] = await Promise.all([
        listWorkspaceMembers(orgId, wsId),
        listInvitations({ scope: "workspace", workspace_id: wsId, status: "pending" }).catch(() => []),
      ])
      setMembers(mems)
      setPendingInvites(invites)
    }
    catch (e) { setError((e as Error).message) }
    finally { setLoading(false) }
  }, [orgId, wsId])

  useEffect(() => { load() }, [load])

  async function handleAdd(user: UserResult) {
    setAdding(true); setError(null)
    try {
      await addWorkspaceMember(orgId, wsId, user.user_id, addRole)
      if (isGrc && addGrcRole) {
        await updateWorkspaceMemberGrcRole(orgId, wsId, user.user_id, addGrcRole)
      }
      await load()
    }
    catch (e) { setError((e as Error).message) }
    finally { setAdding(false) }
  }

  async function handleRoleChange(userId: string, role: string) {
    setChangingRoleId(userId); setError(null)
    try {
      await updateWorkspaceMemberRole(orgId, wsId, userId, role)
      setMembers(prev => prev.map(m => m.user_id === userId ? { ...m, role } : m))
    }
    catch (e) { setError((e as Error).message) }
    finally { setChangingRoleId(null) }
  }

  async function handleGrcRoleChange(userId: string, grcRoleCode: string | null) {
    setChangingRoleId(userId + ":grc"); setError(null)
    try {
      const updated = await updateWorkspaceMemberGrcRole(orgId, wsId, userId, grcRoleCode)
      setMembers(prev => prev.map(m => m.user_id === userId ? { ...m, grc_role_code: updated.grc_role_code } : m))
    }
    catch (e) { setError((e as Error).message) }
    finally { setChangingRoleId(null) }
  }

  async function handleRemove(userId: string) {
    setRemovingId(userId); setError(null)
    try { await removeWorkspaceMember(orgId, wsId, userId); setConfirmRemoveId(null); await load() }
    catch (e) { setError((e as Error).message) }
    finally { setRemovingId(null) }
  }

  async function handleRevokeInvite(inviteId: string) {
    setRevokingId(inviteId)
    try { await revokeInvitation(inviteId); await load() }
    catch (e) { setError((e as Error).message) }
    finally { setRevokingId(null) }
  }

  async function handleInviteExternal(e: React.FormEvent) {
    e.preventDefault()
    if (!inviteEmail.trim()) return
    setInviting(true); setInviteError(null); setInviteSuccess(null)
    try {
      await createInvitation({
        email: inviteEmail.trim(),
        scope: "workspace",
        org_id: orgId,
        workspace_id: wsId,
        role: "contributor",
        grc_role_code: isGrc ? inviteGrcRole : undefined,
      })
      setInviteSuccess(`Invitation sent to ${inviteEmail.trim()} as ${grcRoleLabel(inviteGrcRole)}. They'll be automatically added to the correct group when they accept.`)
      setInviteEmail("")
      await load()
    }
    catch (e) { setInviteError((e as Error).message) }
    finally { setInviting(false) }
  }

  if (loading) return <div className="space-y-2 pt-2">{[...Array(2)].map((_, i) => <div key={i} className="h-8 bg-muted animate-pulse rounded-lg" />)}</div>

  return (
    <div className="pt-3 border-t border-border mt-3 space-y-3">
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
          <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
          <p className="text-xs text-red-500">{error}</p>
        </div>
      )}

      {/* Add existing platform user */}
      <div className="space-y-2">
        <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Add existing user</p>
        <div className="flex items-center gap-2">
          <div className="flex-1">
            <UserSearchInput onSelect={handleAdd} orgId={orgId} disabled={adding} />
          </div>
          <select
            className="h-8 rounded border border-border bg-background text-xs px-2 focus:outline-none focus:ring-1 focus:ring-ring shrink-0"
            value={addRole}
            onChange={e => setAddRole(e.target.value)}
            title="Workspace role"
          >
            {WS_ROLES.map(r => <option key={r} value={r} className="capitalize">{r}</option>)}
          </select>
          {isGrc && (
            <select
              className={`h-8 rounded border px-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-ring shrink-0 ${grcRoleBadgeClass(addGrcRole)}`}
              value={addGrcRole}
              onChange={e => setAddGrcRole(e.target.value)}
              title="GRC role"
            >
              {GRC_ROLES.map(r => <option key={r.code} value={r.code} className="bg-background text-foreground">{r.label}</option>)}
            </select>
          )}
        </div>
        {adding && <p className="text-xs text-muted-foreground flex items-center gap-1"><RefreshCw className="h-3 w-3 animate-spin" />Adding member…</p>}
      </div>

      {/* Invite external user */}
      <div className="space-y-2">
        <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Invite by email</p>
        <form onSubmit={handleInviteExternal} className="rounded-lg border border-border bg-muted/20 p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Input
              type="email"
              className="h-8 text-xs flex-1"
              placeholder="user@domain.com"
              value={inviteEmail}
              onChange={e => setInviteEmail(e.target.value)}
              required
            />
            {isGrc && (
              <select
                className={`h-8 rounded border px-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-ring shrink-0 ${grcRoleBadgeClass(inviteGrcRole)}`}
                value={inviteGrcRole}
                onChange={e => setInviteGrcRole(e.target.value)}
                title="GRC role"
              >
                {GRC_ROLES.map(r => <option key={r.code} value={r.code} className="bg-background text-foreground">{r.label}</option>)}
              </select>
            )}
            <Button type="submit" size="sm" className="h-8 px-3 shrink-0" disabled={inviting || !inviteEmail.trim()}>
              {inviting ? <RefreshCw className="h-3 w-3 animate-spin" /> : <UserPlus className="h-3 w-3" />}
              <span className="ml-1.5 hidden sm:inline">Send Invite</span>
            </Button>
          </div>
          {isGrc && (
            <div className="space-y-1">
              <button
                type="button"
                className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                onClick={() => setShowMatrix(v => !v)}
              >
                <Shield className="h-3 w-3" />
                {showMatrix ? "Hide" : "Show"} what {grcRoleLabel(inviteGrcRole)} can access
                {showMatrix ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              </button>
              {showMatrix && <GrcRolePermissionHint grcRoleCode={inviteGrcRole} />}
            </div>
          )}
          {inviteSuccess && (
            <div className="flex items-start gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0 mt-0.5" />
              <p className="text-xs text-green-700">{inviteSuccess}</p>
            </div>
          )}
          {inviteError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
              <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
              <p className="text-xs text-red-500">{inviteError}</p>
            </div>
          )}
        </form>
      </div>

      {/* Pending invitations */}
      {pendingInvites.length > 0 && (
        <div className="space-y-1">
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Pending invitations ({pendingInvites.length})</p>
          {pendingInvites.map(inv => (
            <div key={inv.id} className="flex items-center justify-between rounded-lg px-3 py-1.5 bg-amber-500/5 border border-amber-500/20 group/row">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <Mail className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                <span className="text-xs truncate text-amber-800 dark:text-amber-300">{inv.email}</span>
              </div>
              <div className="flex items-center gap-1.5 shrink-0 ml-2">
                {inv.grc_role_code ? (
                  <Badge variant="outline" className={`text-[10px] ${grcRoleBadgeClass(inv.grc_role_code)}`}>
                    {grcRoleLabel(inv.grc_role_code)}
                  </Badge>
                ) : null}
                <span className="text-[10px] text-muted-foreground">Pending</span>
                <button
                  className="opacity-0 group-hover/row:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                  onClick={() => handleRevokeInvite(inv.id)}
                  disabled={revokingId === inv.id}
                  title="Revoke invitation"
                >
                  {revokingId === inv.id ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <X className="h-3.5 w-3.5" />}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Current members */}
      {members.length === 0 ? (
        <p className="text-xs text-muted-foreground py-1">No members yet.</p>
      ) : (
        <div className="space-y-1">
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Members ({members.length})</p>
          {isGrc && (
            <div className="flex items-center gap-2 px-3 pb-1">
              <span className="text-[10px] text-muted-foreground flex-1">Name</span>
              <span className="text-[10px] text-muted-foreground w-20 text-right">WS Role</span>
              <span className="text-[10px] text-muted-foreground w-28 text-right flex items-center gap-1 justify-end">
                <Shield className="h-3 w-3" /> GRC Role
              </span>
              <div className="w-4" />
            </div>
          )}
          {members.map(m => {
            const isMe = m.user_id === currentUserId
            const label = m.display_name ?? m.email ?? m.user_id
            return (
              <div key={m.id} className="flex items-center justify-between rounded-lg px-3 py-1.5 bg-muted/40 hover:bg-muted/60 group/row transition-colors">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <div className="w-5 h-5 rounded-full bg-primary/15 flex items-center justify-center text-[10px] font-medium text-primary shrink-0">{label[0].toUpperCase()}</div>
                  <span className="text-xs truncate">{label}{isMe && <span className="ml-1 text-muted-foreground">(you)</span>}</span>
                </div>
                <div className="flex items-center gap-1.5 shrink-0 ml-2">
                  {/* Workspace role */}
                  {isMe ? (
                    <Badge variant="outline" className={`text-[10px] capitalize ${roleBadgeClass(m.role)}`}>{m.role}</Badge>
                  ) : (
                    <select
                      className={`h-6 rounded border px-1.5 text-[10px] font-medium cursor-pointer focus:outline-none focus:ring-1 focus:ring-ring ${roleBadgeClass(m.role)}`}
                      value={m.role}
                      disabled={changingRoleId === m.user_id}
                      onChange={e => handleRoleChange(m.user_id, e.target.value)}
                      title="Workspace role"
                    >
                      {WS_ROLES.map(r => <option key={r} value={r} className="bg-background text-foreground capitalize">{r}</option>)}
                    </select>
                  )}

                  {/* GRC role (GRC workspaces only) */}
                  {isGrc && (
                    isMe ? (
                      m.grc_role_code ? (
                        <Badge variant="outline" className={`text-[10px] ${grcRoleBadgeClass(m.grc_role_code)}`}>
                          {grcRoleLabel(m.grc_role_code)}
                        </Badge>
                      ) : (
                        <span className="text-[10px] text-muted-foreground italic">No GRC role</span>
                      )
                    ) : (
                      <select
                        className={`h-6 rounded border px-1.5 text-[10px] font-medium cursor-pointer focus:outline-none focus:ring-1 focus:ring-ring ${m.grc_role_code ? grcRoleBadgeClass(m.grc_role_code) : "border-border bg-background text-muted-foreground"}`}
                        value={m.grc_role_code ?? ""}
                        disabled={changingRoleId === m.user_id + ":grc"}
                        onChange={e => handleGrcRoleChange(m.user_id, e.target.value || null)}
                        title="GRC role"
                      >
                        <option value="" className="bg-background text-foreground">— no GRC role —</option>
                        {GRC_ROLES.map(r => <option key={r.code} value={r.code} className="bg-background text-foreground">{r.label}</option>)}
                      </select>
                    )
                  )}

                  {!isMe && (
                    confirmRemoveId === m.user_id ? (
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] text-red-600">Remove?</span>
                        <button className="text-destructive text-[10px] font-medium hover:underline" onClick={() => handleRemove(m.user_id)} disabled={removingId === m.user_id}>{removingId === m.user_id ? "…" : "Yes"}</button>
                        <button className="text-muted-foreground text-[10px] hover:underline" onClick={() => setConfirmRemoveId(null)}>No</button>
                      </div>
                    ) : (
                      <button className="opacity-0 group-hover/row:opacity-100 text-muted-foreground hover:text-destructive transition-opacity" onClick={() => setConfirmRemoveId(m.user_id)} title="Remove member">
                        <UserMinus className="h-3.5 w-3.5" />
                      </button>
                    )
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function OrgWorkspacesPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([]);
  const [memberCounts, setMemberCounts] = useState<Record<string, number>>({});
  const [expandedMembers, setExpandedMembers] = useState<Record<string, boolean>>({});
  const [expandedDesc, setExpandedDesc] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createSlug, setCreateSlug] = useState("");
  const [createType, setCreateType] = useState<string>("project");
  const [slugManual, setSlugManual] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Delete state
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const loadWorkspaces = useCallback(async (id: string) => {
    setError(null);
    try {
      const data = await listWorkspaces(id);
      setWorkspaces(data);
      const counts: Record<string, number> = {};
      await Promise.allSettled(
        data.map(async (ws) => {
          try {
            const members = await listWorkspaceMembers(id, ws.id);
            counts[ws.id] = members.length;
          } catch {
            counts[ws.id] = 0;
          }
        })
      );
      setMemberCounts(counts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workspaces");
    }
  }, []);

  useEffect(() => {
    async function init() {
      try {
        let defaultOrgId: string | undefined
        try {
          const props = await fetchUserProperties()
          defaultOrgId = props["default_org_id"] || undefined
        } catch {}
        const access = await fetchAccessContext(defaultOrgId)
        const id = access.current_org?.org_id;
        if (!id) { setError("No organization found. Complete onboarding first."); return; }
        setOrgId(id);
        setCurrentUserId(access.user_id ?? null);
        await loadWorkspaces(id);
      } catch {
        setError("Failed to load organization.");
      } finally {
        setIsLoading(false);
      }
    }
    init();
  }, [loadWorkspaces]);

  function handleNameChange(value: string) {
    setCreateName(value);
    if (!slugManual) setCreateSlug(slugify(value));
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId || !createName.trim()) return;
    setCreating(true);
    setCreateError(null);
    try {
      await createWorkspace(orgId, {
        name: createName.trim(),
        slug: createSlug.trim() || slugify(createName.trim()),
        workspace_type_code: createType,
      });
      setCreateName("");
      setCreateSlug("");
      setCreateType("project");
      setSlugManual(false);
      setShowCreate(false);
      await loadWorkspaces(orgId);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create workspace");
    } finally {
      setCreating(false);
    }
  }

  function startEdit(ws: WorkspaceResponse) {
    setEditingId(ws.id);
    setEditName(ws.name);
    setEditDescription(ws.description ?? "");
    setSaveError(null);
    setSaveSuccess(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setSaveError(null);
  }

  async function handleSaveEdit(e: React.FormEvent, wsId: string) {
    e.preventDefault();
    if (!orgId) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(null);
    try {
      const updated = await updateWorkspace(orgId, wsId, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
      });
      setWorkspaces((prev) => prev.map((w) => (w.id === wsId ? updated : w)));
      setSaveSuccess(wsId);
      setEditingId(null);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to update workspace");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(wsId: string) {
    if (!orgId) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await updateWorkspace(orgId, wsId, { is_disabled: true });
      setConfirmDeleteId(null);
      await loadWorkspaces(orgId);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to disable workspace");
    } finally {
      setDeleting(false);
    }
  }

  function toggleMembers(wsId: string) {
    setExpandedMembers(prev => ({ ...prev, [wsId]: !prev[wsId] }));
  }

  function toggleDesc(wsId: string) {
    setExpandedDesc(prev => ({ ...prev, [wsId]: !prev[wsId] }));
  }

  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">Workspaces</h2>
          <p className="text-sm text-muted-foreground">
            Manage the workspaces within your organization.
          </p>
        </div>
        <div className="flex items-center gap-2 self-end sm:self-auto">
          <Button
            size="sm"
            onClick={() => {
              setShowCreate((v) => !v);
              setCreateError(null);
            }}
            className="gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-3.5 w-3.5" />
            New Workspace
          </Button>
        </div>
      </div>

      {/* Create workspace form */}
      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Create Workspace</CardTitle>
            <CardDescription>
              Add a new workspace to your organization.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="create-name">Name</Label>
                  <Input
                    id="create-name"
                    value={createName}
                    onChange={(e) => handleNameChange(e.target.value)}
                    placeholder="e.g. Production"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="create-slug">Slug</Label>
                  <Input
                    id="create-slug"
                    value={createSlug}
                    onChange={(e) => {
                      setCreateSlug(e.target.value);
                      setSlugManual(true);
                    }}
                    placeholder="e.g. production"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="create-type">Workspace Type</Label>
                <div className="flex gap-2 flex-wrap">
                  {WS_TYPE_OPTIONS.map(t => (
                    <button
                      key={t.code}
                      type="button"
                      onClick={() => setCreateType(t.code)}
                      className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
                        createType === t.code
                          ? `${wsTypeBadgeClass(t.code)} ring-1 ring-current`
                          : "border-border bg-background text-muted-foreground hover:bg-muted"
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
                {createType === "grc" && (
                  <p className="text-xs text-muted-foreground">GRC workspaces include 7 pre-provisioned compliance roles (GRC Lead, SME, Engineer, CISO, Lead Auditor, Staff Auditor, Vendor).</p>
                )}
              </div>

              {createError && (
                <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
                  <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
                  <p className="text-sm text-red-500">{createError}</p>
                </div>
              )}

              <div className="flex items-center gap-2">
                <Button type="submit" size="sm" disabled={creating || !createName.trim()}>
                  {creating ? "Creating…" : "Create Workspace"}
                </Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setShowCreate(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Workspace list */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Layers className="h-5 w-5 text-muted-foreground shrink-0" />
            <div>
              <CardTitle>Workspaces</CardTitle>
              <CardDescription>
                {isLoading
                  ? "Loading…"
                  : `${workspaces.length} workspace${workspaces.length !== 1 ? "s" : ""}`}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {deleteError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 mb-3">
              <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-500">{deleteError}</p>
            </div>
          )}

          {isLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => <SkeletonCard key={i} />)}
            </div>
          ) : error ? (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
              <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          ) : workspaces.length === 0 ? (
            <p className="text-sm text-muted-foreground">No workspaces found. Create one above.</p>
          ) : (
            <div className="space-y-2">
              {workspaces.map((ws) => (
                <div key={ws.id} className="rounded-lg border border-border px-4 py-3">
                  {saveSuccess === ws.id && (
                    <div className="flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 mb-3">
                      <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                      <p className="text-sm text-green-600 dark:text-green-400">Workspace updated.</p>
                    </div>
                  )}

                  {editingId === ws.id ? (
                    <form onSubmit={(e) => handleSaveEdit(e, ws.id)} className="space-y-3">
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        <div className="space-y-1">
                          <Label htmlFor={`edit-name-${ws.id}`}>Name</Label>
                          <Input id={`edit-name-${ws.id}`} value={editName} onChange={(e) => setEditName(e.target.value)} required />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor={`edit-desc-${ws.id}`}>Description</Label>
                          <Input id={`edit-desc-${ws.id}`} value={editDescription} onChange={(e) => setEditDescription(e.target.value)} placeholder="Optional" />
                        </div>
                      </div>
                      {saveError && editingId === ws.id && (
                        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
                          <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
                          <p className="text-sm text-red-500">{saveError}</p>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <Button type="submit" size="sm" disabled={saving || !editName.trim()}>
                          {saving ? "Saving…" : "Save"}
                        </Button>
                        <Button type="button" variant="outline" size="sm" onClick={cancelEdit} disabled={saving}>
                          <X className="h-3.5 w-3.5 mr-1" />
                          Cancel
                        </Button>
                      </div>
                    </form>
                  ) : (
                    <>
                      {/* Row 1: [chevron mobile] + Workspace name */}
                      <div className="flex items-center gap-1.5 min-w-0">
                        <button
                          className="sm:hidden p-0.5 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors shrink-0"
                          onClick={() => toggleDesc(ws.id)}
                          title="Show details"
                        >
                          {expandedDesc[ws.id]
                            ? <ChevronDown className="h-3.5 w-3.5 transition-transform duration-150" />
                            : <ChevronRight className="h-3.5 w-3.5 transition-transform duration-150" />}
                        </button>
                        <button
                          className="sm:pointer-events-none text-sm font-medium text-foreground truncate text-left"
                          onClick={() => toggleDesc(ws.id)}
                        >
                          {ws.name}
                        </button>
                      </div>

                      {/* Row 2: Badges + action icons */}
                      <div className="flex items-center justify-between gap-2 mt-1.5">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <Badge
                            variant="outline"
                            className={`text-xs ${ws.is_active ? "text-green-600 border-green-500/40 bg-green-500/10" : "text-red-500 border-red-500/40 bg-red-500/10"}`}
                          >
                            {ws.is_active ? "Active" : "Inactive"}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={`text-xs ${wsTypeBadgeClass(ws.workspace_type_code)}`}
                          >
                            {wsTypeLabel(ws.workspace_type_code)}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded hover:bg-muted"
                            onClick={() => toggleMembers(ws.id)}
                            title="Manage members"
                          >
                            <Users className="h-3.5 w-3.5" />
                            {memberCounts[ws.id] !== undefined ? memberCounts[ws.id] : "…"}
                            {expandedMembers[ws.id] ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                          </button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => startEdit(ws)}
                            className="gap-1 h-7 px-2 text-muted-foreground hover:text-foreground"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                            <span className="hidden sm:inline">Edit</span>
                          </Button>
                          {ws.is_active ? (
                            confirmDeleteId === ws.id ? (
                              <div className="flex items-center gap-1">
                                <span className="text-xs text-red-600 hidden sm:inline">Disable?</span>
                                <Button variant="destructive" size="sm" className="h-6 px-2 text-xs" onClick={() => handleDelete(ws.id)} disabled={deleting}>
                                  {deleting ? "…" : "Yes"}
                                </Button>
                                <Button variant="outline" size="sm" className="h-6 px-2 text-xs" onClick={() => setConfirmDeleteId(null)}>No</Button>
                              </div>
                            ) : (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                                onClick={() => setConfirmDeleteId(ws.id)}
                                title="Disable workspace"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            )
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 px-2 text-xs text-green-600 hover:text-green-700 hover:bg-green-500/10 gap-1"
                              onClick={async () => {
                                if (!orgId) return;
                                try {
                                  await updateWorkspace(orgId, ws.id, { is_disabled: false });
                                  await loadWorkspaces(orgId);
                                } catch (err) {
                                  setDeleteError(err instanceof Error ? err.message : "Failed to enable workspace");
                                }
                              }}
                              title="Re-enable workspace"
                            >
                              Enable
                            </Button>
                          )}
                        </div>
                      </div>

                      {/* Row 3: Description */}
                      <p className="hidden sm:block text-xs text-muted-foreground mt-1 break-words">
                        /{ws.slug}{ws.description && ` · ${ws.description}`}
                      </p>
                      {expandedDesc[ws.id] && (
                        <p className="sm:hidden text-xs text-muted-foreground mt-1.5 break-words leading-relaxed border-t border-border/40 pt-2">
                          /{ws.slug}{ws.description && ` · ${ws.description}`}
                        </p>
                      )}

                      {expandedMembers[ws.id] && orgId && (
                        <WorkspaceMembersPanel
                          orgId={orgId}
                          wsId={ws.id}
                          wsTypeCode={ws.workspace_type_code}
                          currentUserId={currentUserId}
                        />
                      )}
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
