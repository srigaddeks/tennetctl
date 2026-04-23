"use client";

import Link from "next/link";
import { use, useEffect, useRef, useState } from "react";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  Field,
  Input,
  Select,
  Skeleton,
  Textarea,
} from "@/components/ui";
import { useMe } from "@/features/auth/hooks/use-auth";
import { useTemplateAnalytics, useTemplateGroups, usePatchTemplate, useTemplate, useTestSend, useUpsertBodies } from "@/features/notify/hooks/use-templates";
import { useCreateTemplateVariable, useResolveVariables, useTemplateVariables } from "@/features/notify/hooks/use-template-variables";
import type { NotifyTemplateVariable, NotifyVarType } from "@/types/api";

const PRIORITY_OPTIONS: Array<{ id: number; label: string }> = [
  { id: 1, label: "Low" },
  { id: 2, label: "Normal" },
  { id: 3, label: "High" },
  { id: 4, label: "Critical" },
];

function AnalyticsCard({ label, value, tone }: { label: string; value: number; tone?: "red" | "success" }) {
  const valueColor =
    tone === "red"
      ? "var(--danger)"
      : tone === "success"
      ? "var(--success)"
      : "var(--info)";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        padding: "8px 12px",
        borderRadius: 6,
        border: "1px solid var(--border)",
        background: "var(--bg-surface)",
        minWidth: 72,
      }}
      data-testid={`analytics-${label.toLowerCase()}`}
    >
      <div
        style={{
          fontSize: 10,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "var(--text-muted)",
          fontWeight: 600,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: 18,
          fontWeight: 700,
          color: valueColor,
          lineHeight: 1,
        }}
      >
        {value.toLocaleString()}
      </div>
    </div>
  );
}

function varTypeTone(t: NotifyVarType): "default" | "cyan" {
  return t === "static" ? "default" : "cyan";
}

function renderPreview(html: string, resolved: Record<string, string>): string {
  return html.replace(/\{\{\s*(\w+)\s*\}\}/g, (_, name) => resolved[name] ?? `{{${name}}}`);
}

function AddVariableForm({
  templateId,
  onDone,
}: {
  templateId: string;
  onDone: () => void;
}) {
  const create = useCreateTemplateVariable(templateId);
  const [form, setForm] = useState<{
    name: string; var_type: NotifyVarType; static_value: string; sql_template: string; description: string;
  }>({ name: "", var_type: "static", static_value: "", sql_template: "", description: "" });
  const [err, setErr] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    const body =
      form.var_type === "static"
        ? { name: form.name, var_type: "static" as NotifyVarType, static_value: form.static_value, description: form.description || undefined }
        : { name: form.name, var_type: "dynamic_sql" as NotifyVarType, sql_template: form.sql_template, description: form.description || undefined };
    create.mutate(body, {
      onSuccess: () => { setForm({ name: "", var_type: "static", static_value: "", sql_template: "", description: "" }); onDone(); },
      onError: (e) => setErr(e.message),
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        borderRadius: 8,
        border: "1px solid var(--border-bright)",
        background: "var(--bg-elevated)",
        padding: 12,
        marginTop: 8,
      }}
    >
      <Field label="Name" htmlFor="var-name">
        <Input
          id="var-name"
          data-testid="input-var-name"
          placeholder="e.g. user_name"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
        />
      </Field>
      <div style={{ display: "flex", gap: 16 }}>
        {(["static", "dynamic_sql"] as NotifyVarType[]).map((vt) => (
          <label
            key={vt}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 12,
              color: form.var_type === vt ? "var(--text-primary)" : "var(--text-secondary)",
              cursor: "pointer",
            }}
          >
            <input
              type="radio"
              data-testid={`radio-var-type-${vt === "static" ? "static" : "dynamic"}`}
              checked={form.var_type === vt}
              onChange={() => setForm((f) => ({ ...f, var_type: vt }))}
              style={{ accentColor: "var(--accent)" }}
            />
            {vt === "static" ? "Static" : "Dynamic SQL"}
          </label>
        ))}
      </div>
      {form.var_type === "static" ? (
        <Field label="Value" htmlFor="var-static-value">
          <Input
            id="var-static-value"
            data-testid="input-var-static-value"
            placeholder="Literal value"
            value={form.static_value}
            onChange={(e) => setForm((f) => ({ ...f, static_value: e.target.value }))}
          />
        </Field>
      ) : (
        <Field label="SQL Template" htmlFor="var-sql-template">
          <Textarea
            id="var-sql-template"
            data-testid="input-var-sql-template"
            rows={3}
            placeholder="SELECT display_name FROM &quot;03_iam&quot;.v_users WHERE id = $actor_user_id"
            value={form.sql_template}
            onChange={(e) => setForm((f) => ({ ...f, sql_template: e.target.value }))}
          />
        </Field>
      )}
      <Field label="Description (optional)" htmlFor="var-desc">
        <Input
          id="var-desc"
          value={form.description}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
        />
      </Field>
      {err && <p style={{ fontSize: 12, color: "var(--danger)" }}>{err}</p>}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <Button type="button" variant="ghost" size="sm" onClick={onDone}>Cancel</Button>
        <Button type="submit" size="sm" data-testid="btn-submit-variable" disabled={create.isPending}>
          {create.isPending ? "Saving…" : "Add variable"}
        </Button>
      </div>
    </form>
  );
}

