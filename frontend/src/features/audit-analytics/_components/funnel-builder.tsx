"use client";

import { useState } from "react";

import { Button, ErrorState } from "@/components/ui";
import { useAuditFunnel } from "@/features/audit-analytics/hooks/use-audit-events";
import type { AuditFunnelStep } from "@/types/api";

export function FunnelBuilder() {
  const [steps, setSteps] = useState<string[]>(["", ""]);
  const [result, setResult] = useState<AuditFunnelStep[] | null>(null);
  const funnel = useAuditFunnel();

  function setStep(i: number, val: string) {
    setSteps((prev) => prev.map((s, idx) => (idx === i ? val : s)));
  }

  function addStep() {
    setSteps((prev) => [...prev, ""]);
  }

  function removeStep(i: number) {
    setSteps((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function run() {
    const clean = steps.map((s) => s.trim()).filter(Boolean);
    if (clean.length < 2) return;
    const res = await funnel.mutateAsync({ steps: clean });
    setResult(res.steps);
  }

  const maxUsers = result ? Math.max(1, ...result.map((s) => s.users)) : 1;

  return (
    <div
      className="flex flex-col gap-5 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="audit-funnel-builder"
    >
      <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
        Funnel Analysis
      </div>

      <div className="flex flex-col gap-2">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-2">
            <span className="w-5 shrink-0 text-center text-[10px] font-semibold text-zinc-400">
              {i + 1}
            </span>
            <input
              className="min-w-0 flex-1 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-1.5 font-mono text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              placeholder="event.key"
              value={step}
              onChange={(e) => setStep(i, e.target.value)}
              data-testid={`audit-funnel-step-${i}`}
            />
            {steps.length > 2 && (
              <button
                onClick={() => removeStep(i)}
                className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                aria-label={`Remove step ${i + 1}`}
              >
                ✕
              </button>
            )}
          </div>
        ))}
        {steps.length < 8 && (
          <button
            onClick={addStep}
            className="mt-1 text-left text-xs text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
          >
            + Add step
          </button>
        )}
      </div>

      <Button
        size="sm"
        loading={funnel.isPending}
        onClick={() => void run()}
        data-testid="audit-funnel-run"
        disabled={steps.filter((s) => s.trim()).length < 2}
      >
        Run funnel
      </Button>

      {funnel.isError && (
        <ErrorState
          message={
            funnel.error instanceof Error ? funnel.error.message : "Funnel failed"
          }
          retry={() => void run()}
        />
      )}

      {result && result.length > 0 && (
        <div className="flex flex-col gap-2" data-testid="audit-funnel-result">
          {result.map((step, i) => {
            const barPct = Math.round((step.users / maxUsers) * 100);
            return (
              <div key={`${step.event_key}-${i}`} className="flex flex-col gap-0.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-mono text-zinc-800 dark:text-zinc-200">
                    {i + 1}. {step.event_key}
                  </span>
                  <span className="tabular-nums text-zinc-500">
                    {step.users.toLocaleString()} ({step.conversion_pct}%)
                  </span>
                </div>
                <div className="relative h-2 w-full rounded bg-zinc-100 dark:bg-zinc-800">
                  <div
                    className="absolute inset-y-0 left-0 rounded bg-blue-500"
                    style={{ width: `${barPct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
