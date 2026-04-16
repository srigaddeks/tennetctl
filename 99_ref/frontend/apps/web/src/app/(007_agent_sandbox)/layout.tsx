"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { AppSidebar, SidebarInset, SidebarProvider, Topbar } from "@kcontrol/ui";
import { ChevronRight, Bot } from "lucide-react";
import { fetchMe, logoutUser, fetchUserProperties } from "@/lib/api/auth";
import { fetchAccessContext } from "@/lib/api/access";
import { ImpersonationBanner } from "@/components/layout/ImpersonationBanner";
import { AgentSandboxProvider } from "@/lib/context/AgentSandboxContext";

const AGENT_SANDBOX_BREADCRUMBS: Record<string, string> = {
  "/agent-sandbox": "Overview",
  "/agent-sandbox/agents": "Agents",
  "/agent-sandbox/tools": "Agent Tools",
  "/agent-sandbox/runs": "Agent Runs",
  "/agent-sandbox/scenarios": "Test Scenarios",
  "/agent-sandbox/playground": "Playground",
  "/agent-sandbox/registry": "Agent Registry",
}

export default function AgentSandboxLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthed, setIsAuthed] = useState(false);
  const [userName, setUserName] = useState<string | undefined>(undefined);
  const [userEmail, setUserEmail] = useState<string | undefined>(undefined);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);

  useEffect(() => {
    fetchMe()
      .then(async (user) => {
        let props: Record<string, string> = {};
        try {
          props = await fetchUserProperties();
        } catch {}

        const firstName = props["first_name"] ?? "";
        const lastName = props["last_name"] ?? "";
        const displayName =
          [firstName, lastName].filter(Boolean).join(" ") ||
          props["display_name"] ||
          undefined;

        setUserEmail(user.email);
        setUserName(displayName);

        try {
          const access = await fetchAccessContext();
          const allActions = [
            ...(access.platform?.actions ?? []),
            ...(access.current_org?.actions ?? []),
            ...(access.current_workspace?.actions ?? []),
          ];
          const superAdmin = allActions.some((a) =>
            [
              "feature_flag_registry.view",
              "group_access_assignment.assign",
              "access_governance_console.view",
            ].includes(`${a.feature_code}.${a.action_code}`)
          );
          setIsSuperAdmin(superAdmin);

          // Check for agent_sandbox access — super admins always have access
          const agentSandboxAccess = superAdmin || allActions.some((a) =>
            a.feature_code === "agent_sandbox" && a.action_code === "view"
          );

          if (!agentSandboxAccess) {
            router.replace("/dashboard");
            return;
          }
        } catch {
          router.replace("/dashboard");
          return;
        }

        setIsAuthed(true);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  if (!isAuthed) {
    return (
      <SidebarProvider>
        <AppSidebar variant="agent_sandbox" onSignOut={logoutUser} />
        <SidebarInset className="flex flex-col">
          <Topbar title="K-Control" />
          <main className="flex-1 p-4 md:p-6 lg:p-8" />
        </SidebarInset>
      </SidebarProvider>
    );
  }

  return (
    <AgentSandboxProvider>
    <SidebarProvider>
      <AppSidebar
        userName={userName}
        userEmail={userEmail}
        isSuperAdmin={isSuperAdmin}
        variant="agent_sandbox"
        onSignOut={logoutUser}
      />
      <SidebarInset className="flex flex-col">
        <ImpersonationBanner />
        <Topbar title="K-Control" />
        {/* Breadcrumb */}
        {pathname !== "/agent-sandbox" && (
          <div className="flex items-center gap-1.5 px-4 md:px-6 lg:px-8 py-2 border-b border-border bg-muted/20 text-xs">
            <Bot className="h-3 w-3 text-primary shrink-0" />
            <Link href="/agent-sandbox" className="text-muted-foreground hover:text-foreground transition-colors">
              Agent Sandbox
            </Link>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="font-medium text-foreground">
              {AGENT_SANDBOX_BREADCRUMBS[pathname] ?? pathname.split("/").pop()?.replace(/-/g, " ")}
            </span>
          </div>
        )}
        <main className="flex-1 p-4 md:p-6 lg:p-8">{children}</main>
      </SidebarInset>
    </SidebarProvider>
    </AgentSandboxProvider>
  );
}
