"use client";

import { useEffect, useState } from "react";

import { Modal } from "@/components/modal";
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
} from "@/components/ui";
import {
  useCreateSubscription,
  useDeleteSubscription,
  useSubscriptionList,
  useUpdateSubscription,
} from "@/features/notify/hooks/use-notify-settings";
import { useTemplates } from "@/features/notify/hooks/use-templates";
import type {
  NotifySubscription,
  NotifySubscriptionRecipientMode,
  NotifySubscriptionUpdate,
} from "@/types/api";

import {
  CHANNEL_OPTIONS,
  RECIPIENT_MODES,
  type TemplateOption,
} from "./notify-settings-constants";

export function SubscriptionsSection({ orgId }: { orgId: string | null }) {
  const subs = useSubscriptionList(orgId);
  const del = useDeleteSubscription(orgId);
  const templates = useTemplates(orgId);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editRow, setEditRow] = useState<NotifySubscription | null>(null);

  const items = subs.data?.items ?? [];
  const templateLabel = (id: string) =>
    templates.data?.items.find((t) => t.id === id)?.key ?? id.slice(0, 8) + "…";

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold">Subscriptions</h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Trigger rules: when an audit event matches the pattern, fan out to the configured template + channel. Recipient is determined by the recipient model.
          </p>
        </div>
        <Button data-testid="btn-new-subscription" onClick={() => setDialogOpen(true)} disabled={!orgId}>
          + New Subscription
        </Button>
      </div>
      {subs.isLoading && <Skeleton className="h-16 w-full" />}
      {subs.isError && <ErrorState message={subs.error instanceof Error ? subs.error.message : "Load failed"} />}
      {!subs.isLoading && items.length === 0 && (
        <EmptyState title="No subscriptions yet" description="Subscribe to an audit event pattern to start fanning out notifications." />
      )}
      {items.length > 0 && (
        <Table>
          <THead>
            <tr>
              <TH>Name</TH>
              <TH>Event pattern</TH>
              <TH>Template</TH>
              <TH>Channel</TH>
              <TH>Recipients</TH>
              <TH>Actions</TH>
            </tr>
          </THead>
          <TBody>
            {items.map((s) => (
              <TR key={s.id} data-testid={`sub-row-${s.id}`}>
                <TD>
                  <span>{s.name}</span>
                  {!s.is_active && (
                    <Badge tone="zinc" className="ml-2">inactive</Badge>
                  )}
                </TD>
                <TD><span className="font-mono text-xs">{s.event_key_pattern}</span></TD>
                <TD><span className="text-xs">{templateLabel(s.template_id)}</span></TD>
                <TD><Badge tone="blue">{s.channel_code}</Badge></TD>
                <TD>
                  <span className="text-xs">{s.recipient_mode}</span>
                  {s.recipient_mode !== "actor" && (
                    <span className="ml-1 font-mono text-[10px] text-zinc-500">
                      {JSON.stringify(s.recipient_filter)}
                    </span>
                  )}
                </TD>
                <TD>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      data-testid={`sub-edit-${s.id}`}
                      onClick={() => setEditRow(s)}
                      className="text-xs text-zinc-700 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      data-testid={`sub-delete-${s.id}`}
                      disabled={del.isPending}
                      onClick={() => {
                        if (confirm(`Delete subscription "${s.name}"?`)) del.mutate(s.id);
                      }}
                      className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </div>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}

      {orgId && (
        <>
          <NewSubscriptionDialog
            open={dialogOpen}
            onClose={() => setDialogOpen(false)}
            orgId={orgId}
            templates={(templates.data?.items ?? []).map((t) => ({ id: t.id, key: t.key }))}
          />
          <EditSubscriptionDialog
            open={editRow !== null}
            onClose={() => setEditRow(null)}
            orgId={orgId}
            row={editRow}
            templates={(templates.data?.items ?? []).map((t) => ({ id: t.id, key: t.key }))}
          />
        </>
      )}
    </section>
  );
}

function EditSubscriptionDialog({
  open,
  onClose,
  orgId,
  row,
  templates,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
  row: NotifySubscription | null;
  templates: TemplateOption[];
}) {
  const update = useUpdateSubscription(orgId);
  const [form, setForm] = useState({
    name: "",
    event_key_pattern: "",
    template_id: "",
    channel_id: 1,
    is_active: true,
  });
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (row) {
      setForm({
        name: row.name,
        event_key_pattern: row.event_key_pattern,
        template_id: row.template_id,
        channel_id: row.channel_id,
        is_active: row.is_active,
      });
      setErr(null);
    }
  }, [row]);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!row) return;
    setErr(null);
    const body: NotifySubscriptionUpdate = {};
    if (form.name !== row.name) body.name = form.name;
    if (form.event_key_pattern !== row.event_key_pattern) body.event_key_pattern = form.event_key_pattern;
    if (form.template_id !== row.template_id) body.template_id = form.template_id;
    if (form.channel_id !== row.channel_id) body.channel_id = form.channel_id;
    if (form.is_active !== row.is_active) body.is_active = form.is_active;
    if (Object.keys(body).length === 0) {
      onClose();
      return;
    }
    update.mutate(
      { id: row.id, body },
      {
        onSuccess: () => onClose(),
        onError: (e) => setErr(e.message),
      },
    );
  }

  if (!row) return null;

  return (
    <Modal open={open} onClose={onClose} title={`Edit "${row.name}"`} size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" data-testid="sub-edit-form">
        <Field label="Name" htmlFor="sub-edit-name">
          <Input id="sub-edit-name" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
        </Field>
        <Field label="Event key pattern" htmlFor="sub-edit-event">
          <Input id="sub-edit-event" value={form.event_key_pattern} onChange={(e) => setForm((f) => ({ ...f, event_key_pattern: e.target.value }))} />
        </Field>
        <Field label="Template" htmlFor="sub-edit-template">
          <Select
            id="sub-edit-template"
            value={form.template_id}
            onChange={(e) => setForm((f) => ({ ...f, template_id: e.target.value }))}
          >
            {templates.map((t) => (
              <option key={t.id} value={t.id}>{t.key}</option>
            ))}
          </Select>
        </Field>
        <Field label="Channel" htmlFor="sub-edit-channel">
          <Select
            id="sub-edit-channel"
            value={form.channel_id}
            onChange={(e) => setForm((f) => ({ ...f, channel_id: Number(e.target.value) }))}
          >
            {CHANNEL_OPTIONS.filter((c) => c.id !== 3).map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </Select>
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
            data-testid="sub-edit-is-active"
          />
          Active
        </label>
        {err && <p className="text-xs text-red-500">{err}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={update.isPending} data-testid="sub-edit-submit">
            {update.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function NewSubscriptionDialog({
  open,
  onClose,
  orgId,
  templates,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
  templates: TemplateOption[];
}) {
  const create = useCreateSubscription(orgId);
  const [form, setForm] = useState({
    name: "",
    event_key_pattern: "",
    template_id: "",
    channel_id: 1,
    recipient_mode: "actor" as NotifySubscriptionRecipientMode,
    recipient_filter_text: "",
  });
  const [err, setErr] = useState<string | null>(null);

  function parseFilter(): Record<string, unknown> {
    const raw = form.recipient_filter_text.trim();
    if (!raw) return {};
    const items = raw.split(",").map((s) => s.trim()).filter(Boolean);
    if (form.recipient_mode === "users") return { user_ids: items };
    if (form.recipient_mode === "roles") return { role_codes: items };
    return {};
  }

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    if (!form.template_id) {
      setErr("Pick a template first.");
      return;
    }
    create.mutate(
      {
        org_id: orgId,
        name: form.name,
        event_key_pattern: form.event_key_pattern,
        template_id: form.template_id,
        channel_id: form.channel_id,
        recipient_mode: form.recipient_mode,
        recipient_filter: parseFilter(),
      },
      {
        onSuccess: () => {
          setForm({
            name: "", event_key_pattern: "", template_id: "",
            channel_id: 1, recipient_mode: "actor", recipient_filter_text: "",
          });
          onClose();
        },
        onError: (e) => setErr(e.message),
      },
    );
  }

  const modeHelp = RECIPIENT_MODES.find((m) => m.value === form.recipient_mode)?.help;

  return (
    <Modal open={open} onClose={onClose} title="New Subscription" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field label="Name" htmlFor="sub-name">
          <Input id="sub-name" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Alert admins on user delete" />
        </Field>
        <Field label="Event key pattern" htmlFor="sub-event" hint="e.g. iam.users.deleted or iam.users.*">
          <Input id="sub-event" value={form.event_key_pattern} onChange={(e) => setForm((f) => ({ ...f, event_key_pattern: e.target.value }))} placeholder="iam.users.*" />
        </Field>
        <Field label="Template" htmlFor="sub-template">
          <Select
            id="sub-template"
            value={form.template_id}
            onChange={(e) => setForm((f) => ({ ...f, template_id: e.target.value }))}
          >
            <option value="">— Select template —</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>{t.key}</option>
            ))}
          </Select>
        </Field>
        <Field label="Channel" htmlFor="sub-channel" hint="In-app is always added automatically.">
          <Select
            id="sub-channel"
            value={form.channel_id}
            onChange={(e) => setForm((f) => ({ ...f, channel_id: Number(e.target.value) }))}
          >
            {CHANNEL_OPTIONS.filter((c) => c.id !== 3).map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </Select>
        </Field>
        <Field label="Recipient mode" htmlFor="sub-mode" hint={modeHelp}>
          <Select
            id="sub-mode"
            value={form.recipient_mode}
            onChange={(e) => setForm((f) => ({ ...f, recipient_mode: e.target.value as NotifySubscriptionRecipientMode }))}
          >
            {RECIPIENT_MODES.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </Select>
        </Field>
        {form.recipient_mode !== "actor" && (
          <Field
            label={form.recipient_mode === "users" ? "User IDs" : "Role codes"}
            htmlFor="sub-filter"
            hint="Comma-separated."
          >
            <Input
              id="sub-filter"
              value={form.recipient_filter_text}
              onChange={(e) => setForm((f) => ({ ...f, recipient_filter_text: e.target.value }))}
              placeholder={form.recipient_mode === "users" ? "uuid-1, uuid-2" : "admin, owner"}
            />
          </Field>
        )}
        {err && <p className="text-xs text-red-500">{err}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={create.isPending}>{create.isPending ? "Creating…" : "Create"}</Button>
        </div>
      </form>
    </Modal>
  );
}
