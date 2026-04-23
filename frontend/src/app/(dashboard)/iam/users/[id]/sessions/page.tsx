"use client";

import Link from "next/link";
import { useState } from "react";
import { useParams } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { useUser } from "@/features/iam-users/hooks/use-users";
import {
  useSessions,
  useRevokeSession,
} from "@/features/iam-sessions/hooks/use-sessions";
import { ApiClientError } from "@/lib/api";

export default function UserSessionsPage() {
  const params = useParams();
  const userId = typeof params.id === "string" ? params.id : "";
  const { toast: showToast } = useToast();

  const { data: user, isLoading: userLoading, isError: userError } = useUser(userId);
  const {
    data: sessionsData,
    isLoading: sessionsLoading,
    isError: sessionsIsError,
  } = useSessions({ user_id: userId, limit: 200 });
  const revokeSession = useRevokeSession();

  const [revokingId, setRevokingId] = useState<string | null>(null);

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

  const userName = user?.display_name ?? user?.email ?? userId.slice(0, 8);
  const sessions = sessionsData?.items ?? [];
  const activeSessions = sessions.filter((s) => s.is_active);

  if (userLoading || sessionsLoading) {
    return (
      <>
        <PageHeader
          title="Sessions"
          description="Loading…"
          testId="heading-user-sessions"
        />
        <div className="px-8 py-6 space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </>
    );
  }

  if (userError || sessionsIsError) {
    return (
      <>
        <PageHeader
          title="Sessions"
          description="Error"
          testId="heading-user-sessions"
        />
        <div className="px-8 py-6">
          <ErrorState message="Failed to load sessions." />
          <div className="mt-4">
            <Link
              href={`/iam/users/${userId}`}
              style={{ color: "var(--text-secondary)" }}
              className="text-sm hover:underline"
            >
              ← Back to user
            </Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Sessions"
        description={`All sessions for ${userName}`}
        testId="heading-user-sessions"
        breadcrumbs={[
          { label: "IAM", href: "/iam/users" },
          { label: "Users", href: "/iam/users" },
          { label: userName, href: `/iam/users/${userId}` },
          { label: "Sessions" },
        ]}
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in" data-testid="user-sessions-body">

        {/* Summary bar */}
        <div className="mb-6 flex items-center gap-6">
          <div>
            <p className="label-caps" style={{ color: "var(--text-muted)" }}>
              Total
            </p>
            <p
              className="text-2xl font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              {sessions.length}
            </p>
          </div>
          <div
            style={{
              width: "1px",
              height: "36px",
              background: "var(--border)",
            }}
          />
          <div>
            <p className="label-caps" style={{ color: "var(--text-muted)" }}>
              Active
            </p>
            <p
              className="text-2xl font-semibold"
              style={{ color: "var(--success)" }}
            >
              {activeSessions.length}
            </p>
          </div>
          <div
            style={{
              width: "1px",
              height: "36px",
              background: "var(--border)",
            }}
          />
          <div>
            <p className="label-caps" style={{ color: "var(--text-muted)" }}>
              Revoked / Expired
            </p>
            <p
              className="text-2xl font-semibold"
              style={{ color: "var(--text-secondary)" }}
            >
              {sessions.length - activeSessions.length}
            </p>
          </div>
        </div>

        {/* Sessions table */}
        <section
          className="rounded-lg p-6"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
        >
          {sessions.length === 0 ? (
            <EmptyState
              title="No sessions"
              description="No sessions found for this user."
            />
          ) : (
            <Table>
              <THead>
                <tr>
                  <TH>Created</TH>
                  <TH>Last Active</TH>
                  <TH>Expires</TH>
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
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {session.created_at.slice(0, 16).replace("T", " ")}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {session.last_activity_at
                          ? session.last_activity_at.slice(0, 16).replace("T", " ")
                          : "—"}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {session.expires_at.slice(0, 16).replace("T", " ")}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {session.ip_address ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="text-xs"
                        style={{
                          color: "var(--text-secondary)",
                          display: "block",
                          maxWidth: "220px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                        title={session.user_agent ?? undefined}
                      >
                        {session.user_agent
                          ? session.user_agent.slice(0, 50) +
                            (session.user_agent.length > 50 ? "…" : "")
                          : "—"}
                      </span>
                    </TD>
                    <TD>
                      <Badge
                        tone={
                          session.is_active
                            ? "success"
                            : session.revoked_at
                            ? "danger"
                            : "default"
                        }
                        dot={session.is_active}
                      >
                        {session.is_active
                          ? "active"
                          : session.revoked_at
                          ? "revoked"
                          : "expired"}
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
                        <span
                          style={{ color: "var(--text-muted)", fontSize: "12px" }}
                        >
                          —
                        </span>
                      )}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </section>
      </div>
    </>
  );
}
