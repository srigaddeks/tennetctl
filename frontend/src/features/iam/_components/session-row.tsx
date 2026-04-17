"use client";

import { Button, Badge, TD, TR } from "@/components/ui";
import type { SessionReadShape } from "@/types/api";

type Props = {
  session: SessionReadShape;
  isCurrent: boolean;
  onRevoke: (id: string) => void;
  isRevoking: boolean;
};

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function SessionRow({ session, isCurrent, onRevoke, isRevoking }: Props) {
  return (
    <TR data-testid={`session-row-${session.id}`}>
      <TD>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-zinc-500">{session.id.slice(0, 8)}…</span>
          {isCurrent && (
            <span data-testid="badge-current-session"><Badge tone="emerald">
              This device
            </Badge></span>
          )}
        </div>
      </TD>
      <TD>
        <span className="text-sm text-zinc-600 dark:text-zinc-400">
          {relativeTime(session.created_at)}
        </span>
      </TD>
      <TD>
        <span className="text-sm text-zinc-600 dark:text-zinc-400">
          {relativeTime(session.updated_at)}
        </span>
      </TD>
      <TD>
        {session.is_valid ? (
          <Badge tone="emerald">Active</Badge>
        ) : (
          <Badge tone="red">Revoked</Badge>
        )}
      </TD>
      <TD>
        {isCurrent ? (
          <span className="text-xs text-zinc-400">Current</span>
        ) : (
          <Button
            variant="danger"
            size="sm"
            data-testid={`btn-revoke-session-${session.id}`}
            onClick={() => onRevoke(session.id)}
            disabled={isRevoking}
          >
            Sign out
          </Button>
        )}
      </TD>
    </TR>
  );
}
