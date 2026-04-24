"use client";

import { useState } from "react";

import { ApplicationScopeBar } from "@/components/application-scope-bar";
import { PageHeader } from "@/components/page-header";
import { LogExplorer } from "@/features/monitoring/_components/log-explorer";
import { LogLiveTail } from "@/features/monitoring/_components/log-live-tail";

type Tab = "explorer" | "live";

const TABS: { id: Tab; label: string }[] = [
  { id: "explorer", label: "Explorer" },
  { id: "live", label: "Live Tail" },
];

export default function LogsPage() {
  const [tab, setTab] = useState<Tab>("explorer");
  const [livePulse] = useState(false);
  const [appId, setAppId] = useState<string | null>(null);

  return (
    <>
      <PageHeader
        title="Logs"
        description="Structured log explorer + live tail over SSE."
        testId="heading-monitoring-logs"
      />

      {/* Tab bar */}
      <div
        className="flex items-center gap-1 border-b px-6"
        style={{
          background: "var(--bg-surface)",
          borderColor: "var(--border)",
        }}
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            data-testid={`monitoring-logs-tab-${t.id}`}
            className="relative flex items-center gap-2 px-4 py-3 text-[13px] font-medium transition-colors duration-150"
            style={{
              color: tab === t.id ? "var(--text-primary)" : "var(--text-muted)",
            }}
          >
            {/* Live dot for live tab */}
            {t.id === "live" && (
              <span className="relative flex h-2 w-2">
                {tab === "live" ? (
                  <>
                    <span
                      className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
                      style={{ background: "var(--success)" }}
                    />
                    <span
                      className="relative inline-flex h-2 w-2 rounded-full"
                      style={{ background: "var(--success)" }}
                    />
                  </>
                ) : (
                  <span
                    className="inline-flex h-2 w-2 rounded-full"
                    style={{ background: "var(--border-bright)" }}
                  />
                )}
              </span>
            )}
            {t.label}
            {/* Active indicator */}
            {tab === t.id && (
              <span
                className="absolute bottom-0 left-0 right-0 h-px"
                style={{ background: "#9d6ef8" }}
              />
            )}
          </button>
        ))}

        {/* Right side: quick status indicators */}
        <div className="ml-auto flex items-center gap-4 py-2">
          {tab === "live" && (
            <span
              className="font-mono-data text-[11px]"
              style={{ color: livePulse ? "var(--success)" : "var(--text-muted)" }}
            >
              {livePulse ? "● STREAMING" : "○ IDLE"}
            </span>
          )}
          <span
            className="label-caps"
            style={{ color: "var(--text-muted)" }}
          >
            IBM Plex Mono
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        <div className="mb-4">
          <ApplicationScopeBar
            appId={appId}
            onChange={setAppId}
            label="Filter logs by application"
          />
        </div>
        {tab === "explorer" ? <LogExplorer /> : <LogLiveTail />}
      </div>
    </>
  );
}
