"use client";

import Link from "next/link";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { ApplicationScopeBar, AppAvatar } from "@/components/application-scope-bar";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { Modal } from "@/components/modal";
import {
  useUser,
  useUpdateUser,
  useDeleteUser,
} from "@/features/iam-users/hooks/use-users";
import {
  useSessions,
  useRevokeSession,
} from "@/features/iam-sessions/hooks/use-sessions";
import {
  useOrgMemberships,
  useWorkspaceMemberships,
} from "@/features/iam-memberships/hooks/use-memberships";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { useWorkspaces } from "@/features/iam-workspaces/hooks/use-workspaces";
import { useApplications } from "@/features/iam-applications/hooks/use-applications";
import { ApiClientError } from "@/lib/api";

const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  email_password: "Email + Password",
  magic_link: "Magic Link",
  google_oauth: "Google OAuth",
  github_oauth: "GitHub OAuth",
};

export default function UserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = typeof params.id === "string" ? params.id : "";
  const { toast: showToast } = useToast();

  const { data: user, isLoading, isError, error } = useUser(userId);
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const { data: sessionsData } = useSessions({ limit: 10 });
  const revokeSession = useRevokeSession();

  const { data: orgMembershipsData } = useOrgMemberships({ user_id: userId });
  const { data: wsMembershipsData } = useWorkspaceMemberships({ user_id: userId });
  const { data: allOrgs } = useOrgs({ limit: 500 });
  const { data: allWorkspaces } = useWorkspaces({ limit: 500 });
  // Pull a broad set of applications; we filter client-side to the user's orgs.
  // Backend does not yet support app_id-scoped role lookups per user, so we
  // show "apps reachable via org membership" as the best-available heuristic.
  const { data: allApps } = useApplications({ limit: 500 });

  const [appFilter, setAppFilter] = useState<string | null>(null);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [deleteEmailInput, setDeleteEmailInput] = useState("");
  const [confirmStatusOpen, setConfirmStatusOpen] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<"active" | "inactive" | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  function openDeactivate() {
    setPendingStatus("inactive");
    setConfirmStatusOpen(true);
  }

  function openReactivate() {
    setPendingStatus("active");
    setConfirmStatusOpen(true);
  }

  async function handleStatusChange() {
    if (!user || !pendingStatus) return;
    try {
      await updateUser.mutateAsync({ id: user.id, body: { status: pendingStatus } });
      showToast(
        pendingStatus === "active"
          ? "User reactivated successfully."
          : "User deactivated. All sessions revoked.",
        "success",
      );
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Failed to update user status.";
      showToast(msg, "error");
    } finally {
      setConfirmStatusOpen(false);
      setPendingStatus(null);
    }
  }

  async function handleDelete() {
    if (!user) return;
    try {
      await deleteUser.mutateAsync(user.id);
      showToast("User permanently deleted and pseudonymized.", "success");
      router.push("/iam/users");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Failed to delete user.";
      showToast(msg, "error");
    } finally {
      setConfirmDeleteOpen(false);
      setDeleteEmailInput("");
    }
  }

  async function handleRevoke(sessionId: string) {
    setRevokingId(sessionId);
    try {
      await revokeSession.mutateAsync(sessionId);
      showToast("Session revoked.", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Failed to revoke session.";
      showToast(msg, "error");
    } finally {
      setRevokingId(null);
    }
  }

  if (isLoading) {
    return (
      <>
        <PageHeader title="User" description="Loading…" testId="heading-user-detail" />
        <div className="px-8 py-6 space-y-3">
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
          <Skeleton className="h-32 w-full" />
        </div>
      </>
    );
  }

  if (isError || !user) {
    return (
      <>
        <PageHeader title="User" description="Not found" testId="heading-user-detail" />
        <div className="px-8 py-6">
          <ErrorState
            message={error instanceof Error ? error.message : "User not found."}
          />
        </div>
      </>
    );
  }

  const initial = (user.display_name?.trim() || user.email?.trim() || user.id)
    .slice(0, 1)
    .toUpperCase();

  const deleteEmailMatches = deleteEmailInput === (user.email ?? "");

  const sessions = sessionsData?.items ?? [];
  const orgMemberships = orgMembershipsData?.items ?? [];
  const wsMemberships = wsMembershipsData?.items ?? [];

  return (
    <>
      <PageHeader
        title={user.display_name ?? user.id}
        description={user.email ?? "No email"}
        testId="heading-user-detail"
        breadcrumbs={[
          { label: "IAM", href: "/iam/users" },
          { label: "Users", href: "/iam/users" },
          { label: user.display_name ?? user.email ?? user.id.slice(0, 8) },
        ]}
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6 animate-fade-in">
        <div className="mb-5">
          <ApplicationScopeBar
            appId={appFilter}
            onChange={setAppFilter}
            label="Show user's roles in application"
          />
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-4">
          <StatCard
            label="Status"
            value={user.is_active ? "Active" : "Inactive"}
            sub="account state"
            accent={user.is_active ? "green" : "red"}
          />
          <StatCard
            label="Auth Type"
            value={ACCOUNT_TYPE_LABELS[user.account_type] ?? user.account_type}
            sub="authentication method"
            accent="blue"
          />
          <StatCard
            label="Created"
            value={user.created_at.slice(0, 10)}
            sub={`ID: ${user.id.slice(0, 8)}…`}
            accent="blue"
          />
        </div>

        {/* Profile card */}
        <section
          className="rounded-lg p-6"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
          data-testid="user-profile-section"
        >
          <h2
            className="label-caps mb-5"
            style={{ color: "var(--text-secondary)" }}
          >
            Profile
          </h2>

          {/* Avatar + name header */}
          <div className="flex items-center gap-4 mb-6">
            {user.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={user.avatar_url}
                alt=""
                className="h-14 w-14 rounded-full object-cover"
                style={{ border: "2px solid var(--border-bright)" }}
              />
            ) : (
              <div
                className="flex h-14 w-14 items-center justify-center rounded-full text-xl font-bold"
                style={{
                  background: "var(--accent-muted)",
                  color: "var(--accent)",
                  border: "2px solid var(--accent-dim)",
                }}
              >
                {initial}
              </div>
            )}
            <div>
              <p
                className="text-lg font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {user.display_name ?? "—"}
              </p>
              <p
                className="text-sm"
                style={{ color: "var(--text-secondary)" }}
              >
                {user.email ?? "no email set"}
              </p>
            </div>
            <div className="ml-auto flex items-center gap-2" data-testid="user-status-section">
              <Badge
                tone={user.is_active ? "success" : "warning"}
                dot={user.is_active}
                data-testid="user-status-badge"
              >
                {user.is_active ? "Active" : "Inactive"}
              </Badge>
              {user.is_active ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={openDeactivate}
                  data-testid="btn-deactivate"
                >
                  Deactivate
                </Button>
              ) : (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={openReactivate}
                  data-testid="btn-reactivate"
                >
                  Reactivate
                </Button>
              )}
              <Button
                variant="danger"
                size="sm"
                onClick={() => {
                  setDeleteEmailInput("");
                  setConfirmDeleteOpen(true);
                }}
                data-testid="btn-delete"
              >
                Delete
              </Button>
            </div>
          </div>

          {/* Detail grid */}
          <div
            className="grid grid-cols-2 gap-x-8 gap-y-4 pt-5"
            style={{ borderTop: "1px solid var(--border)" }}
          >
            <div>
              <p
                className="label-caps mb-1"
                style={{ color: "var(--text-muted)" }}
              >
                User ID
              </p>
              <p
                className="font-mono-data text-xs"
                style={{ color: "var(--text-secondary)" }}
                data-testid="user-id"
              >
                {user.id}
              </p>
            </div>
            <div>
              <p
                className="label-caps mb-1"
                style={{ color: "var(--text-muted)" }}
              >
                Account Type
              </p>
              <p
                className="text-sm"
                style={{ color: "var(--text-primary)" }}
                data-testid="user-account-type"
              >
                {ACCOUNT_TYPE_LABELS[user.account_type] ?? user.account_type}
              </p>
            </div>
            <div>
              <p
                className="label-caps mb-1"
                style={{ color: "var(--text-muted)" }}
              >
                Email
              </p>
              <p
                className="text-sm"
                style={{ color: "var(--text-primary)" }}
                data-testid="user-email"
              >
                {user.email ?? "—"}
              </p>
            </div>
            <div>
              <p
                className="label-caps mb-1"
                style={{ color: "var(--text-muted)" }}
              >
                Display Name
              </p>
              <p
                className="text-sm"
                style={{ color: "var(--text-primary)" }}
                data-testid="user-display-name"
              >
                {user.display_name ?? "—"}
              </p>
            </div>
            <div>
              <p
                className="label-caps mb-1"
                style={{ color: "var(--text-muted)" }}
              >
                Created
              </p>
              <p
                className="font-mono-data text-xs"
                style={{ color: "var(--text-secondary)" }}
              >
                {user.created_at}
              </p>
            </div>
            <div>
              <p
                className="label-caps mb-1"
                style={{ color: "var(--text-muted)" }}
              >
                Last Updated
              </p>
              <p
                className="font-mono-data text-xs"
                style={{ color: "var(--text-secondary)" }}
              >
                {user.updated_at}
              </p>
            </div>
          </div>
        </section>

        {/* Active Sessions section */}
        <section
          className="rounded-lg p-6"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
          data-testid="user-sessions-section"
        >
          <div className="mb-5 flex items-center justify-between">
            <h2
              className="label-caps"
              style={{ color: "var(--text-secondary)" }}
            >
              Active Sessions
              <span
                className="ml-2 rounded px-1.5 py-0.5 font-mono-data"
                style={{
                  background: "var(--bg-elevated)",
                  color: "var(--text-muted)",
                  fontSize: "10px",
                }}
              >
                {sessions.filter((s) => s.is_active).length}
              </span>
            </h2>
            <Link
              href={`/iam/users/${userId}/sessions`}
              className="text-xs hover:underline"
              style={{ color: "var(--accent)" }}
            >
              View all sessions →
            </Link>
          </div>

          {sessions.length === 0 ? (
            <EmptyState
              title="No sessions"
              description="No sessions found."
            />
          ) : (
            <Table>
              <THead>
                <tr>
                  <TH>Created</TH>
                  <TH>Last Active</TH>
                  <TH>IP Address</TH>
                  <TH>Device / UA</TH>
                  <TH>Status</TH>
                  <TH>Action</TH>
                </tr>
              </THead>
              <TBody>
                {sessions.map((session) => (
                  <TR
                    key={session.id}
                    style={
                      session.is_active
                        ? { borderLeft: "2px solid var(--accent)" }
                        : undefined
                    }
                    data-testid={`session-row-${session.id}`}
                  >
                    <TD>
                      <span className="font-mono-data text-xs" style={{ color: "var(--text-secondary)" }}>
                        {session.created_at.slice(0, 16).replace("T", " ")}
                      </span>
                    </TD>
                    <TD>
                      <span className="font-mono-data text-xs" style={{ color: "var(--text-secondary)" }}>
                        {session.last_activity_at
                          ? session.last_activity_at.slice(0, 16).replace("T", " ")
                          : "—"}
                      </span>
                    </TD>
                    <TD>
                      <span className="font-mono-data text-xs" style={{ color: "var(--text-secondary)" }}>
                        {session.ip_address ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="text-xs"
                        style={{
                          color: "var(--text-secondary)",
                          display: "block",
                          maxWidth: "200px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                        title={session.user_agent ?? undefined}
                      >
                        {session.user_agent
                          ? session.user_agent.slice(0, 40) + (session.user_agent.length > 40 ? "…" : "")
                          : "—"}
                      </span>
                    </TD>
                    <TD>
                      <Badge
                        tone={session.is_active ? "success" : session.revoked_at ? "danger" : "default"}
                        dot={session.is_active}
                      >
                        {session.is_active ? "active" : session.revoked_at ? "revoked" : "expired"}
                      </Badge>
                    </TD>
                    <TD>
                      {session.is_active ? (
                        <Button
                          variant="danger"
                          size="sm"
                          loading={revokingId === session.id}
                          onClick={() => handleRevoke(session.id)}
                          data-testid={`btn-revoke-${session.id}`}
                        >
                          Revoke
                        </Button>
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>—</span>
                      )}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </section>

        {/* Memberships section */}
        <section
          className="rounded-lg p-6"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
          data-testid="user-memberships-section"
        >
          <h2
            className="label-caps mb-5"
            style={{ color: "var(--text-secondary)" }}
          >
            Memberships
          </h2>

          {orgMemberships.length === 0 && wsMemberships.length === 0 ? (
            <EmptyState
              title="No memberships"
              description="This user does not belong to any org or workspace yet."
            />
          ) : (
            <div className="space-y-4">
              {orgMemberships.length > 0 && (
                <div>
                  <p
                    className="text-xs font-medium mb-2"
                    style={{ color: "var(--text-muted)" }}
                  >
                    Organisations
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {orgMemberships.map((m) => {
                      const org = allOrgs?.items.find((o) => o.id === m.org_id);
                      return (
                        <Link
                          key={m.id}
                          href={`/iam/orgs/${m.org_id}`}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                            padding: "4px 10px",
                            background: "var(--bg-elevated)",
                            border: "1px solid var(--border)",
                            borderRadius: "6px",
                            textDecoration: "none",
                            fontSize: "12px",
                            color: "var(--accent)",
                          }}
                        >
                          {org?.display_name ?? org?.slug ?? m.org_id.slice(0, 8)}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              )}

              {wsMemberships.length > 0 && (
                <div>
                  <p
                    className="text-xs font-medium mb-2"
                    style={{ color: "var(--text-muted)" }}
                  >
                    Workspaces
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {wsMemberships.map((m) => {
                      const ws = allWorkspaces?.items.find((w) => w.id === m.workspace_id);
                      return (
                        <Link
                          key={m.id}
                          href={`/iam/workspaces/${m.workspace_id}`}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                            padding: "4px 10px",
                            background: "var(--bg-elevated)",
                            border: "1px solid var(--border)",
                            borderRadius: "6px",
                            textDecoration: "none",
                            fontSize: "12px",
                            color: "var(--success)",
                          }}
                        >
                          {ws?.display_name ?? ws?.slug ?? m.workspace_id.slice(0, 8)}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Applications & Roles section */}
        <section
          className="rounded-lg p-6"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
          data-testid="user-applications-section"
        >
          <div className="mb-5 flex items-center justify-between">
            <h2
              className="label-caps"
              style={{ color: "var(--text-secondary)" }}
            >
              Applications & Roles
            </h2>
            <p
              className="text-xs"
              style={{ color: "var(--text-muted)" }}
            >
              Apps reachable via this user&apos;s org memberships
            </p>
          </div>

          {(() => {
            const userOrgIds = new Set(orgMemberships.map((m) => m.org_id));
            const apps = (allApps?.items ?? []).filter((a) =>
              a.org_id ? userOrgIds.has(a.org_id) : false,
            );

            if (apps.length === 0) {
              return (
                <EmptyState
                  title="No applications"
                  description="This user is not a member of any org that owns applications."
                />
              );
            }

            return (
              <Table>
                <THead>
                  <tr>
                    <TH>Application</TH>
                    <TH>Organisation</TH>
                    <TH>Roles</TH>
                    <TH>Hub</TH>
                  </tr>
                </THead>
                <TBody>
                  {apps.map((app) => {
                    const org = allOrgs?.items.find((o) => o.id === app.org_id);
                    // Role per-application isn't modelled yet (ADR-018 roadmap).
                    // Best-available signal: show a "member" badge if the user
                    // belongs to the app's org. Real role codes will surface
                    // once application_id is added to role assignments.
                    const rolesForOrg = orgMemberships
                      .filter((m) => m.org_id === app.org_id)
                      .map(() => "member");
                    return (
                      <TR key={app.id} data-testid={`user-app-row-${app.id}`}>
                        <TD>
                          <div className="flex items-center gap-2">
                            <AppAvatar code={app.code} size={20} />
                            <div>
                              <p
                                className="text-sm font-medium"
                                style={{ color: "var(--text-primary)" }}
                              >
                                {app.label ?? app.code ?? app.id.slice(0, 8)}
                              </p>
                              <p
                                className="font-mono-data text-xs"
                                style={{ color: "var(--text-muted)" }}
                              >
                                {app.code ?? "—"}
                              </p>
                            </div>
                          </div>
                        </TD>
                        <TD>
                          <span
                            className="text-xs"
                            style={{ color: "var(--text-secondary)" }}
                          >
                            {org?.display_name ?? org?.slug ?? app.org_id.slice(0, 8)}
                          </span>
                        </TD>
                        <TD>
                          {rolesForOrg.length === 0 ? (
                            <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>
                              —
                            </span>
                          ) : (
                            <div className="flex flex-wrap gap-1">
                              {rolesForOrg.map((role, i) => (
                                <Badge key={`${app.id}-${role}-${i}`} tone="blue">
                                  {role}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </TD>
                        <TD>
                          <Link
                            href={`/iam/applications/${app.id}`}
                            className="text-xs hover:underline"
                            style={{ color: "var(--accent)" }}
                            data-testid={`user-app-hub-${app.id}`}
                          >
                            Hub →
                          </Link>
                        </TD>
                      </TR>
                    );
                  })}
                </TBody>
              </Table>
            );
          })()}
        </section>

        {/* Audit trail link */}
        <Link
          href={`/audit?actor_user_id=${userId}`}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 20px",
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            textDecoration: "none",
          }}
          data-testid="user-audit-link"
        >
          <div>
            <p
              className="text-sm font-medium"
              style={{ color: "var(--text-primary)" }}
            >
              Audit History
            </p>
            <p
              className="text-xs mt-0.5"
              style={{ color: "var(--text-secondary)" }}
            >
              All actions performed by this user
            </p>
          </div>
          <span style={{ color: "#ff6b35", fontSize: "14px" }}>View audit history →</span>
        </Link>
      </div>

      {/* Deactivate / Reactivate confirmation modal */}
      <Modal
        open={confirmStatusOpen}
        onClose={() => setConfirmStatusOpen(false)}
        title={pendingStatus === "active" ? "Reactivate user?" : "Deactivate user?"}
      >
        <div className="space-y-4">
          {pendingStatus === "inactive" ? (
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Deactivating will immediately revoke all active sessions. The user
              will be blocked from signing in until reactivated. Their data is
              preserved.
            </p>
          ) : (
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              The user will be able to sign in again. No sessions are restored
              automatically.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => setConfirmStatusOpen(false)}
              data-testid="btn-cancel-status"
            >
              Cancel
            </Button>
            <Button
              variant={pendingStatus === "inactive" ? "danger" : "primary"}
              onClick={handleStatusChange}
              loading={updateUser.isPending}
              data-testid="btn-confirm-status"
            >
              {pendingStatus === "active" ? "Reactivate" : "Deactivate"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete confirmation modal — requires typing email */}
      <Modal
        open={confirmDeleteOpen}
        onClose={() => setConfirmDeleteOpen(false)}
        title="Permanently delete user"
      >
        <div className="space-y-4">
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            This action is <strong style={{ color: "var(--danger)" }}>irreversible</strong>. The user&apos;s email and
            display name will be pseudonymized. Audit history is preserved.
          </p>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Type the user&apos;s email address to confirm:
          </p>
          <Field label={`Email: ${user.email ?? "—"}`}>
            <Input
              value={deleteEmailInput}
              onChange={(e) => setDeleteEmailInput(e.target.value)}
              placeholder={user.email ?? ""}
              data-testid="input-confirm-email"
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => {
                setConfirmDeleteOpen(false);
                setDeleteEmailInput("");
              }}
              data-testid="btn-cancel-delete"
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              disabled={!deleteEmailMatches}
              loading={deleteUser.isPending}
              data-testid="btn-confirm-delete"
            >
              Permanently Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
