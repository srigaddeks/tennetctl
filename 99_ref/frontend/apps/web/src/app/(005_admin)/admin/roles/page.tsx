"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Card, CardContent, Button, Input } from "@kcontrol/ui";
import {
  ChevronDown,
  ChevronRight,
  Plus,
  X,
  Shield,
  ShieldCheck,
  ShieldPlus,
  Lock,
  Globe,
  Building2,
  Layers,
  Search,
  Pencil,
  Check,
  AlertTriangle,
  CheckSquare,
  Square,
  RefreshCw,
  Trash2,
  Ban,
  Power,
  History,
  Users,
  Copy,
} from "lucide-react";
import {
  listRoles,
  listFeatureFlags,
  createRole,
  updateRole,
  deleteRole,
  assignPermissionToRole,
  revokePermissionFromRole,
  listAuditEvents,
  listGroupsUsingRole,
  listGroups,
  assignRoleToGroup,
  revokeRoleFromGroup,
} from "@/lib/api/admin";
import { listOrgs } from "@/lib/api/orgs";
import type {
  RoleResponse,
  RoleLevelResponse,
  RolePermissionResponse,
  RoleGroupResponse,
  FeaturePermissionResponse,
  UpdateRoleRequest,
  AuditEventResponse,
  GroupResponse,
} from "@/lib/types/admin";

type ScopeNames = Record<string, string>;

// ── Constants ─────────────────────────────────────────────────────────────────

const LEVEL_META: Record<string, { label: string; icon: React.FC<{ className?: string }>; color: string; desc: string }> = {
  super_admin: { label: "Super Admin", icon: ShieldCheck, color: "text-red-500 bg-red-500/10 border-red-500/20",    desc: "Full platform control — only for internal admins" },
  platform:    { label: "Platform",    icon: Globe,       color: "text-violet-500 bg-violet-500/10 border-violet-500/20", desc: "Platform-wide permissions across all orgs" },
  org:         { label: "Org",         icon: Building2,   color: "text-blue-500 bg-blue-500/10 border-blue-500/20",  desc: "Org-scoped — can be assigned to org groups" },
  workspace:   { label: "Workspace",   icon: Layers,      color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20", desc: "Workspace-scoped — granular access within a workspace" },
};

const ACTION_ORDER = ["view", "create", "update", "delete", "assign", "revoke", "enable", "disable"];

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

function RoleScopeBadge({ role, orgNames }: { role: RoleResponse; orgNames: ScopeNames }) {
  if (role.scope_workspace_id) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-emerald-600 bg-emerald-500/10 border-emerald-500/20">
        <Layers className="w-3 h-3" />
        {orgNames[role.scope_workspace_id] ?? role.scope_workspace_id.slice(0, 8)}
      </span>
    );
  }
  if (role.scope_org_id) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-blue-600 bg-blue-500/10 border-blue-500/20">
        <Building2 className="w-3 h-3" />
        {orgNames[role.scope_org_id] ?? role.scope_org_id.slice(0, 8)}
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
        <div className="h-4 w-36 bg-muted rounded" />
        <div className="h-4 w-20 bg-muted rounded" />
      </div>
      <div className="h-3 w-52 bg-muted rounded" />
    </div>
  );
}

// ── Permission Matrix ─────────────────────────────────────────────────────────

