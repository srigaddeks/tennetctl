"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { Sidebar } from "./sidebar";
import { SidebarProvider, useSidebar } from "./sidebar-context";
import { Button } from "@/components/ui/button";

const BARE_ROUTES = ["/sign-in", "/sign-up"];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <AppShellInner>{children}</AppShellInner>
    </SidebarProvider>
  );
}

function AppShellInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";
  const { open, toggle, close } = useSidebar();
  const bare = BARE_ROUTES.some((r) => pathname.startsWith(r));

  if (bare) return <>{children}</>;

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <Sidebar />
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={close}
          aria-hidden="true"
        />
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile topbar — hamburger only */}
        <header className="flex items-center h-12 px-3 border-b border-border bg-surface md:hidden">
          <Button variant="ghost" size="icon" onClick={toggle} aria-label={open ? "Close menu" : "Open menu"}>
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
          <span className="ml-2 text-sm font-semibold text-foreground">k-forensics</span>
        </header>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
