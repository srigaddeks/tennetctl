"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { AppSidebar, SidebarInset, SidebarProvider, Topbar } from "@kcontrol/ui";
import { ChevronRight, FlaskRound } from "lucide-react";
import { fetchMe, logoutUser, fetchUserProperties } from "@/lib/api/auth";
import { fetchAccessContext } from "@/lib/api/access";
import { ImpersonationBanner } from "@/components/layout/ImpersonationBanner";
import { SandboxOrgWorkspaceProvider } from "@/lib/context/SandboxOrgWorkspaceContext";

const SANDBOX_BREADCRUMBS: Record<string, string> = {
  "/sandbox": "Overview",
  "/sandbox/connectors": "Connectors",
  "/sandbox/datasets": "Datasets",
  "/sandbox/signals": "Signals",
  "/sandbox/threat-types": "Threat Types",
  "/sandbox/policies": "Control Tests",
  "/sandbox/runs": "Sandbox Runs",
  "/sandbox/live-sessions": "Live Sessions",
  "/sandbox/libraries": "Control Libraries",
  "/sandbox/promotions": "Promotions",
  "/sandbox/ssf-streams": "SSF Streams",
}

export default function SandboxLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthed, setIsAuthed] = useState(false);
  const [userName, setUserName] = useState<string | undefined>(undefined);
  const [userEmail, setUserEmail] = useState<string | undefined>(undefined);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [hasSandboxAccess, setHasSandboxAccess] = useState(false);

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

          // Check for sandbox access — super admins always have access
          const sandboxAccess = superAdmin || allActions.some((a) =>
            a.feature_code === "sandbox" && a.action_code === "view"
          );
          setHasSandboxAccess(sandboxAccess);

          if (!sandboxAccess) {
            router.replace("/dashboard");
            return;
          }
        } catch {
          // If access check fails, deny sandbox access
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
        <AppSidebar variant="sandbox" onSignOut={logoutUser} linkComponent={Link} />
        <SidebarInset className="flex flex-col">
          <Topbar title="K-Control" />
          <main className="flex-1 p-4 md:p-6 lg:p-8" />
        </SidebarInset>
      </SidebarProvider>
    );
  }

  return (
    <SandboxOrgWorkspaceProvider>
    <SidebarProvider>
      <AppSidebar
        userName={userName}
        userEmail={userEmail}
        isSuperAdmin={isSuperAdmin}
        variant="sandbox"
        onSignOut={logoutUser}
        linkComponent={Link}
      />
      <SidebarInset className="flex flex-col">
        <ImpersonationBanner />
        <Topbar title="K-Control" />
        {/* Breadcrumb */}
        {pathname !== "/sandbox" && (
          <div className="flex items-center gap-1.5 px-4 md:px-6 lg:px-8 py-2 border-b border-border bg-muted/20 text-xs">
            <FlaskRound className="h-3 w-3 text-primary shrink-0" />
            <Link href="/sandbox" className="text-muted-foreground hover:text-foreground transition-colors">
              Sandbox
            </Link>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="font-medium text-foreground">
              {SANDBOX_BREADCRUMBS[pathname] ?? pathname.split("/").pop()?.replace(/-/g, " ")}
            </span>
          </div>
        )}
        <main className="flex-1 p-4 md:p-6 lg:p-8">{children}</main>
      </SidebarInset>
    </SidebarProvider>
    </SandboxOrgWorkspaceProvider>
  );
}
