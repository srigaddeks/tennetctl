"use client";

import { Button, Badge, TD, TR } from "@/components/ui";
import type { SessionReadShape } from "@/types/api";

type Props = {
  session: SessionReadShape;
  isCurrent: boolean;
  onRevoke: (id: string) => void;
  isRevoking: boolean;
};

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

/**
 * Parse a User-Agent into a short "Chrome on macOS" label.
 * Conservative — avoids pulling ua-parser-js for 6 platform checks.
 */
function deviceLabel(ua: string | null): { device: string; os: string } {
  if (!ua) return { device: "Unknown", os: "" };
  const u = ua.toLowerCase();

  let device = "Browser";
  if (u.includes("firefox/")) device = "Firefox";
  else if (u.includes("edg/")) device = "Edge";
  else if (u.includes("opr/") || u.includes("opera/")) device = "Opera";
  else if (u.includes("chrome/") && !u.includes("edg/")) device = "Chrome";
  else if (u.includes("safari/") && !u.includes("chrome/")) device = "Safari";
  else if (u.startsWith("curl/")) device = "curl";
  else if (u.includes("python-requests") || u.includes("httpx/")) device = "Python SDK";
  else if (u.includes("node-fetch") || u.includes("axios")) device = "Node SDK";

  let os = "";
  if (u.includes("mac os x") || u.includes("macintosh")) os = "macOS";
  else if (u.includes("windows")) os = "Windows";
  else if (u.includes("android")) os = "Android";
  else if (u.includes("iphone") || u.includes("ipad") || u.includes("ios")) os = "iOS";
  else if (u.includes("linux")) os = "Linux";

  return { device, os };
}

export function SessionRow({ session, isCurrent, onRevoke, isRevoking }: Props) {
  const { device, os } = deviceLabel(session.user_agent);
  const lastActive = session.last_activity_at ?? session.updated_at;
  return (
    <TR data-testid={`session-row-${session.id}`}>
      <TD>
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
              {device}
              {os && <span className="text-zinc-500 dark:text-zinc-400"> · {os}</span>}
            </span>
            {isCurrent && (
              <span data-testid="badge-current-session">
                <Badge tone="emerald">This device</Badge>
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-[11px] text-zinc-500">
            {session.ip_address && (
              <span className="font-mono">{session.ip_address}</span>
            )}
            <span
              className="font-mono text-zinc-400"
              title={session.id}
            >
              {session.id.slice(0, 8)}
            </span>
          </div>
        </div>
      </TD>
      <TD>
        <span
          className="text-sm text-zinc-600 dark:text-zinc-400"
          title={new Date(session.created_at).toLocaleString()}
        >
          {relativeTime(session.created_at)}
        </span>
      </TD>
      <TD>
        <span
          className="text-sm text-zinc-600 dark:text-zinc-400"
          title={new Date(lastActive).toLocaleString()}
        >
          {relativeTime(lastActive)}
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
