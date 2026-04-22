"use client";

import { useEffect, useState } from "react";

import { Modal } from "@/components/modal";
import { Button, Field, Input, Select } from "@/components/ui";
import { useUpdateTemplateGroup } from "@/features/notify/hooks/use-notify-settings";
import type { NotifyTemplateGroup, NotifyTemplateGroupUpdate } from "@/types/api";

import { CATEGORY_OPTIONS, type SmtpConfigOption } from "./notify-settings-constants";

export function EditGroupDialog({
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
  smtpConfigs: SmtpConfigOption[];
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