function TestSendDialog({
  open,
  onClose,
  templateId,
}: {
  open: boolean;
  onClose: () => void;
  templateId: string;
}) {
  const send = useTestSend();
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [result, setResult] = useState<string | null>(null);

  function handleSend(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    send.mutate(
      { id: templateId, to_email: email },
      {
        onSuccess: (d) => { setResult(`Sent to ${d.sent_to}`); toast.toast(`Sent to ${d.sent_to}`, "success"); },
        onError: (e) => { setResult(e.message); toast.toast(e.message, "error"); },
      },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="Test Send" size="sm">
      <form onSubmit={handleSend} className="flex flex-col gap-4">
        <Field label="Recipient email" htmlFor="test-send-email">
          <Input
            id="test-send-email"
            type="email"
            data-testid="input-test-send-email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        {result && (
          <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>{result}</p>
        )}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Close</Button>
          <Button type="submit" data-testid="btn-send-test" disabled={send.isPending || !email}>
            {send.isPending ? "Sending…" : "Send test"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function TemplateDesignerPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const me = useMe();
  const orgId = me.data?.session?.org_id ?? null;
  const toast = useToast();

  const { data: template, isLoading } = useTemplate(id);
  const groups = useTemplateGroups(orgId);
  const vars = useTemplateVariables(id);
  const patch = usePatchTemplate(orgId);
  const upsertBodies = useUpsertBodies();
  const resolve = useResolveVariables();
  const analytics = useTemplateAnalytics(id);

  const [channelId, setChannelId] = useState<number>(1);

  const [bodiesByChannel, setBodiesByChannel] = useState<
    Record<number, { body_html: string; body_text: string }>
  >({ 1: { body_html: "", body_text: "" }, 2: { body_html: "", body_text: "" }, 3: { body_html: "", body_text: "" } });

  const bodyHtml = bodiesByChannel[channelId]?.body_html ?? "";
  const bodyText = bodiesByChannel[channelId]?.body_text ?? "";
  const setBodyHtml = (v: string) =>
    setBodiesByChannel((m) => ({ ...m, [channelId]: { ...m[channelId], body_html: v } }));
  const setBodyText = (v: string) =>
    setBodiesByChannel((m) => ({ ...m, [channelId]: { ...m[channelId], body_text: v } }));

  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const [showVars, setShowVars] = useState(false);
  const [addingVar, setAddingVar] = useState(false);
  const [testSendOpen, setTestSendOpen] = useState(false);

  const htmlRef = useRef<HTMLTextAreaElement>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);
  const activeTextareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (!template) return;
    const next: Record<number, { body_html: string; body_text: string }> = {
      1: { body_html: "", body_text: "" },
      2: { body_html: "", body_text: "" },
      3: { body_html: "", body_text: "" },
    };
    for (const b of template.bodies ?? []) {
      next[b.channel_id] = { body_html: b.body_html ?? "", body_text: b.body_text ?? "" };
    }
    setBodiesByChannel(next);
  }, [template]);

  function insertVariable(name: string) {
    const ta = activeTextareaRef.current;
    if (!ta) return;
    const token = `{{ ${name} }}`;
    const start = ta.selectionStart ?? ta.value.length;
    const end = ta.selectionEnd ?? ta.value.length;
    const newVal = ta.value.slice(0, start) + token + ta.value.slice(end);
    if (ta === htmlRef.current) setBodyHtml(newVal);
    if (ta === textRef.current) setBodyText(newVal);
    setTimeout(() => {
      ta.setSelectionRange(start + token.length, start + token.length);
      ta.focus();
    }, 0);
  }

  function handleSaveBody() {
    const authored = Object.entries(bodiesByChannel)
      .filter(([, body]) => body.body_html || body.body_text)
      .map(([chId, body]) => ({
        channel_id: Number(chId),
        body_html: body.body_html,
        body_text: body.body_text,
      }));
    upsertBodies.mutate(
      { id, bodies: authored },
      {
        onSuccess: () => toast.toast("Bodies saved", "success"),
        onError: (e) => toast.toast(e.message, "error"),
      },
    );
  }

  function handlePreview() {
    resolve.mutate(
      { templateId: id },
      {
        onSuccess: (resolved) => {
          const rendered = renderPreview(bodyHtml, resolved as Record<string, string>);
          setPreviewHtml(rendered);
        },
        onError: (e) => toast.toast(e.message, "error"),
      },
    );
  }

  function handleMetaBlur(field: string, value: string | number) {
    if (!template) return;
    patch.mutate({ id, patch: { [field]: value } });
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4 p-8">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!template) {
    return (
      <div style={{ padding: 32, color: "var(--text-secondary)" }}>
        Template not found.
      </div>
    );
  }

  const CHANNELS = [
    { id: 1, label: "Email" },
    { id: 2, label: "Web Push" },
    { id: 3, label: "In-app" },
  ];

  return (
    <div
      style={{ display: "flex", height: "calc(100vh - 64px)", flexDirection: "column" }}
      data-testid="designer-page"
    >
      {/* Header bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 24px",
          borderBottom: "1px solid var(--border)",
          background: "var(--bg-surface)",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Link
            href="/notify/templates"
            style={{
              fontSize: 13,
              color: "var(--text-muted)",
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            ← Templates
          </Link>
          <span style={{ color: "var(--border-bright)" }}>/</span>
          <span
            style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 13,
              fontWeight: 600,
              color: "var(--text-primary)",
            }}
          >
            {template.key}
          </span>
          <Badge tone={template.is_active ? "emerald" : "default"} dot={template.is_active}>
            {template.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Button
            variant="ghost"
            size="sm"
            data-testid="btn-toggle-variables"
            onClick={() => setShowVars((v) => !v)}
          >
            {showVars ? "Hide vars" : "Variables"} ({vars.data?.items.length ?? 0})
          </Button>
          <Button
            variant="ghost"
            size="sm"
            data-testid="btn-preview"
            onClick={handlePreview}
            disabled={resolve.isPending}
          >
            {resolve.isPending ? "Resolving…" : "Preview"}
          </Button>
          <Button
            variant="accent"
            size="sm"
            data-testid="btn-test-send"
            onClick={() => setTestSendOpen(true)}
          >
            Test send
          </Button>
        </div>
      </div>

      {/* Analytics summary */}
      {analytics.data && analytics.data.total_deliveries > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: 10,
            padding: "10px 24px",
            borderBottom: "1px solid var(--border)",
            background: "var(--bg-base)",
            flexShrink: 0,
          }}
          data-testid="template-analytics"
        >
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "var(--text-muted)",
              marginRight: 4,
            }}
          >
            Delivery Analytics
          </span>
          <AnalyticsCard label="Total" value={analytics.data.total_deliveries} />
          <AnalyticsCard label="Sent" value={analytics.data.by_status.sent ?? 0} />
          <AnalyticsCard label="Delivered" value={analytics.data.by_status.delivered ?? 0} tone="success" />
          <AnalyticsCard label="Opened" value={(analytics.data.by_status.opened ?? 0) + (analytics.data.by_event_type.open ?? 0)} tone="success" />
          <AnalyticsCard label="Clicked" value={(analytics.data.by_status.clicked ?? 0) + (analytics.data.by_event_type.click ?? 0)} tone="success" />
          <AnalyticsCard label="Bounced" value={analytics.data.by_status.bounced ?? 0} tone="red" />
          <AnalyticsCard label="Failed" value={analytics.data.by_status.failed ?? 0} tone="red" />
        </div>
      )}

      {/* Body */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Left — editor */}
        <div
          style={{
            width: "55%",
            display: "flex",
            flexDirection: "column",
            overflowY: "auto",
            borderRight: "1px solid var(--border)",
          }}
        >
          {/* Metadata */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 16,
              borderBottom: "1px solid var(--border)",
              padding: 20,
            }}
          >
            <Field label="Subject" htmlFor="meta-subject">
              <Input
                id="meta-subject"
                defaultValue={template.subject}
                onBlur={(e) => handleMetaBlur("subject", e.target.value)}
              />
            </Field>
            <Field label="Reply-to" htmlFor="meta-reply-to">
              <Input
                id="meta-reply-to"
                defaultValue={template.reply_to ?? ""}
                onBlur={(e) => handleMetaBlur("reply_to", e.target.value || "")}
              />
            </Field>
            <Field label="Group" htmlFor="meta-group">
              <Select
                id="meta-group"
                defaultValue={template.group_id}
                onBlur={(e) => handleMetaBlur("group_id", e.target.value)}
              >
                {(groups.data?.items ?? []).map((g) => (
                  <option key={g.id} value={g.id}>{g.label}</option>
                ))}
              </Select>
            </Field>
            <Field label="Priority" htmlFor="meta-priority">
              <Select
                id="meta-priority"
                defaultValue={template.priority_id}
                onBlur={(e) => handleMetaBlur("priority_id", Number(e.target.value))}
              >
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </Select>
            </Field>
          </div>

          {/* Channel tabs */}
          <div style={{ display: "flex", borderBottom: "1px solid var(--border)", flexShrink: 0 }}>
            {CHANNELS.map((ch) => (
              <button
                key={ch.id}
                type="button"
                data-testid={`channel-tab-${ch.id}`}
                onClick={() => setChannelId(ch.id)}
                style={{
                  padding: "8px 20px",
                  fontSize: 13,
                  fontWeight: 500,
                  color: channelId === ch.id ? "var(--text-primary)" : "var(--text-muted)",
                  background: "none",
                  border: "none",
                  borderBottom: channelId === ch.id ? "2px solid var(--info)" : "2px solid transparent",
                  cursor: "pointer",
                  transition: "color 0.15s",
                }}
              >
                {ch.label}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", flex: 1, flexDirection: "column", gap: 12, padding: 20 }}>
            {channelId === 1 && (
              <div>
                <label
                  style={{
                    display: "block",
                    marginBottom: 6,
                    fontSize: 11,
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    color: "var(--text-muted)",
                  }}
                >
                  HTML body
                </label>
                <Textarea
                  ref={htmlRef}
                  data-testid="textarea-body-html"
                  rows={12}
                  className="font-mono text-xs"
                  placeholder="<h1>Hello {{ user_name }}</h1>"
                  value={bodyHtml}
                  onChange={(e) => setBodyHtml(e.target.value)}
                  onFocus={() => { activeTextareaRef.current = htmlRef.current; }}
                />
              </div>
            )}
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: 6,
                  fontSize: 11,
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  color: "var(--text-muted)",
                }}
              >
                {channelId === 1 ? "Plain text" : channelId === 2 ? "Push notification body" : "In-app body"}
              </label>
              <Textarea
                ref={textRef}
                data-testid="textarea-body-text"
                rows={channelId === 1 ? 4 : 10}
                placeholder={
                  channelId === 1
                    ? "Plain-text fallback"
                    : channelId === 2
                    ? "Short body shown in the browser push notification"
                    : "Body shown in the notification bell"
                }
                value={bodyText}
                onChange={(e) => setBodyText(e.target.value)}
                onFocus={() => { activeTextareaRef.current = textRef.current; }}
              />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <Button
                data-testid="btn-save-body"
                onClick={handleSaveBody}
                disabled={upsertBodies.isPending}
              >
                {upsertBodies.isPending ? "Saving…" : "Save body"}
              </Button>
            </div>
          </div>
        </div>

        {/* Right — preview + variables */}
        <div
          style={{
            width: "45%",
            display: "flex",
            flexDirection: "column",
            overflowY: "auto",
            background: "var(--bg-base)",
          }}
        >
          {/* Preview pane */}
          <div style={{ flex: 1, padding: 20 }}>
            <p
              style={{
                marginBottom: 10,
                fontSize: 11,
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                color: "var(--text-muted)",
              }}
            >
              Rendered Preview
            </p>
            {previewHtml ? (
              <div
                data-testid="preview-pane"
                style={{
                  minHeight: 200,
                  borderRadius: 8,
                  border: "1px solid var(--border)",
                  background: "#ffffff",
                  padding: 16,
                  color: "#111",
                }}
                // eslint-disable-next-line react/no-danger
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />
            ) : (
              <div
                data-testid="preview-pane"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  minHeight: 200,
                  borderRadius: 8,
                  border: "1px dashed var(--border-bright)",
                  gap: 8,
                }}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M12 5C6.48 5 2 12 2 12s4.48 7 10 7 10-7 10-7S17.52 5 12 5z" stroke="var(--text-muted)" strokeWidth="1.5"/>
                  <circle cx="12" cy="12" r="3" stroke="var(--text-muted)" strokeWidth="1.5"/>
                </svg>
                <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
                  Click &quot;Preview&quot; to render
                </p>
              </div>
            )}
          </div>

          {/* Variable panel */}
          {showVars && (
            <div
              style={{
                borderTop: "1px solid var(--border)",
                padding: 20,
                background: "var(--bg-surface)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                <p
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    color: "var(--text-muted)",
                  }}
                >
                  Variables — click to insert at cursor
                </p>
                <Button
                  size="sm"
                  variant="ghost"
                  data-testid="btn-add-variable"
                  onClick={() => setAddingVar((v) => !v)}
                >
                  {addingVar ? "Cancel" : "+ Add"}
                </Button>
              </div>

              {addingVar && (
                <AddVariableForm templateId={id} onDone={() => setAddingVar(false)} />
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
                {(vars.data?.items ?? []).map((v: NotifyTemplateVariable) => (
                  <button
                    key={v.id}
                    type="button"
                    data-testid={`var-pill-${v.name}`}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      padding: "8px 12px",
                      borderRadius: 6,
                      border: "1px solid var(--border)",
                      background: "var(--bg-elevated)",
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "border-color 0.15s",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--info)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border)";
                    }}
                    onClick={() => insertVariable(v.name)}
                  >
                    <code
                      style={{
                        fontFamily: "'IBM Plex Mono', monospace",
                        fontSize: 12,
                        color: "var(--info)",
                      }}
                    >
                      {`{{ ${v.name} }}`}
                    </code>
                    <Badge tone={varTypeTone(v.var_type)}>
                      {v.var_type === "static" ? "static" : "SQL"}
                    </Badge>
                    {v.description && (
                      <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>
                        {v.description}
                      </span>
                    )}
                  </button>
                ))}
                {vars.data?.items.length === 0 && (
                  <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    No variables registered for this template.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <TestSendDialog
        open={testSendOpen}
        onClose={() => setTestSendOpen(false)}
        templateId={id}
      />
    </div>
  );
}
