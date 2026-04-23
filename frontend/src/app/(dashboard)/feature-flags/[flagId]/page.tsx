"use client";

import Link from "next/link";
import { use, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import { Badge, Button, ErrorState, Skeleton } from "@/components/ui";
import { FlagEnvironmentsPanel } from "@/features/featureflags/flag-environments-panel";
import { FlagOverridesPanel } from "@/features/featureflags/flag-overrides-panel";
// FlagPermissionsPanel removed in phase 23R — role access is now managed
// from /iam/roles → Capabilities tab against the unified capability catalog.
import { FlagRulesPanel } from "@/features/featureflags/flag-rules-panel";
import {
  useDeleteFlag,
  useFlag,
} from "@/features/featureflags/hooks/use-flags";
import { ApiClientError } from "@/lib/api";

type Tab = "environments" | "rules" | "overrides";

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
      <div className="p-8 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-5 w-96" />
        <div className="flex gap-3 mt-6">
          <Skeleton className="h-24 flex-1 rounded-xl" />
          <Skeleton className="h-24 flex-1 rounded-xl" />
          <Skeleton className="h-24 flex-1 rounded-xl" />
        </div>
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

  const scopeAccent =
    flag.scope === "global"
      ? "var(--warning)"
      : flag.scope === "org"
        ? "var(--accent)"
        : "#a855f7";

  const tabs: { id: Tab; label: string; description: string }[] = [
    { id: "environments", label: "Environments",  description: "Per-env enable/disable + rollout" },
    { id: "rules",        label: "Rules",         description: "Targeting rules and conditions"   },
    { id: "overrides",    label: "Overrides",     description: "Per-entity forced values"         },
  ];

  return (
    <>
      <PageHeader
        title={flag.flag_key}
        description={flag.description ?? "No description — add one via the edit panel."}
        testId="heading-flag-detail"
        breadcrumbs={[
          { label: "Feature Flags", href: "/feature-flags" },
          { label: flag.flag_key },
        ]}
        actions={
          <>
            <Link
              href={`/feature-flags/evaluate?flag_key=${encodeURIComponent(flag.flag_key)}`}
              className="inline-flex h-10 items-center rounded-lg border px-4 text-sm font-medium transition"
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--border-bright)",
                color: "var(--text-secondary)",
              }}
            >
              Evaluate in sandbox →
            </Link>
            <Button variant="danger" onClick={onDelete} loading={del.isPending}>
              Delete
            </Button>
          </>
        }
      />

      {/* Flag metadata strip */}
      <div
        className="px-8 pt-4 pb-0"
        style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-surface)" }}
      >
        {/* Overview cards */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 mb-5">
          {/* Status */}
          <div
            className="rounded-xl px-4 py-3"
            style={{
              background: "var(--bg-elevated)",
              border: `1px solid ${flag.is_active ? "var(--success)" : "var(--border)"}`,
            }}
          >
            <div className="label-caps mb-1.5" style={{ color: "var(--text-muted)" }}>Status</div>
            <div className="flex items-center gap-2">
              <span
                className="h-2 w-2 rounded-full"
                style={{ background: flag.is_active ? "var(--success)" : "var(--text-muted)" }}
              />
              <span
                className="text-sm font-semibold"
                style={{ color: flag.is_active ? "var(--success)" : "var(--text-muted)" }}
              >
                {flag.is_active ? "Enabled" : "Disabled"}
              </span>
            </div>
          </div>

          {/* Scope */}
          <div
            className="rounded-xl px-4 py-3"
            style={{
              background: "var(--bg-elevated)",
              border: `1px solid ${scopeAccent}`,
            }}
          >
            <div className="label-caps mb-1.5" style={{ color: "var(--text-muted)" }}>Scope</div>
            <Badge tone={scopeTone}>{flag.scope}</Badge>
          </div>

          {/* Value type */}
          <div
            className="rounded-xl px-4 py-3"
            style={{
              background: "var(--bg-elevated)",
              border: "1px solid var(--border)",
            }}
          >
            <div className="label-caps mb-1.5" style={{ color: "var(--text-muted)" }}>Value type</div>
            <Badge tone="default">{flag.value_type}</Badge>
          </div>

          {/* Default value */}
          <div
            className="rounded-xl px-4 py-3"
            style={{
              background: "var(--bg-elevated)",
              border: "1px solid var(--border)",
            }}
          >
            <div className="label-caps mb-1.5" style={{ color: "var(--text-muted)" }}>Default value</div>
            <code
              className="text-sm font-semibold font-mono-data"
              style={{ color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}
            >
              {JSON.stringify(flag.default_value)}
            </code>
          </div>
        </div>

        {/* Scope context */}
        {(flag.org_id || flag.application_id) && (
          <div className="flex items-center gap-3 mb-4 text-xs" style={{ color: "var(--text-muted)" }}>
            {flag.org_id && (
              <span>
                org:{" "}
                <Link
                  href={`/iam/orgs/${flag.org_id}`}
                  className="transition hover:opacity-80"
                  style={{ color: "var(--accent)", fontFamily: "var(--font-mono)" }}
                >
                  {flag.org_id.slice(0, 8)}…
                </Link>
              </span>
            )}
            {flag.application_id && (
              <span>
                app:{" "}
                <Link
                  href="/iam/applications"
                  className="transition hover:opacity-80"
                  style={{ color: "var(--accent)", fontFamily: "var(--font-mono)" }}
                >
                  {flag.application_id.slice(0, 8)}…
                </Link>
              </span>
            )}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              data-testid={`tab-${t.id}`}
              className="relative px-4 py-3 text-sm transition"
              style={{
                borderBottom: tab === t.id ? `2px solid var(--accent)` : "2px solid transparent",
                color: tab === t.id ? "var(--accent)" : "var(--text-secondary)",
                background: "transparent",
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {tab === "environments" && <FlagEnvironmentsPanel flag={flag} />}
        {tab === "rules"        && <FlagRulesPanel flag={flag} />}
        {tab === "overrides"    && <FlagOverridesPanel flag={flag} />}
      </div>
    </>
  );
}
