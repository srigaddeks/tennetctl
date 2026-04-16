"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
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
  ArrowLeft,
  Building2,
  Layers,
  Mail,
  Plus,
  Trash2,
  UserMinus,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Search,
  Settings,
  Save,
  X,
  Users,
  ShieldCheck,
  BookOpen,
  ClipboardList,
  Clock,
  UserCheck,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { listOrgs, listOrgMembers, addOrgMember, removeOrgMember } from "@/lib/api/orgs";
import { listWorkspaces, createWorkspace, listWorkspaceMembers, addWorkspaceMember, removeWorkspaceMember, updateWorkspaceMemberGrcRole } from "@/lib/api/workspaces";
import { listInvitations, createInvitation, revokeInvitation, resendInvitation } from "@/lib/api/invitations";
import { listAdminUsers, getEntitySettings, getEntitySettingKeys, setEntitySetting, deleteEntitySetting } from "@/lib/api/admin";
import { engagementsApi } from "@/lib/api/engagements";
import { listFrameworks } from "@/lib/api/grc";
import type { OrgResponse, OrgMemberResponse, WorkspaceResponse, WorkspaceMemberResponse } from "@/lib/types/orgs";
import type { InvitationResponse } from "@/lib/api/invitations";
import type { UserSummaryResponse, SettingResponse, SettingKeyResponse } from "@/lib/types/admin";
import type { Engagement } from "@/lib/api/engagements";
import type { FrameworkResponse } from "@/lib/types/grc";

type Tab = "overview" | "members" | "workspaces" | "invitations" | "settings";

