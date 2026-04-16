"use client";

import Link from "next/link";
import { use, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { FlagEnvironmentsPanel } from "@/features/featureflags/flag-environments-panel";
import { FlagOverridesPanel } from "@/features/featureflags/flag-overrides-panel";
import { FlagPermissionsPanel } from "@/features/featureflags/flag-permissions-panel";
import { FlagRulesPanel } from "@/features/featureflags/flag-rules-panel";
import {
  useDeleteFlag,
  useFlag,
} from "@/features/featureflags/hooks/use-flags";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";

type Tab = "environments" | "rules" | "overrides" | "permissions";

export default function FlagDetailPage({
  params,
}: {
  params: Promise<{ flagId: string }>;
}) {
  const { flagId } = use(params);
  const { toast } = useToast();
  const { data: flag, isLoading, isError, error, refetch } = useFlag(flagId);
  const del = useDeleteFlag();
  const [tab, setTab] = useState<Tab>("environments");

  async function onDelete() {
    if (!flag) return;
    if (!confirm(`Delete flag "${flag.flag_key}"? This soft-deletes it.`))
      return;
    try {
      await del.mutateAsync(flag.id);
      toast("Flag deleted", "success");
      window.location.href = "/feature-flags";
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  if (isLoading) {
    return (
      <div className="p-8">
        <Skeleton className="h-8 w-64" />
      </div>
    );
  }
  if (isError || !flag) {
    return (
      <div className="p-8">
        <ErrorState
          message={error instanceof Error ? error.message : "Flag not found"}
          retry={() => refetch()}
        />
      </div>
    );
  }

  const scopeTone =
    flag.scope === "global"
      ? "amber"
      : flag.scope === "org"
        ? "blue"
        : "purple";

  return (
    <>
      <PageHeader
        title={flag.flag_key}
        description={
          flag.description ?? "No description — add one via the edit panel."
        }
        testId="heading-flag-detail"
        actions={
          <>
            <Link
              href={`/feature-flags/evaluate?flag_key=${encodeURIComponent(flag.flag_key)}`}
              className="inline-flex h-10 items-center rounded-lg border border-zinc-200 bg-white px-4 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50 dark:hover:bg-zinc-800"
            >
              Try in sandbox →
            </Link>
            <Button variant="danger" onClick={onDelete} loading={del.isPending}>
              Delete
            </Button>
          </>
        }
      />

      <div className="border-b border-zinc-200 bg-white px-8 pt-3 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex flex-wrap items-center gap-1.5 pb-3">
          <Badge tone={scopeTone}>{flag.scope}</Badge>
          <Badge tone="zinc">{flag.value_type}</Badge>
          <Badge tone={flag.is_active ? "emerald" : "zinc"}>
            {flag.is_active ? "active" : "inactive"}
          </Badge>
          <span className="ml-2 text-xs text-zinc-500">
            default ={" "}
            <code className="rounded bg-zinc-100 px-1 py-0.5 text-[11px] dark:bg-zinc-800">
              {JSON.stringify(flag.default_value)}
            </code>
          </span>
          {flag.org_id && (
            <span className="text-xs text-zinc-500">
              · org {flag.org_id.slice(0, 8)}…
            </span>
          )}
          {flag.application_id && (
            <span className="text-xs text-zinc-500">
              · app {flag.application_id.slice(0, 8)}…
            </span>
          )}
        </div>
        <div className="flex gap-1">
          {(
            [
              { id: "environments", label: "Environments" },
              { id: "rules", label: "Rules" },
              { id: "overrides", label: "Overrides" },
              { id: "permissions", label: "Permissions" },
            ] as const
          ).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id as Tab)}
              data-testid={`tab-${t.id}`}
              className={cn(
                "border-b-2 px-3 py-2 text-sm transition",
                tab === t.id
                  ? "border-zinc-900 text-zinc-900 dark:border-zinc-100 dark:text-zinc-50"
                  : "border-transparent text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {tab === "environments" && <FlagEnvironmentsPanel flag={flag} />}
        {tab === "rules" && <FlagRulesPanel flag={flag} />}
        {tab === "overrides" && <FlagOverridesPanel flag={flag} />}
        {tab === "permissions" && <FlagPermissionsPanel flag={flag} />}
      </div>
    </>
  );
}
