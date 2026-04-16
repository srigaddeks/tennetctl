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
  Users,
  UserPlus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Search,
  Mail,
  Clock,
  X,
  XCircle,
  Send,
  Upload,
} from "lucide-react";
import { fetchAccessContext } from "@/lib/api/access";
import { listOrgMembers, addOrgMember, removeOrgMember, updateOrgMemberRole } from "@/lib/api/orgs";
import {
  listInvitations,
  createInvitation,
  revokeInvitation,
} from "@/lib/api/invitations";
import type { InvitationResponse } from "@/lib/api/invitations";
import { fetchMe, fetchUserProperties } from "@/lib/api/auth";
import type { OrgMemberResponse } from "@/lib/types/orgs";

const ORG_ROLES = ["owner", "admin", "member", "viewer", "billing"] as const;

function roleBadgeClass(role: string) {
  switch (role) {
    case "owner":
      return "bg-purple-500/10 text-purple-600 border-purple-500/20";
    case "admin":
      return "bg-blue-500/10 text-blue-600 border-blue-500/20";
    case "member":
      return "bg-green-500/10 text-green-600 border-green-500/20";
    case "viewer":
      return "bg-gray-500/10 text-gray-600 border-gray-500/20";
    case "billing":
      return "bg-amber-500/10 text-amber-600 border-amber-500/20";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function inviteStatusBadge(status: string) {
  switch (status) {
    case "pending":
      return "bg-amber-500/10 text-amber-600 border-amber-500/20";
    case "accepted":
      return "bg-green-500/10 text-green-600 border-green-500/20";
    case "expired":
      return "bg-gray-500/10 text-gray-600 border-gray-500/20";
    case "revoked":
      return "bg-red-500/10 text-red-500 border-red-500/20";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function SkeletonRow() {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border px-4 py-3 animate-pulse">
      <div className="flex items-center gap-3 min-w-0">
        <div className="h-8 w-8 rounded-full bg-muted shrink-0" />
        <div className="space-y-1 min-w-0">
          <div className="h-3.5 w-32 rounded bg-muted" />
          <div className="h-3 w-48 rounded bg-muted" />
        </div>
      </div>
      <div className="h-5 w-16 rounded bg-muted" />
    </div>
  );
}

export default function OrgMembersPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [members, setMembers] = useState<OrgMemberResponse[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search/filter
  const [search, setSearch] = useState("");

  // Invite form
  const [showInvite, setShowInvite] = useState(false);
  const [inviteMode, setInviteMode] = useState<"single" | "bulk">("single");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<string>("member");
  const [bulkEmails, setBulkEmails] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);

  // Pending invitations
  const [invitations, setInvitations] = useState<InvitationResponse[]>([]);
  const [invitationsLoading, setInvitationsLoading] = useState(false);

  // Confirm remove
  const [confirmRemoveId, setConfirmRemoveId] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [removeError, setRemoveError] = useState<string | null>(null);

  // Revoke invite
  const [revokingInviteId, setRevokingInviteId] = useState<string | null>(null);

  // Role change
  const [changingRoleId, setChangingRoleId] = useState<string | null>(null);
  const [roleChangeError, setRoleChangeError] = useState<string | null>(null);

  const fileRef = useRef<HTMLInputElement>(null);

  const loadMembers = useCallback(async (id: string) => {
    setError(null);
    try {
      const data = await listOrgMembers(id);
      setMembers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load members");
    }
  }, []);

  const loadInvitations = useCallback(async () => {
    if (!orgId) return;
    setInvitationsLoading(true);
    try {
      const data = await listInvitations({ scope: "organization", org_id: orgId, status: "pending" });
      setInvitations(data);
    } catch {
      // Non-critical — silently ignore
    } finally {
      setInvitationsLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    async function init() {
      try {
        let defaultOrgId: string | undefined
        try {
          const props = await fetchUserProperties()
          defaultOrgId = props["default_org_id"] || undefined
        } catch {}
        const [access, me] = await Promise.all([fetchAccessContext(defaultOrgId), fetchMe()])
        setCurrentUserId(me.user_id)
        const id = access.current_org?.org_id
        if (!id) {
          setError("No organization found. Complete onboarding first.")
          return
        }
        setOrgId(id)
        await Promise.all([loadMembers(id), loadInvitations()])
      } catch {
        setError("Failed to load organization.")
      } finally {
        setIsLoading(false)
      }
    }
    init()
  }, [loadMembers, loadInvitations]);

  async function handleInviteSingle(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId || !inviteEmail.trim()) return;
    setInviting(true);
    setInviteError(null);
    setInviteSuccess(null);
    try {
      await createInvitation({
        email: inviteEmail.trim(),
        scope: "organization",
        org_id: orgId,
        role: inviteRole,
      });
      setInviteSuccess(`Invitation sent to ${inviteEmail.trim()}`);
      setInviteEmail("");
      await loadInvitations();
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : "Failed to send invitation");
    } finally {
      setInviting(false);
    }
  }

  async function handleInviteBulk(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId) return;
    const emails = bulkEmails
      .split(/[\n,;]+/)
      .map((s) => s.trim())
      .filter((s) => s.includes("@"));
    if (emails.length === 0) {
      setInviteError("No valid email addresses found.");
      return;
    }
    setInviting(true);
    setInviteError(null);
    setInviteSuccess(null);
    let sent = 0;
    let failed = 0;
    for (const email of emails) {
      try {
        await createInvitation({
          email,
          scope: "organization",
          org_id: orgId,
          role: inviteRole,
        });
        sent++;
      } catch {
        failed++;
      }
    }
    if (failed > 0) {
      setInviteSuccess(`Sent ${sent} invitation${sent !== 1 ? "s" : ""}. ${failed} failed.`);
    } else {
      setInviteSuccess(`Sent ${sent} invitation${sent !== 1 ? "s" : ""} successfully.`);
    }
    setBulkEmails("");
    await loadInvitations();
    setInviting(false);
  }

  function handleCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      if (text) setBulkEmails(text);
    };
    reader.readAsText(file);
    if (fileRef.current) fileRef.current.value = "";
  }

  async function handleRemove(userId: string) {
    if (!orgId) return;
    setRemovingId(userId);
    setRemoveError(null);
    try {
      await removeOrgMember(orgId, userId);
      setConfirmRemoveId(null);
      await loadMembers(orgId);
    } catch (err) {
      setRemoveError(err instanceof Error ? err.message : "Failed to remove member");
    } finally {
      setRemovingId(null);
    }
  }

  async function handleRevokeInvite(inviteId: string) {
    setRevokingInviteId(inviteId);
    try {
      await revokeInvitation(inviteId);
      await loadInvitations();
    } catch {
      // silently ignore
    } finally {
      setRevokingInviteId(null);
    }
  }

  async function handleRoleChange(userId: string, newRole: string) {
    if (!orgId) return;
    setChangingRoleId(userId);
    setRoleChangeError(null);
    try {
      await updateOrgMemberRole(orgId, userId, newRole);
      setMembers((prev) => prev.map((m) => m.user_id === userId ? { ...m, role: newRole } : m));
    } catch (err) {
      setRoleChangeError(err instanceof Error ? err.message : "Failed to update role");
    } finally {
      setChangingRoleId(null);
    }
  }

  // Filter members by search
  const filteredMembers = search.trim()
    ? members.filter((m) => {
        const q = search.toLowerCase();
        return (
          m.display_name?.toLowerCase().includes(q) ||
          m.email?.toLowerCase().includes(q) ||
          m.role.toLowerCase().includes(q) ||
          m.user_id.toLowerCase().includes(q)
        );
      })
    : members;

  const roleCounts = members.reduce<Record<string, number>>((acc, m) => {
    acc[m.role] = (acc[m.role] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">Members</h2>
          <p className="text-sm text-muted-foreground">
            Manage who has access to your organization.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {orgId && (
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                if (orgId) {
                  await loadMembers(orgId);
                  await loadInvitations();
                }
              }}
              disabled={isLoading}
              className="gap-1.5"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </Button>
          )}
          <Button
            size="sm"
            onClick={() => {
              setShowInvite((v) => !v);
              setInviteError(null);
              setInviteSuccess(null);
            }}
            className="gap-1.5"
          >
            <UserPlus className="h-3.5 w-3.5" />
            Invite
          </Button>
        </div>
      </div>

      {/* Stats */}
      {!isLoading && !error && (
        <div className="flex items-center gap-3 flex-wrap text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <Users className="h-3.5 w-3.5" />
            {members.length} member{members.length !== 1 ? "s" : ""}
          </span>
          {Object.entries(roleCounts).map(([role, count]) => (
            <Badge
              key={role}
              variant="outline"
              className={`text-[10px] capitalize ${roleBadgeClass(role)}`}
            >
              {count} {role}{count !== 1 ? "s" : ""}
            </Badge>
          ))}
          {invitations.length > 0 && (
            <span className="flex items-center gap-1 text-amber-600">
              <Clock className="h-3 w-3" />
              {invitations.length} pending invite{invitations.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      )}

      {/* Invite form */}
      {showInvite && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Invite Members</CardTitle>
                <CardDescription>
                  Send email invitations to join your organization.
                </CardDescription>
              </div>
              <button
                onClick={() => setShowInvite(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Mode toggle */}
            <div className="flex gap-1 p-0.5 bg-muted rounded-lg w-fit">
              <button
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  inviteMode === "single"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => setInviteMode("single")}
              >
                Single
              </button>
              <button
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  inviteMode === "bulk"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => setInviteMode("bulk")}
              >
                Bulk
              </button>
            </div>

            {inviteMode === "single" ? (
              <form onSubmit={handleInviteSingle} className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="invite-email">Email address</Label>
                    <Input
                      id="invite-email"
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="colleague@company.com"
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="invite-role">Role</Label>
                    <select
                      id="invite-role"
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      {ORG_ROLES.map((r) => (
                        <option key={r} value={r} className="capitalize">
                          {r}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <Button
                  type="submit"
                  size="sm"
                  disabled={inviting || !inviteEmail.trim()}
                  className="gap-1.5"
                >
                  <Send className="h-3.5 w-3.5" />
                  {inviting ? "Sending…" : "Send Invitation"}
                </Button>
              </form>
            ) : (
              <form onSubmit={handleInviteBulk} className="space-y-4">
                <div className="space-y-1.5">
                  <Label>Email addresses (one per line, comma, or semicolon separated)</Label>
                  <textarea
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[100px] font-mono"
                    value={bulkEmails}
                    onChange={(e) => setBulkEmails(e.target.value)}
                    placeholder={"alice@company.com\nbob@company.com\ncarol@company.com"}
                  />
                </div>
                <div className="flex items-center gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="bulk-role">Role for all</Label>
                    <select
                      id="bulk-role"
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      {ORG_ROLES.map((r) => (
                        <option key={r} value={r} className="capitalize">
                          {r}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="submit"
                    size="sm"
                    disabled={inviting || !bulkEmails.trim()}
                    className="gap-1.5"
                  >
                    <Send className="h-3.5 w-3.5" />
                    {inviting ? "Sending…" : "Send Invitations"}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => fileRef.current?.click()}
                    className="gap-1.5"
                  >
                    <Upload className="h-3.5 w-3.5" />
                    Upload CSV
                  </Button>
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".csv,.txt"
                    className="hidden"
                    onChange={handleCsvUpload}
                  />
                </div>
              </form>
            )}

            {inviteError && (
              <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
                <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
                <p className="text-sm text-red-500">{inviteError}</p>
              </div>
            )}
            {inviteSuccess && (
              <div className="flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2">
                <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                <p className="text-sm text-green-600 dark:text-green-400">
                  {inviteSuccess}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Pending invitations */}
      {invitations.length > 0 && (
        <Card>
          <CardHeader className="py-3 px-4">
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-amber-500" />
              <CardTitle className="text-sm">
                Pending Invitations ({invitations.length})
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="space-y-1.5">
              {invitations.map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Mail className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">
                        {inv.email}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Sent{" "}
                        {new Date(inv.created_at).toLocaleDateString(undefined, {
                          dateStyle: "medium",
                        })}
                        {inv.expires_at && (
                          <>
                            {" · Expires "}
                            {new Date(inv.expires_at).toLocaleDateString(undefined, {
                              dateStyle: "medium",
                            })}
                          </>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <Badge
                      variant="outline"
                      className={`text-[10px] capitalize ${inviteStatusBadge(inv.status)}`}
                    >
                      {inv.status}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={`text-[10px] capitalize ${roleBadgeClass(inv.role || "")}`}
                    >
                      {inv.role || "None"}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                      onClick={() => handleRevokeInvite(inv.id)}
                      disabled={revokingInviteId === inv.id}
                      title="Revoke invitation"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      {!isLoading && !error && members.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9 h-9"
            placeholder="Search members by name, email, or role..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      {/* Members list */}
      <Card>
        <CardHeader className="py-3 px-4">
          <div className="flex items-center gap-3">
            <Users className="h-4 w-4 text-muted-foreground shrink-0" />
            <CardTitle className="text-sm">
              {isLoading
                ? "Loading…"
                : search.trim()
                  ? `${filteredMembers.length} of ${members.length} members`
                  : `${members.length} member${members.length !== 1 ? "s" : ""}`}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          {(removeError || roleChangeError) && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 mb-3">
              <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-500">{removeError || roleChangeError}</p>
            </div>
          )}

          {isLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <SkeletonRow key={i} />
              ))}
            </div>
          ) : error ? (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
              <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          ) : filteredMembers.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              {search.trim()
                ? `No members match "${search}"`
                : "No members found. Invite someone to get started."}
            </p>
          ) : (
            <div className="space-y-1.5">
              {filteredMembers.map((member) => {
                const isCurrentUser = member.user_id === currentUserId;
                const displayName =
                  member.display_name || member.email || member.user_id;
                const initials = member.display_name
                  ? member.display_name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .slice(0, 2)
                      .toUpperCase()
                  : (member.email?.[0] ?? "?").toUpperCase();

                return (
                  <div
                    key={member.id}
                    className="flex items-center justify-between rounded-lg border border-border px-4 py-2.5 hover:bg-accent/20 transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold select-none">
                        {initials}
                      </span>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {displayName}
                          {isCurrentUser && (
                            <span className="ml-1.5 text-xs text-muted-foreground">
                              (you)
                            </span>
                          )}
                        </p>
                        {member.email && member.display_name && (
                          <p className="text-xs text-muted-foreground truncate">
                            {member.email}
                          </p>
                        )}
                        {member.joined_at && (
                          <p className="text-[10px] text-muted-foreground">
                            Joined{" "}
                            {new Date(member.joined_at).toLocaleDateString(
                              undefined,
                              { dateStyle: "medium" }
                            )}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      {isCurrentUser ? (
                        <Badge
                          variant="outline"
                          className={`text-xs capitalize ${roleBadgeClass(member.role)}`}
                        >
                          {member.role}
                        </Badge>
                      ) : (
                        <select
                          className={`h-6 rounded border px-1.5 text-xs font-medium cursor-pointer focus:outline-none focus:ring-1 focus:ring-ring ${roleBadgeClass(member.role)}`}
                          value={member.role}
                          disabled={changingRoleId === member.user_id}
                          onChange={(e) => handleRoleChange(member.user_id, e.target.value)}
                          title="Change role"
                        >
                          {ORG_ROLES.map((r) => (
                            <option key={r} value={r} className="bg-background text-foreground capitalize">{r}</option>
                          ))}
                        </select>
                      )}
                      {!isCurrentUser && (
                        <>
                          {confirmRemoveId === member.user_id ? (
                            <div className="flex items-center gap-1">
                              <span className="text-xs text-red-600">Remove?</span>
                              <Button
                                variant="destructive"
                                size="sm"
                                className="h-6 px-2 text-xs"
                                onClick={() => handleRemove(member.user_id)}
                                disabled={removingId === member.user_id}
                              >
                                {removingId === member.user_id
                                  ? "Removing…"
                                  : "Yes"}
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                className="h-6 px-2 text-xs"
                                onClick={() => setConfirmRemoveId(null)}
                              >
                                No
                              </Button>
                            </div>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                              onClick={() => setConfirmRemoveId(member.user_id)}
                              title="Remove member"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
