"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { Terminal, Zap, CheckCircle2, XCircle, Circle } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  Field,
  Input,
  Textarea,
} from "@/components/ui";
import { useFlags } from "@/features/featureflags/hooks/use-flags";
import { useEvaluate } from "@/features/featureflags/hooks/use-evaluate";
import { ApiClientError } from "@/lib/api";
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
            ? "default"
            : "emerald";
  return <Badge tone={tone as "purple" | "blue" | "red" | "default" | "emerald"}>{reason}</Badge>;
}

type TraceStep = {
  ok: boolean;
  label: string;
  detail: string;
};

function TraceRow({ step, index }: { step: TraceStep; index: number }) {
  return (
    <div className="flex items-start gap-3 py-2.5" style={{ borderBottom: "1px solid var(--border)" }}>
      {/* Step number + icon */}
      <div className="flex flex-col items-center gap-1 shrink-0 pt-0.5">
        <div
          className="flex h-5 w-5 items-center justify-center rounded-full text-[9px] font-bold"
          style={step.ok ? {
            background: "var(--success-muted)",
            border: "1px solid var(--success)",
            color: "var(--success)",
          } : {
            background: "var(--bg-elevated)",
            border: "1px solid var(--border)",
            color: "var(--text-muted)",
          }}
        >
          {index + 1}
        </div>
        {step.ok
          ? <CheckCircle2 className="h-3 w-3" style={{ color: "var(--success)" }} />
          : <Circle className="h-3 w-3" style={{ color: "var(--text-muted)" }} />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>
          {step.label}
        </div>
        <div
          className="mt-0.5 text-[11px] break-all"
          style={{
            color: step.ok ? "var(--text-secondary)" : "var(--text-muted)",
            fontFamily: "var(--font-mono)",
          }}
        >
          {step.detail}
        </div>
      </div>
      <div className="shrink-0">
        {step.ok
          ? <span className="label-caps text-[9px]" style={{ color: "var(--success)" }}>PASS</span>
          : <span className="label-caps text-[9px]" style={{ color: "var(--text-muted)" }}>SKIP</span>}
      </div>
    </div>
  );
}

// ─── Flag key autocomplete input ──────────────────────────────────────────────

function FlagKeyInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const { data } = useFlags({ limit: 500 });
  const [showDropdown, setShowDropdown] = useState(false);
  const [highlighted, setHighlighted] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const allKeys = (data?.items ?? []).map((f) => f.flag_key);
  const matches = value.trim()
    ? allKeys.filter((k) => k.toLowerCase().includes(value.toLowerCase()))
    : allKeys.slice(0, 10);

  function select(key: string) {
    onChange(key);
    setShowDropdown(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!showDropdown || matches.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted((h) => Math.min(h + 1, matches.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      select(matches[highlighted]);
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setShowDropdown(true);
          setHighlighted(0);
        }}
        onFocus={() => setShowDropdown(true)}
        onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
        onKeyDown={handleKeyDown}
        placeholder="new_checkout_flow"
        autoFocus
        data-testid="evaluate-flag-key"
        className="h-10 w-full rounded-lg border px-3 text-sm transition focus:outline-none"
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid var(--border)",
          color: "var(--text-primary)",
          fontFamily: "var(--font-mono)",
          fontSize: "13px",
          letterSpacing: "0.01em",
        }}
        onFocusCapture={(e) => {
          (e.target as HTMLInputElement).style.borderColor = "var(--accent)";
          (e.target as HTMLInputElement).style.boxShadow = "0 0 0 3px var(--accent-muted)";
        }}
        onBlurCapture={(e) => {
          (e.target as HTMLInputElement).style.borderColor = "var(--border)";
          (e.target as HTMLInputElement).style.boxShadow = "none";
        }}
      />
      {showDropdown && matches.length > 0 && (
        <div
          className="absolute left-0 right-0 z-50 mt-1 overflow-hidden rounded-lg"
          style={{
            background: "var(--bg-elevated)",
            border: "1px solid var(--border-bright)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
            maxHeight: "220px",
            overflowY: "auto",
          }}
        >
          {matches.map((k, i) => (
            <button
              key={k}
              type="button"
              onMouseDown={() => select(k)}
              className="flex w-full items-center px-3 py-2 text-left transition"
              style={{
                background: i === highlighted ? "var(--accent-muted)" : "transparent",
                color: i === highlighted ? "var(--accent)" : "var(--text-secondary)",
                fontFamily: "var(--font-mono)",
                fontSize: "12px",
                borderBottom: i < matches.length - 1 ? "1px solid var(--border)" : "none",
              }}
            >
              {k}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Environment tab bar ──────────────────────────────────────────────────────

function EnvTabBar({
  value,
  onChange,
}: {
  value: FlagEnvironment;
  onChange: (v: FlagEnvironment) => void;
}) {
  return (
    <div
      className="flex gap-1 rounded-lg p-1"
      style={{
        background: "var(--bg-elevated)",
        border: "1px solid var(--border)",
      }}
    >
      {ENVS.map((env) => {
        const active = value === env;
        return (
          <button
            key={env}
            type="button"
            onClick={() => onChange(env)}
            data-testid={`evaluate-env-tab-${env}`}
            className="flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition"
            style={active ? {
              background: "var(--accent)",
              color: "white",
              boxShadow: "0 1px 4px rgba(45,126,247,0.4)",
            } : {
              background: "transparent",
              color: "var(--text-muted)",
            }}
          >
            {env}
          </button>
        );
      })}
    </div>
  );
}

// ─── Main evaluator ───────────────────────────────────────────────────────────

function EvaluateClient() {
  const params = useSearchParams();
  const { toast } = useToast();
  const [flagKey, setFlagKey] = useState(params.get("flag_key") ?? "");
  const [env, setEnv] = useState<FlagEnvironment>("prod");
  const [userId, setUserId] = useState("");
  const [orgId, setOrgId] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
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
          workspace_id: workspaceId || undefined,
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

  const isPositiveResult = result && !result.reason.includes("disabled") && !result.reason.includes("inactive") && result.reason !== "flag_not_found";

  const traceSteps: TraceStep[] = result
    ? [
        {
          ok: result.flag_id !== null,
          label: "Flag resolved",
          detail: result.flag_id
            ? `${result.flag_scope} scope · id:${result.flag_id.slice(0, 12)}…`
            : "flag_key not found at any scope",
        },
        {
          ok: result.reason !== "flag_disabled_in_env" && result.reason !== "flag_not_found" && result.reason !== "flag_inactive",
          label: "Flag active + environment enabled",
          detail:
            result.reason === "flag_disabled_in_env"
              ? "environment state is disabled — default value served"
              : result.reason === "flag_inactive"
                ? "flag is inactive at definition layer — default served"
                : "flag is active and enabled in this environment",
        },
        {
          ok: result.override_id !== null,
          label: "Override matched",
          detail: result.override_id
            ? `${result.reason} · override:${result.override_id.slice(0, 12)}…`
            : "no override configured for this entity",
        },
        {
          ok: result.reason === "rule_match",
          label: "Rule matched",
          detail: result.rule_id
            ? `rule:${result.rule_id.slice(0, 12)}… matched — rollout included this entity`
            : "no rule matched or rollout hash excluded this entity",
        },
        {
          ok: true,
          label: "Final resolution",
          detail: `reason:${result.reason}`,
        },
      ]
    : [];

  return (
    <>
      <PageHeader
        title="Evaluation Sandbox"
        description="Resolve any flag against an environment and context. The evaluator walks: scope → active → env enabled → overrides → rules → default."
        testId="heading-evaluate"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* ── Input panel ── */}
          <form
            onSubmit={onSubmit}
            className="flex flex-col gap-4 rounded-xl p-6"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
            }}
            data-testid="evaluate-form"
          >
            {/* Panel header */}
            <div className="flex items-center gap-2 mb-1">
              <div
                className="flex h-7 w-7 items-center justify-center rounded-lg"
                style={{ background: "var(--accent-muted)", border: "1px solid var(--accent-dim)" }}
              >
                <Terminal className="h-3.5 w-3.5" style={{ color: "var(--accent)" }} />
              </div>
              <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Evaluation Input
              </span>
            </div>

            {/* Flag key — prominent, monospace, with autocomplete */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  className="label-caps"
                  style={{ color: "var(--text-secondary)", fontSize: "10px" }}
                >
                  FLAG KEY <span style={{ color: "var(--danger)" }}>*</span>
                </label>
                <span className="text-[10px]" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  start typing to search
                </span>
              </div>
              <FlagKeyInput value={flagKey} onChange={setFlagKey} />
            </div>

            {/* Environment — tab bar */}
            <div>
              <div className="mb-1.5">
                <label
                  className="label-caps"
                  style={{ color: "var(--text-secondary)", fontSize: "10px" }}
                >
                  ENVIRONMENT <span style={{ color: "var(--danger)" }}>*</span>
                </label>
              </div>
              <EnvTabBar value={env} onChange={setEnv} />
            </div>

            {/* Context IDs */}
            <div className="grid grid-cols-2 gap-3">
              <Field label="User ID" hint="optional">
                <Input
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="uuid"
                  style={{ fontFamily: "var(--font-mono)", fontSize: "11px" }}
                  data-testid="evaluate-user-id"
                />
              </Field>
              <Field label="Org ID" hint="optional">
                <Input
                  value={orgId}
                  onChange={(e) => setOrgId(e.target.value)}
                  placeholder="uuid"
                  style={{ fontFamily: "var(--font-mono)", fontSize: "11px" }}
                />
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Workspace ID" hint="optional">
                <Input
                  value={workspaceId}
                  onChange={(e) => setWorkspaceId(e.target.value)}
                  placeholder="uuid"
                  style={{ fontFamily: "var(--font-mono)", fontSize: "11px" }}
                  data-testid="evaluate-workspace-id"
                />
              </Field>
              <Field label="Application ID" hint="optional">
                <Input
                  value={applicationId}
                  onChange={(e) => setApplicationId(e.target.value)}
                  placeholder="uuid"
                  style={{ fontFamily: "var(--font-mono)", fontSize: "11px" }}
                />
              </Field>
            </div>

            <Field label="Context attrs (JSON)" hint="additional attributes for rule conditions">
              <Textarea
                rows={5}
                value={attrsStr}
                onChange={(e) => setAttrsStr(e.target.value)}
                style={{ fontFamily: "var(--font-mono)", fontSize: "11px" }}
                data-testid="evaluate-attrs"
              />
            </Field>

            <Button
              type="submit"
              variant="primary"
              loading={evalM.isPending}
              data-testid="evaluate-submit"
            >
              <Zap className="h-3.5 w-3.5 mr-1.5" />
              Evaluate
            </Button>
          </form>

          {/* ── Result panel ── */}
          <div
            className="flex flex-col gap-4 rounded-xl p-6"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
            }}
          >
            {/* Panel header */}
            <div className="flex items-center gap-2 mb-1">
              <div
                className="flex h-7 w-7 items-center justify-center rounded-lg"
                style={{
                  background: result ? (isPositiveResult ? "var(--success-muted)" : "var(--danger-muted)") : "var(--bg-elevated)",
                  border: `1px solid ${result ? (isPositiveResult ? "var(--success)" : "var(--danger)") : "var(--border)"}`,
                }}
              >
                {result
                  ? isPositiveResult
                    ? <CheckCircle2 className="h-3.5 w-3.5" style={{ color: "var(--success)" }} />
                    : <XCircle className="h-3.5 w-3.5" style={{ color: "var(--danger)" }} />
                  : <Terminal className="h-3.5 w-3.5" style={{ color: "var(--text-muted)" }} />}
              </div>
              <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Evaluation Result
              </span>
            </div>

            {!result && !evalM.isPending && (
              <div
                className="flex-1 rounded-xl flex flex-col items-center justify-center gap-3 py-16 text-center"
                style={{
                  border: "1px dashed var(--border-bright)",
                  background: "var(--bg-elevated)",
                }}
              >
                <Terminal className="h-8 w-8" style={{ color: "var(--text-muted)" }} />
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  Configure your context and run the evaluator.
                </p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  The resolved value and full trace will appear here.
                </p>
              </div>
            )}

            {evalM.isPending && (
              <div
                className="flex-1 rounded-xl flex items-center justify-center gap-2 py-16"
                style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }}
              >
                <div
                  className="h-4 w-4 rounded-full animate-spin"
                  style={{ border: "2px solid var(--accent-dim)", borderTopColor: "var(--accent)" }}
                />
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  Evaluating…
                </span>
              </div>
            )}

            {result && (
              <>
                {/* Resolved value */}
                <div
                  className="rounded-xl p-5"
                  style={{
                    background: isPositiveResult ? "var(--success-muted)" : "var(--bg-elevated)",
                    border: `1px solid ${isPositiveResult ? "var(--success)" : "var(--border)"}`,
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="label-caps" style={{ color: "var(--text-muted)" }}>
                      Resolved Value
                    </span>
                    <ReasonBadge reason={result.reason} />
                  </div>
                  <pre
                    className="overflow-x-auto whitespace-pre-wrap text-xl font-bold"
                    style={{
                      color: isPositiveResult ? "var(--success)" : "var(--text-primary)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {JSON.stringify(result.value, null, 2)}
                  </pre>
                </div>

                {/* Evaluation trace */}
                <div
                  className="rounded-xl overflow-hidden"
                  style={{
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--border)",
                  }}
                >
                  <div
                    className="px-4 py-2.5 flex items-center gap-2"
                    style={{ borderBottom: "1px solid var(--border)" }}
                  >
                    <span className="label-caps" style={{ color: "var(--text-muted)" }}>
                      Evaluation Trace
                    </span>
                    <span
                      className="ml-auto text-[10px] font-medium"
                      style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                    >
                      {traceSteps.filter((s) => s.ok).length}/{traceSteps.length} steps matched
                    </span>
                  </div>
                  <div className="px-4 pb-2">
                    {traceSteps.map((step, i) => (
                      <TraceRow key={i} step={step} index={i} />
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default function EvaluatePage() {
  return (
    <Suspense fallback={
      <div
        className="flex items-center justify-center p-8"
        style={{ color: "var(--text-muted)" }}
      >
        Loading sandbox…
      </div>
    }>
      <EvaluateClient />
    </Suspense>
  );
}
