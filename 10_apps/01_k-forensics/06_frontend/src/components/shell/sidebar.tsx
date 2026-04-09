"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Building2, Layers, ChevronDown, ChevronUp,
  LogOut, Settings, Moon, Sun,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useAuth } from "@/lib/auth-context";
import { listOrgs, listWorkspaces } from "@/lib/api";
import { NAV_GROUPS } from "./nav-config";
import { useSidebar } from "./sidebar-context";
import { cn } from "@/lib/cn";
import type { OrgData, WorkspaceData } from "@/types/api";

export function Sidebar() {
  const pathname = usePathname() ?? "";
  const { open, close } = useSidebar();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border bg-surface md:flex">
        <SidebarContent pathname={pathname} />
      </aside>

      {/* Mobile drawer */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-border bg-surface shadow-lg transition-transform duration-200 md:hidden",
          open ? "translate-x-0" : "-translate-x-full"
        )}
        aria-modal={open}
        role="dialog"
        aria-label="Navigation"
      >
        <SidebarContent pathname={pathname} onNavigate={close} />
      </aside>
    </>
  );
}

function SidebarContent({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate?: () => void;
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* App branding */}
      <div className="flex items-center gap-2.5 border-b border-border px-4 py-3.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-foreground text-background">
          <span className="text-xs font-black">KF</span>
        </div>
        <div className="min-w-0 flex-1">
          <span className="text-sm font-semibold text-foreground">k-forensics</span>
          <p className="truncate text-[10px] text-foreground-muted">Digital forensics platform</p>
        </div>
      </div>

      {/* Scope switcher */}
      <ScopeSwitcher />

      {/* Nav groups */}
      <nav className="flex-1 overflow-y-auto py-2" aria-label="Main navigation">
        {NAV_GROUPS.map((group) => (
          <div key={group.label} className="mb-1">
            <div className="px-4 pb-1 pt-3">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-foreground-subtle">
                {group.label}
              </span>
            </div>
            <ul className="space-y-px px-2">
              {group.items.map((item) => {
                const isActive =
                  (item.href === "/" && pathname === "/") ||
                  (item.href !== "/" && (pathname === item.href || pathname.startsWith(`${item.href}/`)));
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      className={cn(
                        "group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] transition-colors",
                        isActive
                          ? "bg-surface-3 font-medium text-foreground"
                          : "text-foreground-muted hover:bg-surface-2 hover:text-foreground"
                      )}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <Icon
                        className={cn(
                          "h-4 w-4 shrink-0 transition-colors",
                          isActive
                            ? "text-foreground"
                            : "text-foreground-subtle group-hover:text-foreground-muted"
                        )}
                      />
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.badge && (
                        <span className="rounded-sm border border-border bg-surface-2 px-1 py-px font-mono text-[9px] text-foreground-subtle">
                          {item.badge}
                        </span>
                      )}
                      {isActive && (
                        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-foreground" />
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* User profile popup at bottom */}
      <UserProfileFooter />
    </div>
  );
}

function ScopeSwitcher() {
  const auth = useAuth();
  const [open, setOpen] = React.useState(false);
  const [orgs, setOrgs] = React.useState<OrgData[]>([]);
  const [workspaces, setWorkspaces] = React.useState<WorkspaceData[]>([]);
  const [selectedOrgId, setSelectedOrgId] = React.useState<string | null>(null);
  const router = useRouter();

  const accessToken = auth.status === "authenticated" ? auth.accessToken : null;

  const currentOrgName = React.useMemo(() => {
    if (typeof window === "undefined") return "—";
    const token = localStorage.getItem("kf_access");
    if (!token) return "—";
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.org_name ?? payload.oid?.slice(0, 8) ?? "—";
    } catch {
      return "—";
    }
  }, []);

  const currentWsName = React.useMemo(() => {
    if (typeof window === "undefined") return "—";
    const token = localStorage.getItem("kf_access");
    if (!token) return "—";
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.ws_name ?? payload.wid?.slice(0, 8) ?? "—";
    } catch {
      return "—";
    }
  }, []);

  async function handleOpen() {
    setOpen(true);
    if (!accessToken || orgs.length > 0) return;
    const res = await listOrgs(accessToken);
    if (res.ok) {
      setOrgs(res.data.items);
      if (res.data.items.length > 0) {
        const firstOrgId = res.data.items[0].id;
        setSelectedOrgId(firstOrgId);
        const wsRes = await listWorkspaces(accessToken, firstOrgId);
        if (wsRes.ok) setWorkspaces(wsRes.data.items);
      }
    }
  }

  async function handleOrgSelect(orgId: string) {
    if (!accessToken) return;
    setSelectedOrgId(orgId);
    const wsRes = await listWorkspaces(accessToken, orgId);
    if (wsRes.ok) setWorkspaces(wsRes.data.items);
  }

  function handleScopeSwitch(orgId: string, wsId: string) {
    setOpen(false);
    router.push(`/?org_id=${orgId}&workspace_id=${wsId}`);
  }

  if (auth.status !== "authenticated") return null;

  return (
    <div className="relative border-b border-border">
      <button
        className="flex items-center gap-2 w-full px-4 py-2.5 text-left transition-colors hover:bg-surface-2"
        onClick={handleOpen}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 text-[11px] text-foreground-muted">
            <Building2 size={11} />
            <span className="truncate">{currentOrgName}</span>
            <span className="text-foreground-subtle">/</span>
            <Layers size={11} />
            <span className="truncate">{currentWsName}</span>
          </div>
        </div>
        <ChevronDown size={12} className="text-foreground-subtle shrink-0" />
      </button>

      {open && (
        <div className="fixed inset-0 z-[100]" onClick={() => setOpen(false)}>
          <div
            className="absolute left-4 top-[110px] w-[240px] bg-surface border border-border rounded-md shadow-lg overflow-hidden z-[101]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-3 py-2 font-semibold text-xs border-b border-border">Switch scope</div>
            <div className="py-1.5">
              <p className="px-3 py-1 text-[9px] uppercase tracking-wider text-foreground-muted font-semibold">
                Organisations
              </p>
              {orgs.map((o) => (
                <button
                  key={o.id}
                  className={cn(
                    "flex items-center gap-2 w-full px-3 py-1.5 text-xs text-left transition-colors hover:bg-surface-2",
                    o.id === selectedOrgId && "bg-surface-2 font-semibold"
                  )}
                  onClick={() => handleOrgSelect(o.id)}
                >
                  <Building2 size={12} className="text-foreground-muted" />
                  {o.name ?? o.slug ?? o.id.slice(0, 8)}
                </button>
              ))}
            </div>
            <div className="py-1.5 border-t border-border">
              <p className="px-3 py-1 text-[9px] uppercase tracking-wider text-foreground-muted font-semibold">
                Workspaces
              </p>
              {workspaces.map((ws) => (
                <button
                  key={ws.id}
                  className={cn(
                    "flex items-center gap-2 w-full px-3 py-1.5 text-xs text-left transition-colors hover:bg-surface-2"
                  )}
                  onClick={() => handleScopeSwitch(ws.org_id, ws.id)}
                >
                  <Layers size={12} className="text-foreground-muted" />
                  {ws.name ?? ws.slug ?? ws.id.slice(0, 8)}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function UserProfileFooter() {
  const auth = useAuth();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [popupOpen, setPopupOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!popupOpen) return;
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setPopupOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [popupOpen]);

  const me = auth.status === "authenticated" ? auth.me : null;
  if (!me) return null;

  const displayName = me.username ?? "User";
  const initial = displayName[0]?.toUpperCase() ?? "?";

  async function handleSignOut() {
    await auth.signOut();
    router.push("/sign-in");
  }

  return (
    <div className="relative border-t border-border" ref={ref}>
      <button
        className="flex items-center gap-2.5 w-full px-4 py-3 text-left transition-colors hover:bg-surface-2"
        onClick={() => setPopupOpen(!popupOpen)}
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-3 text-foreground-muted text-xs font-bold">
          {initial}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-foreground truncate">{displayName}</div>
          <div className="text-[11px] text-foreground-muted truncate">{me.email ?? "No email"}</div>
        </div>
        {popupOpen ? (
          <ChevronDown size={14} className="text-foreground-subtle shrink-0" />
        ) : (
          <ChevronUp size={14} className="text-foreground-subtle shrink-0" />
        )}
      </button>

      {popupOpen && (
        <div className="absolute bottom-full left-2 right-2 mb-1 bg-surface border border-border rounded-md shadow-lg overflow-hidden z-50">
          {/* User info */}
          <div className="px-3 py-2.5 border-b border-border">
            <div className="text-xs font-semibold text-foreground">{displayName}</div>
            <div className="text-[11px] text-foreground-muted">{me.email ?? "No email set"}</div>
            <div className="text-[10px] text-foreground-subtle font-mono mt-0.5">
              session {me.session_id.slice(0, 8)}…
            </div>
          </div>

          {/* Actions */}
          <div className="py-1">
            <button
              className="flex items-center gap-2.5 w-full px-3 py-2 text-xs text-foreground-muted transition-colors hover:bg-surface-2 hover:text-foreground"
              onClick={() => { setPopupOpen(false); router.push("/settings/profile"); }}
            >
              <Settings size={13} />
              Settings
            </button>
            <button
              className="flex items-center gap-2.5 w-full px-3 py-2 text-xs text-foreground-muted transition-colors hover:bg-surface-2 hover:text-foreground"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? <Sun size={13} /> : <Moon size={13} />}
              {theme === "dark" ? "Light mode" : "Dark mode"}
            </button>
          </div>

          <div className="border-t border-border py-1">
            <button
              className="flex items-center gap-2.5 w-full px-3 py-2 text-xs text-[color:var(--danger)] transition-colors hover:bg-surface-2"
              onClick={handleSignOut}
            >
              <LogOut size={13} />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
