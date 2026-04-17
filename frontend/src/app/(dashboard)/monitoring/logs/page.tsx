"use client";

import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { LogExplorer } from "@/features/monitoring/_components/log-explorer";
import { LogLiveTail } from "@/features/monitoring/_components/log-live-tail";
import { cn } from "@/lib/cn";

type Tab = "explorer" | "live";

export default function LogsPage() {
  const [tab, setTab] = useState<Tab>("explorer");

  return (
    <>
      <PageHeader
        title="Logs"
        description="Structured log explorer + live tail over SSE."
        testId="heading-monitoring-logs"
      />
      <div className="flex border-b border-zinc-200 px-8 dark:border-zinc-800">
        {(["explorer", "live"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            data-testid={`monitoring-logs-tab-${t}`}
            className={cn(
              "px-4 py-2.5 text-sm font-medium capitalize transition-colors",
              tab === t
                ? "border-b-2 border-zinc-900 text-zinc-900 dark:border-zinc-100 dark:text-zinc-100"
                : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300",
            )}
          >
            {t === "live" ? "Live tail" : "Explorer"}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {tab === "explorer" ? <LogExplorer /> : <LogLiveTail />}
      </div>
    </>
  );
}
