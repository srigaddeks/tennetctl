"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { AppSidebar, SidebarInset, SidebarProvider, Topbar } from "@kcontrol/ui";
import { ChevronRight, ShieldCheck } from "lucide-react";
import { fetchMe, logoutUser, fetchUserProperties } from "@/lib/api/auth";
import { fetchAccessContext } from "@/lib/api/access";
import { ImpersonationBanner } from "@/components/layout/ImpersonationBanner";
import { useSidebarCounts } from "@/lib/hooks/useSidebarCounts";

const ADMIN_BREADCRUMBS: Record<string, string> = {
  "/admin": "Overview",
  "/admin/feature-flags": "Feature Flags",
  "/admin/roles": "Roles",
  "/admin/groups": "Groups",
  "/admin/users": "Users",
  "/admin/orgs": "Organizations",
  "/admin/audit": "Audit Log",
  "/admin/notifications": "Notifications",
  "/admin/license-profiles": "License Profiles",
  "/admin/feedback": "Feedback & Support",
  "/admin/docs": "Document Library",
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthed, setIsAuthed] = useState(false);
  const [userName, setUserName] = useState<string | undefined>(undefined);
  const [userEmail, setUserEmail] = useState<string | undefined>(undefined);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);

  const badgeCounts = useSidebarCounts(undefined, isAuthed);

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
          const actions = access.platform?.actions ?? [];
          const superAdmin = actions.some((a) =>
            [
              "feature_flag_registry.view",
              "group_access_assignment.assign",
              "access_governance_console.view",
            ].includes(`${a.feature_code}.${a.action_code}`)
          );

          if (!superAdmin) {
            router.replace("/dashboard");
            return;
          }

          setIsSuperAdmin(true);
        } catch {
          // If access check fails, deny admin access
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
        <AppSidebar variant="admin" onSignOut={logoutUser} linkComponent={Link} />
        <SidebarInset className="flex flex-col">
          <Topbar title="K-Control" />
          <main className="flex-1 p-4 md:p-6 lg:p-8" />
        </SidebarInset>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider>
      <AppSidebar
        userName={userName}
        userEmail={userEmail}
        isSuperAdmin={isSuperAdmin}
        variant="admin"
        onSignOut={logoutUser}
        badgeCounts={badgeCounts}
        linkComponent={Link}
      />
      <SidebarInset className="flex flex-col">
        <ImpersonationBanner />
        <Topbar title="K-Control" />
        {/* Breadcrumb */}
        {pathname !== "/admin" && (
          <div className="flex items-center gap-1.5 px-4 md:px-6 lg:px-8 py-2 border-b border-border bg-muted/20 text-xs">
            <ShieldCheck className="h-3 w-3 text-primary shrink-0" />
            <Link href="/admin" className="text-muted-foreground hover:text-foreground transition-colors">
              Super Admin
            </Link>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="font-medium text-foreground">
              {ADMIN_BREADCRUMBS[pathname] ?? pathname.split("/").pop()?.replace(/-/g, " ")}
            </span>
          </div>
        )}
        <main className="flex-1 p-4 md:p-6 lg:p-8">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
