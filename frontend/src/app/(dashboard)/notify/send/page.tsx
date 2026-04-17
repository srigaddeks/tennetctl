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
        description="Send a notification directly — bypasses the audit-event subscription flow. Use for magic links, OTP codes, password reset, and other on-demand sends."
        testId="heading-notify-send"
      />

      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="notify-send-body">
        <div className="grid max-w-4xl grid-cols-1 gap-8 lg:grid-cols-2">
          {/* Test form */}
          <div>
            <h2 className="mb-4 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
              Send a test delivery
            </h2>
            <form onSubmit={handleSend} className="flex flex-col gap-4">
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
              <Field label="Deep link (optional)" htmlFor="send-deep-link" hint="Where the notification click navigates. Must start with /">
                <Input
                  id="send-deep-link"
                  data-testid="input-send-deep-link"
                  placeholder="/audit"
                  value={form.deep_link}
                  onChange={(e) => setForm((f) => ({ ...f, deep_link: e.target.value }))}
                />
              </Field>
              <Field label="Schedule for (optional)" htmlFor="send-send-at" hint="Leave empty to send immediately">
                <Input
                  id="send-send-at"
                  data-testid="input-send-send-at"
                  type="datetime-local"
                  value={form.send_at}
                  onChange={(e) => setForm((f) => ({ ...f, send_at: e.target.value }))}
                />
              </Field>
              {err && <p className="text-xs text-red-500" data-testid="send-error">{err}</p>}
              {result && (
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-800 dark:bg-emerald-950">
                  <p className="text-xs text-emerald-700 dark:text-emerald-300">
                    Delivery queued:
                    <code className="ml-1 font-mono">{result.delivery_id}</code>
                  </p>
                </div>
              )}
              <div className="flex justify-end">
                <Button
                  type="submit"
                  data-testid="btn-send"
                  disabled={loading || !form.template_key || !form.recipient_user_id || !orgId}
                >
                  {loading ? "Sending…" : "Send"}
                </Button>
              </div>
            </form>
          </div>

          {/* API reference */}
          <div>
            <h2 className="mb-4 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
              API reference
            </h2>
            <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 font-mono text-xs dark:border-zinc-800 dark:bg-zinc-900">
              <div className="mb-2 flex items-center gap-2">
                <Badge tone="emerald">POST</Badge>
                <span className="text-zinc-600 dark:text-zinc-400">/v1/notify/send</span>
              </div>
              <pre className="text-zinc-700 dark:text-zinc-300">{`{
  "org_id": "string",
  "template_key": "string",
  "recipient_user_id": "string",
  "channel_code": "email|webpush|in_app",
  "variables": {
    "key": "value"  // optional overrides
  }
}`}</pre>
              <div className="mt-3 border-t border-zinc-200 pt-3 dark:border-zinc-700">
                <p className="mb-1 text-zinc-500">Response (201):</p>
                <pre className="text-zinc-700 dark:text-zinc-300">{`{
  "ok": true,
  "data": {
    "delivery_id": "uuid-v7"
  }
}`}</pre>
              </div>
              <div className="mt-3 border-t border-zinc-200 pt-3 dark:border-zinc-700">
                <p className="text-zinc-500">
                  Delivery is picked up by the worker and sent via the
                  template&#39;s SMTP config (email) or VAPID key (web push).
                  Use <code>GET /v1/notify/deliveries?recipient_user_id=X</code> to
                  track status.
                </p>
              </div>
            </div>

            <div className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900">
              <p className="mb-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                Node: <code>notify.send.transactional</code>
              </p>
              <pre className="text-xs text-zinc-700 dark:text-zinc-300">{`await run_node(pool, "notify.send.transactional", ctx, {
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
    </>
  );
}
