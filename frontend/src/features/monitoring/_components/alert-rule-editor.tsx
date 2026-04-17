"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import {
  Button,
  Field,
  Input,
  Select,
  Textarea,
} from "@/components/ui";
import {
  useAlertRule,
  useCreateAlertRule,
  useUpdateAlertRule,
} from "@/features/monitoring/hooks/use-alert-rules";
import type {
  AlertConditionOp,
  AlertRuleCreateRequest,
  AlertSeverity,
  AlertTarget,
  LastToken,
} from "@/types/api";

const SEVERITIES: AlertSeverity[] = ["info", "warn", "error", "critical"];
const OPS: AlertConditionOp[] = ["gt", "gte", "lt", "lte", "eq", "ne"];
const TIMERANGES: LastToken[] = ["15m", "1h", "24h", "7d", "30d", "90d"];
const BUCKETS = ["1m", "5m", "1h", "1d"] as const;
const AGGREGATES = [
  "sum",
  "avg",
  "min",
  "max",
  "count",
  "rate",
  "p50",
  "p95",
  "p99",
] as const;
const LOG_SEVERITIES = [
  { label: "debug (5)", value: 5 },
  { label: "info (9)", value: 9 },
  { label: "warn (13)", value: 13 },
  { label: "error (17)", value: 17 },
  { label: "fatal (21)", value: 21 },
];

type Props = {
  ruleId?: string | null;
};

function buildMetricsDsl(
  metricKey: string,
  aggregate: string,
  bucket: string,
  timerange: LastToken,
): Record<string, unknown> {
  return {
    target: "metrics",
    metric_key: metricKey,
    aggregate,
    bucket,
    timerange: { last: timerange },
  };
}

function buildLogsDsl(
  severityMin: number,
  bodyContains: string,
  timerange: LastToken,
): Record<string, unknown> {
  const dsl: Record<string, unknown> = {
    target: "logs",
    timerange: { last: timerange },
    severity_min: severityMin,
  };
  if (bodyContains) dsl.body_contains = bodyContains;
  return dsl;
}