const ORG_ROLES = ["owner", "admin", "member", "viewer", "billing"] as const;
const WS_ROLES = ["owner", "admin", "contributor", "viewer", "readonly"] as const;
const GRC_ROLES = [
  { value: "grc_practitioner",  label: "GRC Practitioner" },
  { value: "grc_engineer",      label: "Engineer" },
  { value: "grc_ciso",          label: "CISO / Exec" },
  { value: "grc_lead_auditor",  label: "Lead Auditor" },
  { value: "grc_staff_auditor", label: "Staff Auditor" },
  { value: "grc_vendor",        label: "Vendor" },
] as const;

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function getInitials(email: string | null, username: string | null): string {
  const source = email || username || "?";
  const parts = source.split(/[@._-]/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return source.slice(0, 2).toUpperCase();
}

function accountStatusClass(status: string) {
  switch (status) {
    case "active": return "text-green-500 border-green-500/30 bg-green-500/5";
    case "suspended": return "text-red-500 border-red-500/30 bg-red-500/5";
    case "pending": return "text-amber-500 border-amber-500/30 bg-amber-500/5";
    default: return "text-muted-foreground border-border";
  }
}

// ── UserSearchInput ──────────────────────────────────────────────────────────

interface UserSearchInputProps {
  onSelect: (user: UserSummaryResponse) => void;
  orgId: string;
  disabled?: boolean;
  placeholder?: string;
}

function UserSearchInput({ onSelect, orgId, disabled, placeholder = "Search by email or username…" }: UserSearchInputProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UserSummaryResponse[]>([]);
  const [open, setOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await listAdminUsers({ search: query.trim(), limit: 8, org_id: orgId });
        setResults(data.users);
        setOpen(true);
      } catch {
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, orgId]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleSelect(user: UserSummaryResponse) {
    onSelect(user);
    setQuery("");
    setResults([]);
    setOpen(false);
  }

  return (
    <div ref={containerRef} className="relative flex-1">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className="pl-8 text-sm"
        />
      </div>
      {open && (
        <div className="absolute z-50 top-full mt-1 left-0 right-0 rounded-xl border border-border bg-background shadow-lg overflow-hidden">
          {results.length === 0 ? (
            <div className="px-4 py-3 text-sm text-muted-foreground">No users found.</div>
          ) : (
            <ul>
              {results.map((user) => (
                <li key={user.user_id}>
                  <button
                    type="button"
                    onMouseDown={() => handleSelect(user)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-muted/50 transition-colors text-left"
                  >
                    <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary shrink-0">
                      {getInitials(user.email, user.username)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground truncate">{user.email ?? user.username ?? user.user_id}</p>
                      {user.email && user.username && (
                        <p className="text-xs text-muted-foreground truncate">@{user.username}</p>
                      )}
                    </div>
                    <Badge variant="outline" className={`text-xs shrink-0 ${accountStatusClass(user.account_status)}`}>
                      {user.account_status}
                    </Badge>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      {searching && (
        <p className="text-xs text-muted-foreground mt-1 px-1">Searching…</p>
      )}
    </div>
  );
}

// ── Members section ────────────────────────────────────────────────────────

function MembersSection({ orgId }: { orgId: string }) {
  const [members, setMembers] = useState<OrgMemberResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newRole, setNewRole] = useState<string>("member");
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [addError, setAddError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await listOrgMembers(orgId);
      setMembers(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load members");
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => { load(); }, [load]);

  async function handleAdd(user: UserSummaryResponse) {
    setAdding(true);
    setAddError(null);
    try {
      await addOrgMember(orgId, user.user_id, newRole);
      await load();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : "Failed to add member");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(userId: string) {
    setRemoving(userId);
    try {
      await removeOrgMember(orgId, userId);
      await load();
    } catch { /* silent */ }
    finally { setRemoving(null); }
  }

  function roleBadgeClass(role: string) {
    switch (role) {
      case "owner": return "text-red-500 border-red-500/30 bg-red-500/5";
      case "admin": return "text-primary border-primary/30 bg-primary/5";
      case "billing": return "text-amber-500 border-amber-500/30 bg-amber-500/5";
      default: return "text-muted-foreground border-border";
    }
  }

  if (loading) return <div className="h-20 bg-muted rounded-xl animate-pulse" />;
  if (error) return <p className="text-sm text-red-500">{error}</p>;

  return (
    <div className="space-y-4">
      {members.length === 0 ? (
        <p className="text-sm text-muted-foreground">No members yet.</p>
      ) : (
        <div className="space-y-2">
          {members.map((m) => (
            <div key={m.user_id} className="flex items-center justify-between gap-3 rounded-xl border border-border bg-background px-4 py-3">
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary shrink-0">
                  {m.user_id.slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <code className="font-mono text-xs text-foreground truncate block">{m.user_id}</code>
                  {m.joined_at && (
                    <p className="text-xs text-muted-foreground">Joined {formatDate(m.joined_at)}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant="outline" className={`text-xs ${roleBadgeClass(m.role)}`}>
                  {m.role}
                </Badge>
                <button
                  onClick={() => handleRemove(m.user_id)}
                  disabled={removing === m.user_id}
                  className="rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors disabled:opacity-50"
                  title="Remove member"
                >
                  <UserMinus className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="rounded-xl border border-border bg-muted/20 p-4 space-y-3">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Add member</p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <UserSearchInput onSelect={handleAdd} orgId={orgId} disabled={adding} />
          <select
            value={newRole}
            onChange={(e) => setNewRole(e.target.value)}
            disabled={adding}
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 shrink-0 disabled:opacity-50"
          >
            {ORG_ROLES.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
        {addError && <p className="text-xs text-red-500">{addError}</p>}
      </div>
    </div>
  );
}

// ── Workspace row with expand ──────────────────────────────────────────────

function WorkspaceRow({ orgId, workspace }: { orgId: string; workspace: WorkspaceResponse; onDeleted: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [members, setMembers] = useState<WorkspaceMemberResponse[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [newRole, setNewRole] = useState("contributor");
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [updatingGrcRole, setUpdatingGrcRole] = useState<string | null>(null);
  const [addError, setAddError] = useState<string | null>(null);
  // GRC invite state
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteGrcRole, setInviteGrcRole] = useState("grc_practitioner");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState(false);

  async function handleGrcRoleChange(userId: string, grcRoleCode: string | null) {
    setUpdatingGrcRole(userId);
    try {
      await updateWorkspaceMemberGrcRole(orgId, workspace.id, userId, grcRoleCode);
      await loadMembers();
    } catch { /* silent — user sees no change */ }
    finally { setUpdatingGrcRole(null); }
  }

  async function loadMembers() {
    setMembersLoading(true);
    try {
      const data = await listWorkspaceMembers(orgId, workspace.id);
      setMembers(data);
    } catch { /* silent */ }
    finally { setMembersLoading(false); }
  }

  function handleExpand() {
    if (!expanded) loadMembers();
    setExpanded((v) => !v);
  }

  async function handleAddMember(user: UserSummaryResponse) {
    setAdding(true);
    setAddError(null);
    try {
      await addWorkspaceMember(orgId, workspace.id, user.user_id, newRole);
      await loadMembers();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : "Failed to add member");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemoveMember(userId: string) {
    setRemoving(userId);
    try {
      await removeWorkspaceMember(orgId, workspace.id, userId);
      await loadMembers();
    } catch { /* silent */ }
    finally { setRemoving(null); }
  }

  async function handleInviteGrcMember(e: React.FormEvent) {
    e.preventDefault();
    setInviting(true);
    setInviteError(null);
    setInviteSuccess(false);
    try {
      await createInvitation({
        email: inviteEmail.trim(),
        scope: "workspace",
        org_id: orgId,
        workspace_id: workspace.id,
        role: "contributor",
        grc_role_code: inviteGrcRole,
      });
      setInviteEmail("");
      setInviteSuccess(true);
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : "Failed to send invitation");
    } finally {
      setInviting(false);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <button
        onClick={handleExpand}
        className="w-full flex items-center gap-3 px-4 py-3.5 hover:bg-muted/30 transition-colors text-left"
      >
        <span className="text-muted-foreground shrink-0">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </span>
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-purple-500/10">
          <Layers className="h-3.5 w-3.5 text-purple-500" />
        </div>
        <div className="flex-1 min-w-0 flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold text-foreground">{workspace.name}</span>
          <code className="font-mono text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{workspace.slug}</code>
          <Badge variant="outline" className="text-xs text-muted-foreground">
            {WORKSPACE_TYPE_LABELS[workspace.workspace_type_code] ?? workspace.workspace_type_code}
          </Badge>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-border p-4 bg-muted/10 space-y-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Members</p>
          {membersLoading ? (
            <div className="h-12 bg-muted rounded-lg animate-pulse" />
          ) : (
            <>
              {members.length > 0 && (
                <div className="space-y-1.5">
                  {members.map((m) => (
                    <div key={m.user_id} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background px-3 py-2">
                      <div className="flex flex-col min-w-0 flex-1">
                        <code className="font-mono text-xs text-foreground truncate">{m.email ?? m.user_id}</code>
                        {m.display_name && <span className="text-xs text-muted-foreground truncate">{m.display_name}</span>}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Badge variant="outline" className="text-xs text-muted-foreground">{m.role}</Badge>
                        <select
                          value={m.grc_role_code ?? ""}
                          onChange={(e) => handleGrcRoleChange(m.user_id, e.target.value || null)}
                          disabled={updatingGrcRole === m.user_id}
                          title="GRC role"
                          className="rounded border border-border bg-background px-2 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 disabled:opacity-50"
                        >
                          <option value="">No GRC role</option>
                          {GRC_ROLES.map((r) => (
                            <option key={r.value} value={r.value}>{r.label}</option>
                          ))}
                        </select>
                        <button
                          onClick={() => handleRemoveMember(m.user_id)}
                          disabled={removing === m.user_id}
                          className="rounded-lg p-1 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors disabled:opacity-50"
                        >
                          <UserMinus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex flex-col gap-2 sm:flex-row">
                <UserSearchInput onSelect={handleAddMember} orgId={orgId} disabled={adding} />
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  disabled={adding}
                  className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50"
                >
                  {WS_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              {addError && <p className="text-xs text-red-500">{addError}</p>}

              <form onSubmit={handleInviteGrcMember} className="mt-3 rounded-lg border border-border bg-muted/10 p-3 space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Invite external GRC member by email</p>
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <Input
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="auditor@firm.com"
                      className="flex-1 h-8 text-sm"
                      required
                    />
                    <select
                      value={inviteGrcRole}
                      onChange={(e) => setInviteGrcRole(e.target.value)}
                      className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    >
                      {GRC_ROLES.map((r) => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                    <Button type="submit" size="sm" disabled={inviting || !inviteEmail.trim()} className="gap-1.5 shrink-0 h-8">
                      <Mail className="h-3.5 w-3.5" />
                      {inviting ? "Sending…" : "Invite"}
                    </Button>
                  </div>
                  {inviteError && <p className="text-xs text-red-500">{inviteError}</p>}
                  {inviteSuccess && (
                    <div className="flex items-center gap-1.5 text-xs text-green-600 dark:text-green-400">
                      <CheckCircle2 className="h-3.5 w-3.5" /> GRC invitation sent.
                    </div>
                  )}
                </form>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── Workspaces section ─────────────────────────────────────────────────────

const WORKSPACE_TYPE_LABELS: Record<string, string> = {
  project: "K-Control",
  grc: "GRC",
  sandbox: "Sandbox",
};

function WorkspacesSection({ orgId }: { orgId: string }) {
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newSlug, setNewSlug] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await listWorkspaces(orgId);
      setWorkspaces(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load workspaces");
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => { load(); }, [load]);

  function slugify(val: string) {
    return val.toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/--+/g, "-");
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      await createWorkspace(orgId, {
        name: newName.trim(),
        slug: newSlug.trim() || slugify(newName.trim()),
        workspace_type_code: "project",
      });
      setNewName("");
      setNewSlug("");
      setShowCreate(false);
      await load();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create workspace");
    } finally {
      setCreating(false);
    }
  }

  if (loading) return <div className="h-20 bg-muted rounded-xl animate-pulse" />;
  if (error) return <p className="text-sm text-red-500">{error}</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{workspaces.length} {workspaces.length === 1 ? "workspace" : "workspaces"}</p>
        <Button size="sm" variant="outline" onClick={() => setShowCreate((v) => !v)} className="gap-1.5">
          <Plus className="h-3.5 w-3.5" />
          New Workspace
        </Button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="rounded-xl border border-primary/30 bg-primary/5 p-4 space-y-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">New workspace</p>
          <div className="space-y-1">
            <Label htmlFor="ws-name">Name</Label>
            <Input
              id="ws-name"
              value={newName}
              onChange={(e) => {
                setNewName(e.target.value);
                setNewSlug(slugify(e.target.value));
              }}
              placeholder="e.g. Production"
              required
            />
          </div>
          {createError && <p className="text-xs text-red-500">{createError}</p>}
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={creating || !newName.trim()}>
              {creating ? "Creating…" : "Create"}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setShowCreate(false)}>Cancel</Button>
          </div>
        </form>
      )}

      {workspaces.length === 0 ? (
        <p className="text-sm text-muted-foreground">No workspaces in this organization yet.</p>
      ) : (
        <div className="space-y-2">
          {workspaces.map((ws) => (
            <WorkspaceRow key={ws.id} orgId={orgId} workspace={ws} onDeleted={load} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Invitations section ────────────────────────────────────────────────────

type InviteMode = "team" | "auditor";

const GRC_ROLE_LABELS: Record<string, string> = {
  grc_lead: "GRC Lead",
  grc_sme: "GRC SME",
  grc_engineer: "Engineer",
  grc_ciso: "CISO / Exec",
  grc_lead_auditor: "Lead Auditor",
  grc_staff_auditor: "Staff Auditor",
  grc_vendor: "Vendor",
};

function InvitationsSection({ orgId }: { orgId: string }) {
  const [invitations, setInvitations] = useState<InvitationResponse[]>([]);
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [resending, setResending] = useState<string | null>(null);
  const [mode, setMode] = useState<InviteMode>("team");

  // Team invite state
  const [teamEmail, setTeamEmail] = useState("");
  const [teamRole, setTeamRole] = useState("member");
  const [teamSending, setTeamSending] = useState(false);
  const [teamError, setTeamError] = useState<string | null>(null);
  const [teamSuccess, setTeamSuccess] = useState(false);

  // Auditor invite state
  const [auditorEmail, setAuditorEmail] = useState("");
  const [auditorGrcRole, setAuditorGrcRole] = useState("grc_staff_auditor");
  const [auditorWorkspaceId, setAuditorWorkspaceId] = useState("");
  const [auditorEngagementId, setAuditorEngagementId] = useState("");
  const [auditorFrameworkId, setAuditorFrameworkId] = useState("");
  const [auditorSending, setAuditorSending] = useState(false);
  const [auditorError, setAuditorError] = useState<string | null>(null);
  const [auditorSuccess, setAuditorSuccess] = useState(false);

  // Data for auditor form
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [engagementsLoading, setEngagementsLoading] = useState(false);
  const [frameworks, setFrameworks] = useState<FrameworkResponse[]>([]);
  const [frameworksLoading, setFrameworksLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [invData, wsData] = await Promise.all([
        listInvitations({ org_id: orgId }),
        listWorkspaces(orgId),
      ]);
      setInvitations(invData);
      setWorkspaces(wsData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load invitations");
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => { load(); }, [load]);

  // Load engagements and frameworks when auditor mode is selected
  useEffect(() => {
    if (mode !== "auditor") return;
    setEngagementsLoading(true);
    setFrameworksLoading(true);
    engagementsApi.list(orgId)
      .then(setEngagements)
      .catch(() => setEngagements([]))
      .finally(() => setEngagementsLoading(false));
    listFrameworks()
      .then((res) => setFrameworks(res.items ?? []))
      .catch(() => setFrameworks([]))
      .finally(() => setFrameworksLoading(false));
  }, [mode, orgId]);

  async function handleTeamInvite(e: React.FormEvent) {
    e.preventDefault();
    setTeamSending(true);
    setTeamError(null);
    setTeamSuccess(false);
    try {
      await createInvitation({ email: teamEmail.trim(), scope: "organization", org_id: orgId, role: teamRole });
      setTeamEmail("");
      setTeamSuccess(true);
      await load();
    } catch (err) {
      setTeamError(err instanceof Error ? err.message : "Failed to send invitation");
    } finally {
      setTeamSending(false);
    }
  }

  async function handleAuditorInvite(e: React.FormEvent) {
    e.preventDefault();
    setAuditorSending(true);
    setAuditorError(null);
    setAuditorSuccess(false);
    try {
      await createInvitation({
        email: auditorEmail.trim(),
        scope: auditorWorkspaceId ? "workspace" : "organization",
        org_id: orgId,
        workspace_id: auditorWorkspaceId || undefined,
        role: "viewer",
        grc_role_code: auditorGrcRole,
        engagement_id: auditorEngagementId || undefined,
        framework_id: auditorFrameworkId || undefined,
      });
      setAuditorEmail("");
      setAuditorEngagementId("");
      setAuditorFrameworkId("");
      setAuditorSuccess(true);
      await load();
    } catch (err) {
      setAuditorError(err instanceof Error ? err.message : "Failed to send invitation");
    } finally {
      setAuditorSending(false);
    }
  }

  async function handleRevoke(invId: string) {
    setRevoking(invId);
    try {
      await revokeInvitation(invId);
      await load();
    } catch { /* silent */ }
    finally { setRevoking(null); }
  }

  async function handleResend(invId: string) {
    setResending(invId);
    try {
      await resendInvitation(invId);
      await load();
    } catch { /* silent */ }
    finally { setResending(null); }
  }

  function statusClass(status: string) {
    switch (status) {
      case "pending": return "text-amber-500 border-amber-500/30 bg-amber-500/5";
      case "accepted": return "text-green-500 border-green-500/30 bg-green-500/5";
      case "revoked": return "text-red-500 border-red-500/30 bg-red-500/5";
      case "expired": return "text-muted-foreground border-border";
      default: return "text-muted-foreground border-border";
    }
  }

  function statusIcon(status: string) {
    switch (status) {
      case "pending": return <Clock className="h-3 w-3" />;
      case "accepted": return <UserCheck className="h-3 w-3" />;
      default: return null;
    }
  }

  const auditorInvitations = invitations.filter(i => !!i.grc_role_code);
  const teamInvitations = invitations.filter(i => !i.grc_role_code);

  if (loading) return <div className="h-20 bg-muted rounded-xl animate-pulse" />;

  return (
    <div className="space-y-6">
      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* Mode selector */}
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => setMode("team")}
          className={`flex items-start gap-3 rounded-xl border p-4 text-left transition-all ${
            mode === "team"
              ? "border-primary bg-primary/5 ring-1 ring-primary/20"
              : "border-border bg-muted/20 hover:border-primary/40 hover:bg-muted/40"
          }`}
        >
          <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${mode === "team" ? "bg-primary/15" : "bg-muted"}`}>
            <Users className={`h-4 w-4 ${mode === "team" ? "text-primary" : "text-muted-foreground"}`} />
          </div>
          <div>
            <p className={`text-sm font-semibold ${mode === "team" ? "text-foreground" : "text-muted-foreground"}`}>Team Member</p>
            <p className="text-xs text-muted-foreground mt-0.5">Add a colleague to this organization</p>
          </div>
        </button>

        <button
          type="button"
          onClick={() => setMode("auditor")}
          className={`flex items-start gap-3 rounded-xl border p-4 text-left transition-all ${
            mode === "auditor"
              ? "border-primary bg-primary/5 ring-1 ring-primary/20"
              : "border-border bg-muted/20 hover:border-primary/40 hover:bg-muted/40"
          }`}
        >
          <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${mode === "auditor" ? "bg-primary/15" : "bg-muted"}`}>
            <ShieldCheck className={`h-4 w-4 ${mode === "auditor" ? "text-primary" : "text-muted-foreground"}`} />
          </div>
          <div>
            <p className={`text-sm font-semibold ${mode === "auditor" ? "text-foreground" : "text-muted-foreground"}`}>External Auditor</p>
            <p className="text-xs text-muted-foreground mt-0.5">Invite an auditor with GRC role &amp; scope</p>
          </div>
        </button>
      </div>

      {/* Team invite form */}
      {mode === "team" && (
        <form onSubmit={handleTeamInvite} className="rounded-xl border border-border bg-muted/20 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <p className="text-sm font-semibold text-foreground">Invite team member</p>
          </div>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="team-email" className="text-xs text-muted-foreground">Email address</Label>
              <Input
                id="team-email"
                type="email"
                value={teamEmail}
                onChange={(e) => setTeamEmail(e.target.value)}
                placeholder="colleague@company.com"
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="team-role" className="text-xs text-muted-foreground">Organization role</Label>
              <select
                id="team-role"
                value={teamRole}
                onChange={(e) => setTeamRole(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                {ORG_ROLES.map((r) => (
                  <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">
                {teamRole === "owner" && "Full control including billing and deletion."}
                {teamRole === "admin" && "Manage members, workspaces, and settings."}
                {teamRole === "member" && "Access workspaces they are added to."}
                {teamRole === "viewer" && "Read-only access across the organization."}
                {teamRole === "billing" && "Manage billing and subscriptions only."}
              </p>
            </div>
          </div>
          {teamError && <p className="text-xs text-red-500">{teamError}</p>}
          {teamSuccess && (
            <div className="flex items-center gap-1.5 text-xs text-green-600 dark:text-green-400">
              <CheckCircle2 className="h-3.5 w-3.5" /> Invitation sent.
            </div>
          )}
          <Button type="submit" size="sm" disabled={teamSending || !teamEmail.trim()} className="gap-1.5">
            <Mail className="h-3.5 w-3.5" />
            {teamSending ? "Sending…" : "Send invitation"}
          </Button>
        </form>
      )}

      {/* Auditor invite form */}
      {mode === "auditor" && (
        <form onSubmit={handleAuditorInvite} className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <p className="text-sm font-semibold text-foreground">Invite external auditor</p>
          </div>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="aud-email" className="text-xs text-muted-foreground">Auditor email address</Label>
              <Input
                id="aud-email"
                type="email"
                value={auditorEmail}
                onChange={(e) => setAuditorEmail(e.target.value)}
                placeholder="auditor@firm.com"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="aud-grc-role" className="text-xs text-muted-foreground flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3" /> GRC role
                </Label>
                <select
                  id="aud-grc-role"
                  value={auditorGrcRole}
                  onChange={(e) => setAuditorGrcRole(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  {GRC_ROLES.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="aud-workspace" className="text-xs text-muted-foreground flex items-center gap-1">
                  <Layers className="h-3 w-3" /> Workspace (optional)
                </Label>
                <select
                  id="aud-workspace"
                  value={auditorWorkspaceId}
                  onChange={(e) => setAuditorWorkspaceId(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="">All workspaces</option>
                  {workspaces.map((ws) => (
                    <option key={ws.id} value={ws.id}>{ws.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="aud-framework" className="text-xs text-muted-foreground flex items-center gap-1">
                  <BookOpen className="h-3 w-3" /> Framework (optional)
                </Label>
                {frameworksLoading ? (
                  <div className="h-10 bg-muted rounded-lg animate-pulse" />
                ) : (
                  <select
                    id="aud-framework"
                    value={auditorFrameworkId}
                    onChange={(e) => { setAuditorFrameworkId(e.target.value); setAuditorEngagementId(""); }}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  >
                    <option value="">All frameworks</option>
                    {frameworks.map((fw) => (
                      <option key={fw.id} value={fw.id}>{fw.name}</option>
                    ))}
                  </select>
                )}
              </div>

              {auditorFrameworkId && (
                <div className="space-y-1.5">
                  <Label htmlFor="aud-engagement" className="text-xs text-muted-foreground flex items-center gap-1">
                    <ClipboardList className="h-3 w-3" /> Engagement (optional)
                  </Label>
                  {engagementsLoading ? (
                    <div className="h-10 bg-muted rounded-lg animate-pulse" />
                  ) : (
                    <select
                      id="aud-engagement"
                      value={auditorEngagementId}
                      onChange={(e) => setAuditorEngagementId(e.target.value)}
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    >
                      <option value="">All engagements</option>
                      {engagements.map((eng) => (
                        <option key={eng.id} value={eng.id}>
                          {eng.engagement_name} — {eng.auditor_firm}
                        </option>
                      ))}
                    </select>
                  )}
                  {engagements.length === 0 && !engagementsLoading && (
                    <p className="text-xs text-muted-foreground"><Link href="/audit-workspace/grc" className="underline text-primary">Create an engagement</Link> to scope access.</p>
                  )}
                </div>
              )}
            </div>

            {/* Summary card */}
            {auditorEmail && (
              <div className="rounded-lg border border-primary/20 bg-background p-3 space-y-1.5">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Invite summary</p>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="flex items-center gap-1 rounded-md bg-muted px-2 py-1">
                    <Mail className="h-3 w-3 text-muted-foreground" />
                    {auditorEmail}
                  </span>
                  <span className="flex items-center gap-1 rounded-md bg-primary/10 text-primary px-2 py-1">
                    <ShieldCheck className="h-3 w-3" />
                    {GRC_ROLE_LABELS[auditorGrcRole] ?? auditorGrcRole}
                  </span>
                  {auditorWorkspaceId && (
                    <span className="flex items-center gap-1 rounded-md bg-muted px-2 py-1">
                      <Layers className="h-3 w-3 text-muted-foreground" />
                      {workspaces.find(w => w.id === auditorWorkspaceId)?.name ?? "Workspace"}
                    </span>
                  )}
                  {auditorEngagementId && (
                    <span className="flex items-center gap-1 rounded-md bg-muted px-2 py-1">
                      <ClipboardList className="h-3 w-3 text-muted-foreground" />
                      {engagements.find(e => e.id === auditorEngagementId)?.engagement_name ?? "Engagement"}
                    </span>
                  )}
                  {auditorFrameworkId && (
                    <span className="flex items-center gap-1 rounded-md bg-muted px-2 py-1">
                      <BookOpen className="h-3 w-3 text-muted-foreground" />
                      {frameworks.find(f => f.id === auditorFrameworkId)?.name ?? "Framework"}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
          {auditorError && <p className="text-xs text-red-500">{auditorError}</p>}
          {auditorSuccess && (
            <div className="flex items-center gap-1.5 text-xs text-green-600 dark:text-green-400">
              <CheckCircle2 className="h-3.5 w-3.5" /> Auditor invitation sent.
            </div>
          )}
          <Button type="submit" size="sm" disabled={auditorSending || !auditorEmail.trim()} className="gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5" />
            {auditorSending ? "Sending…" : "Send auditor invitation"}
          </Button>
        </form>
      )}

      {/* Invitation list */}
      <div className="space-y-4">
        {/* Auditor invitations */}
        {auditorInvitations.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5" /> Auditor invitations
            </p>
            {auditorInvitations.map((inv) => (
              <div key={inv.id} className="flex items-center justify-between gap-3 rounded-xl border border-border bg-background px-4 py-3">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <ShieldCheck className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{inv.email}</p>
                    <div className="flex flex-wrap items-center gap-1.5 mt-0.5">
                      {inv.grc_role_code && (
                        <span className="text-xs text-primary font-medium">{GRC_ROLE_LABELS[inv.grc_role_code] ?? inv.grc_role_code}</span>
                      )}
                      {inv.workspace_id && (
                        <>
                          <span className="text-xs text-muted-foreground">·</span>
                          <span className="text-xs text-muted-foreground flex items-center gap-0.5">
                            <Layers className="h-3 w-3" />
                            {workspaces.find(w => w.id === inv.workspace_id)?.name ?? "Workspace"}
                          </span>
                        </>
                      )}
                      <span className="text-xs text-muted-foreground">·</span>
                      <span className="text-xs text-muted-foreground">Sent {formatDate(inv.created_at)}</span>
                      {inv.expires_at && (
                        <>
                          <span className="text-xs text-muted-foreground">·</span>
                          <span className="text-xs text-muted-foreground flex items-center gap-0.5">
                            <Clock className="h-3 w-3" /> Expires {formatDate(inv.expires_at)}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant="outline" className={`text-xs flex items-center gap-1 ${statusClass(inv.status)}`}>
                    {statusIcon(inv.status)}
                    {inv.status}
                  </Badge>
                  {inv.status === "pending" && (
                    <>
                      <button
                        onClick={() => handleResend(inv.id)}
                        disabled={resending === inv.id}
                        className="rounded-lg p-1.5 text-muted-foreground hover:bg-primary/10 hover:text-primary transition-colors disabled:opacity-50"
                        title="Resend invitation"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${resending === inv.id ? "animate-spin" : ""}`} />
                      </button>
                      <button
                        onClick={() => handleRevoke(inv.id)}
                        disabled={revoking === inv.id}
                        className="rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors disabled:opacity-50"
                        title="Revoke invitation"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Team invitations */}
        {teamInvitations.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5" /> Team invitations
            </p>
            {teamInvitations.map((inv) => (
              <div key={inv.id} className="flex items-center justify-between gap-3 rounded-xl border border-border bg-background px-4 py-3">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{inv.email}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {inv.role ? inv.role.charAt(0).toUpperCase() + inv.role.slice(1) : "Member"} · Sent {formatDate(inv.created_at)}
                      {inv.expires_at && ` · Expires ${formatDate(inv.expires_at)}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant="outline" className={`text-xs flex items-center gap-1 ${statusClass(inv.status)}`}>
                    {statusIcon(inv.status)}
                    {inv.status}
                  </Badge>
                  {inv.status === "pending" && (
                    <>
                      <button
                        onClick={() => handleResend(inv.id)}
                        disabled={resending === inv.id}
                        className="rounded-lg p-1.5 text-muted-foreground hover:bg-primary/10 hover:text-primary transition-colors disabled:opacity-50"
                        title="Resend invitation"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${resending === inv.id ? "animate-spin" : ""}`} />
                      </button>
                      <button
                        onClick={() => handleRevoke(inv.id)}
                        disabled={revoking === inv.id}
                        className="rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors disabled:opacity-50"
                        title="Revoke invitation"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {invitations.length === 0 && (
          <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border p-8 text-center">
            <Mail className="h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">No invitations yet.</p>
            <p className="text-xs text-muted-foreground">Invite team members or external auditors above.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Entity Settings table ──────────────────────────────────────────────────

function EntitySettingsTable({ entityType, entityId, label }: { entityType: string; entityId: string; label: string }) {
  const [keys, setKeys] = useState<SettingKeyResponse[]>([]);
  const [settings, setSettings] = useState<SettingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [k, s] = await Promise.all([
        getEntitySettingKeys(entityType, entityId),
        getEntitySettings(entityType, entityId),
      ]);
      setKeys(k);
      setSettings(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, [entityType, entityId]);

  useEffect(() => { load(); }, [load]);

  function currentValue(code: string): string | null {
    const found = settings.find((s) => s.key === code);
    return found ? found.value : null;
  }

  function startEdit(code: string) {
    setEditingKey(code);
    setEditValue(currentValue(code) ?? "");
  }

  function cancelEdit() {
    setEditingKey(null);
    setEditValue("");
  }

  async function handleSave(code: string) {
    setSaving(code);
    try {
      await setEntitySetting(entityType, entityId, code, editValue);
      setEditingKey(null);
      setEditValue("");
      await load();
    } catch { /* silent */ }
    finally { setSaving(null); }
  }

  async function handleDelete(code: string) {
    setDeleting(code);
    try {
      await deleteEntitySetting(entityType, entityId, code);
      await load();
    } catch { /* silent */ }
    finally { setDeleting(null); }
  }

  if (loading) return <div className="h-16 bg-muted rounded-xl animate-pulse" />;
  if (error) return <p className="text-sm text-red-500">{error}</p>;

  if (keys.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-muted/10 px-6 py-8 text-center">
        <Settings className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">No setting keys defined for this {label.toLowerCase()}.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/30">
            <th className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Key</th>
            <th className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground hidden md:table-cell">Description</th>
            <th className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Value</th>
            <th className="text-right px-4 py-2.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground w-28">Actions</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((k) => {
            const val = currentValue(k.code);
            const isEditing = editingKey === k.code;
            return (
              <tr key={k.code} className="border-b border-border last:border-b-0 hover:bg-muted/20 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex flex-col gap-0.5">
                    <span className="font-medium text-foreground">{k.name}</span>
                    <code className="text-xs text-muted-foreground font-mono">{k.code}</code>
                  </div>
                </td>
                <td className="px-4 py-3 text-muted-foreground text-xs hidden md:table-cell">{k.description}</td>
                <td className="px-4 py-3">
                  {isEditing ? (
                    <div className="flex items-center gap-2">
                      <Input
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="text-sm h-8"
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleSave(k.code);
                          if (e.key === "Escape") cancelEdit();
                        }}
                      />
                    </div>
                  ) : val !== null ? (
                    <code className="text-xs font-mono bg-muted px-2 py-1 rounded text-foreground">{val}</code>
                  ) : (
                    <span className="text-xs text-muted-foreground italic">not set</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  {isEditing ? (
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleSave(k.code)}
                        disabled={saving === k.code}
                        className="rounded-lg p-1.5 text-green-600 hover:bg-green-500/10 transition-colors disabled:opacity-50"
                        title="Save"
                      >
                        <Save className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition-colors"
                        title="Cancel"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => startEdit(k.code)}
                        className="h-7 text-xs px-2"
                      >
                        {val !== null ? "Edit" : "Set"}
                      </Button>
                      {val !== null && (
                        <button
                          onClick={() => handleDelete(k.code)}
                          disabled={deleting === k.code}
                          className="rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors disabled:opacity-50"
                          title="Clear value"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Settings section ──────────────────────────────────────────────────────

function SettingsSection({ orgId }: { orgId: string }) {
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([]);
  const [wsLoading, setWsLoading] = useState(true);

  useEffect(() => {
    listWorkspaces(orgId)
      .then(setWorkspaces)
      .catch(() => {})
      .finally(() => setWsLoading(false));
  }, [orgId]);

  return (
    <div className="space-y-8">
      {/* Org Settings */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold text-foreground">Organization Settings</h3>
        </div>
        <EntitySettingsTable entityType="org" entityId={orgId} label="organization" />
      </div>

      {/* Workspace Settings */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-purple-500" />
          <h3 className="text-sm font-semibold text-foreground">Workspace Settings</h3>
        </div>
        {wsLoading ? (
          <div className="h-16 bg-muted rounded-xl animate-pulse" />
        ) : workspaces.length === 0 ? (
          <p className="text-sm text-muted-foreground">No workspaces in this organization.</p>
        ) : (
          <div className="space-y-5">
            {workspaces.map((ws) => (
              <div key={ws.id} className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">{ws.name}</span>
                  <code className="font-mono text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{ws.slug}</code>
                </div>
                <EntitySettingsTable entityType="workspace" entityId={ws.id} label="workspace" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────

export default function OrgDetailPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const router = useRouter();
  const [org, setOrg] = useState<OrgResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  useEffect(() => {
    listOrgs()
      .then((orgs) => {
        const found = orgs.find((o) => o.id === orgId);
        if (found) setOrg(found);
        else router.replace("/workspaces");
      })
      .catch(() => router.replace("/workspaces"))
      .finally(() => setLoading(false));
  }, [orgId, router]);

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "members", label: "Members" },
    { id: "workspaces", label: "Workspaces" },
    { id: "invitations", label: "Invitations" },
    { id: "settings", label: "Settings" },
  ];

  if (loading) {
    return (
      <div className="space-y-6 max-w-4xl">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="h-32 bg-muted rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (!org) return null;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Back */}
      <Button variant="ghost" size="sm" asChild className="gap-1.5 -ml-2 text-muted-foreground hover:text-foreground">
        <Link href="/workspaces">
          <ArrowLeft className="h-4 w-4" />
          All organizations
        </Link>
      </Button>

      {/* Org header */}
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10">
          <Building2 className="h-6 w-6 text-primary" />
        </div>
        <div className="flex flex-col gap-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-2xl font-semibold text-foreground">{org.name}</h2>
            <Badge variant="outline" className="text-xs text-muted-foreground capitalize">
              {org.org_type_code.replace(/_/g, " ")}
            </Badge>
            {!org.is_active && (
              <Badge variant="outline" className="text-xs text-red-500 border-red-500/30">Inactive</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground font-mono">{org.slug}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl border border-border bg-muted/30 p-1.5 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-all ${
              activeTab === tab.id
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {activeTab === "overview" && "Organization Details"}
            {activeTab === "members" && "Members"}
            {activeTab === "workspaces" && "Workspaces"}
            {activeTab === "invitations" && "Invitations"}
            {activeTab === "settings" && "Settings"}
          </CardTitle>
          <CardDescription>
            {activeTab === "overview" && "Basic information about this organization."}
            {activeTab === "members" && "Manage who has access to this organization."}
            {activeTab === "workspaces" && "Manage workspaces and their members."}
            {activeTab === "invitations" && "Invite people and manage pending invitations."}
            {activeTab === "settings" && "Configure settings for this organization and its workspaces."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              {[
                { label: "Name", value: org.name },
                { label: "Slug", value: <code className="font-mono text-xs">{org.slug}</code> },
                { label: "Type", value: <span className="capitalize">{org.org_type_code.replace(/_/g, " ")}</span> },
                { label: "Status", value: org.is_active ? <span className="text-green-600 dark:text-green-400">Active</span> : <span className="text-red-500">Inactive</span> },
                { label: "Created", value: formatDate(org.created_at) },
                { label: "ID", value: <code className="font-mono text-xs text-muted-foreground">{org.id}</code> },
              ].map(({ label, value }) => (
                <div key={label} className="flex flex-col gap-1">
                  <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{label}</span>
                  <span className="text-sm text-foreground">{value}</span>
                </div>
              ))}
            </div>
          )}
          {activeTab === "members" && <MembersSection orgId={orgId} />}
          {activeTab === "workspaces" && <WorkspacesSection orgId={orgId} />}
          {activeTab === "invitations" && <InvitationsSection orgId={orgId} />}
          {activeTab === "settings" && <SettingsSection orgId={orgId} />}
        </CardContent>
      </Card>
    </div>
  );
}
