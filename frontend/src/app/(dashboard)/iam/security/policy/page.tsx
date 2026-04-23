"use client";

import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { ErrorState, Skeleton } from "@/components/ui";
import { OrgOverrideList } from "@/features/iam/_components/OrgOverrideList";
import { PolicyForm } from "@/features/iam/_components/PolicyForm";
import { useGlobalPolicy } from "@/features/iam/hooks/use-auth-policy";

type Tab = "global" | "org";

const TABS: { key: Tab; label: string; desc: string }[] = [
  { key: "global", label: "Global defaults", desc: "Baseline policy applied to all organisations" },
  { key: "org", label: "Per-org overrides", desc: "Organisation-specific policy exceptions" },
];

export default function PolicyPage() {
  const [tab, setTab] = useState<Tab>("global");
  const { data: entries, isLoading, isError, error } = useGlobalPolicy();

  return (
    <>
      <PageHeader
        title="Auth Policy"
        description="Global defaults and per-org overrides for password, lockout, session, magic-link, OTP, and password-reset behaviour."
        testId="heading-iam-policy"
      />
      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in" data-testid="iam-policy-body">
        {/* Tabs */}
        <div
          className="mb-6 flex border-b"
          style={{ borderColor: "var(--border)" }}
        >
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              className="px-4 py-2.5 text-xs font-medium transition-colors"
              style={{
                color: tab === t.key ? "var(--accent)" : "var(--text-secondary)",
                borderBottom: tab === t.key
                  ? "2px solid var(--accent)"
                  : "2px solid transparent",
                background: "transparent",
              }}
              onClick={() => setTab(t.key)}
              data-testid={`tab-${t.key}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab description */}
        <p
          className="mb-5 text-xs"
          style={{ color: "var(--text-muted)" }}
        >
          {TABS.find((t) => t.key === tab)?.desc}
        </p>

        {tab === "global" && (
          <>
            {isLoading && (
              <div className="max-w-2xl flex flex-col gap-3">
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-9 w-full" />
              </div>
            )}
            {isError && (
              <ErrorState
                message={(error as Error)?.message ?? "Failed to load policy"}
                retry={() => void 0}
              />
            )}
            {!isLoading && !isError && (
              <div className="max-w-2xl">
                <PolicyForm entries={entries ?? []} />
              </div>
            )}
          </>
        )}

        {tab === "org" && <OrgOverrideList />}
      </div>
    </>
  );
}
