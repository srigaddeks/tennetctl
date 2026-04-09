"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { User, Building2, Layers, Users, Key } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/cn";

const TABS = [
  { id: "profile", label: "Profile", icon: User, href: "/settings/profile" },
  { id: "orgs", label: "Organizations", icon: Building2, href: "/settings/orgs" },
  { id: "workspaces", label: "Workspaces", icon: Layers, href: "/settings/workspaces" },
  { id: "members", label: "Members", icon: Users, href: "/settings/members" },
  { id: "password", label: "Password", icon: Key, href: "/settings/password" },
] as const;

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const router = useRouter();
  const pathname = usePathname() ?? "";

  React.useEffect(() => {
    if (status === "unauthenticated") router.replace("/sign-in");
  }, [status, router]);

  if (status === "loading") {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <span className="text-sm text-foreground-muted">Loading…</span>
      </div>
    );
  }

  return (
    <div className="flex flex-1 max-w-[1100px] w-full px-6 py-8 gap-8">
      <nav className="w-[200px] shrink-0 flex flex-col gap-0.5 hidden md:flex">
        <div className="text-[10px] font-bold text-foreground-muted uppercase tracking-wider px-2.5 pb-2">
          Settings
        </div>
        {TABS.map(({ id, label, icon: Icon, href }) => {
          const isActive =
            pathname === href ||
            (id === "profile" && pathname === "/settings") ||
            (pathname.startsWith(`${href}/`));
          return (
            <Link
              key={id}
              href={href}
              className={cn(
                "flex items-center gap-2 px-2.5 py-2 rounded-md text-sm font-medium transition-colors text-foreground-muted",
                "hover:bg-surface-2 hover:text-foreground",
                isActive && "bg-surface-2 text-foreground"
              )}
            >
              <Icon size={15} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
}
