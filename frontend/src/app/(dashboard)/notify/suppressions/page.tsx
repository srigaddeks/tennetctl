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
  "red" | "amber" | "zinc" | "blue"
> = {
  hard_bounce: "red",
  complaint: "amber",
  manual: "zinc",
  unsubscribe: "blue",
};

export default function NotifySuppressionsPage() {
  const me = useMe();
  const orgId = me.data?.session?.org_id ?? null;

  const list = useSuppressions(orgId);
  const remove = useRemoveSuppression(orgId);
  const [addOpen, setAddOpen] = useState(false);

  const items = list.data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Notify Suppressions"
        description="Email addresses that cannot receive notifications — bounced, complained, unsubscribed, or manually held."
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
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="suppressions-body">
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
              {items.map((s) => (
                <TR key={s.id} data-testid={`suppression-row-${s.id}`}>
                  <TD>
                    <span className="font-mono text-xs">{s.email}</span>
                  </TD>
                  <TD>
                    <Badge tone={REASON_TONE[s.reason_code] ?? "zinc"}>
                      {s.reason_code}
                    </Badge>
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">{s.notes ?? "—"}</span>
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
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
                      className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50"
                    >
                      Remove
                    </button>
                  </TD>
                </TR>
              ))}
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
        {err && <p className="text-xs text-red-500">{err}</p>}
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
