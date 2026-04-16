"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppSidebar, SidebarInset, SidebarProvider, Topbar } from "@kcontrol/ui";
import { fetchMe, logoutUser, fetchUserProperties } from "@/lib/api/auth";
import { fetchAccessContext } from "@/lib/api/access";
import { OrgWorkspaceProvider } from "@/lib/context/OrgWorkspaceContext";
import { ViewProvider, useView } from "@/lib/context/ViewContext";
import { CopilotProvider } from "@/lib/context/CopilotContext";
import Link from "next/link";
import { ViewGuard } from "@/components/layout/ViewGuard";
import { ImpersonationBanner } from "@/components/layout/ImpersonationBanner";
import { CopilotTrigger } from "@/components/copilot/CopilotTrigger";
import { FeedbackTrigger } from "@/components/layout/FeedbackTrigger";
import { NotificationTrigger } from "@/components/layout/NotificationTrigger";
import { CopilotPanel } from "@/components/copilot/CopilotPanel";
import { useAccess } from "@/components/providers/AccessProvider";
import { useCopilotPageContext } from "@/lib/hooks/useCopilotPageContext";
import { useSidebarCounts } from "@/lib/hooks/useSidebarCounts";
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext";

/** Inner shell that consumes ViewContext (must be inside ViewProvider) */
function DashboardShell({
  userName,
  userEmail,
  isSuperAdmin,
  children,
}: {
  userName?: string;
  userEmail?: string;
  isSuperAdmin: boolean;
  children: React.ReactNode;
}) {
  const { activeView, activeViewDef, availableViews, setActiveView, ready: viewReady } = useView();
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace();
  const { hasFeature, isLoading: isAccessLoading } = useAccess();
  const badgeCounts = useSidebarCounts(selectedOrgId, ready, selectedWorkspaceId);
  const pageContext = useCopilotPageContext();
  const showAuditorWorkspace =
    hasFeature("audit_workspace_auditor_portfolio") ||
    hasFeature("audit_workspace_engagement_membership");

  // Only show view badge when user has multiple views
  const showViewBadge = availableViews.length > 1;

  return (
    <CopilotProvider>
      <SidebarProvider>
        <AppSidebar
          userName={userName}
          userEmail={userEmail}
          isSuperAdmin={isSuperAdmin}
          onSignOut={logoutUser}
          allowedRoutes={activeViewDef.allowedRoutes}
          viewLabel={showViewBadge ? activeViewDef.label : undefined}
          viewColor={showViewBadge ? activeViewDef.color : undefined}
          availableViews={availableViews}
          activeViewId={activeView}
          onViewSelect={setActiveView}
          badgeCounts={badgeCounts}
          linkComponent={Link}
          loading={!viewReady || isAccessLoading}
          showAuditorWorkspace={showAuditorWorkspace}
        />
        <SidebarInset className="flex flex-col min-w-0 overflow-hidden h-svh">
          <ImpersonationBanner />
          <Topbar title="K-Control" actions={
            <>
              <FeedbackTrigger />
              <NotificationTrigger />
              <CopilotTrigger />
            </>
          } />
          {/* Main content area + persistent copilot panel side by side */}
          <div className="flex flex-1 min-h-0 overflow-hidden">
            <main key={`${selectedOrgId}:${selectedWorkspaceId}`} className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 min-w-0">
              <ViewGuard>{children}</ViewGuard>
            </main>
            {ready && <CopilotPanel pageContext={pageContext} />}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </CopilotProvider>
  );
}

export default function KControlLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [isAuthed, setIsAuthed] = useState(false);
  const [userName, setUserName] = useState<string | undefined>(undefined);
  const [userEmail, setUserEmail] = useState<string | undefined>(undefined);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);

  useEffect(() => {
    fetchMe()
      .then(async (user) => {
        // Check onboarding gate — redirect to setup if not complete.
        // Skip for external/assignee users (user_category !== "full") — they don't onboard.
        let props: Record<string, string> = {};
        try {
          props = await fetchUserProperties();
          if (user.user_category === "full" && props["onboarding_complete"] !== "true") {
            router.replace("/onboarding");
            return;
          }
        } catch {
          if (user.user_category === "full") {
            router.replace("/onboarding");
            return;
          }
        }

        // Derive display name from properties
        const firstName = props["first_name"] ?? "";
        const lastName = props["last_name"] ?? "";
        const displayName = [firstName, lastName].filter(Boolean).join(" ") || props["display_name"] || undefined;

        setUserEmail(user.email);
        setUserName(displayName);

        // Determine super admin status from platform access context
        try {
          const access = await fetchAccessContext();
          const platformActions = access.platform?.actions ?? [];
          const superAdminMarker = platformActions.some((a) =>
            ["feature_flag_registry.view", "group_access_assignment.assign", "access_governance_console.view"]
              .includes(`${a.feature_code}.${a.action_code}`)
          );
          setIsSuperAdmin(superAdminMarker);
        } catch {
          // Non-blocking — just won't show admin menu
        }

        setIsAuthed(true);
      })
      .catch(() => {
        router.replace("/login");
      });
  }, [router]);

  if (!isAuthed) {
    return (
      <SidebarProvider>
        <AppSidebar onSignOut={logoutUser} allowedRoutes={[]} />
        <SidebarInset className="flex flex-col">
          <Topbar title="K-Control" />
          <main className="flex-1 p-4 md:p-6 lg:p-8" />
        </SidebarInset>
      </SidebarProvider>
    );
  }

  return (
    <OrgWorkspaceProvider>
      <ViewProvider>
        <DashboardShell
          userName={userName}
          userEmail={userEmail}
          isSuperAdmin={isSuperAdmin}
        >
          {children}
        </DashboardShell>
      </ViewProvider>
    </OrgWorkspaceProvider>
  );
}
