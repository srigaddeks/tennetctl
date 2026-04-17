"use client";

import { useRouter } from "next/navigation";
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
} from "@/components/ui";
import { useMe } from "@/features/auth/hooks/use-auth";
import { useCreateTemplate, useTemplateGroups, useTemplates } from "@/features/notify/hooks/use-templates";
import type { NotifyPriorityCode, NotifyTemplate } from "@/types/api";

const PRIORITY_OPTIONS: Array<{ id: number; label: string }> = [
  { id: 1, label: "Low" },
  { id: 2, label: "Normal" },
  { id: 3, label: "High" },
  { id: 4, label: "Critical" },
];

function priorityTone(code: NotifyPriorityCode): "zinc" | "blue" | "amber" | "red" {
  switch (code) {
    case "low":      return "zinc";
    case "normal":   return "blue";
    case "high":     return "amber";
    case "critical": return "red";
  }
}

function NewTemplateDialog({
  open,
  onClose,
  orgId,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
}) {
  const router = useRouter();
  const groups = useTemplateGroups(orgId);
  const create = useCreateTemplate(orgId);
  const [form, setForm] = useState({ key: "", group_id: "", subject: "", priority_id: 2 });
  const [err, setErr] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    if (!form.key || !form.group_id || !form.subject) {
      setErr("All fields are required.");
      return;
    }
    create.mutate(
      { org_id: orgId, key: form.key, group_id: form.group_id, subject: form.subject, priority_id: form.priority_id },
      {
        onSuccess: (t) => { onClose(); router.push(`/notify/templates/${t.id}`); },
        onError: (e) => setErr(e.message),
      },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="New Template" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field label="Key" htmlFor="tmpl-key">
          <Input
            id="tmpl-key"
            data-testid="input-template-key"
            placeholder="e.g. welcome-email"
            value={form.key}
            onChange={(e) => setForm((f) => ({ ...f, key: e.target.value }))}
          />
        </Field>
        <Field label="Group" htmlFor="tmpl-group">
          <Select
            id="tmpl-group"
            data-testid="select-template-group"
            value={form.group_id}
            onChange={(e) => setForm((f) => ({ ...f, group_id: e.target.value }))}
          >
            <option value="">Select a group…</option>
            {(groups.data?.items ?? []).map((g) => (
              <option key={g.id} value={g.id}>
                {g.label} ({g.category_code})
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Subject" htmlFor="tmpl-subject">
          <Input
            id="tmpl-subject"
            data-testid="input-template-subject"
            placeholder="Email subject line"
            value={form.subject}
            onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
          />
        </Field>
        <Field label="Priority" htmlFor="tmpl-priority">
          <Select
            id="tmpl-priority"
            value={form.priority_id}
            onChange={(e) => setForm((f) => ({ ...f, priority_id: Number(e.target.value) }))}
          >
            {PRIORITY_OPTIONS.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </Select>
        </Field>
        {err && <p className="text-xs text-red-500">{err}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" data-testid="btn-create-template" disabled={create.isPending}>
            {create.isPending ? "Creating…" : "Create template"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function TemplatesPage() {
  const router = useRouter();
  const me = useMe();
  const orgId = me.data?.session?.org_id ?? null;
  const { data, isLoading, isError, error, refetch } = useTemplates(orgId);
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <>
      <PageHeader
        title="Templates"
        description="Email and notification templates. Each template belongs to a group with its own SMTP config."
        testId="heading-notify-templates"
        actions={
          <Button data-testid="btn-new-template" onClick={() => setDialogOpen(true)}>
            + New template
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="notify-templates-body">
        {isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
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
            title="No templates yet"
            description="Create a template to start sending notifications."
          />
        )}
        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Key</TH>
                <TH>Group</TH>
                <TH>Subject</TH>
                <TH>Priority</TH>
                <TH>Status</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((t: NotifyTemplate) => (
                <TR
                  key={t.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/notify/templates/${t.id}`)}
                  data-testid={`template-row-${t.id}`}
                >
                  <TD><span className="font-mono text-sm">{t.key}</span></TD>
                  <TD><span className="text-sm text-zinc-600 dark:text-zinc-400">{t.group_key}</span></TD>
                  <TD><span className="text-sm">{t.subject}</span></TD>
                  <TD>
                    <Badge tone={priorityTone(t.priority_code as NotifyPriorityCode)}>
                      {t.priority_label}
                    </Badge>
                  </TD>
                  <TD>
                    <Badge tone={t.is_active ? "emerald" : "zinc"}>
                      {t.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      {orgId && (
        <NewTemplateDialog open={dialogOpen} onClose={() => setDialogOpen(false)} orgId={orgId} />
      )}
    </>
  );
}
