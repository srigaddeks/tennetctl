"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Badge,
  Button,
  Input,
} from "@kcontrol/ui";
import {
  Users,
  Shield,
  UserPlus,
  RefreshCw,
  Trash2,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Building2,
  FileText,
  Briefcase,
  Search,
} from "lucide-react";
import {
  getGrcTeam,
  assignGrcRole,
  revokeGrcRole,
  listAccessGrants,
  createAccessGrant,
  revokeAccessGrant,
} from "@/lib/api/grcRoles";
import type { GrcTeamMember, GrcTeamResponse, GrcAccessGrant } from "@/lib/api/grcRoles";
import { createInvitation, listInvitations, revokeInvitation, resendInvitation } from "@/lib/api/invitations";
import type { InvitationResponse } from "@/lib/api/invitations";
import { listOrgMembers } from "@/lib/api/orgs";
import type { OrgMemberResponse } from "@/lib/types/orgs";
import { engagementsApi } from "@/lib/api/engagements";
import { listDeployments } from "@/lib/api/grc";
import { Mail } from "lucide-react";

// ── Constants ─────────────────────────────────────────────────────────────────

const GRC_ROLES = [
  { code: "grc_practitioner", label: "GRC Practitioner", group: "internal" as const },
  { code: "grc_engineer", label: "Engineer", group: "internal" as const },
  { code: "grc_ciso", label: "CISO / Exec", group: "internal" as const },
  { code: "grc_lead_auditor", label: "Lead Auditor", group: "auditor" as const },
  { code: "grc_staff_auditor", label: "Staff Auditor", group: "auditor" as const },
  { code: "grc_vendor", label: "Vendor", group: "vendor" as const },
] as const;

function grcRoleLabel(code: string): string {
  return GRC_ROLES.find((r) => r.code === code)?.label ?? code;
}

function grcRoleBadgeClass(code: string): string {
  switch (code) {
    case "grc_practitioner": return "bg-purple-500/10 text-purple-700 border-purple-500/20";
    case "grc_engineer": return "bg-green-500/10 text-green-600 border-green-500/20";
    case "grc_ciso": return "bg-indigo-500/10 text-indigo-700 border-indigo-500/20";
    case "grc_lead_auditor": return "bg-amber-500/10 text-amber-700 border-amber-500/20";
    case "grc_staff_auditor": return "bg-amber-500/10 text-amber-600 border-amber-500/20";
    case "grc_vendor": return "bg-stone-500/10 text-stone-600 border-stone-500/20";
    default: return "bg-muted text-muted-foreground border-border";
  }
}