function PermissionMatrix({
  role,
  allPermissions,
  flagNameMap,
  onAssign,
  onRevoke,
}: {
  role: RoleResponse;
  allPermissions: FeaturePermissionResponse[];
  flagNameMap: Record<string, string>;
  onAssign: (featurePermissionId: string) => Promise<void>;
  onRevoke: (featurePermissionId: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permSearch, setPermSearch] = useState("");

  const assignedByPermId = Object.fromEntries(role.permissions.map(p => [p.feature_permission_id, p.id]));

  const byFlag: Record<string, FeaturePermissionResponse[]> = {};
  for (const p of allPermissions) {
    (byFlag[p.feature_flag_code] ??= []).push(p);
  }
  let flags = Object.keys(byFlag).sort();
  for (const flag of flags) {
    byFlag[flag].sort((a, b) => {
      const ai = ACTION_ORDER.indexOf(a.permission_action_code);
      const bi = ACTION_ORDER.indexOf(b.permission_action_code);
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    });
  }

  // Filter by search
  if (permSearch.trim()) {
    const q = permSearch.toLowerCase();
    flags = flags.filter(f => f.toLowerCase().includes(q));
  }

  const handleToggle = async (perm: FeaturePermissionResponse) => {
    setBusy(perm.id); setError(null);
    try {
      const isAssigned = !!assignedByPermId[perm.id];
      if (isAssigned) {
        await onRevoke(perm.id);
      } else {
        await onAssign(perm.id);
      }
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(null); }
  };

  if (Object.keys(byFlag).length === 0) return <p className="text-xs text-muted-foreground py-2">No permissions available.</p>;

  const totalAssigned = Object.keys(assignedByPermId).length;
  const totalAvailable = allPermissions.length;

  return (
    <div className="space-y-3">
      {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1.5 w-3 h-3 text-muted-foreground" />
          <input
            className="w-full h-6 pl-6 pr-2 rounded border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Filter features..."
            value={permSearch}
            onChange={e => setPermSearch(e.target.value)}
          />
        </div>
        <span className="text-xs text-muted-foreground shrink-0">{totalAssigned}/{totalAvailable} assigned</span>
      </div>
      {flags.length === 0 && permSearch.trim() && (
        <p className="text-xs text-muted-foreground py-2 text-center">No features match "{permSearch}"</p>
      )}
      {flags.map(flag => {
        const perms = byFlag[flag];
        const assignedCount = perms.filter(p => assignedByPermId[p.id]).length;
        const flagName = flagNameMap[flag];
        const isSuperAdminRole = role.code === "platform_super_admin";
        return (
          <div key={flag}>
            <div className="flex items-center gap-2 mb-1.5">
              <div className="flex flex-col min-w-0">
                {flagName && <span className="text-xs font-semibold text-foreground">{flagName}</span>}
                <span className="font-mono text-[11px] text-muted-foreground">{flag}</span>
              </div>
              <span className="text-xs text-muted-foreground shrink-0">({assignedCount}/{perms.length})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {perms.map(perm => {
                const assigned = !!assignedByPermId[perm.id];
                const isBusy = busy === perm.id;
                const isLocked = isSuperAdminRole;
                return (
                  <button
                    key={perm.id}
                    onClick={() => !isBusy && !isLocked && handleToggle(perm)}
                    disabled={isBusy || isLocked}
                    title={isLocked ? "platform_super_admin always has all permissions" : perm.name}
                    className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium transition-all
                      ${isBusy ? "opacity-50 cursor-wait" : isLocked ? "cursor-default opacity-75" : "cursor-pointer"}
                      ${assigned
                        ? isLocked
                          ? "border-amber-500/30 bg-amber-500/10 text-amber-600"
                          : "border-primary/30 bg-primary/10 text-primary hover:bg-primary/15"
                        : "border-border bg-muted/40 text-muted-foreground"
                      }`}
                  >
                    {assigned
                      ? isLocked ? <Lock className="w-3 h-3 shrink-0" /> : <CheckSquare className="w-3 h-3 shrink-0" />
                      : <Square className="w-3 h-3 shrink-0" />
                    }
                    {perm.permission_action_code}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Groups Tab ────────────────────────────────────────────────────────────────

function GroupsTab({ roleId, roleLevelCode }: { roleId: string; roleLevelCode: string }) {
  const [assignedGroups, setAssignedGroups] = useState<RoleGroupResponse[]>([]);
  const [allGroups, setAllGroups] = useState<GroupResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPicker, setShowPicker] = useState(false);
  const [pickerSearch, setPickerSearch] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loaded = useRef(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [assignedRes, allRes] = await Promise.all([
        listGroupsUsingRole(roleId),
        listGroups(),
      ]);
      setAssignedGroups(assignedRes.groups);
      setAllGroups(allRes.groups);
    } catch {}
    finally { setLoading(false); }
  }, [roleId]);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    reload();
  }, [reload]);

  const assignedIds = new Set(assignedGroups.map(g => g.id));

  const handleAssign = async (groupId: string) => {
    setBusy(groupId); setError(null);
    try {
      await assignRoleToGroup(groupId, roleId);
      await reload();
      setShowPicker(false);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(null); }
  };

  const handleRevoke = async (groupId: string) => {
    setBusy(groupId); setError(null);
    try {
      await revokeRoleFromGroup(groupId, roleId);
      setAssignedGroups(prev => prev.filter(g => g.id !== groupId));
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(null); }
  };

  // Groups that match the role level and aren't already assigned
  const availableGroups = allGroups.filter(g =>
    !assignedIds.has(g.id) &&
    g.role_level_code === roleLevelCode &&
    g.is_active &&
    !g.is_locked &&
    (pickerSearch === "" ||
      g.name.toLowerCase().includes(pickerSearch.toLowerCase()) ||
      g.code.toLowerCase().includes(pickerSearch.toLowerCase()))
  );

  if (loading) return (
    <div className="space-y-2 py-1">
      {[...Array(3)].map((_, i) => <div key={i} className="h-8 bg-muted rounded-lg animate-pulse" />)}
    </div>
  );

  const totalUsers = assignedGroups.reduce((s, g) => s + g.member_count, 0);

  return (
    <div className="space-y-3">
      {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{assignedGroups.length} group{assignedGroups.length !== 1 ? "s" : ""}</span>
          {totalUsers > 0 && <><span>·</span><span>{totalUsers} user{totalUsers !== 1 ? "s" : ""} affected</span></>}
        </div>
        <button
          onClick={() => { setShowPicker(v => !v); setPickerSearch(""); }}
          className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-primary/30 text-primary hover:bg-primary/10 transition-colors"
        >
          <Plus className="w-3 h-3" /> Add Group
        </button>
      </div>

      {/* Group picker */}
      {showPicker && (
        <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-2">
          <div className="relative">
            <Search className="absolute left-2 top-1.5 w-3 h-3 text-muted-foreground" />
            <input
              autoFocus
              className="w-full h-7 pl-6 pr-2 rounded border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              placeholder="Search groups..."
              value={pickerSearch}
              onChange={e => setPickerSearch(e.target.value)}
            />
          </div>
          {availableGroups.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-2">
              {pickerSearch ? `No groups match "${pickerSearch}"` : `No available groups with "${roleLevelCode}" scope`}
            </p>
          ) : (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {availableGroups.map(g => (
                <button
                  key={g.id}
                  onClick={() => handleAssign(g.id)}
                  disabled={busy === g.id}
                  className="w-full flex items-center justify-between rounded-lg px-3 py-2 bg-background hover:bg-primary/5 border border-transparent hover:border-primary/20 transition-colors text-left"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Users className="w-3.5 h-3.5 shrink-0 text-primary" />
                    <span className="text-sm font-medium truncate">{g.name}</span>
                    <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{g.code}</span>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0 flex items-center gap-1">
                    {busy === g.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                    {g.member_count} members
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Assigned groups */}
      {assignedGroups.length === 0 && !showPicker ? (
        <p className="text-xs text-muted-foreground py-4 text-center">No groups are using this role.</p>
      ) : (
        <div className="space-y-1">
          {assignedGroups.map(g => (
            <div key={g.id} className="flex items-center justify-between rounded-lg px-3 py-2 bg-muted/40 hover:bg-muted/60 transition-colors group/grp">
              <div className="flex items-center gap-2 min-w-0">
                <Users className={`w-3.5 h-3.5 shrink-0 ${g.is_system ? "text-amber-500" : "text-primary"}`} />
                <span className="text-sm font-medium truncate">{g.name}</span>
                <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{g.code}</span>
                <LevelBadge code={g.role_level_code} />
                {g.is_system && (
                  <span className="text-[10px] text-amber-600 bg-amber-500/10 border border-amber-500/20 rounded-full px-1.5 py-0.5">System</span>
                )}
                {!g.is_active && (
                  <span className="text-[10px] text-muted-foreground bg-muted border border-border rounded-full px-1.5 py-0.5">Inactive</span>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Users className="w-3 h-3" />
                  {g.member_count}
                </span>
                {!g.is_system && (
                  <button
                    onClick={() => handleRevoke(g.id)}
                    disabled={busy === g.id}
                    title="Remove this group from the role"
                    className="opacity-0 group-hover/grp:opacity-100 p-1 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all"
                  >
                    {busy === g.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Audit Tab ─────────────────────────────────────────────────────────────────

function AuditTab({ roleId }: { roleId: string }) {
  const [events, setEvents] = useState<AuditEventResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const limit = 15;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listAuditEvents({ entity_type: "role", entity_id: roleId, limit, offset })
      .then(r => { if (!cancelled) { setEvents(r.events); setTotal(r.total); } })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [roleId, offset]);

  const EVENT_COLORS: Record<string, string> = {
    role_created: "text-emerald-500 bg-emerald-500/10",
    role_updated: "text-blue-500 bg-blue-500/10",
    role_deleted: "text-red-500 bg-red-500/10",
    role_permission_assigned: "text-violet-500 bg-violet-500/10",
    role_permission_revoked: "text-orange-500 bg-orange-500/10",
  };

  if (loading) return (
    <div className="space-y-2 py-1">
      {[...Array(3)].map((_, i) => <div key={i} className="h-8 bg-muted rounded-lg animate-pulse" />)}
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
            {e.event_type.replace("role_", "").replace(/_/g, " ")}
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

// ── Role Row ──────────────────────────────────────────────────────────────────

function RoleRow({
  role,
  allPermissions,
  flagNameMap,
  orgNames,
  onUpdate,
  onDelete,
  onDuplicate,
  onAssignPermission,
  onRevokePermission,
}: {
  role: RoleResponse;
  allPermissions: FeaturePermissionResponse[];
  flagNameMap: Record<string, string>;
  orgNames: ScopeNames;
  onUpdate: (r: RoleResponse) => void;
  onDelete: (roleId: string) => void;
  onDuplicate: (original: RoleResponse) => Promise<void>;
  onAssignPermission: (roleId: string, featurePermissionId: string) => Promise<void>;
  onRevokePermission: (roleId: string, featurePermissionId: string) => Promise<void>;
}) {
  const [expanded, setExpanded] = useState(false);
  const [tab, setTab] = useState<"permissions" | "groups" | "audit">("permissions");
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [editName, setEditName] = useState(role.name);
  const [editDesc, setEditDesc] = useState(role.description ?? "");
  const [saving, setSaving] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [duplicating, setDuplicating] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const handleSave = async () => {
    setSaving(true); setSaveError(null);
    try {
      const updated = await updateRole(role.id, { name: editName, description: editDesc });
      onUpdate(updated);
      setEditing(false);
    } catch (e) { setSaveError((e as Error).message); }
    finally { setSaving(false); }
  };

  const handleToggleDisabled = async () => {
    setToggling(true); setSaveError(null);
    try {
      const updated = await updateRole(role.id, { is_disabled: !role.is_disabled });
      onUpdate(updated);
    } catch (e) { setSaveError((e as Error).message); }
    finally { setToggling(false); }
  };

  const handleDelete = async () => {
    setDeleting(true); setSaveError(null);
    try {
      await deleteRole(role.id);
      onDelete(role.id);
    } catch (e) { setSaveError((e as Error).message); setDeleting(false); setConfirmDelete(false); }
  };

  const handleDuplicate = async () => {
    setDuplicating(true); setSaveError(null);
    try {
      await onDuplicate(role);
    } catch (e) { setSaveError((e as Error).message); }
    finally { setDuplicating(false); }
  };

  const assignedCount = role.permissions.length;
  const isInactive = role.is_disabled || !role.is_active;

  const LEVEL_BORDER: Record<string, string> = {
    super_admin: "border-l-red-500",
    platform:    "border-l-violet-500",
    org:         "border-l-blue-500",
    workspace:   "border-l-emerald-500",
  };
  const levelBorderCls = LEVEL_BORDER[role.role_level_code] ?? "border-l-border";

  return (
    <div className="group/role">
      <div
        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border border-l-[3px] ${levelBorderCls} transition-colors cursor-pointer
          ${isInactive ? "opacity-60 bg-muted/20" : expanded ? "border-primary/20 bg-primary/5" : "border-border bg-card hover:border-border/80 hover:bg-muted/30"}`}
        onClick={() => setExpanded(v => !v)}
      >
        <span className="text-muted-foreground shrink-0">
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </span>

        <Shield className={`w-4 h-4 shrink-0 ${role.is_system ? "text-amber-500" : isInactive ? "text-muted-foreground" : "text-primary"}`} />

        <div className="flex-1 min-w-0 flex items-center gap-2 flex-wrap">
          <span className={`font-medium text-sm ${isInactive ? "line-through text-muted-foreground" : ""}`}>{role.name}</span>
          <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{role.code}</span>
          <LevelBadge code={role.role_level_code} />
          <RoleScopeBadge role={role} orgNames={orgNames} />
          {role.is_system && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-amber-600 bg-amber-500/10 border-amber-500/20">
              <Lock className="w-3 h-3" /> System
            </span>
          )}
          {isInactive && !role.is_system && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-muted-foreground bg-muted border-border">
              <Ban className="w-3 h-3" /> Disabled
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 shrink-0 text-xs text-muted-foreground" onClick={e => e.stopPropagation()}>
          <span className="flex items-center gap-1">
            <ShieldPlus className="w-3 h-3" />
            {assignedCount}
          </span>
          {!role.is_system && (
            <button
              className="opacity-0 group-hover/role:opacity-100 p-1 rounded hover:bg-muted transition-opacity"
              onClick={e => { e.stopPropagation(); setEditing(v => !v); if (!expanded) setExpanded(true); }}
              title="Edit"
            >
              <Pencil className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Expanded panel */}
      {expanded && (
        <div className="mt-1 mb-2 rounded-xl border border-border bg-card overflow-hidden">
          {/* Edit inline */}
          {editing && !role.is_system && (
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
              <div className="flex items-center gap-2 flex-wrap">
                <Button size="sm" onClick={handleSave} disabled={saving} className="h-7 px-3 text-xs">
                  <Check className="w-3 h-3 mr-1" /> {saving ? "Saving…" : "Save"}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setEditName(role.name); setEditDesc(role.description ?? ""); }} className="h-7 px-3 text-xs">Cancel</Button>
                <div className="ml-auto flex items-center gap-2">
                  <button
                    className="flex items-center gap-1 text-xs px-2 py-1 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    onClick={handleDuplicate}
                    disabled={duplicating}
                    title="Duplicate this role with its permissions"
                  >
                    <Copy className="w-3 h-3" />{duplicating ? "Duplicating…" : "Duplicate"}
                  </button>
                  <button
                    className={`flex items-center gap-1 text-xs px-2 py-1 rounded border transition-colors
                      ${role.is_disabled
                        ? "text-emerald-600 border-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                        : "text-orange-600 border-orange-300 hover:bg-orange-50 dark:hover:bg-orange-900/20"
                      }`}
                    onClick={handleToggleDisabled}
                    disabled={toggling}
                  >
                    {role.is_disabled
                      ? <><Power className="w-3 h-3" />{toggling ? "Enabling…" : "Enable"}</>
                      : <><Ban className="w-3 h-3" />{toggling ? "Disabling…" : "Disable"}</>
                    }
                  </button>
                  {!confirmDelete ? (
                    <button
                      className="flex items-center gap-1 text-xs px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      onClick={() => setConfirmDelete(true)}
                    >
                      <Trash2 className="w-3 h-3" /> Delete
                    </button>
                  ) : (
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
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Detail info */}
          {!editing && (
            <div className="px-4 py-3 border-b border-border space-y-2">
              {role.description && (
                <p className="text-xs text-muted-foreground">{role.description}</p>
              )}
              <div className="grid grid-cols-3 gap-x-4 gap-y-1.5 text-xs">
                <div>
                  <span className="text-muted-foreground">Code</span>
                  <p className="font-mono text-foreground">{role.code}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Level</span>
                  <p className="text-foreground">{role.role_level_code}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Tenant</span>
                  <p className="font-mono text-muted-foreground">{role.tenant_key}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Created</span>
                  <p className="text-foreground">{formatDateTime(role.created_at)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Updated</span>
                  <p className="text-foreground">{formatDateTime(role.updated_at)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status</span>
                  <p className={role.is_active && !role.is_disabled ? "text-emerald-500 font-medium" : "text-muted-foreground"}>
                    {role.is_disabled ? "Disabled" : role.is_active ? "Active" : "Inactive"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="flex border-b border-border overflow-x-auto">
            {(["permissions", "groups", "audit"] as const).map(t => (
              <button
                key={t}
                className={`px-4 py-2 text-xs font-medium capitalize transition-colors border-b-2 -mb-px whitespace-nowrap
                  ${tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}
                onClick={() => setTab(t)}
              >
                {t === "permissions" ? `Permissions (${assignedCount})` : t === "groups" ? "Groups" : "Audit"}
              </button>
            ))}
            {role.code === "platform_super_admin" ? (
              <span className="ml-auto flex items-center text-xs text-amber-600 px-4 gap-1">
                <Lock className="w-3 h-3" /> All permissions locked — always assigned
              </span>
            ) : role.is_system && (
              <span className="ml-auto flex items-center text-xs text-amber-600 px-4 gap-1">
                <Lock className="w-3 h-3" /> System role
              </span>
            )}
          </div>

          {/* Tab content */}
          <div className="p-4">
            {tab === "permissions" && (
              <PermissionMatrix
                role={role}
                allPermissions={allPermissions}
                flagNameMap={flagNameMap}
                onAssign={fpId => onAssignPermission(role.id, fpId)}
                onRevoke={fpId => onRevokePermission(role.id, fpId)}
              />
            )}
            {tab === "groups" && <GroupsTab roleId={role.id} roleLevelCode={role.role_level_code} />}
            {tab === "audit" && <AuditTab roleId={role.id} />}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Create Role Dialog ────────────────────────────────────────────────────────

function CreateRoleDialog({
  levels,
  onCreated,
  onClose,
}: {
  levels: RoleLevelResponse[];
  onCreated: (r: RoleResponse) => void;
  onClose: () => void;
}) {
  const ASSIGNABLE = levels.filter(l => l.code !== "super_admin");
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [level, setLevel] = useState(ASSIGNABLE[0]?.code ?? "platform");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [codeEdited, setCodeEdited] = useState(false);

  const toSnakeCase = (s: string) => s.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "").replace(/_+/g, "_").replace(/^_|_$/g, "");

  const handleNameChange = (v: string) => {
    setName(v);
    if (!codeEdited) setCode(toSnakeCase(v));
  };
  const handleCodeChange = (v: string) => {
    setCode(v.toLowerCase().replace(/[^a-z0-9_]/g, "_"));
    setCodeEdited(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setError(null);
    try {
      const r = await createRole({ code, name, description: desc, role_level_code: level });
      onCreated(r);
      onClose();
    } catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <Card className="w-full max-w-lg">
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-base">Create Role</h2>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>
          </div>

          {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Name <span className="text-destructive">*</span></label>
                <Input value={name} onChange={e => handleNameChange(e.target.value)} placeholder="e.g. Org Viewer" required className="h-8 text-sm" autoFocus />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                  Code <span className="text-destructive">*</span>
                  {!codeEdited && name && <span className="text-[10px] text-primary/70 font-normal">(auto-generated)</span>}
                </label>
                <Input
                  value={code} onChange={e => handleCodeChange(e.target.value)}
                  placeholder="e.g. org_viewer" required pattern="[a-z0-9_]+" className="h-8 text-sm font-mono"
                />
                <p className="text-[10px] text-muted-foreground mt-0.5">Cannot be changed after creation</p>
              </div>
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Description</label>
              <Input value={desc} onChange={e => setDesc(e.target.value)} placeholder="What can this role do?" className="h-8 text-sm" />
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-2 block">Scope Level <span className="text-destructive">*</span></label>
              <div className="space-y-2">
                {ASSIGNABLE.map(l => {
                  const m = LEVEL_META[l.code];
                  const Icon = m?.icon ?? Shield;
                  return (
                    <label key={l.code} className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                      ${level === l.code ? "border-primary/50 bg-primary/5" : "border-border hover:border-border/80 hover:bg-muted/30"}`}>
                      <input type="radio" name="level" value={l.code} checked={level === l.code} onChange={() => setLevel(l.code)} className="mt-0.5" />
                      <div className="flex items-start gap-2">
                        <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${m?.color.split(" ")[0] ?? "text-muted-foreground"}`} />
                        <div>
                          <div className="text-sm font-medium">{l.name}</div>
                          <div className="text-xs text-muted-foreground">{m?.desc ?? l.description}</div>
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="flex gap-2 pt-1">
              <Button type="submit" disabled={saving} className="flex-1 h-9">
                {saving ? "Creating..." : "Create Role"}
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
  level,
  roles,
  allPermissions,
  flagNameMap,
  orgNames,
  onUpdate,
  onDelete,
  onDuplicate,
  onAssignPermission,
  onRevokePermission,
}: {
  level: RoleLevelResponse;
  roles: RoleResponse[];
  allPermissions: FeaturePermissionResponse[];
  flagNameMap: Record<string, string>;
  orgNames: ScopeNames;
  onUpdate: (r: RoleResponse) => void;
  onDelete: (roleId: string) => void;
  onDuplicate: (original: RoleResponse) => Promise<void>;
  onAssignPermission: (roleId: string, featurePermissionId: string) => Promise<void>;
  onRevokePermission: (roleId: string, featurePermissionId: string) => Promise<void>;
}) {
  const [open, setOpen] = useState(true);
  const m = LEVEL_META[level.code];
  const Icon = m?.icon ?? Shield;

  if (roles.length === 0) return null;

  const systemCount = roles.filter(r => r.is_system).length;
  const customCount = roles.length - systemCount;
  const disabledCount = roles.filter(r => r.is_disabled).length;

  return (
    <div className="space-y-2">
      <button
        className="w-full flex items-center gap-2 px-1 py-1 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors"
        onClick={() => setOpen(v => !v)}
      >
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        <Icon className={`w-4 h-4 ${m?.color.split(" ")[0] ?? "text-muted-foreground"}`} />
        <span>{level.name}</span>
        <span className="text-xs font-normal text-muted-foreground ml-1">{m?.desc}</span>
        <span className="ml-auto flex items-center gap-2 font-normal text-xs text-muted-foreground">
          {systemCount > 0 && <span className="text-amber-600">{systemCount} system</span>}
          {customCount > 0 && <span>{customCount} custom</span>}
          {disabledCount > 0 && <span className="text-orange-500">{disabledCount} disabled</span>}
        </span>
      </button>
      {open && (
        <div className="space-y-2 pl-2">
          {roles.map(r => (
            <RoleRow
              key={r.id}
              role={r}
              allPermissions={allPermissions}
              flagNameMap={flagNameMap}
              orgNames={orgNames}
              onUpdate={onUpdate}
              onDelete={onDelete}
              onDuplicate={onDuplicate}
              onAssignPermission={onAssignPermission}
              onRevokePermission={onRevokePermission}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Custom Roles Section ───────────────────────────────────────────────────────

function CustomRolesSection({
  roles,
  allPermissions,
  flagNameMap,
  orgNames,
  onUpdate,
  onDelete,
  onDuplicate,
  onAssignPermission,
  onRevokePermission,
}: {
  roles: RoleResponse[];
  allPermissions: FeaturePermissionResponse[];
  flagNameMap: Record<string, string>;
  orgNames: ScopeNames;
  onUpdate: (r: RoleResponse) => void;
  onDelete: (roleId: string) => void;
  onDuplicate: (original: RoleResponse) => Promise<void>;
  onAssignPermission: (roleId: string, featurePermissionId: string) => Promise<void>;
  onRevokePermission: (roleId: string, featurePermissionId: string) => Promise<void>;
}) {
  const [orgFilter, setOrgFilter] = useState<string | null>(null);

  // Group by org
  const byOrg: Record<string, RoleResponse[]> = {};
  for (const r of roles) {
    const key = r.scope_org_id ?? "__platform__";
    (byOrg[key] ??= []).push(r);
  }
  const orgIds = Object.keys(byOrg).sort((a, b) => {
    const na = orgNames[a] ?? a;
    const nb = orgNames[b] ?? b;
    return na.localeCompare(nb);
  });

  const filteredOrgIds = orgFilter ? orgIds.filter(id => id === orgFilter) : orgIds;

  if (roles.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Building2 className="w-8 h-8 mx-auto mb-3 opacity-40" />
        <p className="text-sm">No custom roles yet.</p>
        <p className="text-xs mt-1">Org admins can create custom roles scoped to their organization.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Org filter pills */}
      {orgIds.length > 1 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-muted-foreground">Filter by org:</span>
          <button
            onClick={() => setOrgFilter(null)}
            className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
              orgFilter === null
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border text-muted-foreground hover:border-primary/40 hover:text-foreground"
            }`}
          >
            All orgs
          </button>
          {orgIds.map(id => (
            <button
              key={id}
              onClick={() => setOrgFilter(id === orgFilter ? null : id)}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors flex items-center gap-1 ${
                orgFilter === id
                  ? "bg-blue-500 text-white border-blue-500"
                  : "border-border text-muted-foreground hover:border-blue-400 hover:text-foreground"
              }`}
            >
              <Building2 className="w-3 h-3" />
              {orgNames[id] ?? id.slice(0, 8)}
            </button>
          ))}
        </div>
      )}

      {/* Per-org sections */}
      {filteredOrgIds.map(orgId => {
        const orgRoles = byOrg[orgId] ?? [];
        const orgName = orgNames[orgId] ?? orgId.slice(0, 8);
        return (
          <div key={orgId} className="space-y-2">
            <div className="flex items-center gap-2 py-1">
              <Building2 className="w-3.5 h-3.5 text-blue-500 shrink-0" />
              <span className="text-sm font-semibold text-foreground">{orgName}</span>
              <span className="text-xs text-muted-foreground">({orgRoles.length} role{orgRoles.length !== 1 ? "s" : ""})</span>
              <div className="flex-1 h-px bg-border" />
            </div>
            <div className="space-y-2 pl-2">
              {orgRoles.map(r => (
                <RoleRow
                  key={r.id}
                  role={r}
                  allPermissions={allPermissions}
                  flagNameMap={flagNameMap}
                  orgNames={orgNames}
                  onUpdate={onUpdate}
                  onDelete={onDelete}
                  onDuplicate={onDuplicate}
                  onAssignPermission={onAssignPermission}
                  onRevokePermission={onRevokePermission}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AdminRolesPage() {
  const [roles, setRoles] = useState<RoleResponse[]>([]);
  const [levels, setLevels] = useState<RoleLevelResponse[]>([]);
  const [allPermissions, setAllPermissions] = useState<FeaturePermissionResponse[]>([]);
  const [flagNameMap, setFlagNameMap] = useState<Record<string, string>>({});
  const [orgNames, setOrgNames] = useState<ScopeNames>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showCustom, setShowCustom] = useState(false);
  const [search, setSearch] = useState("");

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true);
    setError(null);
    try {
      const [rolesRes, flagsRes] = await Promise.all([listRoles(), listFeatureFlags()]);
      setRoles(rolesRes.roles);
      setLevels(rolesRes.levels);
      setAllPermissions(flagsRes.flags.flatMap(f => f.permissions));
      setFlagNameMap(Object.fromEntries(flagsRes.flags.map(f => [f.code, f.name])));
    } catch (e) { setError((e as Error).message); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Load org names for scope resolution (best-effort)
  useEffect(() => {
    listOrgs().then(orgs => {
      const map: ScopeNames = {};
      for (const o of orgs) map[o.id] = o.name;
      setOrgNames(map);
    }).catch(() => {});
  }, []);

  const handleUpdate = useCallback((updated: RoleResponse) => {
    setRoles(prev => prev.map(r => r.id === updated.id ? updated : r));
  }, []);

  const handleCreated = useCallback((r: RoleResponse) => {
    setRoles(prev => [...prev, r]);
  }, []);

  const handleDelete = useCallback((roleId: string) => {
    setRoles(prev => prev.filter(r => r.id !== roleId));
  }, []);

  const handleDuplicate = useCallback(async (original: RoleResponse) => {
    const suffix = "_copy";
    let newCode = original.code + suffix;
    // Ensure unique code
    const existingCodes = new Set(roles.map(r => r.code));
    let i = 1;
    while (existingCodes.has(newCode)) { newCode = original.code + suffix + i; i++; }
    const created = await createRole({
      code: newCode,
      name: `${original.name} (Copy)`,
      description: original.description,
      role_level_code: original.role_level_code,
    });
    // Assign all same permissions
    for (const p of original.permissions) {
      try {
        await assignPermissionToRole(created.id, p.feature_permission_id);
      } catch { /* skip duplicates */ }
    }
    // Reload to get the full role with permissions
    const [rolesRes] = await Promise.all([listRoles()]);
    setRoles(rolesRes.roles);
  }, [roles]);

  const handleAssignPermission = useCallback(async (roleId: string, permId: string) => {
    const updated = await assignPermissionToRole(roleId, permId);
    setRoles(prev => prev.map(r => r.id === roleId ? updated : r));
  }, []);

  const handleRevokePermission = useCallback(async (roleId: string, featurePermissionId: string) => {
    await revokePermissionFromRole(roleId, featurePermissionId);
    setRoles(prev => prev.map(r =>
      r.id === roleId ? { ...r, permissions: r.permissions.filter(p => p.feature_permission_id !== featurePermissionId) } : r
    ));
  }, []);

  // Partition: platform (unscoped), custom (non-system + scoped), system-scoped (hidden)
  const platformRoles = roles.filter(r => !r.scope_org_id && !r.scope_workspace_id);
  const customScopedRoles = roles.filter(r => !r.is_system && (r.scope_org_id || r.scope_workspace_id));
  // system-scoped roles (org_admin, workspace_admin, etc.) — never shown in admin UI

  const activeRoles = showCustom ? customScopedRoles : platformRoles;

  const filtered = search.trim()
    ? activeRoles.filter(r => r.name.toLowerCase().includes(search.toLowerCase()) || r.code.toLowerCase().includes(search.toLowerCase()))
    : activeRoles;

  const LEVEL_ORDER = ["super_admin", "platform", "org", "workspace"];
  const rolesByLevel = Object.fromEntries(LEVEL_ORDER.map(lc => [lc, filtered.filter(r => r.role_level_code === lc)]));

  const platformCount = platformRoles.length;
  const customCount = customScopedRoles.length;
  const disabledRoles = roles.filter(r => r.is_disabled).length;
  const totalPermissions = platformRoles.reduce((s, r) => s + r.permissions.length, 0);

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Roles</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Platform governance roles and custom org roles — assign feature permissions by scope level
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
          <Button onClick={() => setShowCreate(true)} size="sm" className="h-8 px-3 shrink-0">
            <Plus className="w-3.5 h-3.5 mr-1" /> New Role
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Platform Roles",    value: platformCount,    icon: Globe,      borderCls: "border-l-violet-500", iconCls: "text-violet-500", numCls: "text-violet-600 dark:text-violet-400" },
          { label: "Custom Roles",      value: customCount,      icon: Building2,  borderCls: "border-l-blue-500",   iconCls: "text-blue-500",   numCls: "text-blue-600 dark:text-blue-400" },
          { label: "Disabled",          value: disabledRoles,    icon: Ban,        borderCls: "border-l-muted-foreground", iconCls: "text-muted-foreground", numCls: "text-foreground" },
          { label: "Total Permissions", value: totalPermissions, icon: ShieldPlus, borderCls: "border-l-emerald-500", iconCls: "text-emerald-500", numCls: "text-emerald-600 dark:text-emerald-400" },
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

      {/* View toggle + search filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3">
        <div className="flex items-center gap-3 flex-wrap">
          {/* View toggle */}
          <div className="flex items-center gap-1 p-1 rounded-xl border border-border bg-muted/30 w-fit shrink-0">
            <button
              onClick={() => { setShowCustom(false); setSearch(""); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                !showCustom
                  ? "bg-background text-foreground shadow-sm border border-border"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Globe className="w-4 h-4" />
              Platform Roles
            </button>
            <button
              onClick={() => { setShowCustom(true); setSearch(""); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                showCustom
                  ? "bg-background text-foreground shadow-sm border border-border"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Building2 className="w-4 h-4" />
              Custom Roles
              {customCount > 0 && (
                <span className={`text-xs px-1.5 py-0.5 rounded-full font-semibold ${
                  showCustom ? "bg-blue-500 text-white" : "bg-muted text-muted-foreground"
                }`}>
                  {customCount}
                </span>
              )}
            </button>
          </div>

          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
            <Input
              className="pl-9 h-9"
              placeholder="Search roles by name or code..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Context note */}
      {!showCustom && (
        <p className="text-xs text-muted-foreground">
          Platform roles are global governance roles. System-provisioned org/workspace roles (e.g. org_admin, workspace_admin) are managed automatically — not shown here.
        </p>
      )}
      {showCustom && (
        <p className="text-xs text-muted-foreground">
          Custom roles are created by org admins, scoped to their organization.
        </p>
      )}

      {/* Permission legend (platform only) */}
      {!showCustom && (
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="font-medium">Permissions:</span>
          <span className="flex items-center gap-1 text-primary">
            <CheckSquare className="w-3 h-3" /> Assigned — click to revoke
          </span>
          <span className="flex items-center gap-1">
            <Square className="w-3 h-3" /> Not assigned — click to grant
          </span>
          <span className="flex items-center gap-1 ml-2 text-amber-600">
            <Lock className="w-3 h-3" /> System (read-only)
          </span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => <Skeleton key={i} />)}
        </div>
      )}

      {/* Roles */}
      {!loading && !error && (
        <div className="space-y-6">
          {showCustom ? (
            <CustomRolesSection
              roles={filtered}
              allPermissions={allPermissions}
              flagNameMap={flagNameMap}
              orgNames={orgNames}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
              onDuplicate={handleDuplicate}
              onAssignPermission={handleAssignPermission}
              onRevokePermission={handleRevokePermission}
            />
          ) : search.trim() ? (
            filtered.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No roles match &quot;{search}&quot;</p>
            ) : (
              <div className="space-y-2">
                {filtered.map(r => (
                  <RoleRow
                    key={r.id}
                    role={r}
                    allPermissions={allPermissions}
                    flagNameMap={flagNameMap}
                    orgNames={orgNames}
                    onUpdate={handleUpdate}
                    onDelete={handleDelete}
                    onDuplicate={handleDuplicate}
                    onAssignPermission={handleAssignPermission}
                    onRevokePermission={handleRevokePermission}
                  />
                ))}
              </div>
            )
          ) : (
            levels.map(lvl => (
              <LevelSection
                key={lvl.code}
                level={lvl}
                roles={rolesByLevel[lvl.code] ?? []}
                allPermissions={allPermissions}
                flagNameMap={flagNameMap}
                orgNames={orgNames}
                onUpdate={handleUpdate}
                onDelete={handleDelete}
                onDuplicate={handleDuplicate}
                onAssignPermission={handleAssignPermission}
                onRevokePermission={handleRevokePermission}
              />
            ))
          )}
        </div>
      )}

      {/* Create dialog */}
      {showCreate && (
        <CreateRoleDialog
          levels={levels}
          onCreated={handleCreated}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  );
}
