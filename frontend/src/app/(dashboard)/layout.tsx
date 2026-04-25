"use client";

import { CommandPalette } from "@/components/command-palette";
import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/topbar";
import { ImpersonationBanner } from "@/features/iam/_components/impersonation-banner";
import { useMe } from "@/features/auth/hooks/use-auth";
import { PageViewTracker } from "@/lib/track-router";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const me = useMe();
  const u = me.data?.user.id ?? null;
  const o = me.data?.session.org_id ?? null;
  const w = me.data?.session.workspace_id ?? null;
  return (
    <div className="flex min-h-dvh flex-col">
      <PageViewTracker actorUserId={u} orgId={o} workspaceId={w} />
      <ImpersonationBanner />
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
      </div>
      <CommandPalette />
    </div>
  );
}