function scopeIcon(type: string) {
  switch (type) {
    case "workspace": return <Building2 className="h-3 w-3" />;
    case "framework": return <FileText className="h-3 w-3" />;
    case "engagement": return <Briefcase className="h-3 w-3" />;
    default: return <Shield className="h-3 w-3" />;
  }
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface GrcTeamPanelProps {
  orgId: string;
  workspaceId?: string;
  engagementId?: string;
  onAssignRole?: () => void;
}

interface WorkspaceOption {
  id: string;
  name: string;
}

// ── Member Card ───────────────────────────────────────────────────────────────

interface ScopeOption { id: string; name: string; type: "framework" | "engagement" }

function MemberCard({
  member,
  orgId,
  scopeOptions,
  onRevoke,
  onGrantAccess,
  onRevokeGrant,
  onChangeRole,
  revoking,
  changingRole,
}: {
  member: GrcTeamMember;
  orgId: string;
  scopeOptions: ScopeOption[];
  onRevoke: (id: string) => void;
  onGrantAccess: (assignmentId: string, scopeType: string, scopeId: string) => void;
  onRevokeGrant: (assignmentId: string, grantId: string) => void;
  onChangeRole: (member: GrcTeamMember, newRole: string) => void;
  revoking: string | null;
  changingRole: string | null;
}) {
  const [expanded, setExpanded] = useState(false);
  const [addingGrant, setAddingGrant] = useState(false);
  const [selectedScopeId, setSelectedScopeId] = useState("");
  const [editingRole, setEditingRole] = useState(false);
  const initials = (member.display_name ?? member.email ?? "?")[0].toUpperCase();

  async function submitGrant() {
    if (!selectedScopeId) return;
    const opt = scopeOptions.find(o => o.id === selectedScopeId);
    if (!opt) return;
    await onGrantAccess(member.assignment_id, opt.type, opt.id);
    setAddingGrant(false);
    setSelectedScopeId("");
  }

  return (
    <div className="rounded-lg border border-border bg-card p-3 space-y-2">
      {/* Header row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary shrink-0">
            {initials}
          </div>
          <div className="min-w-0">
            <div className="font-medium text-sm truncate">
              {member.display_name ?? member.email ?? "Unknown"}
            </div>
            {member.display_name && member.email && (
              <div className="text-xs text-muted-foreground truncate">{member.email}</div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {editingRole ? (
            <select
              autoFocus
              className="h-6 rounded border border-border bg-background text-xs px-1.5 focus:outline-none focus:ring-1 focus:ring-ring"
              defaultValue={member.grc_role_code}
              disabled={changingRole === member.assignment_id}
              onChange={e => { onChangeRole(member, e.target.value); setEditingRole(false); }}
              onBlur={() => setEditingRole(false)}
            >
              <optgroup label="Internal">
                {GRC_ROLES.filter(r => r.group === "internal").map(r => (
                  <option key={r.code} value={r.code}>{r.label}</option>
                ))}
              </optgroup>
              <optgroup label="Auditors">
                {GRC_ROLES.filter(r => r.group === "auditor").map(r => (
                  <option key={r.code} value={r.code}>{r.label}</option>
                ))}
              </optgroup>
              <optgroup label="Vendors">
                {GRC_ROLES.filter(r => r.group === "vendor").map(r => (
                  <option key={r.code} value={r.code}>{r.label}</option>
                ))}
              </optgroup>
            </select>
          ) : (
            <button
              className={`text-xs px-1.5 py-0.5 rounded border transition-colors ${grcRoleBadgeClass(member.grc_role_code)} hover:opacity-80`}
              onClick={() => setEditingRole(true)}
              title="Click to change role"
              disabled={changingRole === member.assignment_id}
            >
              {changingRole === member.assignment_id ? (
                <RefreshCw className="h-3 w-3 animate-spin" />
              ) : (
                grcRoleLabel(member.grc_role_code)
              )}
            </button>
          )}
          <button
            className="flex items-center gap-0.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-1 py-0.5 rounded hover:bg-muted"
            onClick={() => setExpanded(!expanded)}
            title="Manage access scopes"
          >
            {member.grants.length === 0 ? (
              <span className="text-emerald-600 font-medium">All Frameworks</span>
            ) : (
              <span>{member.grants.length} scope{member.grants.length !== 1 ? "s" : ""}</span>
            )}
            {expanded ? <ChevronDown className="h-3 w-3 ml-0.5" /> : <ChevronRight className="h-3 w-3 ml-0.5" />}
          </button>
          <button
            className="p-1 rounded text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-colors"
            onClick={() => onRevoke(member.assignment_id)}
            disabled={revoking === member.assignment_id}
            title="Revoke role"
          >
            {revoking === member.assignment_id ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Trash2 className="h-3.5 w-3.5" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded scope management */}
      {expanded && (
        <div className="pl-2 space-y-1.5 pt-1.5 border-t border-border/50">
          {member.grants.length === 0 ? (
            <p className="text-xs text-muted-foreground italic">
              No scope restrictions — user sees all frameworks & engagements.
            </p>
          ) : (
            member.grants.map((g) => (
              <div key={g.id} className="flex items-center justify-between gap-2 text-xs py-0.5 rounded px-1.5 bg-muted/30">
                <div className="flex items-center gap-1.5 text-muted-foreground min-w-0">
                  {scopeIcon(g.scope_type)}
                  <span className="capitalize text-[10px] font-semibold uppercase tracking-wide">{g.scope_type}</span>
                  <span className="text-foreground font-medium truncate">{g.scope_name ?? g.scope_id.slice(0, 8)}</span>
                </div>
                <button
                  className="text-muted-foreground hover:text-red-500 transition-colors p-0.5 shrink-0"
                  onClick={() => onRevokeGrant(member.assignment_id, g.id)}
                  title="Remove this scope"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))
          )}

          {/* Add scope row */}
          {addingGrant ? (
            <div className="flex items-center gap-1.5 pt-0.5">
              <select
                className="flex-1 h-7 rounded border border-border bg-background text-xs px-2 focus:outline-none focus:ring-1 focus:ring-ring"
                value={selectedScopeId}
                onChange={e => setSelectedScopeId(e.target.value)}
              >
                <option value="">Select framework or engagement…</option>
                {scopeOptions.filter(o => o.type === "framework").length > 0 && (
                  <optgroup label="Frameworks">
                    {scopeOptions.filter(o => o.type === "framework").map(o => (
                      <option key={o.id} value={o.id}>{o.name}</option>
                    ))}
                  </optgroup>
                )}
                {scopeOptions.filter(o => o.type === "engagement").length > 0 && (
                  <optgroup label="Engagements">
                    {scopeOptions.filter(o => o.type === "engagement").map(o => (
                      <option key={o.id} value={o.id}>{o.name}</option>
                    ))}
                  </optgroup>
                )}
              </select>
              <button
                className="h-7 px-2 rounded bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 disabled:opacity-50"
                onClick={submitGrant}
                disabled={!selectedScopeId}
              >
                Add
              </button>
              <button
                className="h-7 px-2 rounded border border-border text-xs hover:bg-muted"
                onClick={() => { setAddingGrant(false); setSelectedScopeId(""); }}
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors py-0.5"
              onClick={() => setAddingGrant(true)}
            >
              <UserPlus className="h-3 w-3" />
              Add scope restriction
            </button>
          )}
        </div>
      )}

      <div className="text-[10px] text-muted-foreground">
        Assigned {new Date(member.assigned_at).toLocaleDateString()}
      </div>
    </div>
  );
}

// ── Role Group Section ────────────────────────────────────────────────────────

function RoleGroupSection({
  title,
  members,
  orgId,
  badgeClass,
  scopeOptions,
  onRevoke,
  onGrantAccess,
  onRevokeGrant,
  onChangeRole,
  revoking,
  changingRole,
}: {
  title: string;
  members: GrcTeamMember[];
  orgId: string;
  badgeClass: string;
  scopeOptions: ScopeOption[];
  onRevoke: (id: string) => void;
  onGrantAccess: (assignmentId: string, scopeType: string, scopeId: string) => void;
  onRevokeGrant: (assignmentId: string, grantId: string) => void;
  onChangeRole: (member: GrcTeamMember, newRole: string) => void;
  revoking: string | null;
  changingRole: string | null;
}) {
  if (members.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</h4>
        <Badge variant="outline" className={`text-[10px] ${badgeClass}`}>
          {members.length}
        </Badge>
      </div>
      <div className="grid gap-2">
        {members.map((m) => (
          <MemberCard
            key={m.assignment_id}
            member={m}
            orgId={orgId}
            scopeOptions={scopeOptions}
            onRevoke={onRevoke}
            onGrantAccess={onGrantAccess}
            onRevokeGrant={onRevokeGrant}
            onChangeRole={onChangeRole}
            revoking={revoking}
            changingRole={changingRole}
          />
        ))}
      </div>
    </div>
  );
}

// ── Shared role selector ──────────────────────────────────────────────────────

function RoleSelector({ value, onChange, className }: { value: string; onChange: (v: string) => void; className?: string }) {
  return (
    <select
      className={`h-8 rounded border border-border bg-background text-xs px-2 focus:outline-none focus:ring-1 focus:ring-ring ${className ?? "w-full"}`}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <optgroup label="Internal Team">
        {GRC_ROLES.filter((r) => r.group === "internal").map((r) => (
          <option key={r.code} value={r.code}>{r.label}</option>
        ))}
      </optgroup>
      <optgroup label="Auditors">
        {GRC_ROLES.filter((r) => r.group === "auditor").map((r) => (
          <option key={r.code} value={r.code}>{r.label}</option>
        ))}
      </optgroup>
      <optgroup label="Vendors">
        {GRC_ROLES.filter((r) => r.group === "vendor").map((r) => (
          <option key={r.code} value={r.code}>{r.label}</option>
        ))}
      </optgroup>
    </select>
  );
}

// ── Scope selector (framework/engagement multi-select) ────────────────────────

interface ScopeTarget { id: string; name: string }

interface ScopeSelection {
  type: "all_frameworks" | "specific_frameworks" | "specific_engagements";
  selectedIds: string[];
}

function ScopeSelector({
  orgId,
  selection,
  onChange,
}: {
  orgId: string;
  selection: ScopeSelection;
  onChange: (s: ScopeSelection) => void;
}) {
  const [frameworks, setFrameworks] = useState<ScopeTarget[]>([]);
  const [engagements, setEngagements] = useState<ScopeTarget[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    (async () => {
      try {
        const [engs, depsRes] = await Promise.all([
          engagementsApi.list(orgId).catch(() => []),
          (listDeployments(orgId) as unknown as Promise<{ items: Array<{ id: string; framework_name?: string; deployment_name?: string }> }>).catch(() => ({ items: [] })),
        ]);
        setEngagements(engs.map((e) => ({ id: e.id, name: e.engagement_name ?? e.engagement_code })));
        // Deduplicate frameworks by name (multiple deployments of same framework)
        const seen = new Set<string>();
        const uniqueFrameworks: ScopeTarget[] = [];
        for (const d of depsRes.items ?? []) {
          const name = d.framework_name ?? d.deployment_name ?? d.id.slice(0, 8);
          if (!seen.has(name)) {
            seen.add(name);
            uniqueFrameworks.push({ id: d.id, name });
          }
        }
        setFrameworks(uniqueFrameworks);
      } catch { /* ignore */ }
      finally { setLoading(false); }
    })();
  }, [orgId]);

  function toggleId(id: string) {
    const ids = selection.selectedIds.includes(id)
      ? selection.selectedIds.filter((x) => x !== id)
      : [...selection.selectedIds, id];
    onChange({ ...selection, selectedIds: ids });
  }

  const targets = selection.type === "specific_frameworks" ? frameworks
    : selection.type === "specific_engagements" ? engagements
    : [];

  return (
    <div className="space-y-2">
      <select
        className="h-8 w-full rounded border border-border bg-background text-xs px-2 focus:outline-none focus:ring-1 focus:ring-ring"
        value={selection.type}
        onChange={(e) => onChange({ type: e.target.value as ScopeSelection["type"], selectedIds: [] })}
        title="Access scope"
      >
        <option value="all_frameworks">All Frameworks & Engagements</option>
        <option value="specific_frameworks">Specific Frameworks</option>
        <option value="specific_engagements">Specific Engagements</option>
      </select>

      {selection.type !== "all_frameworks" && (
        <div className="rounded-lg border border-border bg-background max-h-36 overflow-y-auto">
          {loading ? (
            <div className="px-3 py-2 text-xs text-muted-foreground">Loading...</div>
          ) : targets.length === 0 ? (
            <div className="px-3 py-2 text-xs text-muted-foreground">
              No {selection.type === "specific_frameworks" ? "frameworks" : "engagements"} found
            </div>
          ) : (
            targets.map((t) => (
              <label
                key={t.id}
                className="flex items-center gap-2 px-3 py-1.5 hover:bg-muted/50 cursor-pointer text-xs transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selection.selectedIds.includes(t.id)}
                  onChange={() => toggleId(t.id)}
                  className="rounded border-border"
                />
                <span className="truncate">{t.name}</span>
              </label>
            ))
          )}
        </div>
      )}

      {selection.selectedIds.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selection.selectedIds.map((id) => {
            const target = targets.find((t) => t.id === id);
            return (
              <Badge key={id} variant="secondary" className="text-[10px] gap-1">
                {target?.name ?? id.slice(0, 8)}
                <button className="hover:text-red-500" onClick={() => toggleId(id)}>x</button>
              </Badge>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Add/Invite Panel ──────────────────────────────────────────────────────────

function AddMemberPanel({
  orgId,
  workspaceId,
  scopeOptions,
  onDone,
}: {
  orgId: string;
  workspaceId?: string;
  scopeOptions: ScopeOption[];
  onDone: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"add" | "invite">("add");

  // Shared state
  const [roleCode, setRoleCode] = useState("grc_practitioner");
  const [scope, setScope] = useState<ScopeSelection>({ type: "all_frameworks", selectedIds: [] });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Add member state
  const [userId, setUserId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Array<{ user_id: string; email?: string | null; display_name?: string | null }>>([]);
  const [showDropdown, setShowDropdown] = useState(false);

  // Invite state
  const [inviteEmail, setInviteEmail] = useState("");

  // Pending invitations
  const [pendingInvites, setPendingInvites] = useState<InvitationResponse[]>([]);
  const [revokingInvite, setRevokingInvite] = useState<string | null>(null);

  // Load pending invitations when panel opens
  useEffect(() => {
    if (!open) return;
    (async () => {
      try {
        const invites = await listInvitations({ scope: "workspace", org_id: orgId, status: "pending" });
        setPendingInvites(invites.filter((i) => i.grc_role_code));
      } catch { setPendingInvites([]); }
    })();
  }, [open, orgId]);

  // User search for "Add member" mode
  useEffect(() => {
    if (mode !== "add" || !searchQuery.trim() || !open) {
      setSearchResults([]); setShowDropdown(false); return;
    }
    const timer = setTimeout(async () => {
      try {
        const { listAdminUsers } = await import("@/lib/api/admin");
        const res = await listAdminUsers({ search: searchQuery, limit: 8, org_id: orgId });
        setSearchResults(res?.users ?? []);
        setShowDropdown(true);
      } catch { setSearchResults([]); }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, orgId, open, mode]);

  function reset() {
    setUserId(""); setSearchQuery(""); setInviteEmail("");
    setError(null); setSuccess(null);
    setScope({ type: "all_frameworks", selectedIds: [] });
  }

  async function handleAddMember() {
    if (!userId) return;
    setSubmitting(true); setError(null); setSuccess(null);
    try {
      const assignment = await assignGrcRole(orgId, { user_id: userId, grc_role_code: roleCode });
      // Create access grants for selected scopes
      const grantType = scope.type === "specific_frameworks" ? "framework" : scope.type === "specific_engagements" ? "engagement" : null;
      if (grantType && scope.selectedIds.length > 0) {
        for (const sid of scope.selectedIds) {
          await createAccessGrant(orgId, assignment.id, { scope_type: grantType, scope_id: sid });
        }
      }
      reset();
      setOpen(false);
      onDone();
    } catch (e) { setError((e as Error).message); }
    finally { setSubmitting(false); }
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setSubmitting(true); setError(null); setSuccess(null);
    try {
      // For specific scopes, create one invitation per selected item
      // For all_frameworks, create a single org-scoped invitation
      const inviteScope = workspaceId ? "workspace" : "organization";
      const inviteRole = workspaceId ? "viewer" : "member";
      await createInvitation({
        email: inviteEmail.trim(),
        scope: inviteScope,
        org_id: orgId,
        workspace_id: workspaceId,
        role: inviteRole,
        grc_role_code: roleCode,
        framework_ids: scope.type === "specific_frameworks" && scope.selectedIds.length > 0 ? scope.selectedIds : undefined,
        engagement_ids: scope.type === "specific_engagements" && scope.selectedIds.length > 0 ? scope.selectedIds : undefined,
      });

      const scopeLabel = scope.type === "all_frameworks"
        ? "all frameworks"
        : `${scope.selectedIds.length} ${scope.type === "specific_frameworks" ? "framework" : "engagement"}${scope.selectedIds.length !== 1 ? "s" : ""}`;
      setSuccess(`Invitation sent to ${inviteEmail.trim()} as ${grcRoleLabel(roleCode)} (${scopeLabel})`);
      setInviteEmail("");
      // Refresh pending invites
      const invites = await listInvitations({ org_id: orgId, status: "pending" });
      setPendingInvites(invites.filter((i) => i.grc_role_code));
    } catch (e) { setError((e as Error).message); }
    finally { setSubmitting(false); }
  }

  async function handleRevokeInvite(inviteId: string) {
    setRevokingInvite(inviteId);
    try {
      await revokeInvitation(inviteId);
      setPendingInvites((prev) => prev.filter((i) => i.id !== inviteId));
    } catch (e) { setError((e as Error).message); }
    finally { setRevokingInvite(null); }
  }

  if (!open) {
    return (
      <div className="flex items-center gap-2">
        <Button size="sm" variant="outline" className="gap-1.5" onClick={() => { setMode("add"); setOpen(true); reset(); }}>
          <UserPlus className="h-3.5 w-3.5" />
          Add Member
        </Button>
        <Button size="sm" variant="outline" className="gap-1.5" onClick={() => { setMode("invite"); setOpen(true); reset(); }}>
          <Mail className="h-3.5 w-3.5" />
          Invite by Email
        </Button>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-muted/20 p-3 space-y-3">
      {/* Mode toggle + cancel */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 bg-muted/40 rounded-lg p-0.5">
          <button
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${mode === "add" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            onClick={() => { setMode("add"); reset(); }}
          >
            <UserPlus className="h-3 w-3 inline mr-1" />Add Member
          </button>
          <button
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${mode === "invite" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            onClick={() => { setMode("invite"); reset(); }}
          >
            <Mail className="h-3 w-3 inline mr-1" />Invite by Email
          </button>
        </div>
        <button className="text-muted-foreground hover:text-foreground text-xs" onClick={() => setOpen(false)}>Cancel</button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5">
          <AlertCircle className="h-3 w-3 text-red-500 shrink-0" />
          <p className="text-xs text-red-500">{error}</p>
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-1.5">
          <Shield className="h-3 w-3 text-green-500 shrink-0" />
          <p className="text-xs text-green-600">{success}</p>
        </div>
      )}

      <div className="space-y-2">
        {/* Mode: Add existing member */}
        {mode === "add" && (
          <div className="relative">
            <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-muted-foreground" />
            <Input
              className="pl-8 h-8 text-sm"
              placeholder="Search org members..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setUserId(""); }}
            />
            {showDropdown && searchResults.length > 0 && (
              <div className="absolute z-50 top-full mt-1 w-full rounded-lg border border-border bg-popover shadow-lg overflow-hidden max-h-48 overflow-y-auto">
                {searchResults.map((u) => (
                  <button
                    key={u.user_id}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors flex items-center gap-2"
                    onClick={() => { setUserId(u.user_id); setSearchQuery(u.display_name ?? u.email ?? u.user_id); setShowDropdown(false); }}
                  >
                    <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium text-primary shrink-0">
                      {(u.email ?? u.display_name ?? "?")[0].toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      {u.display_name && <div className="text-xs font-medium truncate">{u.display_name}</div>}
                      {u.email && <div className="text-xs text-muted-foreground truncate">{u.email}</div>}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Mode: Invite by email */}
        {mode === "invite" && (
          <Input
            type="email"
            className="h-8 text-sm"
            placeholder="user@domain.com"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
        )}

        {/* GRC Role selector */}
        <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">GRC Role</p>
        <RoleSelector value={roleCode} onChange={setRoleCode} />

        {/* Scope selector */}
        <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Access Scope</p>
        <ScopeSelector
          orgId={orgId}
          selection={scope}
          onChange={setScope}
        />

        {/* Submit */}
        {mode === "add" ? (
          <Button size="sm" className="w-full h-8" disabled={!userId || submitting} onClick={handleAddMember}>
            {submitting ? <RefreshCw className="h-3 w-3 animate-spin mr-1.5" /> : <UserPlus className="h-3 w-3 mr-1.5" />}
            Add as {grcRoleLabel(roleCode)}
          </Button>
        ) : (
          <Button size="sm" className="w-full h-8" disabled={!inviteEmail.trim() || submitting} onClick={(e) => handleInvite(e as unknown as React.FormEvent)}>
            {submitting ? <RefreshCw className="h-3 w-3 animate-spin mr-1.5" /> : <Mail className="h-3 w-3 mr-1.5" />}
            Send Invite as {grcRoleLabel(roleCode)}
          </Button>
        )}
      </div>

      {/* Pending GRC invitations */}
      {pendingInvites.length > 0 && (
        <div className="space-y-1.5 pt-2 border-t border-border/50">
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
            Pending Invitations ({pendingInvites.length})
          </p>
          {pendingInvites.map((inv) => {
            const fwIds = inv.framework_ids ?? (inv.framework_id ? [inv.framework_id] : []);
            const engIds = inv.engagement_ids ?? (inv.engagement_id ? [inv.engagement_id] : []);
            const fwNames = fwIds.map(id => scopeOptions.find(o => o.id === id)?.name ?? id.slice(0, 8));
            const engNames = engIds.map(id => scopeOptions.find(o => o.id === id)?.name ?? id.slice(0, 8));
            const hasScope = fwNames.length > 0 || engNames.length > 0;
            const scopeLabel = fwNames.length > 0 ? fwNames.join(", ") : engNames.length > 0 ? engNames.join(", ") : "All Frameworks";
            return (
              <div key={inv.id} className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-2 py-1.5 space-y-0.5">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <Mail className="h-3 w-3 text-amber-600 shrink-0" />
                    <span className="text-xs text-amber-700 truncate">{inv.email}</span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Badge variant="outline" className={`text-[10px] ${grcRoleBadgeClass(inv.grc_role_code ?? "")}`}>
                      {grcRoleLabel(inv.grc_role_code ?? "")}
                    </Badge>
                    <button
                      className="p-0.5 text-muted-foreground hover:text-red-500 transition-colors"
                      onClick={() => handleRevokeInvite(inv.id)}
                      disabled={revokingInvite === inv.id}
                      title="Revoke invitation"
                    >
                      {revokingInvite === inv.id ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-1 pl-5 text-[10px]">
                  {fwNames.length > 0 ? <FileText className="h-2.5 w-2.5 shrink-0 text-muted-foreground" /> : engNames.length > 0 ? <Briefcase className="h-2.5 w-2.5 shrink-0 text-muted-foreground" /> : null}
                  <span className={hasScope ? "text-foreground font-medium" : "text-emerald-600 font-medium"}>
                    {scopeLabel}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Main Panel ────────────────────────────────────────────────────────────────

export function GrcTeamPanel({ orgId, workspaceId, engagementId }: GrcTeamPanelProps) {
  const [team, setTeam] = useState<GrcTeamResponse | null>(null);
  const [orgMembers, setOrgMembers] = useState<OrgMemberResponse[]>([]);
  const [showOrgMembers, setShowOrgMembers] = useState(false);
  const [scopeOptions, setScopeOptions] = useState<ScopeOption[]>([]);
  const [invitations, setInvitations] = useState<InvitationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [changingRole, setChangingRole] = useState<string | null>(null); // assignment_id being changed
  const [resendingInvite, setResendingInvite] = useState<string | null>(null);
  const [revokingInvite, setRevokingInvite] = useState<string | null>(null);
  const [resentLink, setResentLink] = useState<{ inviteId: string; email: string; url: string } | null>(null);

  const loadTeam = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, members, engs, depsRes, allInvites] = await Promise.all([
        getGrcTeam(orgId, { workspace_id: workspaceId, engagement_id: engagementId }),
        listOrgMembers(orgId).catch(() => [] as OrgMemberResponse[]),
        engagementsApi.list(orgId).catch(() => [] as Array<{ id: string; engagement_name?: string; engagement_code?: string }>),
        (listDeployments(orgId) as unknown as Promise<{ items: Array<{ id: string; framework_name?: string; deployment_name?: string }> }>).catch(() => ({ items: [] })),
        listInvitations({ org_id: orgId }).catch(() => [] as InvitationResponse[]),
      ]);
      setTeam(data);
      setOrgMembers(members);
      // Show GRC invitations that are pending or expired (not accepted/revoked)
      setInvitations(allInvites.filter(i => i.grc_role_code && (i.status === "pending" || i.status === "expired")));

      // Build deduplicated scope options (frameworks + engagements)
      const opts: ScopeOption[] = [];
      const seenNames = new Set<string>();
      for (const d of depsRes.items ?? []) {
        const name = d.framework_name ?? d.deployment_name ?? d.id.slice(0, 8);
        if (!seenNames.has(name)) {
          seenNames.add(name);
          opts.push({ id: d.id, name, type: "framework" });
        }
      }
      for (const e of engs) {
        const name = (e as { engagement_name?: string; engagement_code?: string; id: string }).engagement_name
          ?? (e as { engagement_code?: string }).engagement_code
          ?? (e as { id: string }).id.slice(0, 8);
        opts.push({ id: (e as { id: string }).id, name, type: "engagement" });
      }
      setScopeOptions(opts);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [orgId, workspaceId, engagementId]);

  useEffect(() => { loadTeam(); }, [loadTeam]);

  // Refresh when window/tab regains focus (e.g. after user accepts invite in another tab)
  useEffect(() => {
    function onFocus() { loadTeam(); }
    function onVisibility() { if (document.visibilityState === "visible") loadTeam(); }
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [loadTeam]);

  async function handleRevoke(assignmentId: string) {
    if (!confirm("Revoke this GRC role? All access grants will also be removed.")) return;
    setRevoking(assignmentId);
    try {
      await revokeGrcRole(orgId, assignmentId);
      await loadTeam();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRevoking(null);
    }
  }

  async function handleGrantAccess(assignmentId: string, scopeType: string, scopeId: string) {
    try {
      await createAccessGrant(orgId, assignmentId, { scope_type: scopeType, scope_id: scopeId });
      await loadTeam();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function handleRevokeGrant(assignmentId: string, grantId: string) {
    try {
      await revokeAccessGrant(orgId, assignmentId, grantId);
      await loadTeam();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function handleChangeRole(member: GrcTeamMember, newRoleCode: string) {
    if (newRoleCode === member.grc_role_code) return;
    setChangingRole(member.assignment_id);
    try {
      // Revoke current, assign new (preserves user_id)
      await revokeGrcRole(orgId, member.assignment_id);
      await assignGrcRole(orgId, { user_id: member.user_id, grc_role_code: newRoleCode });
      await loadTeam();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setChangingRole(null);
    }
  }

  async function handleResendInvite(inviteId: string) {
    setResendingInvite(inviteId);
    setResentLink(null);
    try {
      const result = await resendInvitation(inviteId);
      await loadTeam();
      if (result.invite_token) {
        const acceptUrl = `${window.location.origin}/accept-invite?token=${result.invite_token}`;
        setResentLink({ inviteId, email: result.email, url: acceptUrl });
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setResendingInvite(null);
    }
  }

  async function handleRevokeInviteMain(inviteId: string) {
    setRevokingInvite(inviteId);
    try {
      await revokeInvitation(inviteId);
      await loadTeam();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRevokingInvite(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-3 py-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-16 bg-muted animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">GRC Team</h3>
          {team && (
            <Badge variant="secondary" className="text-xs">
              {team.total} member{team.total !== 1 ? "s" : ""}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" className="h-7 px-2" onClick={loadTeam} title="Refresh">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
          <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
          <p className="text-xs text-red-500">{error}</p>
        </div>
      )}

      {resentLink && (
        <div className="rounded-lg border border-blue-500/30 bg-blue-500/5 px-3 py-2 space-y-1.5">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs text-blue-700 font-medium">
              Email not sent (SMTP not configured). Share this link with <span className="font-semibold">{resentLink.email}</span>:
            </p>
            <button className="text-xs text-muted-foreground hover:text-foreground shrink-0" onClick={() => setResentLink(null)}>✕</button>
          </div>
          <div className="flex items-center gap-1.5">
            <input
              readOnly
              value={resentLink.url}
              className="flex-1 h-7 rounded border border-border bg-background text-xs px-2 font-mono truncate"
              onClick={e => (e.target as HTMLInputElement).select()}
            />
            <button
              className="h-7 px-2 rounded bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 shrink-0"
              onClick={() => { navigator.clipboard.writeText(resentLink.url); }}
            >
              Copy
            </button>
          </div>
        </div>
      )}

      {/* Add member / Invite */}
      <AddMemberPanel orgId={orgId} workspaceId={workspaceId} scopeOptions={scopeOptions} onDone={loadTeam} />

      {/* Team groups */}
      {team && (
        <>
          <RoleGroupSection
            title="Internal Team"
            members={team.internal}
            orgId={orgId}
            badgeClass="bg-purple-500/10 text-purple-600"
            scopeOptions={scopeOptions}
            onRevoke={handleRevoke}
            onGrantAccess={handleGrantAccess}
            onRevokeGrant={handleRevokeGrant}
            onChangeRole={handleChangeRole}
            revoking={revoking}
            changingRole={changingRole}
          />
          <RoleGroupSection
            title="Auditors"
            members={team.auditors}
            orgId={orgId}
            badgeClass="bg-amber-500/10 text-amber-600"
            scopeOptions={scopeOptions}
            onRevoke={handleRevoke}
            onGrantAccess={handleGrantAccess}
            onRevokeGrant={handleRevokeGrant}
            onChangeRole={handleChangeRole}
            revoking={revoking}
            changingRole={changingRole}
          />
          <RoleGroupSection
            title="Vendors"
            members={team.vendors}
            orgId={orgId}
            badgeClass="bg-stone-500/10 text-stone-600"
            scopeOptions={scopeOptions}
            onRevoke={handleRevoke}
            onGrantAccess={handleGrantAccess}
            onRevokeGrant={handleRevokeGrant}
            onChangeRole={handleChangeRole}
            revoking={revoking}
            changingRole={changingRole}
          />
          {team.total === 0 && (
            <div className="text-center py-8 text-muted-foreground text-sm">
              <Users className="h-8 w-8 mx-auto mb-2 opacity-40" />
              <p>No GRC roles assigned yet.</p>
              <p className="text-xs mt-1">Use the button above to assign roles to org members.</p>
            </div>
          )}
        </>
      )}

      {/* Pending Invitations section */}
      {invitations.length > 0 && (
        <div className="border border-border/50 rounded-lg overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2.5 bg-muted/30">
            <Mail className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs font-semibold uppercase tracking-wide">Pending Invitations</span>
            <Badge variant="secondary" className="text-xs h-4 px-1.5">{invitations.length}</Badge>
          </div>
          <div className="divide-y divide-border/30">
            {invitations.map(inv => {
              const fwIds = inv.framework_ids ?? (inv.framework_id ? [inv.framework_id] : []);
              const engIds = inv.engagement_ids ?? (inv.engagement_id ? [inv.engagement_id] : []);
              const fwNames = fwIds.map(id => scopeOptions.find(o => o.id === id)?.name ?? id.slice(0, 8));
              const engNames = engIds.map(id => scopeOptions.find(o => o.id === id)?.name ?? id.slice(0, 8));
              const hasScope = fwNames.length > 0 || engNames.length > 0;
              const scopeLabel = fwNames.length > 0 ? fwNames.join(", ") : engNames.length > 0 ? engNames.join(", ") : "All Frameworks";
              const scopeIcon2 = fwNames.length > 0
                ? <FileText className="h-3 w-3 shrink-0" />
                : engNames.length > 0
                ? <Briefcase className="h-3 w-3 shrink-0" />
                : null;
              return (
                <div key={inv.id} className="px-3 py-2.5 hover:bg-muted/20 space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <Mail className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      <span className="text-xs truncate">{inv.email}</span>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <Badge variant="outline" className={`text-[10px] ${grcRoleBadgeClass(inv.grc_role_code ?? "")}`}>
                        {grcRoleLabel(inv.grc_role_code ?? "")}
                      </Badge>
                      <Badge variant="outline" className={inv.status === "expired"
                        ? "text-[10px] bg-red-500/10 text-red-600 border-red-500/20"
                        : "text-[10px] bg-amber-500/10 text-amber-600 border-amber-500/20"
                      }>
                        {inv.status}
                      </Badge>
                      <button
                        className="p-0.5 text-muted-foreground hover:text-primary transition-colors"
                        onClick={() => handleResendInvite(inv.id)}
                        disabled={resendingInvite === inv.id}
                        title="Resend invitation"
                      >
                        {resendingInvite === inv.id
                          ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          : <Mail className="h-3.5 w-3.5" />}
                      </button>
                      <button
                        className="p-0.5 text-muted-foreground hover:text-red-500 transition-colors"
                        onClick={() => handleRevokeInviteMain(inv.id)}
                        disabled={revokingInvite === inv.id}
                        title="Revoke invitation"
                      >
                        {revokingInvite === inv.id
                          ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          : <Trash2 className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>
                  {/* Scope line */}
                  <div className="flex items-center gap-1 pl-5 text-[10px] text-muted-foreground">
                    {scopeIcon2}
                    <span className={hasScope ? "text-foreground font-medium" : "text-emerald-600 font-medium"}>
                      {scopeLabel}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Org Members section */}
      {orgMembers.length > 0 && (
        <div className="border border-border/50 rounded-lg overflow-hidden">
          <button
            className="w-full flex items-center justify-between px-3 py-2.5 bg-muted/30 hover:bg-muted/50 transition-colors text-left"
            onClick={() => setShowOrgMembers(v => !v)}
          >
            <div className="flex items-center gap-2">
              <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-semibold uppercase tracking-wide">Org Members</span>
              <Badge variant="secondary" className="text-xs h-4 px-1.5">{orgMembers.length}</Badge>
            </div>
            {showOrgMembers ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" /> : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />}
          </button>
          {showOrgMembers && (
            <div className="divide-y divide-border/30">
              {orgMembers.map(member => (
                <div key={member.user_id} className="flex items-center justify-between px-3 py-2.5 hover:bg-muted/20">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="h-7 w-7 rounded-full bg-muted flex items-center justify-center shrink-0 text-xs font-semibold uppercase">
                      {(member.display_name || member.email || "?")[0]}
                    </div>
                    <div className="min-w-0">
                      {member.display_name && (
                        <p className="text-xs font-medium truncate">{member.display_name}</p>
                      )}
                      <p className="text-xs text-muted-foreground truncate">{member.email}</p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-[10px] shrink-0 capitalize">
                    {member.role}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
