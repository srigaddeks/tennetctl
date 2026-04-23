"use client";

import { useState } from "react";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Select,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  Textarea,
} from "@/components/ui";
import { useMe } from "@/features/auth/hooks/use-auth";
import {
  useAddSuppression,
  useRemoveSuppression,
  useSuppressions,
} from "@/features/notify/hooks/use-suppressions";
import type { NotifySuppressionReasonCode } from "@/types/api";

const REASON_OPTIONS: { code: NotifySuppressionReasonCode; label: string }[] = [
  { code: "manual", label: "Manual hold" },
  { code: "hard_bounce", label: "Hard bounce" },
  { code: "complaint", label: "Complaint" },
  { code: "unsubscribe", label: "Unsubscribe" },
];

const REASON_TONE: Record<
  NotifySuppressionReasonCode,
  "danger" | "warning" | "default" | "info"
> = {
  hard_bounce: "danger",
  complaint: "warning",
  manual: "default",
  unsubscribe: "info",
};

const REASON_DESCRIPTIONS: Record<NotifySuppressionReasonCode, string> = {
  hard_bounce: "Permanent delivery failure — address is unreachable.",
  complaint:   "Recipient marked the message as spam.",
  manual:      "Manually added by an operator.",
  unsubscribe: "Recipient opted out.",
};

