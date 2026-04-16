"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Card, CardContent, Button, Input, Badge } from "@kcontrol/ui";
import {
  ChevronDown,
  ChevronRight,
  Plus,
  X,
  Users,
  Lock,
  ShieldCheck,
  ShieldPlus,
  UserPlus,
  UserMinus,
  Shield,
  Layers,
  Building2,
  Globe,
  Search,
  Pencil,
  Check,
  GitBranch,
  AlertTriangle,
  RefreshCw,
  Trash2,
  Power,
  Ban,
  History,
} from "lucide-react";
import {
  listGroups,
  getGroup,
  createGroup,
  updateGroup,
  deleteGroup,
  addGroupMember,
  removeGroupMember,
  listGroupMembers,
  listGroupChildren,
  assignRoleToGroup,
  revokeRoleFromGroup,
  setGroupParent,
  listRoles,
  listAdminUsers,
  listAuditEvents,
} from "@/lib/api/admin";
import { listOrgs } from "@/lib/api/orgs";
import { listWorkspaces } from "@/lib/api/workspaces";
import type {
  GroupResponse,
  GroupMemberResponse,
  GroupRoleResponse,
  RoleResponse,
  AuditEventResponse,
} from "@/lib/types/admin";

// ── Constants ─────────────────────────────────────────────────────────────────

