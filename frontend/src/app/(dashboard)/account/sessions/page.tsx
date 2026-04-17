"use client";

import { useState } from "react";

import {
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
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

  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-zinc-200 bg-white px-8 py-6 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between">
          <div>
            <h1
              className="text-xl font-semibold tracking-tight"
              data-testid="sessions-heading"
            >
              Active Sessions
            </h1>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
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

      <div className="mx-auto w-full max-w-4xl px-8 py-6">
        {isLoading && <Skeleton className="h-16 w-full" />}
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
          <Table>
            <THead>
              <tr>
                <TH>Session</TH>
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
        )}
      </div>
    </div>
  );
}
