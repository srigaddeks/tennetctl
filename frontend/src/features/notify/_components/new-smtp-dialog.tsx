"use client";

import { useState } from "react";

import { Modal } from "@/components/modal";
import { Button, Field, Input } from "@/components/ui";
import { useCreateSMTPConfig } from "@/features/notify/hooks/use-notify-settings";

export function NewSMTPDialog({
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
