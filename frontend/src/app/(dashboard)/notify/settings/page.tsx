"use client";

import { useEffect, useState } from "react";

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
} from "@/components/ui";
import { useMe } from "@/features/auth/hooks/use-auth";
import {
  useCreateSMTPConfig,
  useCreateSubscription,
  useCreateTemplateGroup,
  useDeleteSMTPConfig,
  useDeleteSubscription,
  useDeleteTemplateGroup,
  useSMTPConfigs,
  useSubscriptionList,
  useTemplateGroupList,
  useUpdateSMTPConfig,
  useUpdateSubscription,
  useUpdateTemplateGroup,
} from "@/features/notify/hooks/use-notify-settings";
import { useTemplates } from "@/features/notify/hooks/use-templates";
import type {
  NotifyCategoryCode,
  NotifyChannelCode,
  NotifySMTPConfig,
  NotifySMTPConfigUpdate,
  NotifySubscription,
  NotifySubscriptionRecipientMode,
  NotifySubscriptionUpdate,
  NotifyTemplateGroup,
  NotifyTemplateGroupUpdate,
} from "@/types/api";

const CHANNEL_OPTIONS: { id: number; code: NotifyChannelCode; label: string }[] = [
  { id: 1, code: "email",   label: "Email" },
  { id: 2, code: "webpush", label: "Web Push" },
  { id: 3, code: "in_app",  label: "In-app" },
];

const RECIPIENT_MODES: { value: NotifySubscriptionRecipientMode; label: string; help: string }[] = [
  { value: "actor", label: "Actor (default)",        help: "Notify the user who triggered the audit event." },
  { value: "users", label: "Specific users",         help: "Comma-separated user UUIDs in recipient_filter.user_ids." },
  { value: "roles", label: "Users with role(s)",     help: "Comma-separated role codes (e.g. admin, owner) in recipient_filter.role_codes." },
];

const CATEGORY_OPTIONS: { id: number; code: NotifyCategoryCode; label: string }[] = [
  { id: 1, code: "transactional", label: "Transactional" },
  { id: 2, code: "critical",      label: "Critical" },
  { id: 3, code: "marketing",     label: "Marketing" },
  { id: 4, code: "digest",        label: "Digest" },
];

function NewSMTPDialog({
  open,
  onClose,
  orgId,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
}) {
  const create = useCreateSMTPConfig(orgId);
  const [form, setForm] = useState({
    key: "",
    label: "",
    host: "",
    port: 587,
    tls: true,
    username: "",
    auth_vault_key: "",
    from_email: "",
    from_name: "",
  });
  const [err, setErr] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    create.mutate(
      {
        org_id: orgId,
        key: form.key,
        label: form.label,
        host: form.host,
        port: Number(form.port),
        tls: form.tls,
        username: form.username,
        auth_vault_key: form.auth_vault_key,
        from_email: form.from_email || null,
        from_name: form.from_name || null,
      },
      {
        onSuccess: () => {
          setForm({ key: "", label: "", host: "", port: 587, tls: true, username: "", auth_vault_key: "", from_email: "", from_name: "" });
          onClose();
        },
        onError: (e) => setErr(e.message),
      },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="New SMTP Config" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field label="Key" htmlFor="smtp-key" hint="slug, e.g. primary">
          <Input id="smtp-key" value={form.key} onChange={(e) => setForm((f) => ({ ...f, key: e.target.value }))} placeholder="primary" />
        </Field>
        <Field label="Label" htmlFor="smtp-label">
          <Input id="smtp-label" value={form.label} onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))} placeholder="Primary SMTP" />
        </Field>
        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <Field label="Host" htmlFor="smtp-host">
              <Input id="smtp-host" value={form.host} onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))} placeholder="smtp.example.com" />
            </Field>
          </div>
          <Field label="Port" htmlFor="smtp-port">
            <Input id="smtp-port" type="number" value={form.port} onChange={(e) => setForm((f) => ({ ...f, port: Number(e.target.value) }))} />
          </Field>
        </div>
        <Field label="Username" htmlFor="smtp-username">
          <Input id="smtp-username" value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} placeholder="smtp user / API key id" />
        </Field>
        <Field label="Vault auth key" htmlFor="smtp-vault-key" hint="Vault secret key holding SMTP password">
          <Input id="smtp-vault-key" value={form.auth_vault_key} onChange={(e) => setForm((f) => ({ ...f, auth_vault_key: e.target.value }))} placeholder="notify.smtp.primary" />
        </Field>
        <Field label="From email" htmlFor="smtp-from-email" hint="Required when username is an API key (SendGrid, Postmark, Mailgun)">
          <Input id="smtp-from-email" type="email" value={form.from_email} onChange={(e) => setForm((f) => ({ ...f, from_email: e.target.value }))} placeholder="notifications@example.com" />
        </Field>
        <Field label="From name (optional)" htmlFor="smtp-from-name">
          <Input id="smtp-from-name" value={form.from_name} onChange={(e) => setForm((f) => ({ ...f, from_name: e.target.value }))} placeholder="Acme Support" />
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.tls} onChange={(e) => setForm((f) => ({ ...f, tls: e.target.checked }))} />
          Use TLS
        </label>
        {err && <p className="text-xs text-red-500">{err}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={create.isPending}>{create.isPending ? "Creating…" : "Create"}</Button>
        </div>
      </form>
    </Modal>
  );
}

