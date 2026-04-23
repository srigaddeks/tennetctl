"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ChevronDown } from "lucide-react";

import { FEATURES, activeFeature } from "@/config/features";
import { useMe, useSignout } from "@/features/auth/hooks/use-auth";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { useWorkspaces } from "@/features/iam-workspaces/hooks/use-workspaces";
import { NotificationBell } from "@/features/notify/_components/notification-bell";
import { CriticalBanner } from "@/features/notify/_components/notification-list";
import { useInAppNotifications } from "@/features/notify/hooks/use-in-app-notifications";
import { cn } from "@/lib/cn";
import { useWorkspaceContext } from "@/lib/workspace-context";

function abbrev(s: string | null | undefined, max = 12): string {
  if (!s) return "";
  return s.length > max ? s.slice(0, max) + "…" : s;
}

function WorkspaceSelector() {
  const { orgId, workspaceId, setOrgId, setWorkspaceId } = useWorkspaceContext();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const orgs = useOrgs({ limit: 100 });
  const workspaces = useWorkspaces({ org_id: orgId, limit: 100 });

  const orgList = orgs.data?.items ?? [];
  const wsList  = workspaces.data?.items ?? [];

  const selectedOrg = orgList.find((o) => o.id === orgId) ?? null;
  const selectedWs  = wsList.find((w) => w.id === workspaceId) ?? null;

  function handleOrgPick(id: string) {
    setOrgId(id);
    setWorkspaceId(null);
  }

  function handleWsPick(id: string) {
    setWorkspaceId(id);
    setOpen(false);
  }

  // Close on outside click
  function handleBlur(e: React.FocusEvent) {
    if (!ref.current?.contains(e.relatedTarget as Node)) {
      setOpen(false);
    }
  }

  const orgLabel  = selectedOrg  ? abbrev(selectedOrg.display_name ?? selectedOrg.slug)   : null;
  const wsLabel   = selectedWs   ? abbrev(selectedWs.display_name ?? selectedWs.slug)      : null;

  return (
    <div
      ref={ref}
      className="relative shrink-0"
      onBlur={handleBlur}
      data-testid="workspace-selector"
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px] transition"
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid var(--border)",
          color: orgLabel ? "var(--text-primary)" : "var(--text-muted)",
          fontFamily: "var(--font-sans)",
        }}
        data-testid="workspace-selector-trigger"
      >
        {orgLabel ? (
          <>
            <span style={{ color: "var(--text-secondary)" }}>{orgLabel}</span>
            {wsLabel && (
              <>
                <span style={{ color: "var(--border-bright)" }}>›</span>
                <span style={{ color: "var(--text-primary)" }}>{wsLabel}</span>
              </>
            )}
          </>
        ) : (
          <span>Select org</span>
        )}
        <ChevronDown className="h-3 w-3 shrink-0" style={{ color: "var(--text-muted)" }} />
      </button>

      {open && (
        <div
          className="absolute left-0 top-full z-50 mt-1 w-64 overflow-hidden rounded-xl"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-bright)",
            boxShadow: "0 12px 32px rgba(0,0,0,0.5)",
          }}
          data-testid="workspace-selector-dropdown"
        >
          {/* Orgs section */}
          <div
            className="px-3 py-2 text-[10px] tracking-widest uppercase"
            style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}
          >
            Organisations
          </div>
          {orgs.isLoading && (
            <div className="px-3 py-2 text-xs" style={{ color: "var(--text-muted)" }}>Loading…</div>
          )}
          {orgList.map((org) => (
            <button
              key={org.id}
              type="button"
              onClick={() => handleOrgPick(org.id)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition"
              style={
                org.id === orgId
                  ? { background: "var(--accent-muted)", color: "var(--accent)" }
                  : { color: "var(--text-secondary)" }
              }
              onMouseEnter={(e) => {
                if (org.id !== orgId) (e.currentTarget as HTMLElement).style.background = "var(--bg-elevated)";
              }}
              onMouseLeave={(e) => {
                if (org.id !== orgId) (e.currentTarget as HTMLElement).style.background = "transparent";
              }}
              data-testid={`org-option-${org.slug}`}
            >
              {org.id === orgId && (
                <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: "var(--accent)" }} />
              )}
              <span className="truncate">{org.display_name ?? org.slug}</span>
            </button>
          ))}
          {!orgs.isLoading && orgList.length === 0 && (
            <div className="px-3 py-2 text-xs" style={{ color: "var(--text-muted)" }}>No organisations</div>
          )}

          {/* Workspaces section — only visible when org selected */}
          {orgId && (
            <>
              <div
                className="px-3 py-2 text-[10px] tracking-widest uppercase"
                style={{
                  color: "var(--text-muted)",
                  borderTop: "1px solid var(--border)",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                Workspaces
              </div>
              {workspaces.isLoading && (
                <div className="px-3 py-2 text-xs" style={{ color: "var(--text-muted)" }}>Loading…</div>
              )}
              {/* All workspaces option */}
              <button
                type="button"
                onClick={() => { setWorkspaceId(null); setOpen(false); }}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition"
                style={
                  workspaceId === null
                    ? { background: "var(--accent-muted)", color: "var(--accent)" }
                    : { color: "var(--text-muted)" }
                }
                onMouseEnter={(e) => {
                  if (workspaceId !== null) (e.currentTarget as HTMLElement).style.background = "var(--bg-elevated)";
                }}
                onMouseLeave={(e) => {
                  if (workspaceId !== null) (e.currentTarget as HTMLElement).style.background = "transparent";
                }}
                data-testid="ws-option-all"
              >
                {workspaceId === null && (
                  <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: "var(--accent)" }} />
                )}
                <span>All workspaces</span>
              </button>
              {wsList.map((ws) => (
                <button
                  key={ws.id}
                  type="button"
                  onClick={() => handleWsPick(ws.id)}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition"
                  style={
                    ws.id === workspaceId
                      ? { background: "var(--accent-muted)", color: "var(--accent)" }
                      : { color: "var(--text-secondary)" }
                  }
                  onMouseEnter={(e) => {
                    if (ws.id !== workspaceId) (e.currentTarget as HTMLElement).style.background = "var(--bg-elevated)";
                  }}
                  onMouseLeave={(e) => {
                    if (ws.id !== workspaceId) (e.currentTarget as HTMLElement).style.background = "transparent";
                  }}
                  data-testid={`ws-option-${ws.slug}`}
                >
                  {ws.id === workspaceId && (
                    <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: "var(--accent)" }} />
                  )}
                  <span className="truncate">{ws.display_name ?? ws.slug}</span>
                </button>
              ))}
              {!workspaces.isLoading && wsList.length === 0 && (
                <div className="px-3 py-2 text-xs" style={{ color: "var(--text-muted)" }}>No workspaces</div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const current = activeFeature(pathname);
  const me = useMe();
  const signout = useSignout();
  const user = me.data?.user ?? null;
  const session = me.data?.session ?? null;

  const notifs = useInAppNotifications(
    user?.id ?? null,
    session?.org_id ?? null,
  );
  const inAppItems = notifs.data?.items ?? [];

  return (
    <>
      <CriticalBanner items={inAppItems} />
      <header
        className="flex h-12 shrink-0 items-center gap-4 border-b px-4"
        style={{
          background: "var(--bg-surface)",
          borderColor: "var(--border)",
        }}
      >
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 shrink-0 group"
          data-testid="topbar-logo"
        >
          <div
            className="flex h-7 w-7 items-center justify-center rounded text-xs font-bold tracking-wider transition-all duration-150 group-hover:shadow-[0_0_12px_rgba(45,126,247,0.4)]"
            style={{
              background: "var(--accent)",
              color: "white",
              fontFamily: "var(--font-mono)",
            }}
          >
            T
          </div>
          <div className="leading-tight hidden sm:block">
            <div
              className="text-[13px] font-semibold tracking-wide"
              style={{ color: "var(--text-primary)" }}
            >
              TennetCTL
            </div>
            <div
              className="text-[9px] tracking-widest uppercase"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              v0.1 · self-hosted
            </div>
          </div>
        </Link>

        {/* Divider */}
        <div
          className="h-5 w-px shrink-0"
          style={{ background: "var(--border)" }}
          aria-hidden
        />

        {/* Workspace context selector */}
        <WorkspaceSelector />

        {/* Divider */}
        <div
          className="h-5 w-px shrink-0"
          style={{ background: "var(--border)" }}
          aria-hidden
        />

        {/* Feature nav */}
        <nav className="hide-scrollbar flex items-center gap-0.5 overflow-x-auto">
          {FEATURES.map((f) => {
            const active = f.key === current.key;
            const landing = f.subFeatures[0]?.href ?? f.basePath;
            return (
              <Link
                key={f.key}
                href={landing}
                data-testid={f.testId}
                className={cn(
                  "whitespace-nowrap rounded px-2.5 py-1 text-[12px] font-medium transition-all duration-100",
                )}
                style={
                  active
                    ? {
                        background: "var(--accent-muted)",
                        color: "var(--accent-hover)",
                        border: "1px solid var(--accent-dim)",
                      }
                    : {
                        color: "var(--text-secondary)",
                        border: "1px solid transparent",
                      }
                }
                onMouseEnter={(e) => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
                    (e.currentTarget as HTMLElement).style.background = "var(--bg-elevated)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                    (e.currentTarget as HTMLElement).style.background = "transparent";
                  }
                }}
              >
                {f.label}
              </Link>
            );
          })}
        </nav>

        {/* Right actions */}
        <div className="ml-auto flex items-center gap-2">
          {/* Command palette trigger */}
          <button
            type="button"
            onClick={() => {
              window.dispatchEvent(
                new KeyboardEvent("keydown", { key: "k", metaKey: true }),
              );
            }}
            className="hidden items-center gap-1.5 rounded border px-2 py-1 text-[11px] transition-colors duration-100 sm:inline-flex"
            style={{
              borderColor: "var(--border)",
              color: "var(--text-muted)",
              background: "var(--bg-base)",
            }}
            data-testid="topbar-cmdk"
            aria-label="Open command palette"
          >
            <span style={{ color: "var(--text-secondary)" }}>Search</span>
            <kbd
              className="rounded px-1 font-mono text-[9px]"
              style={{
                border: "1px solid var(--border)",
                background: "var(--bg-elevated)",
                color: "var(--text-muted)",
              }}
            >
              ⌘K
            </kbd>
          </button>

          {user && (
            <NotificationBell userId={user.id} orgId={session?.org_id ?? null} />
          )}

          {user ? (
            <div className="flex items-center gap-1.5">
              <Link
                href="/account/security"
                className="flex items-center gap-1.5 rounded border px-2 py-1 transition-all duration-100"
                style={{
                  borderColor: "var(--border)",
                  background: "var(--bg-base)",
                }}
                data-testid="topbar-user"
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--border-bright)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                }}
              >
                {user.avatar_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={user.avatar_url}
                    alt=""
                    className="h-5 w-5 rounded-full border object-cover"
                    style={{ borderColor: "var(--border)" }}
                  />
                ) : (
                  <div
                    className="flex h-5 w-5 items-center justify-center rounded text-[10px] font-bold"
                    style={{
                      background: "var(--accent-dim)",
                      color: "var(--accent-hover)",
                    }}
                  >
                    {(user.display_name ?? user.email ?? "?")
                      .slice(0, 1)
                      .toUpperCase()}
                  </div>
                )}
                <div className="leading-tight hidden sm:block">
                  <div
                    className="text-[11px] font-semibold"
                    style={{ color: "var(--text-primary)" }}
                    data-testid="topbar-user-name"
                  >
                    {user.display_name ?? user.email ?? "Anonymous"}
                  </div>
                </div>
              </Link>
              <button
                type="button"
                data-testid="topbar-signout"
                disabled={signout.isPending}
                className="rounded border px-2 py-1 text-[11px] font-medium transition-all duration-100 disabled:opacity-40"
                style={{
                  borderColor: "var(--border)",
                  color: "var(--text-muted)",
                  background: "var(--bg-base)",
                }}
                onClick={async () => {
                  await signout.mutateAsync();
                  router.replace("/auth/signin");
                }}
              >
                {signout.isPending ? "…" : "Sign out"}
              </button>
            </div>
          ) : (
            <Link
              href="/auth/signin"
              data-testid="topbar-signin"
              className="rounded border px-3 py-1 text-[11px] font-medium transition-all duration-100"
              style={{
                borderColor: "var(--accent)",
                color: "var(--accent-hover)",
                background: "var(--accent-muted)",
              }}
            >
              Sign in
            </Link>
          )}
        </div>
      </header>
    </>
  );
}
