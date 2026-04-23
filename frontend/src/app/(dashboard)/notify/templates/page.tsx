"use client";

import Link from "next/link";
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

function priorityTone(code: NotifyPriorityCode): "default" | "blue" | "amber" | "red" {
  switch (code) {
    case "low":      return "default";
    case "normal":   return "blue";
    case "high":     return "amber";
    case "critical": return "red";
  }
}

function channelIcon(groupKey: string | undefined): React.ReactNode {
  if (!groupKey) return null;
  const k = groupKey.toLowerCase();
  if (k.includes("email")) {
    return (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <rect x="1" y="3" width="12" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2"/>
        <path d="M1 4.5l6 4 6-4" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
      </svg>
    );
  }
  if (k.includes("push") || k.includes("webpush")) {
    return (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M7 1C4.24 1 2 3.24 2 6v3l-1 1.5h12L12 9V6c0-2.76-2.24-5-5-5z" stroke="currentColor" strokeWidth="1.2"/>
        <path d="M5.5 10.5a1.5 1.5 0 003 0" stroke="currentColor" strokeWidth="1.2"/>
      </svg>
    );
  }
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M4.5 7h5M7 4.5v5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}

function TemplateCard({ t, onClick }: { t: NotifyTemplate; onClick: () => void }) {
  const isActive = t.is_active;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === "Enter") onClick(); }}
      data-testid={`template-row-${t.id}`}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        padding: "16px 20px",
        borderRadius: 8,
        border: "1px solid var(--border)",
        background: "var(--bg-surface)",
        cursor: "pointer",
        transition: "border-color 0.15s, background 0.15s",
        outline: "none",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-bright)";
        (e.currentTarget as HTMLDivElement).style.background = "var(--bg-elevated)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)";
        (e.currentTarget as HTMLDivElement).style.background = "var(--bg-surface)";
      }}
    >
      {/* Top row */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
          <span
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 28,
              height: 28,
              borderRadius: 6,
              background: "var(--accent-muted)",
              color: "var(--accent)",
              flexShrink: 0,
            }}
          >
            {channelIcon(t.group_key)}
          </span>
          <span
            style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 13,
              fontWeight: 600,
              color: "var(--text-primary)",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {t.key}
          </span>
        </div>
        <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
          <Badge tone={isActive ? "emerald" : "default"} dot={isActive}>
            {isActive ? "Active" : "Inactive"}
          </Badge>
          <Badge tone={priorityTone(t.priority_code as NotifyPriorityCode)}>
            {t.priority_label}
          </Badge>
        </div>
      </div>

      {/* Subject preview */}
      {t.subject && (
        <p
          style={{
            fontSize: 13,
            color: "var(--text-secondary)",
            margin: 0,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {t.subject}
        </p>
      )}

      {/* Footer */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderTop: "1px solid var(--border)",
          paddingTop: 10,
          marginTop: 4,
        }}
      >
        <span
          style={{
            fontSize: 11,
            color: "var(--text-muted)",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          {t.group_key ?? "—"}
        </span>
        <span
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            fontSize: 11,
            color: "var(--info)",
          }}
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M1 5h8M5 1v8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
          Edit template
        </span>
      </div>
    </div>
  );
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
          {(groups.data?.items ?? []).length === 0 && !groups.isLoading && (
            <p className="mt-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
              No groups yet.{" "}
              <Link href="/notify/settings" style={{ color: "var(--accent)", textDecoration: "underline" }}>
                Create one in Settings →
              </Link>
            </p>
          )}
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
        {err && <p className="text-xs" style={{ color: "var(--danger)" }}>{err}</p>}
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

  const active = data?.items.filter((t) => t.is_active).length ?? 0;
  const total = data?.items.length ?? 0;

  return (
    <>
      <PageHeader
        title="Templates"
        description="Precision-crafted notification templates. Each template belongs to a group with its own delivery config."
        testId="heading-notify-templates"
        actions={
          <Button data-testid="btn-new-template" onClick={() => setDialogOpen(true)}>
            + New template
          </Button>
        }
      />

      <div
        className="flex-1 overflow-y-auto"
        style={{ padding: "24px 32px" }}
        data-testid="notify-templates-body"
      >
        {/* Summary bar */}
        {data && data.items.length > 0 && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 24,
              padding: "10px 16px",
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--bg-surface)",
              marginBottom: 20,
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
              <span
                style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 20,
                  fontWeight: 700,
                  color: "var(--info)",
                }}
              >
                {total}
              </span>
              <span style={{ fontSize: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                Total
              </span>
            </div>
            <div
              style={{
                width: 1,
                height: 24,
                background: "var(--border)",
              }}
            />
            <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
              <span
                style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 20,
                  fontWeight: 700,
                  color: "var(--success)",
                }}
              >
                {active}
              </span>
              <span style={{ fontSize: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                Active
              </span>
            </div>
            <div
              style={{
                width: 1,
                height: 24,
                background: "var(--border)",
              }}
            />
            <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
              <span
                style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 20,
                  fontWeight: 700,
                  color: "var(--text-secondary)",
                }}
              >
                {total - active}
              </span>
              <span style={{ fontSize: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                Inactive
              </span>
            </div>
          </div>
        )}

        {isLoading && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: 16,
            }}
          >
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
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
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: 16,
            }}
          >
            {data.items.map((t: NotifyTemplate) => (
              <TemplateCard
                key={t.id}
                t={t}
                onClick={() => router.push(`/notify/templates/${t.id}`)}
              />
            ))}
          </div>
        )}
      </div>

      {orgId && (
        <NewTemplateDialog open={dialogOpen} onClose={() => setDialogOpen(false)} orgId={orgId} />
      )}
    </>
  );
}
