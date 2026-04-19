"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  Table,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui";
import { useFunnel, useRetention } from "@/features/product-ops/hooks/use-funnels";

export default function FunnelsPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [stepsCsv, setStepsCsv] = useState<string>("page_view, signup_started, signup_completed");
  const [days, setDays] = useState<number>(30);
  const [cohortEvent, setCohortEvent] = useState<string>("signup_completed");
  const [returnEvent, setReturnEvent] = useState<string>("page_view");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const ws = params.get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const funnel = useFunnel();
  const retention = useRetention({
    workspace_id: workspaceId,
    cohort_event: cohortEvent,
    return_event: returnEvent,
    weeks: 8,
  });

  const runFunnel = async () => {
    if (!workspaceId) return;
    const steps = stepsCsv.split(",").map((s) => s.trim()).filter(Boolean);
    if (steps.length === 0) return;
    funnel.mutate({ workspace_id: workspaceId, steps, days });
  };

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Funnels & Retention"
        description="Sequential conversion funnel + weekly retention matrix over evt_product_events. Reuses Phase 10's query DSL shape."
      />

      {!workspaceId && (
        <EmptyState
          title="No workspace selected"
          description="Append ?workspace_id=… to compute funnels."
        />
      )}

      {workspaceId && (
        <>
          {/* Funnel */}
          <section className="flex flex-col gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
            <h3 className="text-sm font-semibold">Funnel</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2">
                <Field label="Steps (comma-separated event_name values)" htmlFor="funnel-steps">
                  <Input
                    id="funnel-steps"
                    value={stepsCsv}
                    onChange={(e) => setStepsCsv(e.target.value)}
                    data-testid="funnel-steps"
                  />
                </Field>
              </div>
              <Field label="Window (days)" htmlFor="funnel-days">
                <Input
                  id="funnel-days"
                  type="number"
                  min={1}
                  max={365}
                  value={String(days)}
                  onChange={(e) => setDays(Math.max(1, Number(e.target.value) || 30))}
                />
              </Field>
            </div>
            <div>
              <Button
                variant="primary"
                onClick={runFunnel}
                disabled={funnel.isPending}
                data-testid="funnel-run"
              >
                {funnel.isPending ? "Computing…" : "Run funnel"}
              </Button>
            </div>

            {funnel.isError && (
              <ErrorState
                message={funnel.error instanceof Error ? funnel.error.message : "Funnel failed"}
              />
            )}

            {funnel.data && (
              <div className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
                <Table>
                  <THead>
                    <TR>
                      <TH>Step</TH>
                      <TH>Event</TH>
                      <TH>Visitors</TH>
                      <TH>CVR (vs first)</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {funnel.data.steps.map((s) => (
                      <TR key={s.step}>
                        <TD>{s.step + 1}</TD>
                        <TD>
                          <code className="text-xs">{s.event_name}</code>
                        </TD>
                        <TD>{s.visitors.toLocaleString()}</TD>
                        <TD>{s.conversion_rate_from_first.toFixed(2)}%</TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              </div>
            )}
          </section>

          {/* Retention */}
          <section className="flex flex-col gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
            <h3 className="text-sm font-semibold">Retention</h3>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Cohort event" htmlFor="cohort-event">
                <Input
                  id="cohort-event"
                  value={cohortEvent}
                  onChange={(e) => setCohortEvent(e.target.value)}
                />
              </Field>
              <Field label="Return event" htmlFor="return-event">
                <Input
                  id="return-event"
                  value={returnEvent}
                  onChange={(e) => setReturnEvent(e.target.value)}
                />
              </Field>
            </div>
            {retention.isLoading && <Skeleton className="h-48 w-full" />}
            {retention.isError && (
              <ErrorState
                message={retention.error instanceof Error ? retention.error.message : "Retention failed"}
              />
            )}
            {retention.data && retention.data.cohorts.length === 0 && (
              <p className="text-sm text-zinc-500">No cohorts in window.</p>
            )}
            {retention.data && retention.data.cohorts.length > 0 && (
              <div className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
                <Table>
                  <THead>
                    <TR>
                      <TH>Cohort week</TH>
                      <TH>Size</TH>
                      <TH>Returned weeks (offsets)</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {retention.data.cohorts.map((c) => (
                      <TR key={c.cohort_week}>
                        <TD>{c.cohort_week}</TD>
                        <TD>{c.cohort_size}</TD>
                        <TD>
                          <code className="text-xs">{JSON.stringify(c.retained_weeks)}</code>
                        </TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
