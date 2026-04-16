"use client";

import { useToast } from "@/components/toast";
import { Badge, EmptyState, Skeleton } from "@/components/ui";
import {
  useFlagStates,
  useUpdateFlagState,
} from "@/features/featureflags/hooks/use-flags";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Flag, FlagEnvironment } from "@/types/api";

const ENV_ORDER: FlagEnvironment[] = ["dev", "staging", "prod", "test"];

const ENV_TONE: Record<FlagEnvironment, "zinc" | "blue" | "emerald" | "red" | "amber" | "purple"> =
  {
    dev: "blue",
    staging: "amber",
    prod: "emerald",
    test: "purple",
  };

export function FlagEnvironmentsPanel({ flag }: { flag: Flag }) {
  const { toast } = useToast();
  const { data: states, isLoading } = useFlagStates(flag.id);
  const update = useUpdateFlagState();

  if (isLoading) return <Skeleton className="h-24 w-full" />;
  if (!states) return <EmptyState title="No states" />;

  async function onToggle(stateId: string, nextEnabled: boolean) {
    try {
      await update.mutateAsync({
        id: stateId,
        body: { is_enabled: nextEnabled },
      });
      toast(nextEnabled ? "Enabled" : "Disabled", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  const sorted = [...states.items].sort(
    (a, b) => ENV_ORDER.indexOf(a.environment) - ENV_ORDER.indexOf(b.environment)
  );

  return (
    <>
      <p className="mb-4 max-w-3xl text-sm text-zinc-500 dark:text-zinc-400">
        Toggle the flag on or off per environment. A disabled flag in an environment always returns the
        default value — rules and overrides are skipped.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {sorted.map((s) => (
          <div
            key={s.id}
            data-testid={`env-card-${s.environment}`}
            className={cn(
              "flex flex-col gap-3 rounded-xl border p-4 transition",
              s.is_enabled
                ? "border-emerald-300 bg-emerald-50/60 dark:border-emerald-900/50 dark:bg-emerald-950/30"
                : "border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
            )}
          >
            <div className="flex items-center justify-between">
              <Badge tone={ENV_TONE[s.environment]}>{s.environment}</Badge>
              <button
                role="switch"
                aria-checked={s.is_enabled}
                onClick={() => onToggle(s.id, !s.is_enabled)}
                data-testid={`toggle-${s.environment}`}
                className={cn(
                  "relative h-6 w-11 rounded-full transition",
                  s.is_enabled
                    ? "bg-emerald-500"
                    : "bg-zinc-300 dark:bg-zinc-700"
                )}
              >
                <span
                  className={cn(
                    "absolute top-0.5 h-5 w-5 rounded-full bg-white transition",
                    s.is_enabled ? "left-5" : "left-0.5"
                  )}
                />
              </button>
            </div>
            <div className="text-xs text-zinc-500 dark:text-zinc-400">
              {s.is_enabled
                ? "Evaluator walks overrides and rules."
                : "Evaluator short-circuits to default value."}
            </div>
            <div className="mt-auto text-[10px] text-zinc-400">
              Env default:{" "}
              <code className="rounded bg-zinc-100 px-1 py-0.5 dark:bg-zinc-800">
                {s.env_default_value === null
                  ? "inherit"
                  : JSON.stringify(s.env_default_value)}
              </code>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