function NewGroupDialog({
  open,
  onClose,
  orgId,
  smtpConfigs,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
  smtpConfigs: { id: string; label: string; key: string }[];
}) {
  const create = useCreateTemplateGroup(orgId);
  const [form, setForm] = useState({
    key: "",
    label: "",
    category_id: 1,
    smtp_config_id: "",
  });
  const [err, setErr] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    create.mutate(
      {
        org_id: orgId,
        key: form.key,
        label: form.label,
        category_id: form.category_id,
        smtp_config_id: form.smtp_config_id || null,
      },
      {
        onSuccess: () => {
          setForm({ key: "", label: "", category_id: 1, smtp_config_id: "" });
          onClose();
        },
        onError: (e) => setErr(e.message),
      },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="New Template Group" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field label="Key" htmlFor="group-key" hint="slug, e.g. onboarding">
          <Input id="group-key" value={form.key} onChange={(e) => setForm((f) => ({ ...f, key: e.target.value }))} placeholder="onboarding" />
        </Field>
        <Field label="Label" htmlFor="group-label">
          <Input id="group-label" value={form.label} onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))} placeholder="Onboarding" />
        </Field>
        <Field label="Category" htmlFor="group-category">
          <Select
            id="group-category"
            value={form.category_id}
            onChange={(e) => setForm((f) => ({ ...f, category_id: Number(e.target.value) }))}
          >
            {CATEGORY_OPTIONS.map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </Select>
        </Field>
        <Field label="SMTP config (optional)" htmlFor="group-smtp" hint="Only needed for email templates">
          <Select
            id="group-smtp"
            value={form.smtp_config_id}
            onChange={(e) => setForm((f) => ({ ...f, smtp_config_id: e.target.value }))}
          >
            <option value="">— none —</option>
            {smtpConfigs.map((s) => (
              <option key={s.id} value={s.id}>{s.label} ({s.key})</option>
            ))}
          </Select>
        </Field>
        {err && <p className="text-xs text-red-500">{err}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={create.isPending}>{create.isPending ? "Creating…" : "Create"}</Button>
        </div>
      </form>
    </Modal>
  );
}

