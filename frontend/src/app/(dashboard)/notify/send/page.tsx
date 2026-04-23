"use client";

import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import { Badge, Button, Field, Input, Select } from "@/components/ui";
import { useMe } from "@/features/auth/hooks/use-auth";
import { apiFetch } from "@/lib/api";
import type { NotifyChannelCode } from "@/types/api";

const CHANNEL_OPTIONS: Array<{ code: NotifyChannelCode; label: string }> = [
  { code: "email",   label: "Email" },
  { code: "webpush", label: "Web Push" },
  { code: "in_app",  label: "In-app" },
];

export default function TransactionalSendPage() {
  const me = useMe();
  const orgId = me.data?.session?.org_id ?? null;
  const toast = useToast();

  const [form, setForm] = useState({
    template_key: "",
    recipient_user_id: "",
    channel_code: "email" as NotifyChannelCode,
    deep_link: "",
    send_at: "",
  });
  const [result, setResult] = useState<{ delivery_id: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const preview = form.template_key && form.recipient_user_id;

  async function handleSend(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!orgId) return;
    setErr(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await apiFetch<{ delivery_id: string }>("/v1/notify/send", {
        method: "POST",
        body: JSON.stringify({
          org_id: orgId,
          template_key: form.template_key,
          recipient_user_id: form.recipient_user_id,
          channel_code: form.channel_code,
          variables: {},
          deep_link: form.deep_link || undefined,
          send_at: form.send_at ? new Date(form.send_at).toISOString() : undefined,
        }),
      });
      setResult(data);
      toast.toast(`Delivery created: ${data.delivery_id}`, "success");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Send failed";
      setErr(msg);
      toast.toast(msg, "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Transactional Send"
        description="Direct notification dispatch — bypasses the audit-event subscription flow. For magic links, OTP codes, password resets, and on-demand sends."
        testId="heading-notify-send"
      />

      <div
        className="flex-1 overflow-y-auto"
        style={{ padding: "24px 32px" }}
        data-testid="notify-send-body"
      >
        {/* Split panel */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 32,
            maxWidth: 960,
          }}
        >
          {/* Left — form */}
          <div
            style={{
              padding: 24,
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--bg-surface)",
              display: "flex",
              flexDirection: "column",
              gap: 20,
            }}
          >
            <div>
              <h2
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "var(--info)",
                  marginBottom: 4,
                }}
              >
                Compose
              </h2>
              <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                Fill in the template key and recipient to dispatch immediately or schedule for later.
              </p>
            </div>

            <form
              onSubmit={handleSend}
              style={{ display: "flex", flexDirection: "column", gap: 16 }}
            >
              <Field label="Template key" htmlFor="send-template-key">
                <Input
                  id="send-template-key"
                  data-testid="input-send-template-key"
                  placeholder="e.g. welcome-email"
                  value={form.template_key}
                  onChange={(e) => setForm((f) => ({ ...f, template_key: e.target.value }))}
                />
              </Field>
              <Field
                label="Recipient user ID or email"
                htmlFor="send-recipient"
                hint="User ID or direct email address"
              >
                <Input
                  id="send-recipient"
                  data-testid="input-send-recipient"
                  placeholder="user-uuid or user@example.com"
                  value={form.recipient_user_id}
                  onChange={(e) => setForm((f) => ({ ...f, recipient_user_id: e.target.value }))}
                />
              </Field>
              <Field label="Channel" htmlFor="send-channel">
                <Select
                  id="send-channel"
                  data-testid="select-send-channel"
                  value={form.channel_code}
                  onChange={(e) => setForm((f) => ({ ...f, channel_code: e.target.value as NotifyChannelCode }))}
                >
                  {CHANNEL_OPTIONS.map((c) => (
                    <option key={c.code} value={c.code}>{c.label}</option>
                  ))}
                </Select>
              </Field>
              <Field
                label="Deep link (optional)"
                htmlFor="send-deep-link"
                hint="Where the notification click navigates. Must start with /"
              >
                <Input
                  id="send-deep-link"
                  data-testid="input-send-deep-link"
                  placeholder="/audit"
                  value={form.deep_link}
                  onChange={(e) => setForm((f) => ({ ...f, deep_link: e.target.value }))}
                />
              </Field>
              <Field
                label="Schedule for (optional)"
                htmlFor="send-send-at"
                hint="Leave empty to send immediately"
              >
                <Input
                  id="send-send-at"
                  data-testid="input-send-send-at"
                  type="datetime-local"
                  value={form.send_at}
                  onChange={(e) => setForm((f) => ({ ...f, send_at: e.target.value }))}
                />
              </Field>

              {err && (
                <div
                  style={{
                    padding: "8px 12px",
                    borderRadius: 6,
                    border: "1px solid var(--danger)",
                    background: "var(--danger-muted)",
                    fontSize: 12,
                    color: "var(--danger)",
                  }}
                  data-testid="send-error"
                >
                  {err}
                </div>
              )}

              {result && (
                <div
                  style={{
                    padding: "10px 14px",
                    borderRadius: 6,
                    border: "1px solid var(--success)",
                    background: "var(--success-muted)",
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                  }}
                >
                  <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--success)" }}>
                    Delivery queued
                  </span>
                  <code
                    style={{
                      fontFamily: "'IBM Plex Mono', monospace",
                      fontSize: 12,
                      color: "var(--success)",
                    }}
                  >
                    {result.delivery_id}
                  </code>
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <Button
                  type="submit"
                  data-testid="btn-send"
                  disabled={loading || !form.template_key || !form.recipient_user_id || !orgId}
                >
                  {loading ? "Sending…" : form.send_at ? "Schedule" : "Send now"}
                </Button>
              </div>
            </form>
          </div>

          {/* Right — preview + reference */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* Live preview */}
            <div
              style={{
                padding: 20,
                borderRadius: 8,
                border: "1px solid var(--border)",
                background: "var(--bg-surface)",
              }}
            >
              <h2
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "var(--text-muted)",
                  marginBottom: 14,
                }}
              >
                Dispatch Preview
              </h2>
              <div
                style={{
                  borderRadius: 6,
                  border: "1px solid var(--border-bright)",
                  background: "var(--bg-elevated)",
                  overflow: "hidden",
                }}
              >
                {[
                  { label: "Template", value: form.template_key || "—" },
                  { label: "Recipient", value: form.recipient_user_id || "—" },
                  { label: "Channel", value: form.channel_code },
                  { label: "Deep link", value: form.deep_link || "none" },
                  { label: "Scheduled", value: form.send_at ? new Date(form.send_at).toLocaleString() : "Immediate" },
                ].map((row, i, arr) => (
                  <div
                    key={row.label}
                    style={{
                      display: "flex",
                      padding: "8px 14px",
                      borderBottom: i < arr.length - 1 ? "1px solid var(--border)" : "none",
                      gap: 12,
                      alignItems: "baseline",
                    }}
                  >
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                        color: "var(--text-muted)",
                        minWidth: 80,
                        flexShrink: 0,
                      }}
                    >
                      {row.label}
                    </span>
                    <span
                      style={{
                        fontFamily: row.label === "Template" || row.label === "Recipient"
                          ? "'IBM Plex Mono', monospace"
                          : undefined,
                        fontSize: 12,
                        color: row.value === "—" || row.value === "none"
                          ? "var(--text-muted)"
                          : "var(--text-primary)",
                      }}
                    >
                      {row.value}
                    </span>
                  </div>
                ))}
              </div>

              {preview && (
                <div
                  style={{
                    marginTop: 12,
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    fontSize: 11,
                    color: "var(--info)",
                  }}
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.2"/>
                    <path d="M6 5v3M6 4h.01" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                  </svg>
                  Ready to dispatch — press Send now or set a schedule.
                </div>
              )}
            </div>

            {/* API reference */}
            <div
              style={{
                padding: 20,
                borderRadius: 8,
                border: "1px solid var(--border)",
                background: "var(--bg-surface)",
              }}
            >
              <h2
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "var(--text-muted)",
                  marginBottom: 14,
                }}
              >
                API Reference
              </h2>
              <div
                style={{
                  borderRadius: 6,
                  border: "1px solid var(--border-bright)",
                  background: "var(--bg-elevated)",
                  padding: "12px 16px",
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 12,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                  <Badge tone="emerald">POST</Badge>
                  <span style={{ color: "var(--info)" }}>/v1/notify/send</span>
                </div>
                <pre style={{ color: "var(--text-secondary)", margin: 0, lineHeight: 1.6 }}>{`{
  "org_id": "string",
  "template_key": "string",
  "recipient_user_id": "string",
  "channel_code": "email|webpush|in_app",
  "variables": {
    "key": "value"  // optional overrides
  }
}`}</pre>
                <div
                  style={{
                    marginTop: 12,
                    paddingTop: 12,
                    borderTop: "1px solid var(--border)",
                  }}
                >
                  <p style={{ color: "var(--text-muted)", marginBottom: 8, fontSize: 11 }}>Response (201):</p>
                  <pre style={{ color: "var(--success)", margin: 0, lineHeight: 1.6 }}>{`{
  "ok": true,
  "data": {
    "delivery_id": "uuid-v7"
  }
}`}</pre>
                </div>
              </div>

              <div
                style={{
                  marginTop: 14,
                  padding: "12px 16px",
                  borderRadius: 6,
                  border: "1px solid var(--border-bright)",
                  background: "var(--bg-elevated)",
                }}
              >
                <p
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    color: "var(--text-muted)",
                    marginBottom: 8,
                  }}
                >
                  Node: <span style={{ color: "var(--info)", fontFamily: "'IBM Plex Mono', monospace", textTransform: "none", letterSpacing: 0 }}>notify.send.transactional</span>
                </p>
                <pre
                  style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontSize: 11,
                    color: "var(--text-secondary)",
                    margin: 0,
                    lineHeight: 1.6,
                    overflow: "auto",
                  }}
                >{`await run_node(pool, "notify.send.transactional", ctx, {
  "org_id": org_id,
  "template_key": "welcome-email",
  "recipient_user_id": user_id,
  "channel_code": "email",
  "variables": {"reset_link": url}
})`}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