const LEVEL_META: Record<string, { label: string; icon: React.FC<{ className?: string }>; color: string }> = {
  super_admin: { label: "Super Admin", icon: ShieldCheck, color: "text-red-500 bg-red-500/10 border-red-500/20" },
  platform:    { label: "Platform",    icon: Globe,       color: "text-violet-500 bg-violet-500/10 border-violet-500/20" },
  org:         { label: "Org",         icon: Building2,   color: "text-blue-500 bg-blue-500/10 border-blue-500/20" },
  workspace:   { label: "Workspace",   icon: Layers,      color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20" },
};

function LevelBadge({ code }: { code: string }) {
  const m = LEVEL_META[code] ?? { label: code, icon: Shield, color: "text-muted-foreground bg-muted border-border" };
  const Icon = m.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${m.color}`}>
      <Icon className="w-3 h-3" />
      {m.label}
    </span>
  );
}

type ScopeNames = Record<string, string>; // id → display name

function ScopeBadge({ group, orgNames, wsNames }: { group: GroupResponse; orgNames: ScopeNames; wsNames: ScopeNames }) {
  if (!group.scope_org_id && !group.scope_workspace_id) return null;
  if (group.scope_workspace_id) {
    const wsName = wsNames[group.scope_workspace_id] ?? group.scope_workspace_id.slice(0, 8) + "…";
    const orgName = group.scope_org_id ? (orgNames[group.scope_org_id] ?? "") : "";
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-emerald-600 bg-emerald-500/10 border-emerald-500/20" title={`Workspace: ${wsName}${orgName ? ` (${orgName})` : ""}`}>
        <Layers className="w-3 h-3" />
        {wsName}
      </span>
    );
  }
  if (group.scope_org_id) {
    const orgName = orgNames[group.scope_org_id] ?? group.scope_org_id.slice(0, 8) + "…";
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-blue-600 bg-blue-500/10 border-blue-500/20" title={`Org: ${orgName}`}>
        <Building2 className="w-3 h-3" />
        {orgName}
      </span>
    );
  }
  return null;
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-4 animate-pulse space-y-2">
      <div className="flex items-center gap-3">
        <div className="h-4 w-48 bg-muted rounded" />
        <div className="h-4 w-20 bg-muted rounded" />
      </div>
      <div className="h-3 w-64 bg-muted rounded" />
    </div>
  );
}

// ── User Search Input ─────────────────────────────────────────────────────────

interface UserResult { user_id: string; email: string | null; username: string | null; display_name: string | null }

function UserSearchInput({ onSelect, disabled }: { onSelect: (u: UserResult) => void; disabled?: boolean }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UserResult[]>([]);
  const [open, setOpen] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query.trim()) { setResults([]); setOpen(false); return; }
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      const res = await listAdminUsers({ search: query, limit: 8 }).catch(() => null);
      setResults((res?.users ?? []).map(u => ({ ...u, display_name: u.display_name ?? null })));
      setOpen(true);
    }, 250);
  }, [query]);

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-muted-foreground" />
        <Input
          className="pl-8 h-8 text-sm"
          placeholder="Search users to add..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          disabled={disabled}
        />
      </div>
      {open && results.length > 0 && (
        <div className="absolute z-50 top-full mt-1 w-full rounded-lg border border-border bg-popover shadow-lg overflow-hidden">
          {results.map(u => (
            <button
              key={u.user_id}
              className="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors flex items-center gap-2"
              onClick={() => { onSelect(u); setQuery(""); setOpen(false); }}
            >
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
  );
}

// ── Members Panel ─────────────────────────────────────────────────────────────

const PAGE_SIZE = 20;

function MembersPanel({
  group,
  onCountChange,
}: {
  group: GroupResponse;
  onCountChange: (delta: number) => void;
}) {
  const [members, setMembers] = useState<GroupMemberResponse[]>([]);
  const [total, setTotal] = useState(group.member_count);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback((off: number) => {
    setLoading(true); setError(null);
    listGroupMembers(group.id, PAGE_SIZE, off)
      .then(r => { setMembers(r.members); setTotal(r.total); setOffset(off); })
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [group.id]);

  useEffect(() => { load(0); }, [load]);

  const handleAdd = async (user: UserResult) => {
    setAdding(true); setError(null);
    try {
      await addGroupMember(group.id, user.user_id);
      onCountChange(1);
      load(offset);
    } catch (e) { setError((e as Error).message); }
    finally { setAdding(false); }
  };

  const handleRemove = async (userId: string) => {
    setRemoving(userId); setError(null);
    try {
      await removeGroupMember(group.id, userId);
      onCountChange(-1);
      // If last item on page and not page 0, go back one page
      const newOff = members.length === 1 && offset > 0 ? offset - PAGE_SIZE : offset;
      load(newOff);
    } catch (e) { setError((e as Error).message); }
    finally { setRemoving(null); }
  };

  return (
    <div className="space-y-3">
      {/* Add member */}
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground">Add member</p>
        <UserSearchInput onSelect={handleAdd} disabled={adding} />
        {adding && <p className="text-xs text-muted-foreground flex items-center gap-1"><RefreshCw className="w-3 h-3 animate-spin" />Adding…</p>}
      </div>

      {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}

      {/* Member list */}
      {loading ? (
        <div className="space-y-1">
          {[...Array(3)].map((_, i) => <div key={i} className="h-9 bg-muted rounded-lg animate-pulse" />)}
        </div>
      ) : total === 0 ? (
        <p className="text-xs text-muted-foreground py-4 text-center">No members yet.</p>
      ) : (
        <>
          <div className="space-y-1">
            {members.map(m => {
              const label = m.display_name ?? m.email ?? m.user_id;
              const sub = m.display_name && m.email ? m.email : null;
              return (
                <div key={m.id} className="flex items-center justify-between rounded-lg px-3 py-2 bg-muted/40 hover:bg-muted/60 group/row transition-colors">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <div className="w-7 h-7 rounded-full bg-primary/15 flex items-center justify-center text-xs font-medium text-primary shrink-0">
                      {label[0].toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium truncate">{label}</div>
                      {sub && <div className="text-xs text-muted-foreground truncate">{sub}</div>}
                    </div>
                    {m.scope_org_name && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-600 border border-blue-500/20 shrink-0">
                        {m.scope_org_name}
                      </span>
                    )}
                    {m.scope_workspace_name && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-600 border border-green-500/20 shrink-0">
                        {m.scope_workspace_name}
                      </span>
                    )}
                  </div>
                  <button
                    className="text-muted-foreground hover:text-destructive transition-colors p-1 rounded opacity-0 group-hover/row:opacity-100"
                    onClick={() => handleRemove(m.user_id)}
                    disabled={removing === m.user_id}
                    title="Remove member"
                  >
                    {removing === m.user_id
                      ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      : <UserMinus className="w-3.5 h-3.5" />}
                  </button>
                </div>
              );
            })}
          </div>
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between pt-1 border-t border-border">
              <span className="text-xs text-muted-foreground">{offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}</span>
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" disabled={offset === 0} onClick={() => load(offset - PAGE_SIZE)} className="h-6 px-2 text-xs">Prev</Button>
                <Button size="sm" variant="ghost" disabled={offset + PAGE_SIZE >= total} onClick={() => load(offset + PAGE_SIZE)} className="h-6 px-2 text-xs">Next</Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Roles Panel ───────────────────────────────────────────────────────────────

function RolesPanel({
  group,
  allRoles,
  onRoleAssigned,
  onRoleRevoked,
}: {
  group: GroupResponse;
  allRoles: RoleResponse[];
  onRoleAssigned: (g: GroupResponse) => void;
  onRoleRevoked: (g: GroupResponse) => void;
}) {
  const [assigning, setAssigning] = useState(false);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const assignedRoleIds = new Set(group.roles.map(r => r.role_id));
  const available = allRoles.filter(r => !assignedRoleIds.has(r.id));

  const handleAssign = async () => {
    if (!selectedRoleId) return;
    setAssigning(true); setError(null);
    try {
      const updated = await assignRoleToGroup(group.id, selectedRoleId);
      onRoleAssigned(updated);
      setSelectedRoleId("");
    } catch (e) { setError((e as Error).message); }
    finally { setAssigning(false); }
  };

  const handleRevoke = async (roleId: string) => {
    setRevoking(roleId); setError(null);
    try {
      await revokeRoleFromGroup(group.id, roleId);
      onRoleRevoked({ ...group, roles: group.roles.filter(r => r.role_id !== roleId) });
    } catch (e) { setError((e as Error).message); }
    finally { setRevoking(null); }
  };

  return (
    <div className="space-y-3">
      {/* Assign role */}
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground">Assign role</p>
        {available.length > 0 ? (
          <div className="flex gap-2">
            <select
              className="flex-1 h-8 rounded-lg border border-border bg-background text-sm px-2 focus:outline-none focus:ring-1 focus:ring-primary"
              value={selectedRoleId}
              onChange={e => setSelectedRoleId(e.target.value)}
            >
              <option value="">Select a role…</option>
              {available.map(r => (
                <option key={r.id} value={r.id}>{r.name} [{r.role_level_code}]</option>
              ))}
            </select>
            <Button size="sm" onClick={handleAssign} disabled={!selectedRoleId || assigning} className="h-8 px-3 gap-1">
              <ShieldPlus className="w-3.5 h-3.5" />
              Assign
            </Button>
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">All available roles are already assigned.</p>
        )}
      </div>

      {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}

      {/* Assigned roles */}
      {group.roles.length === 0 ? (
        <p className="text-xs text-muted-foreground py-4 text-center">No roles assigned yet.</p>
      ) : (
        <div className="space-y-1">
          {group.roles.map(r => (
            <div key={r.id} className="flex items-center justify-between rounded-lg px-3 py-2 bg-muted/40 hover:bg-muted/60 group/row transition-colors">
              <div className="flex items-center gap-2 min-w-0">
                <Shield className="w-3.5 h-3.5 text-primary shrink-0" />
                <span className="text-sm font-medium truncate">{r.role_name}</span>
                <LevelBadge code={r.role_level_code} />
              </div>
              <button
                className="text-muted-foreground hover:text-destructive transition-colors p-1 rounded opacity-0 group-hover/row:opacity-100"
                onClick={() => handleRevoke(r.role_id)}
                disabled={revoking === r.role_id}
                title="Revoke role"
              >
                {revoking === r.role_id
                  ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  : <X className="w-3.5 h-3.5" />}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Audit Tab ─────────────────────────────────────────────────────────────────

function AuditTab({ groupId }: { groupId: string }) {
  const [events, setEvents] = useState<AuditEventResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const limit = 15;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listAuditEvents({ entity_type: "user_group", entity_id: groupId, limit, offset })
      .then(r => { if (!cancelled) { setEvents(r.events); setTotal(r.total); } })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [groupId, offset]);

  const EVENT_COLORS: Record<string, string> = {
    group_created: "text-emerald-500 bg-emerald-500/10",
    group_updated: "text-blue-500 bg-blue-500/10",
    group_deleted: "text-red-500 bg-red-500/10",
    group_member_added: "text-violet-500 bg-violet-500/10",
    group_member_removed: "text-orange-500 bg-orange-500/10",
    group_role_assigned: "text-blue-500 bg-blue-500/10",
    group_role_revoked: "text-orange-500 bg-orange-500/10",
    group_parent_changed: "text-amber-500 bg-amber-500/10",
  };

  if (loading) return (
    <div className="space-y-2 py-1">
      {[...Array(4)].map((_, i) => <div key={i} className="h-8 bg-muted rounded-lg animate-pulse" />)}
    </div>
  );

  if (events.length === 0) return (
    <p className="text-xs text-muted-foreground py-4 text-center">No audit events found.</p>
  );

  return (
    <div className="space-y-2">
      {events.map(e => (
        <div key={e.id} className="flex items-start gap-3 rounded-lg px-3 py-2 bg-muted/30 hover:bg-muted/50 transition-colors">
          <span className={`mt-0.5 px-1.5 py-0.5 rounded text-xs font-medium shrink-0 ${EVENT_COLORS[e.event_type] ?? "text-muted-foreground bg-muted"}`}>
            {e.event_type.replace("group_", "").replace(/_/g, " ")}
          </span>
          <div className="flex-1 min-w-0">
            {e.actor_id && (
              <span className="text-xs text-muted-foreground font-mono">
                by {e.actor_id.slice(0, 8)}…
              </span>
            )}
          </div>
          <span className="text-xs text-muted-foreground shrink-0">{formatDateTime(e.occurred_at)}</span>
        </div>
      ))}
      {total > limit && (
        <div className="flex items-center justify-between pt-1">
          <span className="text-xs text-muted-foreground">{total} total</span>
          <div className="flex gap-1">
            <Button size="sm" variant="ghost" disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - limit))} className="h-6 px-2 text-xs">Prev</Button>
            <Button size="sm" variant="ghost" disabled={offset + limit >= total} onClick={() => setOffset(o => o + limit)} className="h-6 px-2 text-xs">Next</Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Reparent Picker ───────────────────────────────────────────────────────────

function ReparentPicker({
  group,
  allGroups,
  onDone,
}: {
  group: GroupResponse;
  allGroups: GroupResponse[];
  onDone: (updated: GroupResponse) => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [value, setValue] = useState(group.parent_group_id ?? "");

  // Only allow same-level groups as parents (avoids cross-level weirdness)
  const eligible = allGroups.filter(g => g.id !== group.id && !g.is_system && g.role_level_code === group.role_level_code);

  const handleSave = async () => {
    setSaving(true); setError(null);
    try {
      const updated = await setGroupParent(group.id, value || null);
      onDone(updated);
    } catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  };

  return (
    <div className="space-y-2 p-3 border border-border rounded-lg bg-muted/30">
      <p className="text-xs font-medium text-muted-foreground">Move under parent group (same level only)</p>
      {error && <p className="text-xs text-destructive">{error}</p>}
      <div className="flex gap-2">
        <select
          className="flex-1 h-8 rounded-lg border border-border bg-background text-sm px-2 focus:outline-none focus:ring-1 focus:ring-primary"
          value={value}
          onChange={e => setValue(e.target.value)}
        >
          <option value="">(No parent — top-level group)</option>
          {eligible.map(g => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
        <Button size="sm" onClick={handleSave} disabled={saving} className="h-8 px-3">
          <Check className="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  );
}

// ── Group Node ────────────────────────────────────────────────────────────────

function GroupNode({
  group,
  children,
  depth,
  allGroups,
  allRoles,
  onUpdate,
  onDelete,
  onCreated,
  expandSignal,
  showParentCrumb,
  orgNames,
  wsNames,
}: {
  group: GroupResponse;
  children: GroupResponse[];
  depth: number;
  allGroups: GroupResponse[];
  allRoles: RoleResponse[];
  onUpdate: (g: GroupResponse) => void;
  onDelete: (groupId: string) => void;
  onCreated: (g: GroupResponse) => void;
  /** +N = expand all, -N = collapse all (change value to trigger) */
  expandSignal?: number;
  /** Show the parent group name inline (for search results) */
  showParentCrumb?: boolean;
  orgNames: ScopeNames;
  wsNames: ScopeNames;
}) {
  const [expanded, setExpanded] = useState(false);
  const [tab, setTab] = useState<"members" | "roles" | "subgroups" | "audit">("members");
  const [editing, setEditing] = useState(false);
  const [reparenting, setReparenting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [editName, setEditName] = useState(group.name);
  const [editDesc, setEditDesc] = useState(group.description);
  const [saving, setSaving] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [showCreateChild, setShowCreateChild] = useState(false);

  const nodeRef = useRef<HTMLDivElement>(null);
  const [memberCount, setMemberCount] = useState(group.member_count);

  // Respond to expand-all / collapse-all signal
  useEffect(() => {
    if (expandSignal === undefined) return;
    if (expandSignal > 0 && !expanded) setExpanded(true);
    else if (expandSignal < 0 && expanded) setExpanded(false);
  // intentionally only react to signal changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expandSignal]);

  const handleExpand = () => setExpanded(v => !v);

  const handleSaveEdit = async () => {
    setSaving(true); setSaveError(null);
    try {
      const updated = await updateGroup(group.id, { name: editName, description: editDesc });
      onUpdate(updated);
      setEditing(false);
    } catch (e) { setSaveError((e as Error).message); }
    finally { setSaving(false); }
  };

  const handleToggleActive = async () => {
    setToggling(true); setSaveError(null);
    try {
      const updated = await updateGroup(group.id, { is_disabled: group.is_active });
      onUpdate(updated);
    } catch (e) { setSaveError((e as Error).message); }
    finally { setToggling(false); }
  };

  const handleDelete = async () => {
    setDeleting(true); setSaveError(null);
    try {
      await deleteGroup(group.id);
      onDelete(group.id);
    } catch (e) { setSaveError((e as Error).message); setDeleting(false); setConfirmDelete(false); }
  };

  const indentPx = depth * 28;
  const isInactive = !group.is_active;

  const LEVEL_BORDER: Record<string, string> = {
    super_admin: "border-l-red-500",
    platform:    "border-l-violet-500",
    org:         "border-l-blue-500",
    workspace:   "border-l-emerald-500",
  };
  const levelBorderCls = LEVEL_BORDER[group.role_level_code] ?? "border-l-border";

  return (
    <div ref={nodeRef} className="group/node relative" data-group-id={group.id}>
      {/* Tree connector lines */}
      {depth > 0 && (
        <div
          className="absolute top-0 bottom-0 border-l-2 border-border/40"
          style={{ left: (depth - 1) * 28 + 12 }}
        />
      )}
      {/* Row */}
      <div
        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border border-l-[3px] ${levelBorderCls} transition-colors cursor-pointer
          ${isInactive ? "opacity-60 bg-muted/20" : expanded ? "border-primary/20 bg-primary/5" : "border-border bg-card hover:border-border/80 hover:bg-muted/30"}`}
        style={{ marginLeft: indentPx }}
        onClick={handleExpand}
      >
        {/* Hierarchy connector */}
        {depth > 0 && (
          <span className="text-primary/40 mr-0.5 -ml-1 flex items-center">
            <svg width="16" height="16" viewBox="0 0 16 16" className="shrink-0">
              <path d="M0 0 L0 8 L12 8" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </span>
        )}

        {/* Expand chevron */}
        <span className="text-muted-foreground shrink-0">
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </span>

        {/* Icon */}
        <span className={`shrink-0 ${group.is_system ? "text-amber-500" : isInactive ? "text-muted-foreground" : "text-primary"}`}>
          <Users className="w-4 h-4" />
        </span>

        {/* Name + badges */}
        <div className="flex-1 min-w-0 flex items-center gap-2">
          <span className={`font-medium text-sm truncate ${isInactive ? "line-through text-muted-foreground" : ""}`}>{group.name}</span>
          <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{group.code}</span>
          <LevelBadge code={group.role_level_code} />
          {group.is_system && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-amber-600 bg-amber-500/10 border-amber-500/20">
              <Lock className="w-3 h-3" /> System
            </span>
          )}
          {group.is_locked && !group.is_system && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-violet-600 bg-violet-500/10 border-violet-500/20" title="Mapped to a framework control — cannot be deleted or disabled">
              <Lock className="w-3 h-3" /> Framework Mapped
            </span>
          )}
          {isInactive && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-muted-foreground bg-muted border-border">
              <Ban className="w-3 h-3" /> Inactive
            </span>
          )}
          <ScopeBadge group={group} orgNames={orgNames} wsNames={wsNames} />
          {showParentCrumb && group.parent_group_id && (() => {
            const parent = allGroups.find(g => g.id === group.parent_group_id);
            return parent ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs text-muted-foreground bg-muted/60 border-border">
                <GitBranch className="w-3 h-3" />
                {parent.name}
              </span>
            ) : null;
          })()}
        </div>

        {/* Right stats */}
        <div className="flex items-center gap-3 shrink-0 text-xs text-muted-foreground" onClick={e => e.stopPropagation()}>
          <span className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            {group.member_count}
          </span>
          <span className="flex items-center gap-1">
            <Shield className="w-3 h-3" />
            {group.roles.length}
          </span>
          {children.length > 0 && (
            <span className="flex items-center gap-1">
              <GitBranch className="w-3 h-3" />
              {children.length}
            </span>
          )}
          {!group.is_system && (
            <button
              className="opacity-0 group-hover/node:opacity-100 p-1 rounded hover:bg-primary/10 text-primary transition-all"
              onClick={e => { e.stopPropagation(); setShowCreateChild(true); }}
              title="Create sub-group"
            >
              <Plus className="w-3 h-3" />
            </button>
          )}
          {!group.is_system && (
            <button
              className="opacity-0 group-hover/node:opacity-100 p-1 rounded hover:bg-muted transition-all"
              onClick={e => { e.stopPropagation(); setEditing(v => !v); if (!expanded) handleExpand(); }}
              title="Edit"
            >
              <Pencil className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Expanded panel */}
      {expanded && (
        <div className="mt-1 mb-2 rounded-xl border border-border bg-card overflow-hidden" style={{ marginLeft: indentPx + (depth > 0 ? 8 : 0) }}>
          {/* Edit inline */}
          {editing && !group.is_system && (
            <div className="p-4 border-b border-border space-y-3">
              {saveError && <p className="text-xs text-destructive">{saveError}</p>}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Name</label>
                  <Input value={editName} onChange={e => setEditName(e.target.value)} className="h-8 text-sm" />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Description</label>
                  <Input value={editDesc} onChange={e => setEditDesc(e.target.value)} className="h-8 text-sm" />
                </div>
              </div>
              {/* Scope info (read-only) */}
              {(group.scope_org_id || group.scope_workspace_id) && (
                <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 px-3 py-2 text-xs text-blue-700 dark:text-blue-400 space-y-0.5">
                  <div className="font-medium flex items-center gap-1.5">
                    {group.scope_workspace_id ? <Layers className="w-3 h-3" /> : <Building2 className="w-3 h-3" />}
                    Scoped Group
                  </div>
                  {group.scope_org_id && (
                    <div>Org: <span className="font-semibold">{orgNames[group.scope_org_id] ?? group.scope_org_id.slice(0, 8)}</span></div>
                  )}
                  {group.scope_workspace_id && (
                    <div>Workspace: <span className="font-semibold">{wsNames[group.scope_workspace_id] ?? group.scope_workspace_id.slice(0, 8)}</span></div>
                  )}
                </div>
              )}
              <div className="flex items-center gap-2 flex-wrap">
                <Button size="sm" onClick={handleSaveEdit} disabled={saving} className="h-7 px-3 text-xs">
                  <Check className="w-3 h-3 mr-1" /> {saving ? "Saving…" : "Save"}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setEditName(group.name); setEditDesc(group.description); }} className="h-7 px-3 text-xs">
                  Cancel
                </Button>
                <div className="ml-auto flex items-center gap-2">
                  {/* Disable / Enable toggle */}
                  <button
                    className={`flex items-center gap-1 text-xs px-2 py-1 rounded border transition-colors
                      ${group.is_active
                        ? "text-orange-600 border-orange-300 hover:bg-orange-50 dark:hover:bg-orange-900/20"
                        : "text-emerald-600 border-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                      }`}
                    onClick={handleToggleActive}
                    disabled={toggling || (group.is_locked && group.is_active)}
                    title={group.is_locked && group.is_active ? "Cannot disable — group is mapped to a framework control" : group.is_active ? "Disable group" : "Enable group"}
                  >
                    {group.is_active
                      ? <><Ban className="w-3 h-3" />{toggling ? "Disabling…" : "Disable"}</>
                      : <><Power className="w-3 h-3" />{toggling ? "Enabling…" : "Enable"}</>
                    }
                  </button>
                  {/* Delete group */}
                  {!confirmDelete ? (
                    <button
                      className="flex items-center gap-1 text-xs px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      onClick={() => setConfirmDelete(true)}
                    >
                      <Trash2 className="w-3 h-3" /> Delete
                    </button>
                  ) : (
                    <div className="flex flex-col gap-1.5 items-end">
                      {children.length > 0 && (
                        <div className="flex items-center gap-1 text-xs text-amber-600 bg-amber-500/10 border border-amber-500/20 rounded px-2 py-1">
                          <AlertTriangle className="w-3 h-3 shrink-0" />
                          {children.length} sub-group{children.length !== 1 ? "s" : ""} will become top-level
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-red-600">Sure?</span>
                        <button
                          className="text-xs px-2 py-1 rounded border border-red-500 bg-red-500 text-white hover:bg-red-600 transition-colors"
                          onClick={handleDelete}
                          disabled={deleting}
                        >
                          {deleting ? "Deleting…" : "Yes, delete"}
                        </button>
                        <button className="text-xs px-2 py-1 rounded border border-border hover:bg-muted" onClick={() => setConfirmDelete(false)}>
                          No
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Detail info */}
          {!editing && (
            <div className="px-4 py-3 border-b border-border space-y-2">
              {/* Breadcrumb for sub-groups */}
              {depth > 0 && (() => {
                const crumbs: GroupResponse[] = [];
                let cur = allGroups.find(g => g.id === group.parent_group_id);
                while (cur) {
                  crumbs.unshift(cur);
                  cur = allGroups.find(g => g.id === cur!.parent_group_id);
                }
                if (crumbs.length === 0) return null;
                return (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground flex-wrap">
                    {crumbs.map((c, i) => (
                      <span key={c.id} className="flex items-center gap-1">
                        {i > 0 && <ChevronRight className="w-3 h-3 shrink-0" />}
                        <span className="font-medium text-foreground/70">{c.name}</span>
                      </span>
                    ))}
                    <ChevronRight className="w-3 h-3 shrink-0" />
                    <span className="font-semibold text-foreground">{group.name}</span>
                  </div>
                );
              })()}
              {group.description && (
                <p className="text-xs text-muted-foreground">{group.description}</p>
              )}
              <div className="grid grid-cols-3 gap-x-4 gap-y-1.5 text-xs">
                <div>
                  <span className="text-muted-foreground">Code</span>
                  <p className="font-mono text-foreground">{group.code}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Level</span>
                  <p className="text-foreground">{group.role_level_code}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Tenant</span>
                  <p className="font-mono text-muted-foreground">{group.tenant_key}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Created</span>
                  <p className="text-foreground">{formatDateTime(group.created_at)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Updated</span>
                  <p className="text-foreground">{formatDateTime(group.updated_at)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status</span>
                  <p className={group.is_active ? "text-emerald-500 font-medium" : "text-muted-foreground"}>
                    {group.is_active ? "Active" : "Inactive"}
                  </p>
                </div>
                {group.scope_org_id && (
                  <div className="col-span-3">
                    <span className="text-muted-foreground flex items-center gap-1"><Building2 className="w-3 h-3" /> Org Scope</span>
                    <p className="text-foreground font-medium">{orgNames[group.scope_org_id] ?? group.scope_org_id}</p>
                  </div>
                )}
                {group.scope_workspace_id && (
                  <div className="col-span-3">
                    <span className="text-muted-foreground flex items-center gap-1"><Layers className="w-3 h-3" /> Workspace Scope</span>
                    <p className="text-foreground font-medium">{wsNames[group.scope_workspace_id] ?? group.scope_workspace_id}</p>
                  </div>
                )}
              </div>
              {/* Reparent action — visible outside edit mode */}
              {!group.is_system && (
                <div className="pt-1">
                  <button
                    className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
                    onClick={() => setReparenting(v => !v)}
                  >
                    <GitBranch className="w-3 h-3" />
                    {group.parent_group_id
                      ? `Parent: ${allGroups.find(g => g.id === group.parent_group_id)?.name ?? "…"} — change`
                      : "Move under a parent group"}
                  </button>
                  {reparenting && (
                    <div className="mt-2">
                      <ReparentPicker
                        group={group}
                        allGroups={allGroups}
                        onDone={updated => { onUpdate(updated); setReparenting(false); }}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Tabs */}
          <div className="flex border-b border-border overflow-x-auto">
            {(["subgroups", "members", "roles", "audit"] as const).map(t => (
              <button
                key={t}
                className={`px-4 py-2 text-xs font-medium capitalize transition-colors border-b-2 -mb-px whitespace-nowrap
                  ${tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}
                onClick={() => setTab(t)}
              >
                {t === "members"   ? `Members (${memberCount})` :
                 t === "roles"     ? `Roles (${group.roles.length})` :
                 t === "subgroups" ? `Sub-groups (${children.length})` :
                                    "Audit"}
              </button>
            ))}
          </div>

          <div className="p-4">
            {tab === "members" && (
              <MembersPanel
                group={group}
                onCountChange={delta => setMemberCount(c => c + delta)}
              />
            )}
            {tab === "roles" && (
              <RolesPanel
                group={group}
                allRoles={allRoles}
                onRoleAssigned={onUpdate}
                onRoleRevoked={onUpdate}
              />
            )}
            {tab === "subgroups" && (
              <div className="space-y-2">
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 px-3 text-xs gap-1.5"
                    onClick={() => setShowCreateChild(true)}
                  >
                    <Plus className="w-3 h-3" />
                    Add Sub-Group
                  </Button>
                </div>
                {children.length === 0 ? (
                  <div className="flex flex-col items-center gap-3 py-6 text-center">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                      <GitBranch className="w-5 h-5 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">No sub-groups yet</p>
                      <p className="text-xs text-muted-foreground mt-0.5">Create a sub-group nested under this group.</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {children.map(child => (
                      <GroupNodeWithChildren
                        key={child.id}
                        group={child}
                        depth={0}
                        allGroups={allGroups}
                        allRoles={allRoles}
                        onUpdate={onUpdate}
                        onDelete={onDelete}
                        onCreated={onCreated}
                        orgNames={orgNames}
                        wsNames={wsNames}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
            {tab === "audit" && <AuditTab groupId={group.id} />}
          </div>
        </div>
      )}

      {/* Recursive children rendered inline as tree */}
      {children.map(child => (
        <GroupNodeWithChildren
          key={child.id}
          group={child}
          depth={depth + 1}
          allGroups={allGroups}
          allRoles={allRoles}
          onUpdate={onUpdate}
          onDelete={onDelete}
          onCreated={onCreated}
          expandSignal={expandSignal}
          orgNames={orgNames}
          wsNames={wsNames}
        />
      ))}

      {/* Create sub-group dialog */}
      {showCreateChild && (
        <CreateGroupDialog
          allGroups={allGroups}
          prefillParent={group}
          onCreated={g => { onCreated(g); setShowCreateChild(false); if (!expanded) handleExpand(); setTab("subgroups"); }}
          onClose={() => setShowCreateChild(false)}
        />
      )}
    </div>
  );
}

// Wrapper to compute children for each node from the flat list
function GroupNodeWithChildren(props: {
  group: GroupResponse;
  depth: number;
  allGroups: GroupResponse[];
  allRoles: RoleResponse[];
  onUpdate: (g: GroupResponse) => void;
  onDelete: (groupId: string) => void;
  onCreated: (g: GroupResponse) => void;
  expandSignal?: number;
  showParentCrumb?: boolean;
  orgNames: ScopeNames;
  wsNames: ScopeNames;
}) {
  const { group, allGroups, ...rest } = props;
  const children = allGroups.filter(g => g.parent_group_id === group.id);
  return <GroupNode group={group} children={children} allGroups={allGroups} {...rest} />;
}

// ── Create Group Dialog ───────────────────────────────────────────────────────

function CreateGroupDialog({
  allGroups,
  onCreated,
  onClose,
  prefillParent,
}: {
  allGroups: GroupResponse[];
  onCreated: (g: GroupResponse) => void;
  onClose: () => void;
  /** When creating a sub-group, pass the parent so level + parent are pre-filled and locked */
  prefillParent?: GroupResponse;
}) {
  const LEVELS = [
    { code: "super_admin", label: "Super Admin — platform-wide, highest privilege" },
    { code: "platform",    label: "Platform — applies across the whole platform" },
    { code: "org",         label: "Org — scoped to an organisation" },
    { code: "workspace",   label: "Workspace — scoped to a workspace" },
  ];

  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [level, setLevel] = useState(prefillParent?.role_level_code ?? "platform");
  const [parentId, setParentId] = useState(prefillParent?.id ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [codeEdited, setCodeEdited] = useState(false);

  const toSnakeCase = (s: string) => s.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "").replace(/_+/g, "_").replace(/^_|_$/g, "");

  const handleNameChange = (v: string) => {
    setName(v);
    if (!codeEdited) setCode(toSnakeCase(v));
  };
  const handleCodeChange = (v: string) => {
    setCode(v.toLowerCase().replace(/[^a-z0-9_]/g, ""));
    setCodeEdited(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setError(null);
    try {
      const g = await createGroup({ code, name, description: desc, role_level_code: level, parent_group_id: parentId || null });
      onCreated(g);
      onClose();
    } catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  };

  // Only same-level groups as parent candidates
  const parentCandidates = allGroups.filter(g => !g.is_system && g.role_level_code === level);

  const isSubGroupMode = !!prefillParent;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-base">
              {isSubGroupMode ? "Create Sub-Group" : "Create User Group"}
            </h2>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>
          </div>

          {/* Show parent context when creating a sub-group */}
          {isSubGroupMode && prefillParent && (
            <div className="flex items-center gap-2 rounded-lg bg-primary/5 border border-primary/20 px-3 py-2">
              <GitBranch className="w-3.5 h-3.5 text-primary shrink-0" />
              <span className="text-xs text-muted-foreground">Creating under</span>
              <span className="text-sm font-medium">{prefillParent.name}</span>
              <LevelBadge code={prefillParent.role_level_code} />
            </div>
          )}

          {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Name <span className="text-destructive">*</span></label>
                <Input value={name} onChange={e => handleNameChange(e.target.value)} placeholder="e.g. Backend Engineers" required className="h-8 text-sm" autoFocus />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                  Code <span className="text-destructive">*</span>
                  {!codeEdited && name && <span className="text-[10px] text-primary/70 font-normal">(auto)</span>}
                </label>
                <Input
                  value={code} onChange={e => handleCodeChange(e.target.value)}
                  placeholder="e.g. eng_backend" required pattern="[a-z0-9_]+" className="h-8 text-sm font-mono"
                />
                <p className="text-[10px] text-muted-foreground mt-0.5">Cannot be changed after creation</p>
              </div>
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Description <span className="text-destructive">*</span></label>
              <Input value={desc} onChange={e => setDesc(e.target.value)} placeholder="What is this group for?" required className="h-8 text-sm" />
            </div>

            {/* Hide level picker when creating sub-group (level is inherited from parent) */}
            {!isSubGroupMode && (
              <div>
                <label className="text-xs text-muted-foreground mb-2 block">Scope Level <span className="text-destructive">*</span></label>
                <div className="space-y-2">
                  {LEVELS.map(l => (
                    <label key={l.code} className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                      ${level === l.code ? "border-primary/50 bg-primary/5" : "border-border hover:border-border/80 hover:bg-muted/30"}`}>
                      <input type="radio" name="level" value={l.code} checked={level === l.code} onChange={() => { setLevel(l.code); setParentId(""); }} className="mt-0.5" />
                      <div>
                        <div className="text-sm font-medium flex items-center gap-2">
                          {l.code.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}
                          <LevelBadge code={l.code} />
                        </div>
                        <div className="text-xs text-muted-foreground">{l.label}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Hide parent picker when creating sub-group (parent is pre-set) */}
            {!isSubGroupMode && (
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Parent Group (optional — same level only)</label>
                <select
                  className="w-full h-8 rounded-lg border border-border bg-background text-sm px-2 focus:outline-none focus:ring-1 focus:ring-primary"
                  value={parentId}
                  onChange={e => setParentId(e.target.value)}
                >
                  <option value="">(Top-level — no parent)</option>
                  {parentCandidates.map(g => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex gap-2 pt-1">
              <Button type="submit" disabled={saving} className="flex-1 h-9">
                {saving ? "Creating..." : isSubGroupMode ? "Create Sub-Group" : "Create Group"}
              </Button>
              <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

// ── Level Section ─────────────────────────────────────────────────────────────

function LevelSection({
  levelCode,
  rootGroups,
  allGroups,
  allRoles,
  onUpdate,
  onDelete,
  onCreated,
  orgNames,
  wsNames,
}: {
  levelCode: string;
  rootGroups: GroupResponse[];
  allGroups: GroupResponse[];
  allRoles: RoleResponse[];
  onUpdate: (g: GroupResponse) => void;
  onDelete: (groupId: string) => void;
  onCreated: (g: GroupResponse) => void;
  orgNames: ScopeNames;
  wsNames: ScopeNames;
}) {
  const [open, setOpen] = useState(true);
  // Positive = expand all, negative = collapse all, 0 = no signal
  const [expandSignal, setExpandSignal] = useState(0);
  const m = LEVEL_META[levelCode] ?? { label: levelCode, icon: Shield, color: "text-muted-foreground" };
  const Icon = m.icon;

  if (rootGroups.length === 0) return null;

  const totalGroupsInLevel = allGroups.filter(g => g.role_level_code === levelCode).length;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1">
        <button
          className="flex-1 flex items-center gap-2 px-1 py-1 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors"
          onClick={() => setOpen(v => !v)}
        >
          {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          <Icon className={`w-4 h-4 ${m.color.split(" ")[0]}`} />
          <span>{m.label}</span>
          <span className="ml-auto font-normal text-xs text-muted-foreground">{totalGroupsInLevel} group{totalGroupsInLevel !== 1 ? "s" : ""}</span>
        </button>
        {open && (
          <div className="flex items-center gap-1 shrink-0">
            <button
              className="text-xs text-muted-foreground hover:text-foreground px-2 py-0.5 rounded hover:bg-muted transition-colors"
              onClick={() => setExpandSignal(v => v + 1)}
              title="Expand all"
            >
              Expand all
            </button>
            <button
              className="text-xs text-muted-foreground hover:text-foreground px-2 py-0.5 rounded hover:bg-muted transition-colors"
              onClick={() => setExpandSignal(v => v - 1)}
              title="Collapse all"
            >
              Collapse all
            </button>
          </div>
        )}
      </div>
      {open && (
        <div className="space-y-2 pl-2">
          {rootGroups.map(g => (
            <GroupNodeWithChildren
              key={g.id}
              group={g}
              depth={0}
              allGroups={allGroups}
              allRoles={allRoles}
              onUpdate={onUpdate}
              onDelete={onDelete}
              onCreated={onCreated}
              expandSignal={expandSignal}
              orgNames={orgNames}
              wsNames={wsNames}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Custom Groups Section (org-scoped, non-system) ────────────────────────────

function CustomGroupsSection({
  groups,
  allGroups,
  allRoles,
  orgNames,
  wsNames,
  onUpdate,
  onDelete,
  onCreated,
}: {
  groups: GroupResponse[];
  allGroups: GroupResponse[];
  allRoles: RoleResponse[];
  orgNames: ScopeNames;
  wsNames: ScopeNames;
  onUpdate: (g: GroupResponse) => void;
  onDelete: (id: string) => void;
  onCreated: (g: GroupResponse) => void;
}) {
  const [filterOrgId, setFilterOrgId] = useState<string>("all");

  // Group by org
  const byOrg: Record<string, GroupResponse[]> = {};
  for (const g of groups) {
    const key = g.scope_org_id ?? "__platform__";
    (byOrg[key] ??= []).push(g);
  }
  const orgIds = Object.keys(byOrg).filter(k => k !== "__platform__");

  const visibleGroups = filterOrgId === "all" ? groups : groups.filter(g => g.scope_org_id === filterOrgId);

  // Group visible by org for display
  const visibleByOrg: Record<string, GroupResponse[]> = {};
  for (const g of visibleGroups) {
    const key = g.scope_org_id ?? "__platform__";
    (visibleByOrg[key] ??= []).push(g);
  }

  if (groups.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border px-6 py-8 text-center">
        <Users className="w-8 h-8 text-muted-foreground/40 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">No custom groups yet</p>
        <p className="text-xs text-muted-foreground mt-1">Org admins can create custom groups within their org</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Org filter */}
      {orgIds.length > 1 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-muted-foreground">Filter by org:</span>
          <button
            onClick={() => setFilterOrgId("all")}
            className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              filterOrgId === "all"
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/30"
            }`}
          >
            All orgs ({groups.length})
          </button>
          {orgIds.map(orgId => (
            <button
              key={orgId}
              onClick={() => setFilterOrgId(orgId)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors flex items-center gap-1 ${
                filterOrgId === orgId
                  ? "bg-blue-500 text-white border-blue-500"
                  : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/30"
              }`}
            >
              <Building2 className="w-3 h-3" />
              {orgNames[orgId] ?? orgId.slice(0, 8)}
              <span className="opacity-70">({byOrg[orgId]?.length ?? 0})</span>
            </button>
          ))}
        </div>
      )}

      {/* Groups by org */}
      {Object.entries(visibleByOrg).map(([orgId, orgGroups]) => (
        <div key={orgId} className="space-y-2">
          {/* Org header */}
          <div className="flex items-center gap-2 px-1">
            <Building2 className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-sm font-medium text-foreground">
              {orgNames[orgId] ?? orgId.slice(0, 8)}
            </span>
            <span className="text-xs text-muted-foreground">· {orgGroups.length} group{orgGroups.length !== 1 ? "s" : ""}</span>
            <div className="h-px flex-1 bg-border" />
          </div>
          {orgGroups.map(g => (
            <GroupNodeWithChildren
              key={g.id}
              group={g}
              depth={0}
              allGroups={allGroups}
              allRoles={allRoles}
              onUpdate={onUpdate}
              onDelete={onDelete}
              onCreated={onCreated}
              orgNames={orgNames}
              wsNames={wsNames}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AdminGroupsPage() {
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [roles, setRoles] = useState<RoleResponse[]>([]);
  const [orgNames, setOrgNames] = useState<ScopeNames>({});
  const [wsNames, setWsNames] = useState<ScopeNames>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [showCustom, setShowCustom] = useState(false);

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true);
    setError(null);
    try {
      const [gRes, rRes] = await Promise.all([listGroups(), listRoles()]);
      setGroups(gRes.groups);
      setRoles(rRes.roles);

      // Resolve org & workspace names for scoped groups
      try {
        const orgs = await listOrgs();
        const oMap: ScopeNames = {};
        for (const o of orgs) oMap[o.id] = o.name;
        setOrgNames(oMap);

        const wMap: ScopeNames = {};
        await Promise.all(
          orgs.map(async (o) => {
            try {
              const wsList = await listWorkspaces(o.id);
              for (const ws of wsList) wMap[ws.id] = ws.name;
            } catch { /* best-effort */ }
          })
        );
        setWsNames(wMap);
      } catch { /* best-effort */ }
    } catch (e) { setError((e as Error).message); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleUpdate = useCallback((updated: GroupResponse) => {
    setGroups(prev => prev.map(g => g.id === updated.id ? updated : g));
  }, []);
  const handleCreated = useCallback((g: GroupResponse) => {
    setGroups(prev => [...prev, g]);
  }, []);
  const handleDelete = useCallback((groupId: string) => {
    setGroups(prev => prev.filter(g => g.id !== groupId));
  }, []);

  // Partition groups:
  //   platform groups  = no scope at all (the "real" governance groups)
  //   system scoped    = is_system=true + has scope  → infra, never shown
  //   custom scoped    = is_system=false + has scope → org-admin-created, shown in Custom tab
  const platformGroups = groups.filter(g => !g.scope_org_id && !g.scope_workspace_id);
  const customScopedGroups = groups.filter(g => !g.is_system && (g.scope_org_id || g.scope_workspace_id));
  const customGroupCount = customScopedGroups.length;

  // Active set for main view
  const activeGroups = platformGroups;

  const groupById = Object.fromEntries(activeGroups.map(g => [g.id, g]));
  const isTopLevel = (g: GroupResponse) => !g.parent_group_id || !groupById[g.parent_group_id];

  const LEVEL_ORDER = ["super_admin", "platform", "org", "workspace"];

  // Search applies across the visible set
  const searchLower = search.trim().toLowerCase();
  const searchPool = showCustom ? customScopedGroups : activeGroups;
  const filtered = searchLower
    ? searchPool.filter(g =>
        g.name.toLowerCase().includes(searchLower) ||
        g.code.toLowerCase().includes(searchLower)
      )
    : searchPool;

  const groupsByLevel: Record<string, GroupResponse[]> = {};
  for (const lvl of LEVEL_ORDER) groupsByLevel[lvl] = [];
  for (const g of activeGroups.filter(isTopLevel)) {
    (groupsByLevel[g.role_level_code] ??= []).push(g);
  }

  const totalMembers = activeGroups.reduce((s, g) => s + g.member_count, 0);

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">User Groups</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Platform governance groups and org-level custom groups
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
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
          <Button onClick={() => setShowCreate(true)} size="sm" className="h-8 px-3">
            <Plus className="w-3.5 h-3.5 mr-1" /> New Group
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Platform Groups",  value: platformGroups.length,                          icon: Globe,     borderCls: "border-l-violet-500", iconCls: "text-violet-500", numCls: "text-violet-600 dark:text-violet-400" },
          { label: "Custom Groups",    value: customGroupCount,                                icon: Building2, borderCls: "border-l-blue-500",   iconCls: "text-blue-500",   numCls: "text-blue-600 dark:text-blue-400" },
          { label: "Total Members",    value: totalMembers,                                    icon: Users,     borderCls: "border-l-emerald-500", iconCls: "text-emerald-500", numCls: "text-emerald-600 dark:text-emerald-400" },
          { label: "Inactive",         value: activeGroups.filter(g => !g.is_active).length,  icon: Ban,       borderCls: "border-l-muted-foreground", iconCls: "text-muted-foreground", numCls: "text-foreground" },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3 flex items-center gap-3`}>
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <s.icon className={`w-4 h-4 ${s.iconCls}`} />
            </div>
            <div className="min-w-0">
              <div className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</div>
              <div className="text-[11px] text-muted-foreground mt-0.5 truncate">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* View toggle + search row */}
      <div className="rounded-xl border border-border bg-card px-4 py-3">
      <div className="flex items-center gap-3 flex-wrap">
        {/* Tab toggle */}
        <div className="flex items-center rounded-lg border border-border bg-muted/40 p-0.5 gap-0.5 shrink-0">
          <button
            onClick={() => { setShowCustom(false); setSearch(""); }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
              !showCustom
                ? "bg-background shadow-sm text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Globe className="w-3 h-3" /> Platform Groups
          </button>
          <button
            onClick={() => { setShowCustom(true); setSearch(""); }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
              showCustom
                ? "bg-background shadow-sm text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Building2 className="w-3 h-3" /> Custom Groups
            {customGroupCount > 0 && (
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${
                showCustom ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" : "bg-muted text-muted-foreground"
              }`}>
                {customGroupCount}
              </span>
            )}
          </button>
        </div>

        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
          <Input
            className="pl-9 h-9"
            placeholder={showCustom ? "Search custom groups..." : "Search platform groups..."}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Loading skeletons */}
      {loading && (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => <Skeleton key={i} />)}
        </div>
      )}

      {/* Content */}
      {!loading && !error && (
        <div className="space-y-6">
          {showCustom ? (
            /* ── Custom Groups view ── */
            searchLower ? (
              filtered.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">No custom groups match &ldquo;{search}&rdquo;</p>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">{filtered.length} result{filtered.length !== 1 ? "s" : ""}</p>
                  {filtered.map(g => (
                    <GroupNodeWithChildren
                      key={g.id}
                      group={g}
                      depth={0}
                      allGroups={groups}
                      allRoles={roles}
                      onUpdate={handleUpdate}
                      onDelete={handleDelete}
                      onCreated={handleCreated}
                      showParentCrumb={true}
                      orgNames={orgNames}
                      wsNames={wsNames}
                    />
                  ))}
                </div>
              )
            ) : (
              <CustomGroupsSection
                groups={customScopedGroups}
                allGroups={groups}
                allRoles={roles}
                orgNames={orgNames}
                wsNames={wsNames}
                onUpdate={handleUpdate}
                onDelete={handleDelete}
                onCreated={handleCreated}
              />
            )
          ) : (
            /* ── Platform Groups view ── */
            searchLower ? (
              filtered.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">No groups match &ldquo;{search}&rdquo;</p>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">{filtered.length} result{filtered.length !== 1 ? "s" : ""}</p>
                  {filtered.map(g => (
                    <GroupNodeWithChildren
                      key={g.id}
                      group={g}
                      depth={0}
                      allGroups={groups}
                      allRoles={roles}
                      onUpdate={handleUpdate}
                      onDelete={handleDelete}
                      onCreated={handleCreated}
                      showParentCrumb={true}
                      orgNames={orgNames}
                      wsNames={wsNames}
                    />
                  ))}
                </div>
              )
            ) : (
              LEVEL_ORDER.map(lvl => (
                <LevelSection
                  key={lvl}
                  levelCode={lvl}
                  rootGroups={groupsByLevel[lvl] ?? []}
                  allGroups={groups}
                  allRoles={roles}
                  onUpdate={handleUpdate}
                  onDelete={handleDelete}
                  onCreated={handleCreated}
                  orgNames={orgNames}
                  wsNames={wsNames}
                />
              ))
            )
          )}
        </div>
      )}

      {/* Create dialog */}
      {showCreate && (
        <CreateGroupDialog
          allGroups={groups}
          onCreated={handleCreated}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  );
}
