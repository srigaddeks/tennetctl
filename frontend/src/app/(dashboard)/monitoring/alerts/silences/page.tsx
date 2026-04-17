"use client";

import { useMemo, useState } from "react";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import {
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  Textarea,
} from "@/components/ui";
import {
  useAlertRules,
  useCreateSilence,
  useDeleteSilence,
  useSilences,
} from "@/features/monitoring/hooks/use-alerts";

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

  return (
    <>
      <PageHeader
        title="Silences"
        description="Suppress alert notifications for matching rules or labels over a time window."
        testId="heading-monitoring-silences"
        actions={
          <Button
            onClick={() => setOpen(true)}
            data-testid="monitoring-silence-new"
          >
            New silence
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-8 py-6">
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
        {data && data.items.length === 0 && (
          <EmptyState
            title="No silences"
            description="Silences mute notifications for matching alert events over a time window."
          />
        )}
        {data && data.items.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-zinc-200 dark:border-zinc-800">
            <table className="min-w-full text-sm">
              <thead className="bg-zinc-50 text-left text-xs font-medium uppercase tracking-wide text-zinc-600 dark:bg-zinc-900 dark:text-zinc-400">
                <tr>
                  <th className="px-4 py-3">Matcher</th>
                  <th className="px-4 py-3">Reason</th>
                  <th className="px-4 py-3">Starts</th>
                  <th className="px-4 py-3">Ends</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {data.items.map((s) => {
                  const now = Date.now();
                  const active =
                    s.is_active &&
                    new Date(s.starts_at).getTime() <= now &&
                    new Date(s.ends_at).getTime() > now;
                  return (
                    <tr
                      key={s.id}
                      data-testid={`monitoring-silence-row-${s.id}`}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-zinc-600 dark:text-zinc-400">
                        {s.matcher.rule_id ? (
                          <div>rule: {s.matcher.rule_id.slice(0, 8)}</div>
                        ) : null}
                        {s.matcher.labels &&
                          Object.entries(s.matcher.labels).map(([k, v]) => (
                            <div key={k}>
                              {k}={v}
                            </div>
                          ))}
                      </td>
                      <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">
                        {s.reason}
                      </td>
                      <td className="px-4 py-3 text-xs text-zinc-500">
                        {new Date(s.starts_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-xs text-zinc-500">
                        {new Date(s.ends_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        {active ? (
                          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
                            active
                          </span>
                        ) : (
                          <span className="rounded-full bg-zinc-200 px-2 py-0.5 text-[10px] dark:bg-zinc-800">
                            expired
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => {
                            if (confirm("Delete silence?")) {
                              void del.mutateAsync(s.id);
                            }
                          }}
                          data-testid={`monitoring-silence-delete-${s.id}`}
                          className="rounded-md px-2 py-1 text-xs text-zinc-500 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950 dark:hover:text-red-300"
                          aria-label="Delete silence"
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
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
              className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
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
