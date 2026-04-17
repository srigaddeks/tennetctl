"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import {
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

  return (
    <>
      <PageHeader
        title="Alert rules"
        description="Rules that evaluate monitoring DSL queries on a cadence and fire notifications."
        testId="heading-monitoring-alert-rules"
        actions={
          <Link href="/monitoring/alerts/rules/new">
            <Button data-testid="new-rule-button">New rule</Button>
          </Link>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        )}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {data && data.items.length === 0 && !isLoading && (
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
        {data && data.items.length > 0 && (
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
              {data.items.map((r) => {
                const pausedNow =
                  r.paused_until !== null &&
                  new Date(r.paused_until).getTime() > Date.now();
                return (
                  <TR
                    key={r.id}
                    data-testid={`rule-row-${r.id}`}
                  >
                    <TD>
                      <Link
                        href={`/monitoring/alerts/rules/${r.id}`}
                        className="font-medium text-zinc-900 hover:underline dark:text-zinc-50"
                        data-testid={`rule-link-${r.id}`}
                      >
                        {r.name}
                      </Link>
                      {r.description && (
                        <div className="text-xs text-zinc-500">
                          {r.description}
                        </div>
                      )}
                    </TD>
                    <TD className="text-zinc-600 dark:text-zinc-400">
                      {r.target}
                    </TD>
                    <TD className="text-zinc-600 dark:text-zinc-400">
                      {r.severity_label ?? r.severity}
                    </TD>
                    <TD className="font-mono text-xs text-zinc-600 dark:text-zinc-400">
                      {r.condition.op} {r.condition.threshold}
                      {r.condition.for_duration_seconds > 0 && (
                        <> for {r.condition.for_duration_seconds}s</>
                      )}
                    </TD>
                    <TD className="font-mono text-xs text-zinc-600 dark:text-zinc-400">
                      {r.notify_template_key}
                    </TD>
                    <TD>
                      {!r.is_active ? (
                        <span className="rounded-full bg-zinc-200 px-2 py-0.5 text-[10px] dark:bg-zinc-800">
                          disabled
                        </span>
                      ) : pausedNow ? (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
                          paused
                        </span>
                      ) : (
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] text-green-800 dark:bg-green-900/40 dark:text-green-200">
                          active
                        </span>
                      )}
                    </TD>
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
                          className="rounded-md px-2 py-1 text-xs text-zinc-500 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950 dark:hover:text-red-300"
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
    </>
  );
}
