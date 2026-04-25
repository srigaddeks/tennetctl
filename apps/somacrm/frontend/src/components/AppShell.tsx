"use client";

import { useEffect, useState } from "react";

import { PageViewTracker } from "@/lib/track-router";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

type Identity = { userId: string | null; orgId: string | null; workspaceId: string | null };

function useTennetctlIdentity(): Identity {
  const [id, setId] = useState<Identity>({ userId: null, orgId: null, workspaceId: null });
  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = window.localStorage.getItem("somacrm_token");
    if (!token) return;
    const base =
      process.env.NEXT_PUBLIC_TENNETCTL_BACKEND ?? "http://localhost:51734";
    void fetch(`${base}/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!d || !d.ok) return;
        setId({
          userId: d.data.user.id,
          orgId: d.data.session.org_id ?? null,
          workspaceId: d.data.session.workspace_id ?? null,
        });
      })
      .catch(() => {});
  }, []);
  return id;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const id = useTennetctlIdentity();
  return (
    <div className="flex min-h-screen" style={{ backgroundColor: "var(--bg-app)" }}>
      <PageViewTracker
        actorUserId={id.userId}
        orgId={id.orgId}
        workspaceId={id.workspaceId}
      />
      {/* Fixed sidebar */}
      <Sidebar />

      {/* Right side: topbar + scrollable content */}
      <div
        className="flex flex-1 flex-col"
        style={{ marginLeft: "var(--sidebar-width)" }}
      >
        {/* Fixed topbar */}
        <Topbar />

        {/* Scrollable content area */}
        <main
          className="flex-1 overflow-y-auto p-6"
          style={{
            marginTop: "var(--topbar-height)",
            backgroundColor: "var(--bg-app)",
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
