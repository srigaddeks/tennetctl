"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  Field,
  Input,
  Select,
  Textarea,
} from "@/components/ui";
import { useEvaluate } from "@/features/featureflags/hooks/use-evaluate";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { EvalReason, FlagEnvironment } from "@/types/api";

const ENVS: FlagEnvironment[] = ["dev", "staging", "prod", "test"];

function ReasonBadge({ reason }: { reason: EvalReason }) {
  const tone =
    reason.includes("override")
      ? "purple"
      : reason === "rule_match"
        ? "blue"
        : reason === "flag_not_found"
          ? "red"
          : reason.includes("disabled") || reason.includes("inactive")
            ? "zinc"
            : "emerald";
  return <Badge tone={tone}>{reason}</Badge>;
}

function EvaluateClient() {
  const params = useSearchParams();
  const { toast } = useToast();
  const [flagKey, setFlagKey] = useState(params.get("flag_key") ?? "");
  const [env, setEnv] = useState<FlagEnvironment>("prod");
  const [userId, setUserId] = useState("");
  const [orgId, setOrgId] = useState("");
  const [applicationId, setApplicationId] = useState("");
  const [attrsStr, setAttrsStr] = useState("{}");
  const evalM = useEvaluate();

  useEffect(() => {
    const fk = params.get("flag_key");
    if (fk && !flagKey) setFlagKey(fk);
  }, [params, flagKey]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const attrs = JSON.parse(attrsStr || "{}");
      await evalM.mutateAsync({
        flag_key: flagKey,
        environment: env,
        context: {
          user_id: userId || undefined,
          org_id: orgId || undefined,
          application_id: applicationId || undefined,
          attrs,
        },
      });
    } catch (err) {
      const msg =
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
            ? err.message
            : String(err);
      toast(msg, "error");
    }
  }

  const result = evalM.data;

  return (
    <>
      <PageHeader
        title="Evaluation sandbox"
        description="Resolve a flag against a specific environment + context. The evaluator walks: scope match → flag active → env enabled → overrides → rules (priority asc + rollout hash) → fall-through default."
        testId="heading-evaluate"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="grid gap-6 lg:grid-cols-2">
          <form
            onSubmit={onSubmit}
            className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950"
            data-testid="evaluate-form"
          >
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
              Input
            </div>
            <Field label="Flag key" required>
              <Input
                value={flagKey}
                onChange={(e) => setFlagKey(e.target.value)}
                placeholder="new_checkout_flow"
                autoFocus
                data-testid="evaluate-flag-key"
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Environment" required>
                <Select
                  value={env}
                  onChange={(e) => setEnv(e.target.value as FlagEnvironment)}
                  data-testid="evaluate-env"
                >
                  {ENVS.map((e) => (
                    <option key={e} value={e}>
                      {e}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="User ID" hint="optional">
                <Input
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="uuid"
                  className="font-mono text-xs"
                  data-testid="evaluate-user-id"
                />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Org ID" hint="optional">
                <Input
                  value={orgId}
                  onChange={(e) => setOrgId(e.target.value)}
                  placeholder="uuid"
                  className="font-mono text-xs"
                />
              </Field>
              <Field label="Application ID" hint="optional">
                <Input
                  value={applicationId}
                  onChange={(e) => setApplicationId(e.target.value)}
                  placeholder="uuid"
                  className="font-mono text-xs"
                />
              </Field>
            </div>
            <Field label="Attrs (JSON)" hint="additional context used by rule conditions">
              <Textarea
                rows={4}
                value={attrsStr}
                onChange={(e) => setAttrsStr(e.target.value)}
                className="font-mono text-xs"
                data-testid="evaluate-attrs"
              />
            </Field>
            <Button
              type="submit"
              loading={evalM.isPending}
              data-testid="evaluate-submit"
            >
              Evaluate
            </Button>
          </form>

          <div className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-zinc-50">
              Result
            </div>
            {!result && !evalM.isPending && (
              <div className="rounded-md border border-dashed border-zinc-300 bg-zinc-50 p-6 text-center text-sm text-zinc-500 dark:border-zinc-700 dark:bg-zinc-900/50">
                Evaluate a flag to see the resolved value + trace.
              </div>
            )}
            {evalM.isPending && (
              <div className="rounded-md bg-zinc-50 p-6 text-center text-sm text-zinc-500 dark:bg-zinc-900">
                Evaluating…
              </div>
            )}
            {result && (
              <>
                <div
                  className={cn(
                    "rounded-lg border p-4",
                    result.reason.includes("override")
                      ? "border-purple-300 bg-purple-50 dark:border-purple-900/50 dark:bg-purple-950/30"
                      : result.reason === "rule_match"
                        ? "border-blue-300 bg-blue-50 dark:border-blue-900/50 dark:bg-blue-950/30"
                        : result.reason === "flag_not_found"
                          ? "border-red-300 bg-red-50 dark:border-red-900/50 dark:bg-red-950/30"
                          : "border-emerald-300 bg-emerald-50 dark:border-emerald-900/50 dark:bg-emerald-950/30"
                  )}
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Value
                    </span>
                    <ReasonBadge reason={result.reason} />
                  </div>
                  <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-base font-semibold text-zinc-900 dark:text-zinc-50">
                    {JSON.stringify(result.value, null, 2)}
                  </pre>
                </div>
                <div className="space-y-2 rounded-md bg-zinc-50 p-4 text-xs dark:bg-zinc-900">
                  <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                    Trace
                  </div>
                  <Row
                    ok={result.flag_id !== null}
                    label="Flag resolved"
                    detail={result.flag_id ? `${result.flag_scope} · ${result.flag_id.slice(0, 8)}…` : "flag_key not found at any scope"}
                  />
                  <Row
                    ok={
                      result.reason !== "flag_disabled_in_env" &&
                      result.reason !== "flag_not_found" &&
                      result.reason !== "flag_inactive"
                    }
                    label="Flag enabled in environment"
                    detail={
                      result.reason === "flag_disabled_in_env"
                        ? "env state is disabled — default served"
                        : result.reason === "flag_inactive"
                          ? "flag is inactive at the definition layer"
                          : "ok"
                    }
                  />
                  <Row
                    ok={result.override_id !== null}
                    label="Override matched"
                    detail={
                      result.override_id
                        ? `${result.reason} · ${result.override_id.slice(0, 8)}…`
                        : "no override for this entity"
                    }
                  />
                  <Row
                    ok={result.reason === "rule_match"}
                    label="Rule matched"
                    detail={
                      result.rule_id
                        ? `${result.rule_id.slice(0, 8)}…`
                        : "no rule matched (or rollout did not include this entity)"
                    }
                  />
                  <Row
                    ok
                    label="Final resolution"
                    detail={result.reason}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function Row({
  ok,
  label,
  detail,
}: {
  ok: boolean;
  label: string;
  detail: string;
}) {
  return (
    <div className="flex items-start gap-2">
      <span
        className={cn(
          "mt-0.5 flex h-4 w-4 items-center justify-center rounded-full text-[9px]",
          ok
            ? "bg-emerald-500 text-white"
            : "bg-zinc-300 text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300"
        )}
      >
        {ok ? "✓" : "·"}
      </span>
      <div className="flex-1">
        <div className="font-medium text-zinc-800 dark:text-zinc-200">
          {label}
        </div>
        <div className="text-[10px] text-zinc-500 dark:text-zinc-400">
          {detail}
        </div>
      </div>
    </div>
  );
}

export default function EvaluatePage() {
  return (
    <Suspense fallback={<div className="p-8">Loading…</div>}>
      <EvaluateClient />
    </Suspense>
  );
}