export function AlertRuleEditor({ ruleId = null }: Props) {
  const router = useRouter();
  const isEdit = ruleId !== null && ruleId !== "new";
  const existing = useAlertRule(isEdit ? ruleId : null);
  const create = useCreateAlertRule();
  const update = useUpdateAlertRule();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [target, setTarget] = useState<AlertTarget>("metrics");
  const [severity, setSeverity] = useState<AlertSeverity>("warn");
  const [op, setOp] = useState<AlertConditionOp>("gt");
  const [threshold, setThreshold] = useState<number>(0);
  const [forDuration, setForDuration] = useState<number>(0);
  const [notifyTemplate, setNotifyTemplate] = useState("");
  const [recipientUserId, setRecipientUserId] = useState("");

  // Metrics-form state
  const [metricKey, setMetricKey] = useState("");
  const [aggregate, setAggregate] = useState<string>("sum");
  const [bucket, setBucket] = useState<string>("1m");
  const [timerange, setTimerange] = useState<LastToken>("15m");

  // Logs-form state
  const [logSeverityMin, setLogSeverityMin] = useState<number>(13);
  const [bodyContains, setBodyContains] = useState("");

  // Advanced DSL raw
  const [rawMode, setRawMode] = useState(false);
  const [rawDsl, setRawDsl] = useState("");

  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    const rule = existing.data;
    if (!rule) return;
    setName(rule.name);
    setDescription(rule.description ?? "");
    setTarget(rule.target);
    setSeverity(rule.severity);
    setOp(rule.condition.op);
    setThreshold(rule.condition.threshold);
    setForDuration(rule.condition.for_duration_seconds);
    setNotifyTemplate(rule.notify_template_key);
    setRecipientUserId(
      (rule.labels && (rule.labels.recipient_user_id ?? "")) || "",
    );
    const dsl = rule.dsl as Record<string, unknown>;
    if (rule.target === "metrics") {
      setMetricKey(String(dsl.metric_key ?? ""));
      setAggregate(String(dsl.aggregate ?? "sum"));
      setBucket(String(dsl.bucket ?? "1m"));
      const tr = dsl.timerange as { last?: LastToken } | undefined;
      if (tr?.last) setTimerange(tr.last);
    } else {
      setLogSeverityMin(Number(dsl.severity_min ?? 13));
      setBodyContains(String(dsl.body_contains ?? ""));
      const tr = dsl.timerange as { last?: LastToken } | undefined;
      if (tr?.last) setTimerange(tr.last);
    }
    setRawDsl(JSON.stringify(dsl, null, 2));
  }, [existing.data]);

  const submit = async () => {
    setFormError(null);
    if (!name.trim()) {
      setFormError("Name is required");
      return;
    }
    if (!notifyTemplate.trim()) {
      setFormError("Notify template key is required");
      return;
    }
    let dsl: Record<string, unknown>;
    if (rawMode) {
      try {
        dsl = JSON.parse(rawDsl) as Record<string, unknown>;
      } catch {
        setFormError("Raw DSL must be valid JSON");
        return;
      }
    } else if (target === "metrics") {
      if (!metricKey.trim()) {
        setFormError("Metric key is required");
        return;
      }
      dsl = buildMetricsDsl(metricKey.trim(), aggregate, bucket, timerange);
    } else {
      dsl = buildLogsDsl(logSeverityMin, bodyContains.trim(), timerange);
    }
    const labels: Record<string, string> = {};
    if (recipientUserId.trim()) {
      labels.recipient_user_id = recipientUserId.trim();
    }
    const createBody: AlertRuleCreateRequest = {
      name: name.trim(),
      description: description.trim() || null,
      target,
      dsl,
      condition: {
        op,
        threshold,
        for_duration_seconds: forDuration,
      },
      severity,
      notify_template_key: notifyTemplate.trim(),
      labels,
    };
    try {
      if (isEdit && ruleId) {
        // Update schema forbids `target` — omit it.
        const { target: _omit, ...rest } = createBody;
        await update.mutateAsync({ id: ruleId, body: rest });
      } else {
        await create.mutateAsync(createBody);
      }
      router.push("/monitoring/alerts/rules");
    } catch (e) {
      setFormError(
        e instanceof Error ? e.message : "Failed to save rule",
      );
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <Field label="Name" htmlFor="rule-name" required>
        <Input
          id="rule-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          data-testid="rule-name"
        />
      </Field>
      <Field label="Description" htmlFor="rule-desc">
        <Textarea
          id="rule-desc"
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          data-testid="rule-description"
        />
      </Field>

      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
          Target
        </span>
        <div className="flex gap-2" role="radiogroup">
          {(["metrics", "logs"] as AlertTarget[]).map((t) => (
            <button
              key={t}
              type="button"
              data-testid={`rule-target-${t}`}
              onClick={() => setTarget(t)}
              className={
                "rounded-md border px-3 py-1.5 text-xs font-medium " +
                (target === t
                  ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                  : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900")
              }
              aria-pressed={target === t}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
            DSL
          </span>
          <button
            type="button"
            data-testid="rule-raw-toggle"
            onClick={() => setRawMode((v) => !v)}
            className="text-xs text-zinc-500 underline"
          >
            {rawMode ? "Simple form" : "Raw DSL JSON"}
          </button>
        </div>
        {rawMode ? (
          <Textarea
            rows={8}
            value={rawDsl}
            onChange={(e) => setRawDsl(e.target.value)}
            data-testid="rule-dsl-raw"
            className="font-mono text-xs"
          />
        ) : target === "metrics" ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Field label="Metric key" htmlFor="dsl-metric-key" required>
              <Input
                id="dsl-metric-key"
                value={metricKey}
                onChange={(e) => setMetricKey(e.target.value)}
                data-testid="rule-dsl-metric-key"
              />
            </Field>
            <Field label="Aggregate" htmlFor="dsl-agg">
              <Select
                id="dsl-agg"
                value={aggregate}
                onChange={(e) => setAggregate(e.target.value)}
                data-testid="rule-dsl-aggregate"
              >
                {AGGREGATES.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Bucket" htmlFor="dsl-bucket">
              <Select
                id="dsl-bucket"
                value={bucket}
                onChange={(e) => setBucket(e.target.value)}
                data-testid="rule-dsl-bucket"
              >
                {BUCKETS.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Timerange" htmlFor="dsl-tr">
              <Select
                id="dsl-tr"
                value={timerange}
                onChange={(e) => setTimerange(e.target.value as LastToken)}
                data-testid="rule-dsl-timerange"
              >
                {TIMERANGES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Field label="Min severity" htmlFor="dsl-log-sev">
              <Select
                id="dsl-log-sev"
                value={logSeverityMin}
                onChange={(e) =>
                  setLogSeverityMin(Number(e.target.value))
                }
                data-testid="rule-dsl-log-severity"
              >
                {LOG_SEVERITIES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Body contains" htmlFor="dsl-log-body">
              <Input
                id="dsl-log-body"
                value={bodyContains}
                onChange={(e) => setBodyContains(e.target.value)}
                data-testid="rule-dsl-body-contains"
              />
            </Field>
            <Field label="Timerange" htmlFor="dsl-log-tr">
              <Select
                id="dsl-log-tr"
                value={timerange}
                onChange={(e) => setTimerange(e.target.value as LastToken)}
                data-testid="rule-dsl-timerange"
              >
                {TIMERANGES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Field label="Op" htmlFor="cond-op">
          <Select
            id="cond-op"
            value={op}
            onChange={(e) => setOp(e.target.value as AlertConditionOp)}
            data-testid="rule-condition-op"
          >
            {OPS.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Threshold" htmlFor="cond-threshold" required>
          <Input
            id="cond-threshold"
            type="number"
            step="any"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            data-testid="rule-condition-threshold"
          />
        </Field>
        <Field label="For duration (sec)" htmlFor="cond-for">
          <Input
            id="cond-for"
            type="number"
            min={0}
            max={86400}
            value={forDuration}
            onChange={(e) => setForDuration(Number(e.target.value))}
            data-testid="rule-condition-for"
          />
        </Field>
      </div>

      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
          Severity
        </span>
        <div
          className="flex gap-2"
          role="radiogroup"
          data-testid="rule-severity"
        >
          {SEVERITIES.map((s) => (
            <button
              key={s}
              type="button"
              data-testid={`rule-severity-${s}`}
              onClick={() => setSeverity(s)}
              aria-pressed={severity === s}
              className={
                "rounded-md border px-3 py-1.5 text-xs font-medium uppercase " +
                (severity === s
                  ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                  : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900")
              }
            >
              {s}
            </button>
          ))}
        </div>
        {/* Hidden select for E2E driver that prefers Select Options By */}
        <select
          aria-hidden
          className="sr-only"
          data-testid="rule-severity-select"
          value={severity}
          onChange={(e) => setSeverity(e.target.value as AlertSeverity)}
        >
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <Field
        label="Notify template key"
        htmlFor="notify-template"
        required
        hint="e.g. test.alert.template"
      >
        <Input
          id="notify-template"
          value={notifyTemplate}
          onChange={(e) => setNotifyTemplate(e.target.value)}
          data-testid="rule-notify-template"
        />
      </Field>

      <Field
        label="Recipient user id (label)"
        htmlFor="recipient-user"
        hint="Stored in labels.recipient_user_id — notify resolves recipient from this."
      >
        <Input
          id="recipient-user"
          value={recipientUserId}
          onChange={(e) => setRecipientUserId(e.target.value)}
          data-testid="rule-recipient-user-id"
        />
      </Field>

      {formError && (
        <p className="text-xs text-red-600 dark:text-red-400">{formError}</p>
      )}

      <div className="flex justify-end gap-2">
        <Button
          variant="ghost"
          onClick={() => router.push("/monitoring/alerts/rules")}
          data-testid="rule-cancel-button"
        >
          Cancel
        </Button>
        <Button
          onClick={submit}
          loading={create.isPending || update.isPending}
          data-testid="rule-save-button"
        >
          Save
        </Button>
      </div>
    </div>
  );
}