export default function NotifySuppressionsPage() {
  const me = useMe();
  const orgId = me.data?.session?.org_id ?? null;

  const list = useSuppressions(orgId);
  const remove = useRemoveSuppression(orgId);
  const [addOpen, setAddOpen] = useState(false);

  const items = list.data?.items ?? [];

  const byReason = REASON_OPTIONS.reduce(
    (acc, r) => ({ ...acc, [r.code]: items.filter((i) => i.reason_code === r.code).length }),
    {} as Record<NotifySuppressionReasonCode, number>,
  );

  return (
    <>
      <PageHeader
        title="Suppression List"
        description="Addresses blocked from receiving notifications. Hard bounces and complaints are added automatically — manually added entries require operator review to remove."
        testId="heading-notify-suppressions"
        actions={
          <Button
            onClick={() => setAddOpen(true)}
            disabled={!orgId}
            data-testid="btn-add-suppression"
          >
            + Add suppression
          </Button>
        }
      />
      <div
        className="flex-1 overflow-y-auto"
        style={{ padding: "24px 32px" }}
        data-testid="suppressions-body"
      >
        {/* Reason breakdown */}
        {items.length > 0 && (
          <div
            style={{
              display: "flex",
              gap: 16,
              marginBottom: 24,
              flexWrap: "wrap",
            }}
          >
            {REASON_OPTIONS.map((r) => {
              const count = byReason[r.code] ?? 0;
              const tone = REASON_TONE[r.code];
              const color =
                tone === "danger" ? "var(--danger)"
                : tone === "warning" ? "var(--warning)"
                : tone === "info" ? "var(--info)"
                : "var(--text-secondary)";
              const bg =
                tone === "danger" ? "var(--danger-muted)"
                : tone === "warning" ? "var(--warning-muted)"
                : tone === "info" ? "var(--info-muted)"
                : "var(--bg-elevated)";

              return (
                <div
                  key={r.code}
                  style={{
                    flex: 1,
                    minWidth: 140,
                    padding: "12px 16px",
                    borderRadius: 8,
                    border: "1px solid var(--border)",
                    background: "var(--bg-surface)",
                    borderLeft: `3px solid ${color}`,
                  }}
                >
                  <div
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      color: "var(--text-muted)",
                      marginBottom: 4,
                    }}
                  >
                    {r.label}
                  </div>
                  <div
                    style={{
                      fontFamily: "'IBM Plex Mono', monospace",
                      fontSize: 24,
                      fontWeight: 700,
                      color,
                      lineHeight: 1,
                    }}
                  >
                    {count}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Notice */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 12px",
            borderRadius: 6,
            border: "1px solid var(--warning)",
            background: "var(--warning-muted)",
            fontSize: 12,
            color: "var(--warning)",
            marginBottom: 20,
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ flexShrink: 0 }}>
            <path d="M7 1L1 12h12L7 1z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
            <path d="M7 5.5v3M7 10h.01" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
          Sending to suppressed addresses will permanently damage deliverability. Hard bounces and complaints are added automatically and should not be removed without verifying the address is valid.
        </div>

        {list.isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
          </div>
        )}
        {list.isError && (
          <ErrorState
            message={
              list.error instanceof Error ? list.error.message : "Load failed"
            }
            retry={() => list.refetch()}
          />
        )}
        {!list.isLoading && items.length === 0 && (
          <EmptyState
            title="No suppressions"
            description="No addresses are currently blocked. Hard bounces and complaints land here automatically."
          />
        )}
        {items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Email</TH>
                <TH>Reason</TH>
                <TH>Notes</TH>
                <TH>Added</TH>
                <TH></TH>
              </tr>
            </THead>
            <TBody>
              {items.map((s) => {
                const tone = REASON_TONE[s.reason_code] ?? "default";
                const rowBg =
                  tone === "danger" ? "rgba(255, 63, 85, 0.03)"
                  : tone === "warning" ? "rgba(245, 166, 35, 0.03)"
                  : undefined;

                return (
                  <TR
                    key={s.id}
                    data-testid={`suppression-row-${s.id}`}
                    style={rowBg ? { background: rowBg } : undefined}
                  >
                    <TD>
                      <span
                        style={{
                          fontFamily: "'IBM Plex Mono', monospace",
                          fontSize: 12,
                          color: "var(--text-primary)",
                        }}
                      >
                        {s.email}
                      </span>
                    </TD>
                    <TD>
                      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                        <Badge tone={tone}>
                          {s.reason_code}
                        </Badge>
                        <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                          {REASON_DESCRIPTIONS[s.reason_code]}
                        </span>
                      </div>
                    </TD>
                    <TD>
                      <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                        {s.notes ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <span
                        style={{
                          fontFamily: "'IBM Plex Mono', monospace",
                          fontSize: 11,
                          color: "var(--text-muted)",
                        }}
                      >
                        {s.created_at.slice(0, 10)}
                      </span>
                    </TD>
                    <TD>
                      <button
                        type="button"
                        data-testid={`suppression-remove-${s.id}`}
                        disabled={remove.isPending}
                        onClick={() => {
                          if (confirm(`Remove ${s.email} from the suppression list?`)) {
                            remove.mutate(s.id);
                          }
                        }}
                        style={{
                          fontSize: 12,
                          fontWeight: 500,
                          color: "var(--danger)",
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          padding: 0,
                          opacity: remove.isPending ? 0.5 : 1,
                        }}
                      >
                        Remove
                      </button>
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        )}
      </div>

      {orgId && (
        <AddSuppressionDialog
          open={addOpen}
          onClose={() => setAddOpen(false)}
          orgId={orgId}
        />
      )}
    </>
  );
}

function AddSuppressionDialog({
  open,
  onClose,
  orgId,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
}) {
  const add = useAddSuppression(orgId);
  const [form, setForm] = useState({
    email: "",
    reason_code: "manual" as NotifySuppressionReasonCode,
    notes: "",
  });
  const [err, setErr] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    add.mutate(
      {
        org_id: orgId,
        email: form.email,
        reason_code: form.reason_code,
        notes: form.notes || null,
      },
      {
        onSuccess: () => {
          setForm({ email: "", reason_code: "manual", notes: "" });
          onClose();
        },
        onError: (e) => setErr(e.message),
      },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="Add suppression" size="md">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
        data-testid="add-suppression-form"
      >
        <Field label="Email" htmlFor="sup-email" required>
          <Input
            id="sup-email"
            type="email"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            placeholder="user@example.com"
            data-testid="add-suppression-email"
            autoFocus
          />
        </Field>
        <Field label="Reason" htmlFor="sup-reason" required>
          <Select
            id="sup-reason"
            value={form.reason_code}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                reason_code: e.target.value as NotifySuppressionReasonCode,
              }))
            }
            data-testid="add-suppression-reason"
          >
            {REASON_OPTIONS.map((r) => (
              <option key={r.code} value={r.code}>
                {r.label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Notes (optional)" htmlFor="sup-notes">
          <Textarea
            id="sup-notes"
            rows={3}
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            placeholder="Context for why this was added"
            data-testid="add-suppression-notes"
          />
        </Field>
        {err && <p style={{ fontSize: 12, color: "var(--danger)" }}>{err}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={add.isPending || !form.email}
            data-testid="add-suppression-submit"
          >
            {add.isPending ? "Adding…" : "Add"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
