"use client";

import { useMemo, useState } from "react";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  Textarea,
} from "@/components/ui";
import {
  useAlertRules,
  useCreateSilence,
  useDeleteSilence,
  useSilences,
} from "@/features/monitoring/hooks/use-alerts";

function expiryCountdown(endsAt: string): string {
  const ms = new Date(endsAt).getTime() - Date.now();
  if (ms <= 0) return "expired";
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  if (h > 0) return `${h}h ${m}m remaining`;
  return `${m}m remaining`;
}

export default function SilencesPage() {
  const [open, setOpen] = useState(false);
  const [ruleId, setRuleId] = useState<string>("");
  const [labels, setLabels] = useState("");
  const [reason, setReason] = useState("");
  const [hours, setHours] = useState("4");

  const { data, isLoading, isError, error, refetch } = useSilences();
  const rulesQ = useAlertRules();
  const create = useCreateSilence();
  const del = useDeleteSilence();

  const endsAt = useMemo(() => {
    const h = Number(hours) || 4;
    return new Date(Date.now() + h * 3600 * 1000).toISOString();
  }, [hours]);

  const submit = async () => {
    if (!reason) return;
    const parsedLabels: Record<string, string> = {};
    for (const line of labels.split("\n")) {
      const t = line.trim();
      if (!t) continue;
      const eq = t.indexOf("=");
      if (eq <= 0) continue;
      parsedLabels[t.slice(0, eq).trim()] = t.slice(eq + 1).trim();
    }
    const matcher: { rule_id?: string; labels?: Record<string, string> } = {};
    if (ruleId) matcher.rule_id = ruleId;
    if (Object.keys(parsedLabels).length > 0) matcher.labels = parsedLabels;

    await create.mutateAsync({
      matcher,
      starts_at: new Date().toISOString(),
      ends_at: endsAt,
      reason,
    });
    setOpen(false);
    setRuleId("");
    setLabels("");
    setReason("");
    setHours("4");
  };

  const items = data?.items ?? [];
  const activeCount = items.filter((s) => {
    const now = Date.now();
    return (
      s.is_active &&
      new Date(s.starts_at).getTime() <= now &&
      new Date(s.ends_at).getTime() > now
    );
  }).length;
  const expiredCount = items.length - activeCount;

  return (
    <>
      <PageHeader
        title="Silences"
        description="Suppress alert notifications for matching rules or labels over a time window."
        testId="heading-monitoring-silences"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Alerts", href: "/monitoring/alerts" },
          { label: "Silences" },
        ]}
        actions={
          <Button
            variant="accent"
            onClick={() => setOpen(true)}
            data-testid="monitoring-silence-new"
          >
            + New silence
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        <div className="flex flex-col gap-5">

          {/* Stats strip */}
          {!isLoading && items.length > 0 && (
            <div className="flex items-center gap-4 rounded border px-4 py-3"
              style={{ background: "var(--bg-surface)", borderColor: "var(--border)" }}
            >
              <div className="flex items-center gap-2">
                <span className="label-caps" style={{ color: "var(--text-muted)" }}>Active</span>
                <span className="font-mono-data text-[18px] font-semibold" style={{ color: "var(--warning)" }}>{activeCount}</span>
              </div>
              <span className="h-4 w-px" style={{ background: "var(--border)" }} />
              <div className="flex items-center gap-2">
                <span className="label-caps" style={{ color: "var(--text-muted)" }}>Expired</span>
                <span className="font-mono-data text-[18px] font-semibold" style={{ color: "var(--text-secondary)" }}>{expiredCount}</span>
              </div>
              <span className="h-4 w-px" style={{ background: "var(--border)" }} />
              <div className="flex items-center gap-2">
                <span className="label-caps" style={{ color: "var(--text-muted)" }}>Total</span>
                <span className="font-mono-data text-[18px] font-semibold" style={{ color: "var(--text-primary)" }}>{items.length}</span>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </div>
          )}

          {isError && (
            <ErrorState
              message={error instanceof Error ? error.message : "Load failed"}
              retry={() => refetch()}
            />
          )}

          {data && items.length === 0 && (
            <EmptyState
              title="No silences"
              description="Silences mute notifications for matching alert events over a time window."
              action={
                <Button onClick={() => setOpen(true)}>New silence</Button>
              }
            />
          )}

          {items.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Matcher</TH>
                  <TH>Reason</TH>
                  <TH>Window</TH>
                  <TH>Expires</TH>
                  <TH>Status</TH>
                  <TH className="text-right">Actions</TH>
                </tr>
              </THead>
              <TBody>
                {items.map((s) => {
                  const now = Date.now();
                  const active =
                    s.is_active &&
                    new Date(s.starts_at).getTime() <= now &&
                    new Date(s.ends_at).getTime() > now;

                  return (
                    <TR
                      key={s.id}
                      data-testid={`monitoring-silence-row-${s.id}`}
                    >
                      <TD>
                        <div
                          className="font-mono-data text-[11px] flex flex-col gap-0.5"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {s.matcher.rule_id ? (
                            <div style={{ color: "#9d6ef8" }}>
                              rule: {s.matcher.rule_id.slice(0, 12)}…
                            </div>
                          ) : null}
                          {s.matcher.labels &&
                            Object.entries(s.matcher.labels).map(([k, v]) => (
                              <div key={k}>
                                <span style={{ color: "var(--text-muted)" }}>{k}</span>
                                <span style={{ color: "var(--text-primary)" }}>={v}</span>
                              </div>
                            ))}
                          {!s.matcher.rule_id && (!s.matcher.labels || Object.keys(s.matcher.labels).length === 0) && (
                            <span style={{ color: "var(--text-muted)" }}>all alerts</span>
                          )}
                        </div>
                      </TD>
                      <TD>
                        <span
                          className="text-[13px]"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {s.reason}
                        </span>
                      </TD>
                      <TD>
                        <div
                          className="font-mono-data text-[11px] flex flex-col gap-0.5"
                          style={{ color: "var(--text-muted)" }}
                        >
                          <div>{new Date(s.starts_at).toLocaleString()}</div>
                          <div>→ {new Date(s.ends_at).toLocaleString()}</div>
                        </div>
                      </TD>
                      <TD>
                        <span
                          className="font-mono-data text-[11px]"
                          style={{
                            color: active ? "var(--warning)" : "var(--text-muted)",
                          }}
                        >
                          {expiryCountdown(s.ends_at)}
                        </span>
                      </TD>
                      <TD>
                        {active ? (
                          <Badge tone="warning" dot>active</Badge>
                        ) : (
                          <Badge tone="default">expired</Badge>
                        )}
                      </TD>
                      <TD className="text-right">
                        <button
                          type="button"
                          onClick={() => {
                            if (confirm("Delete silence?")) {
                              void del.mutateAsync(s.id);
                            }
                          }}
                          data-testid={`monitoring-silence-delete-${s.id}`}
                          className="flex h-7 w-7 items-center justify-center rounded text-[11px] transition-colors"
                          style={{ color: "var(--text-muted)" }}
                          onMouseEnter={(e) => {
                            (e.currentTarget as HTMLButtonElement).style.background = "var(--danger-muted)";
                            (e.currentTarget as HTMLButtonElement).style.color = "var(--danger)";
                          }}
                          onMouseLeave={(e) => {
                            (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                            (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)";
                          }}
                          aria-label="Delete silence"
                        >
                          ✕
                        </button>
                      </TD>
                    </TR>
                  );
                })}
              </TBody>
            </Table>
          )}
        </div>
      </div>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="New silence"
        size="md"
      >
        <div className="flex flex-col gap-4">
          <Field label="Rule" htmlFor="silence-rule">
            <select
              id="silence-rule"
              value={ruleId}
              onChange={(e) => setRuleId(e.target.value)}
              className="w-full rounded border px-3 py-1.5 text-[13px] transition-all duration-150 focus:outline-none focus:ring-1"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
                color: "var(--text-primary)",
              }}
              data-testid="monitoring-silence-form-rule"
            >
              <option value="">— any rule —</option>
              {rulesQ.data?.items.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Labels (one per line, key=value)" htmlFor="silence-labels">
            <Textarea
              id="silence-labels"
              rows={2}
              value={labels}
              onChange={(e) => setLabels(e.target.value)}
              className="font-mono text-xs"
              placeholder="team=platform"
              data-testid="monitoring-silence-form-labels"
            />
          </Field>
          <Field label="Duration (hours)" htmlFor="silence-hours-new" required>
            <Input
              id="silence-hours-new"
              type="number"
              min="1"
              max="168"
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              data-testid="monitoring-silence-form-hours"
            />
          </Field>
          <Field label="Reason" htmlFor="silence-reason-new" required>
            <Textarea
              id="silence-reason-new"
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              data-testid="monitoring-silence-form-reason"
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={submit}
              loading={create.isPending}
              disabled={!reason}
              data-testid="monitoring-silence-form-submit"
            >
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
