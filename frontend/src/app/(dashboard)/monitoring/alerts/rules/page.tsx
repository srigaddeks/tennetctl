"use client";

import Link from "next/link";
import { useState } from "react";

import { ApplicationScopeBar } from "@/components/application-scope-bar";
import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useAlertRules,
  useDeleteAlertRule,
  usePauseAlertRule,
  useUnpauseAlertRule,
} from "@/features/monitoring/hooks/use-alert-rules";

export default function AlertRulesPage() {
  const { data, isLoading, isError, error, refetch } = useAlertRules();
  const del = useDeleteAlertRule();
  const pause = usePauseAlertRule();
  const unpause = useUnpauseAlertRule();
  const [appId, setAppId] = useState<string | null>(null);

  const items = data?.items ?? [];
  const activeCount = items.filter((r) => {
    const paused = r.paused_until !== null && new Date(r.paused_until).getTime() > Date.now();
    return r.is_active && !paused;
  }).length;
  const pausedCount = items.filter((r) => {
    return r.paused_until !== null && new Date(r.paused_until).getTime() > Date.now();
  }).length;
  const disabledCount = items.filter((r) => !r.is_active).length;

  return (
    <>
      <PageHeader
        title="Alert rules"
        description="Rules that evaluate monitoring DSL queries on a cadence and fire notifications."
        testId="heading-monitoring-alert-rules"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Alerts", href: "/monitoring/alerts" },
          { label: "Rules" },
        ]}
        actions={
          <Link href="/monitoring/alerts/rules/new">
            <Button variant="accent" data-testid="new-rule-button">
              + New rule
            </Button>
          </Link>
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        <div className="flex flex-col gap-5">

          <ApplicationScopeBar
            appId={appId}
            onChange={setAppId}
            label="Filter rules by application"
          />

          {/* Stat strip */}
          {!isLoading && (
            <div className="grid grid-cols-3 gap-3">
              <StatCard
                label="Total rules"
                value={String(items.length)}
                sub="Across all severities"
                accent="blue"
              />
              <StatCard
                label="Active"
                value={String(activeCount)}
                sub="Currently evaluating"
                accent="green"
              />
              <StatCard
                label="Paused / disabled"
                value={String(pausedCount + disabledCount)}
                sub={`${pausedCount} paused · ${disabledCount} disabled`}
                accent="amber"
              />
            </div>
          )}

          {isLoading && (
            <div className="flex flex-col gap-2">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {isError && (
            <ErrorState
              message={error instanceof Error ? error.message : "Load failed"}
              retry={() => refetch()}
            />
          )}

          {data && items.length === 0 && !isLoading && (
            <EmptyState
              title="No alert rules"
              description="Create a rule to start monitoring for conditions."
              action={
                <Link href="/monitoring/alerts/rules/new">
                  <Button data-testid="new-rule-empty-button">New rule</Button>
                </Link>
              }
            />
          )}

          {items.length > 0 && (
            <Table>
              <THead>
                <TR>
                  <TH>Name</TH>
                  <TH>Target</TH>
                  <TH>Severity</TH>
                  <TH>Condition</TH>
                  <TH>Template</TH>
                  <TH>Status</TH>
                  <TH className="text-right">Actions</TH>
                </TR>
              </THead>
              <TBody>
                {items.map((r) => {
                  const pausedNow =
                    r.paused_until !== null &&
                    new Date(r.paused_until).getTime() > Date.now();

                  const statusBadge = !r.is_active ? (
                    <Badge tone="default">disabled</Badge>
                  ) : pausedNow ? (
                    <Badge tone="warning" dot>paused</Badge>
                  ) : (
                    <Badge tone="success" dot>active</Badge>
                  );

                  const severityTone =
                    r.severity === "critical" || r.severity === "error"
                      ? "danger"
                      : r.severity === "warn"
                        ? "warning"
                        : "info";

                  return (
                    <TR
                      key={r.id}
                      data-testid={`rule-row-${r.id}`}
                    >
                      <TD>
                        <div className="flex flex-col gap-0.5">
                          <Link
                            href={`/monitoring/alerts/rules/${r.id}`}
                            className="font-medium text-[13px] transition-colors hover:underline"
                            style={{ color: "var(--text-primary)" }}
                            data-testid={`rule-link-${r.id}`}
                          >
                            {r.name}
                          </Link>
                          {r.description && (
                            <span
                              className="text-[11px]"
                              style={{ color: "var(--text-muted)" }}
                            >
                              {r.description}
                            </span>
                          )}
                        </div>
                      </TD>
                      <TD>
                        <Badge tone="default">{r.target}</Badge>
                      </TD>
                      <TD>
                        <Badge tone={severityTone}>
                          {r.severity_label ?? String(r.severity)}
                        </Badge>
                      </TD>
                      <TD>
                        <span
                          className="font-mono-data text-[11px]"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {r.condition.op} {r.condition.threshold}
                          {r.condition.for_duration_seconds > 0 && (
                            <span style={{ color: "var(--text-muted)" }}>
                              {" "}for {r.condition.for_duration_seconds}s
                            </span>
                          )}
                        </span>
                      </TD>
                      <TD>
                        <span
                          className="font-mono-data text-[11px]"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {r.notify_template_key}
                        </span>
                      </TD>
                      <TD>{statusBadge}</TD>
                      <TD className="text-right">
                        <div className="inline-flex gap-1">
                          <Link href={`/monitoring/alerts/rules/${r.id}`}>
                            <Button
                              variant="ghost"
                              size="sm"
                              data-testid={`rule-edit-${r.id}`}
                            >
                              Edit
                            </Button>
                          </Link>
                          {pausedNow ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => void unpause.mutateAsync(r.id)}
                              data-testid={`rule-unpause-${r.id}`}
                            >
                              Unpause
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                const pausedUntil = new Date(
                                  Date.now() + 3600 * 1000,
                                ).toISOString();
                                void pause.mutateAsync({
                                  id: r.id,
                                  paused_until: pausedUntil,
                                });
                              }}
                              data-testid={`rule-pause-${r.id}`}
                            >
                              Pause 1h
                            </Button>
                          )}
                          <button
                            type="button"
                            onClick={() => {
                              if (confirm(`Delete rule "${r.name}"?`)) {
                                void del.mutateAsync(r.id);
                              }
                            }}
                            data-testid={`rule-delete-${r.id}`}
                            className="flex h-7 w-7 items-center justify-center rounded text-[11px] transition-colors"
                            style={{
                              color: "var(--text-muted)",
                            }}
                            onMouseEnter={(e) => {
                              (e.currentTarget as HTMLButtonElement).style.background = "var(--danger-muted)";
                              (e.currentTarget as HTMLButtonElement).style.color = "var(--danger)";
                            }}
                            onMouseLeave={(e) => {
                              (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                              (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)";
                            }}
                            aria-label="Delete rule"
                          >
                            ✕
                          </button>
                        </div>
                      </TD>
                    </TR>
                  );
                })}
              </TBody>
            </Table>
          )}
        </div>
      </div>
    </>
  );
}
