"use client";

import { useState } from "react";

import { Modal } from "@/components/modal";
import { Button, Field, Input, Select } from "@/components/ui";
import { useCreateTemplateGroup } from "@/features/notify/hooks/use-notify-settings";

import { CATEGORY_OPTIONS, type SmtpConfigOption } from "./notify-settings-constants";

export function NewGroupDialog({
  open,
  onClose,
  orgId,
  smtpConfigs,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
  smtpConfigs: SmtpConfigOption[];
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
