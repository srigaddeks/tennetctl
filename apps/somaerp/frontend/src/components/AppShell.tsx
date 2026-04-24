"use client";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen" style={{ backgroundColor: "var(--bg-app)" }}>
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