export default function NotifySettingsPage() {
  const me = useMe();
  const orgId = me.data?.session?.org_id ?? null;

  const smtp = useSMTPConfigs(orgId);
  const groups = useTemplateGroupList(orgId);
  const deleteSMTP = useDeleteSMTPConfig(orgId);
  const deleteGroup = useDeleteTemplateGroup(orgId);

  const [smtpOpen, setSmtpOpen] = useState(false);
  const [groupOpen, setGroupOpen] = useState(false);
  const [smtpEdit, setSmtpEdit] = useState<NotifySMTPConfig | null>(null);
  const [groupEdit, setGroupEdit] = useState<NotifyTemplateGroup | null>(null);

  const smtpItems = smtp.data?.items ?? [];
  const groupItems = groups.data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Notify Settings"
        description="SMTP servers and template groups. Configure these first before creating templates."
        testId="heading-notify-settings"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-10" data-testid="notify-settings-body">
        {/* SMTP Configs */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">SMTP Configs</h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Email server credentials stored in vault.</p>
            </div>
            <Button data-testid="btn-new-smtp" onClick={() => setSmtpOpen(true)} disabled={!orgId}>
              + New SMTP
            </Button>
          </div>
          {smtp.isLoading && <Skeleton className="h-16 w-full" />}
          {smtp.isError && <ErrorState message={smtp.error instanceof Error ? smtp.error.message : "Load failed"} />}
          {!smtp.isLoading && smtpItems.length === 0 && (
            <EmptyState title="No SMTP configs yet" description="Add a config to send email templates." />
          )}
          {smtpItems.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Key</TH>
                  <TH>Label</TH>
                  <TH>Host</TH>
                  <TH>Username</TH>
                  <TH>TLS</TH>
                  <TH>Actions</TH>
                </tr>
              </THead>
              <TBody>
                {smtpItems.map((s) => (
                  <TR key={s.id} data-testid={`smtp-row-${s.id}`}>
                    <TD><span className="font-mono text-xs">{s.key}</span></TD>
                    <TD>{s.label}</TD>
                    <TD><span className="text-xs">{s.host}:{s.port}</span></TD>
                    <TD><span className="text-xs">{s.username}</span></TD>
                    <TD><Badge tone={s.tls ? "emerald" : "zinc"}>{s.tls ? "Yes" : "No"}</Badge></TD>
                    <TD>
                      <div className="flex gap-3">
                        <button
                          type="button"
                          data-testid={`smtp-edit-${s.id}`}
                          onClick={() => setSmtpEdit(s)}
                          className="text-xs text-zinc-700 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          data-testid={`smtp-delete-${s.id}`}
                          disabled={deleteSMTP.isPending}
                          onClick={() => {
                            if (confirm(`Delete SMTP config "${s.label}"?`)) deleteSMTP.mutate(s.id);
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
        </section>

        {/* Template Groups */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">Template Groups</h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Group templates by purpose (onboarding, billing, etc.). Each group binds to one SMTP config.</p>
            </div>
            <Button data-testid="btn-new-group" onClick={() => setGroupOpen(true)} disabled={!orgId}>
              + New Group
            </Button>
          </div>
          {groups.isLoading && <Skeleton className="h-16 w-full" />}
          {groups.isError && <ErrorState message={groups.error instanceof Error ? groups.error.message : "Load failed"} />}
          {!groups.isLoading && groupItems.length === 0 && (
            <EmptyState title="No template groups yet" description="Create a group before adding templates." />
          )}
          {groupItems.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Key</TH>
                  <TH>Label</TH>
                  <TH>Category</TH>
                  <TH>SMTP</TH>
                  <TH>Actions</TH>
                </tr>
              </THead>
              <TBody>
                {groupItems.map((g) => (
                  <TR key={g.id} data-testid={`group-row-${g.id}`}>
                    <TD><span className="font-mono text-xs">{g.key}</span></TD>
                    <TD>{g.label}</TD>
                    <TD><Badge tone="blue">{g.category_label}</Badge></TD>
                    <TD><span className="text-xs">{g.smtp_config_key ?? "—"}</span></TD>
                    <TD>
                      <div className="flex gap-3">
                        <button
                          type="button"
                          data-testid={`group-edit-${g.id}`}
                          onClick={() => setGroupEdit(g)}
                          className="text-xs text-zinc-700 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          data-testid={`group-delete-${g.id}`}
                          disabled={deleteGroup.isPending}
                          onClick={() => {
                            if (confirm(`Delete group "${g.label}"?`)) deleteGroup.mutate(g.id);
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
        </section>

        {/* Subscriptions */}
        <SubscriptionsSection orgId={orgId} />
      </div>

      {orgId && (
        <>
          <NewSMTPDialog open={smtpOpen} onClose={() => setSmtpOpen(false)} orgId={orgId} />
          <NewGroupDialog open={groupOpen} onClose={() => setGroupOpen(false)} orgId={orgId} smtpConfigs={smtpItems.map((s) => ({ id: s.id, label: s.label, key: s.key }))} />
          <EditSMTPDialog
            open={smtpEdit !== null}
            onClose={() => setSmtpEdit(null)}
            orgId={orgId}
            row={smtpEdit}
          />
          <EditGroupDialog
            open={groupEdit !== null}
            onClose={() => setGroupEdit(null)}
            orgId={orgId}
            row={groupEdit}
            smtpConfigs={smtpItems.map((s) => ({ id: s.id, label: s.label, key: s.key }))}
          />
        </>
      )}
    </>
  );
}

function EditSMTPDialog({
  open,
  onClose,
  orgId,
  row,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
  row: NotifySMTPConfig | null;
}) {
  const update = useUpdateSMTPConfig(orgId);
  const [form, setForm] = useState({
    label: "",
    host: "",
    port: 587,
    tls: true,
    username: "",
    auth_vault_key: "",
    from_email: "",
    from_name: "",
    is_active: true,
  });
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (row) {
      setForm({
        label: row.label,
        host: row.host,
        port: row.port,
        tls: row.tls,
        username: row.username,
        auth_vault_key: row.auth_vault_key,
        from_email: row.from_email ?? "",
        from_name: row.from_name ?? "",
        is_active: row.is_active,
      });
      setErr(null);
    }
  }, [row]);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!row) return;
    setErr(null);
    const body: NotifySMTPConfigUpdate = {};
    if (form.label !== row.label) body.label = form.label;
    if (form.host !== row.host) body.host = form.host;
    if (Number(form.port) !== row.port) body.port = Number(form.port);
    if (form.tls !== row.tls) body.tls = form.tls;
    if (form.username !== row.username) body.username = form.username;
    if (form.auth_vault_key !== row.auth_vault_key) body.auth_vault_key = form.auth_vault_key;
    if ((form.from_email || null) !== row.from_email) body.from_email = form.from_email || null;
    if ((form.from_name || null) !== row.from_name) body.from_name = form.from_name || null;
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
    <Modal open={open} onClose={onClose} title={`Edit SMTP "${row.key}"`} size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" data-testid="smtp-edit-form">
        <Field label="Label" htmlFor="smtp-edit-label">
          <Input id="smtp-edit-label" value={form.label} onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))} />
        </Field>
        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <Field label="Host" htmlFor="smtp-edit-host">
              <Input id="smtp-edit-host" value={form.host} onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))} />
            </Field>
          </div>
          <Field label="Port" htmlFor="smtp-edit-port">
            <Input id="smtp-edit-port" type="number" value={form.port} onChange={(e) => setForm((f) => ({ ...f, port: Number(e.target.value) }))} />
          </Field>
        </div>
        <Field label="Username" htmlFor="smtp-edit-username">
          <Input id="smtp-edit-username" value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} />
        </Field>
        <Field label="Vault auth key" htmlFor="smtp-edit-vault-key">
          <Input id="smtp-edit-vault-key" value={form.auth_vault_key} onChange={(e) => setForm((f) => ({ ...f, auth_vault_key: e.target.value }))} />
        </Field>
        <Field label="From email" htmlFor="smtp-edit-from-email">
          <Input id="smtp-edit-from-email" type="email" value={form.from_email} onChange={(e) => setForm((f) => ({ ...f, from_email: e.target.value }))} />
        </Field>
        <Field label="From name" htmlFor="smtp-edit-from-name">
          <Input id="smtp-edit-from-name" value={form.from_name} onChange={(e) => setForm((f) => ({ ...f, from_name: e.target.value }))} />
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.tls} onChange={(e) => setForm((f) => ({ ...f, tls: e.target.checked }))} />
          Use TLS
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
            data-testid="smtp-edit-is-active"
          />
          Active
        </label>
        {err && <p className="text-xs text-red-500">{err}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={update.isPending} data-testid="smtp-edit-submit">
            {update.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function EditGroupDialog({
  open,
  onClose,
  orgId,
  row,
  smtpConfigs,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
  row: NotifyTemplateGroup | null;
  smtpConfigs: { id: string; label: string; key: string }[];
}) {
  const update = useUpdateTemplateGroup(orgId);
  const [form, setForm] = useState({
    label: "",
    category_id: 1,
    smtp_config_id: "",
    is_active: true,
  });
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (row) {
      setForm({
        label: row.label,
        category_id: row.category_id,
        smtp_config_id: row.smtp_config_id ?? "",
        is_active: row.is_active,
      });
      setErr(null);
    }
  }, [row]);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!row) return;
    setErr(null);
    const body: NotifyTemplateGroupUpdate = {};
    if (form.label !== row.label) body.label = form.label;
    if (form.category_id !== row.category_id) body.category_id = form.category_id;
    const nextSmtp = form.smtp_config_id || null;
    if (nextSmtp !== row.smtp_config_id) body.smtp_config_id = nextSmtp;
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
    <Modal open={open} onClose={onClose} title={`Edit group "${row.key}"`} size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" data-testid="group-edit-form">
        <Field label="Label" htmlFor="group-edit-label">
          <Input id="group-edit-label" value={form.label} onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))} />
        </Field>
        <Field label="Category" htmlFor="group-edit-category">
          <Select
            id="group-edit-category"
            value={form.category_id}
            onChange={(e) => setForm((f) => ({ ...f, category_id: Number(e.target.value) }))}
          >
            {CATEGORY_OPTIONS.map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </Select>
        </Field>
        <Field label="SMTP config" htmlFor="group-edit-smtp">
          <Select
            id="group-edit-smtp"
            value={form.smtp_config_id}
            onChange={(e) => setForm((f) => ({ ...f, smtp_config_id: e.target.value }))}
          >
            <option value="">— none —</option>
            {smtpConfigs.map((s) => (
              <option key={s.id} value={s.id}>{s.label} ({s.key})</option>
            ))}
          </Select>
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
            data-testid="group-edit-is-active"
          />
          Active
        </label>
        {err && <p className="text-xs text-red-500">{err}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={update.isPending} data-testid="group-edit-submit">
            {update.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Subscriptions: trigger rule that turns an audit event into a delivery.
// ──────────────────────────────────────────────────────────────────────────

function SubscriptionsSection({ orgId }: { orgId: string | null }) {
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
  templates: { id: string; key: string }[];
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
  templates: { id: string; key: string }[];
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
