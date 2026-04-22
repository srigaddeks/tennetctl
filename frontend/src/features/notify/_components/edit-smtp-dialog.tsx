"use client";

import { useEffect, useState } from "react";

import { Modal } from "@/components/modal";
import { Button, Field, Input } from "@/components/ui";
import { useUpdateSMTPConfig } from "@/features/notify/hooks/use-notify-settings";
import type { NotifySMTPConfig, NotifySMTPConfigUpdate } from "@/types/api";

export function EditSMTPDialog({
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
