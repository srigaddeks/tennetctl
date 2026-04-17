"use client";

import { useState, useMemo } from "react";

import { Modal } from "@/components/modal";
import { Button, Field, Input, Textarea } from "@/components/ui";
import {
  useCreateSilence,
  useSilenceFromEvent,
} from "@/features/monitoring/hooks/use-alerts";
import type { AlertEvent } from "@/types/api";

type Props = {
  open: boolean;
  onClose: () => void;
  alertEvent?: AlertEvent | null;
  ruleId?: string | null;
};

function toLocalInput(d: Date): string {
  // Format Date to `YYYY-MM-DDTHH:mm` for datetime-local input.
  const pad = (n: number) => n.toString().padStart(2, "0");
  return (
    d.getFullYear() +
    "-" +
    pad(d.getMonth() + 1) +
    "-" +
    pad(d.getDate()) +
    "T" +
    pad(d.getHours()) +
    ":" +
    pad(d.getMinutes())
  );
}

export function SilenceDialog({
  open,
  onClose,
  alertEvent = null,
  ruleId = null,
}: Props) {
  const now = useMemo(() => new Date(), []);
  const plusHour = useMemo(() => new Date(now.getTime() + 3_600_000), [now]);

  const [startsAt, setStartsAt] = useState(toLocalInput(now));
  const [endsAt, setEndsAt] = useState(toLocalInput(plusHour));
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createFromEvent = useSilenceFromEvent();
  const createGeneric = useCreateSilence();

  const submit = async () => {
    setError(null);
    if (!reason.trim()) {
      setError("Reason is required");
      return;
    }
    try {
      const ends = new Date(endsAt).toISOString();
      const starts = new Date(startsAt).toISOString();
      if (alertEvent) {
        await createFromEvent.mutateAsync({
          alertId: alertEvent.id,
          ends_at: ends,
          reason: reason.trim(),
          started_at: alertEvent.started_at,
        });
      } else {
        await createGeneric.mutateAsync({
          matcher: ruleId ? { rule_id: ruleId } : {},
          starts_at: starts,
          ends_at: ends,
          reason: reason.trim(),
        });
      }
      onClose();
      setReason("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create silence");
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Silence alert"
      description={
        alertEvent
          ? `Silence "${alertEvent.rule_name ?? alertEvent.rule_id}" firings.`
          : "Create a silence rule."
      }
      size="md"
    >
      <div
        className="flex flex-col gap-4"
        data-testid="silence-dialog"
      >
        <Field label="Starts at" htmlFor="silence-starts">
          <Input
            id="silence-starts"
            type="datetime-local"
            value={startsAt}
            onChange={(e) => setStartsAt(e.target.value)}
            data-testid="silence-starts-at"
          />
        </Field>
        <Field label="Ends at" htmlFor="silence-ends" required>
          <Input
            id="silence-ends"
            type="datetime-local"
            value={endsAt}
            onChange={(e) => setEndsAt(e.target.value)}
            data-testid="silence-ends-at"
          />
        </Field>
        <Field label="Reason" htmlFor="silence-reason" required>
          <Textarea
            id="silence-reason"
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            data-testid="silence-reason"
          />
        </Field>
        {error && (
          <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} data-testid="silence-cancel">
            Cancel
          </Button>
          <Button
            onClick={submit}
            loading={createFromEvent.isPending || createGeneric.isPending}
            data-testid="silence-save"
          >
            Save
          </Button>
        </div>
      </div>
    </Modal>
  );
}
