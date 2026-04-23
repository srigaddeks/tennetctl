"use client";

import { useState } from "react";

import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
  StatCard,
  TBody,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { SessionRow } from "@/features/iam/_components/session-row";
import {
  useSessions,
  useRevokeSession,
  useRevokeAllOtherSessions,
} from "@/features/iam/hooks/use-sessions";
import { useMe } from "@/features/auth/hooks/use-auth";

export default function SessionsPage() {
  const me = useMe();
  const { data, isLoading, isError, error } = useSessions();
  const revoke = useRevokeSession();
  const revokeAll = useRevokeAllOtherSessions();
  const [revokeAllPending, setRevokeAllPending] = useState(false);

  const currentSessionId = me.data?.session?.id ?? null;
  const items = data?.items ?? [];

  async function handleRevokeAll() {
    if (!currentSessionId) return;
    setRevokeAllPending(true);
    try {
      await revokeAll.mutateAsync(currentSessionId);
    } finally {
      setRevokeAllPending(false);
    }
  }

  const otherCount = items.filter((s) => s.id !== currentSessionId).length;
  const activeCount = items.filter((s) => s.is_valid).length;
  const lastActivity = items.reduce<string | null>((latest, s) => {
    const t = s.last_activity_at ?? s.updated_at;
    if (!latest || t > latest) return t;
    return latest;
  }, null);

  function relativeTime(iso: string | null): string {
    if (!iso) return "—";
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60_000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }

  return (
    <div className="flex flex-1 flex-col animate-fade-in">
      {/* Page header */}
      <div
        className="border-b px-8 py-5"
        style={{
          background: "var(--bg-surface)",
          borderColor: "var(--border)",
        }}
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="label-caps mb-1" style={{ color: "var(--text-muted)" }}>
              Account / Security
            </div>
            <h1
              className="text-xl font-semibold tracking-tight"
              style={{ color: "var(--text-primary)" }}
              data-testid="sessions-heading"
            >
              Active Sessions
            </h1>
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Devices and browsers currently signed in to your account.
            </p>
          </div>
          {otherCount > 0 && (
            <Button
              variant="danger"
              data-testid="btn-revoke-all-sessions"
              onClick={handleRevokeAll}
              disabled={revokeAllPending || revokeAll.isPending}
            >
              Sign out everywhere else ({otherCount})
            </Button>
          )}
        </div>
      </div>

      <div className="mx-auto w-full max-w-5xl px-8 py-6 space-y-6">
        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-4">
          <StatCard
            label="Active Sessions"
            value={isLoading ? "—" : String(activeCount)}
            accent="blue"
          />
          <StatCard
            label="Other Devices"
            value={isLoading ? "—" : String(otherCount)}
            accent={otherCount > 0 ? "amber" : "blue"}
            sub={otherCount > 0 ? "Can be revoked" : "None besides this device"}
          />
          <StatCard
            label="Last Activity"
            value={isLoading ? "—" : relativeTime(lastActivity)}
            accent="green"
          />
        </div>

        {/* Content */}
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        )}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Failed to load sessions"}
          />
        )}

        {!isLoading && !isError && items.length === 0 && (
          <EmptyState
            title="No active sessions"
            description="No other sessions found for your account."
          />
        )}

        {items.length > 0 && (
          <div
            className="rounded overflow-hidden"
            style={{ border: "1px solid var(--border)" }}
          >
            <Table>
              <THead>
                <tr>
                  <TH>Device</TH>
                  <TH>IP Address</TH>
                  <TH>Signed in</TH>
                  <TH>Last active</TH>
                  <TH>Status</TH>
                  <TH>Actions</TH>
                </tr>
              </THead>
              <TBody>
                {items.map((session) => (
                  <SessionRow
                    key={session.id}
                    session={session}
                    isCurrent={session.id === currentSessionId}
                    onRevoke={(id) => revoke.mutate(id)}
                    isRevoking={revoke.isPending && revoke.variables === session.id}
                  />
                ))}
              </TBody>
            </Table>
          </div>
        )}

        {/* Security notice */}
        <div
          className="flex items-start gap-3 rounded px-4 py-3 text-xs"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
          }}
        >
          <span style={{ color: "var(--info)", fontSize: "14px", flexShrink: 0 }}>ⓘ</span>
          <span>
            If you notice a session you don't recognize, revoke it immediately and change your password.
            Each session is bound to the IP and device it was created from.
          </span>
        </div>
      </div>
    </div>
  );
}
