"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppSidebar, SidebarInset, SidebarProvider, Topbar } from "@kcontrol/ui";
import Link from "next/link";
import { fetchMe, logoutUser, fetchUserProperties } from "@/lib/api/auth";
import { fetchAccessContext } from "@/lib/api/access";
import { ImpersonationBanner } from "@/components/layout/ImpersonationBanner";
import { OrgWorkspaceProvider } from "@/lib/context/OrgWorkspaceContext";

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isAuthed, setIsAuthed] = useState(false);
  const [userName, setUserName] = useState<string | undefined>(undefined);
  const [userEmail, setUserEmail] = useState<string | undefined>(undefined);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [currentOrgId, setCurrentOrgId] = useState<string | undefined>(undefined);
  const [currentOrgName, setCurrentOrgName] = useState<string | undefined>(undefined);

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
          // Pass default_org_id so backend returns current_org context
          const defaultOrgId = props["default_org_id"] || undefined;
          const access = await fetchAccessContext(defaultOrgId);
          const actions = access.platform?.actions ?? [];
          setIsSuperAdmin(
            actions.some((a) =>
              [
                "feature_flag_registry.view",
                "group_access_assignment.assign",
                "access_governance_console.view",
              ].includes(`${a.feature_code}.${a.action_code}`)
            )
          );

          if (access.current_org) {
            setCurrentOrgId(access.current_org.org_id);
            setCurrentOrgName(access.current_org.name);
          }
        } catch {}

        setIsAuthed(true);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  if (!isAuthed) {
    return (
      <OrgWorkspaceProvider>
        <SidebarProvider>
          <AppSidebar variant="settings" onSignOut={logoutUser} linkComponent={Link} />
          <SidebarInset className="flex flex-col">
            <Topbar title="K-Control" />
            <main className="flex-1 p-4 md:p-6 lg:p-8" />
          </SidebarInset>
        </SidebarProvider>
      </OrgWorkspaceProvider>
    );
  }

  return (
    <OrgWorkspaceProvider>
      <SidebarProvider>
        <AppSidebar
          userName={userName}
          userEmail={userEmail}
          isSuperAdmin={isSuperAdmin}
          variant="settings"
          currentOrgId={currentOrgId}
          currentOrgName={currentOrgName}
          onSignOut={logoutUser}
          linkComponent={Link}
        />
        <SidebarInset className="flex flex-col">
          <ImpersonationBanner />
          <Topbar title="K-Control" />
          <main className="flex-1 p-4 md:p-6 lg:p-8">{children}</main>
        </SidebarInset>
      </SidebarProvider>
    </OrgWorkspaceProvider>
  );
}
