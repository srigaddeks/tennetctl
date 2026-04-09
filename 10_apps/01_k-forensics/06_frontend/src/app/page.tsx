"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Briefcase, Shield, FileText, Search, Users, Settings,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { getOrg, getWorkspace, tokenStore } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/cn";
import type { OrgData, WorkspaceData } from "@/types/api";

export default function DashboardPage() {
  return (
    <React.Suspense fallback={<Spinner />}>
      <DashboardInner />
    </React.Suspense>
  );
}

function DashboardInner() {
  const auth = useAuth();
  const router = useRouter();
  const params = useSearchParams();

  const accessToken = auth.status === "authenticated" ? auth.accessToken : null;
  const me = auth.status === "authenticated" ? auth.me : null;

  const [org, setOrg] = React.useState<OrgData | null>(null);
  const [workspace, setWorkspace] = React.useState<WorkspaceData | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    if (auth.status === "loading") return;
    if (auth.status === "unauthenticated") { router.replace("/sign-in"); return; }

    const token = accessToken!;

    let orgId = params.get("org_id");
    let workspaceId = params.get("workspace_id");

    if (!orgId || !workspaceId) {
      const { access } = tokenStore.get();
      if (access) {
        try {
          const payload = JSON.parse(atob(access.split(".")[1]));
          orgId = orgId ?? payload.oid ?? null;
          workspaceId = workspaceId ?? payload.wid ?? null;
        } catch { /* ignore */ }
      }
    }

    if (!orgId || !workspaceId) {
      setLoading(false);
      return;
    }

    Promise.all([
      getOrg(orgId, token),
      getWorkspace(workspaceId, token),
    ]).then(([orgRes, wsRes]) => {
      setLoading(false);
      if (orgRes.ok) setOrg(orgRes.data);
      if (wsRes.ok) setWorkspace(wsRes.data);
    });
  }, [auth.status, accessToken, params, router]);

  if (auth.status === "loading" || loading) return <Spinner />;

  return (
    <div className="px-8 py-8 max-w-[860px]">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">
          Welcome back{me?.username ? `, ${me.username}` : ""}
        </h1>
        <p className="text-xs text-foreground-muted mt-1">
          {workspace?.name ?? "Your workspace"} &middot; {org?.name ?? "Your organisation"}
        </p>
      </div>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3.5 mb-10">
        <ModuleCard icon={<Briefcase size={22} />} title="Cases" description="Manage forensic cases and investigations" coming />
        <ModuleCard icon={<Shield size={22} />} title="Evidence" description="Upload and chain-of-custody evidence items" coming />
        <ModuleCard icon={<FileText size={22} />} title="Reports" description="Generate and export investigation reports" coming />
        <ModuleCard icon={<Search size={22} />} title="Search" description="Full-text search across all workspace data" coming />
        <ModuleCard icon={<Users size={22} />} title="Team" description="Manage members, roles, and access" onClick={() => router.push("/settings/members")} />
        <ModuleCard icon={<Settings size={22} />} title="Settings" description="Workspace and organisation configuration" onClick={() => router.push("/settings")} />
      </div>

      {(org || workspace) && (
        <Card>
          <div className="flex items-center px-5 py-3.5">
            <div className="flex flex-col gap-0.5 flex-1">
              <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Organisation</span>
              <span className="text-sm font-medium">{org?.name ?? org?.slug ?? "—"}</span>
            </div>
            <Separator orientation="vertical" className="h-8 mx-5" />
            <div className="flex flex-col gap-0.5 flex-1">
              <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Workspace</span>
              <span className="text-sm font-medium">{workspace?.name ?? workspace?.slug ?? "—"}</span>
            </div>
            <Separator orientation="vertical" className="h-8 mx-5" />
            <div className="flex flex-col gap-0.5 flex-1">
              <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Status</span>
              <Badge variant={workspace?.is_active ? "success" : "danger"}>
                {workspace?.is_active ? "Active" : "Inactive"}
              </Badge>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function ModuleCard({
  icon, title, description, onClick, coming,
}: {
  icon: React.ReactNode; title: string; description: string; onClick?: () => void; coming?: boolean;
}) {
  return (
    <button
      className={cn(
        "flex items-start gap-3.5 p-4 rounded-md border border-border bg-surface text-left transition-colors",
        coming ? "opacity-60 cursor-default" : "cursor-pointer hover:bg-surface-2 hover:border-border-strong"
      )}
      onClick={coming ? undefined : onClick}
      disabled={coming}
    >
      <div className="w-[42px] h-[42px] rounded-md bg-surface-2 flex items-center justify-center text-foreground-muted shrink-0">
        {icon}
      </div>
      <div className="flex flex-col gap-1">
        <span className="text-sm font-semibold flex items-center gap-1.5">
          {title}
          {coming && (
            <Badge variant="default" className="text-[9px]">soon</Badge>
          )}
        </span>
        <span className="text-xs text-foreground-muted leading-relaxed">{description}</span>
      </div>
    </button>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center h-[60vh]">
      <span className="text-sm text-foreground-muted">Loading…</span>
    </div>
  );
}
