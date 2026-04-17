"use client";

import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { ErrorState, Skeleton } from "@/components/ui";
import { OrgOverrideList } from "@/features/iam/_components/OrgOverrideList";
import { PolicyForm } from "@/features/iam/_components/PolicyForm";
import { useGlobalPolicy } from "@/features/iam/hooks/use-auth-policy";

type Tab = "global" | "org";

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
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="iam-policy-body">
        <div className="mb-6 flex gap-2 border-b border-zinc-200 dark:border-zinc-700">
          <button
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              tab === "global"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
            onClick={() => setTab("global")}
            data-testid="tab-global"
          >
            Global defaults
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              tab === "org"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
            onClick={() => setTab("org")}
            data-testid="tab-org"
          >
            Per-org overrides
          </button>
        </div>

        {tab === "global" && (
          <>
            {isLoading && (
              <div className="flex flex-col gap-2">
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
              <PolicyForm entries={entries ?? []} />
            )}
          </>
        )}

        {tab === "org" && <OrgOverrideList />}
      </div>
    </>
  );
}
