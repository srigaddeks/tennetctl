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
import { useTemplateGroups, usePatchTemplate, useTemplate, useTestSend, useUpsertBodies } from "@/features/notify/hooks/use-templates";
import { useCreateTemplateVariable, useResolveVariables, useTemplateVariables } from "@/features/notify/hooks/use-template-variables";
import type { NotifyTemplateVariable, NotifyVarType } from "@/types/api";

const PRIORITY_OPTIONS: Array<{ id: number; label: string }> = [
  { id: 1, label: "Low" },
  { id: 2, label: "Normal" },
  { id: 3, label: "High" },
  { id: 4, label: "Critical" },
];

function varTypeTone(t: NotifyVarType): "zinc" | "blue" {
  return t === "static" ? "zinc" : "blue";
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
    <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-3 rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-900">
      <Field label="Name" htmlFor="var-name">
        <Input
          id="var-name"
          data-testid="input-var-name"
          placeholder="e.g. user_name"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
        />
      </Field>
      <div className="flex gap-3">
        <label className="flex items-center gap-1.5 text-sm cursor-pointer">
          <input
            type="radio"
            data-testid="radio-var-type-static"
            checked={form.var_type === "static"}
            onChange={() => setForm((f) => ({ ...f, var_type: "static" }))}
          />
          Static
        </label>
        <label className="flex items-center gap-1.5 text-sm cursor-pointer">
          <input
            type="radio"
            data-testid="radio-var-type-dynamic"
            checked={form.var_type === "dynamic_sql"}
            onChange={() => setForm((f) => ({ ...f, var_type: "dynamic_sql" }))}
          />
          Dynamic SQL
        </label>
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
      {err && <p className="text-xs text-red-500">{err}</p>}
      <div className="flex justify-end gap-2">
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
        {result && <p className="text-xs text-zinc-600 dark:text-zinc-400">{result}</p>}
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

  // Body state — initialized from template on load
  const [bodyHtml, setBodyHtml] = useState("");
  const [bodyText, setBodyText] = useState("");
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const [showVars, setShowVars] = useState(false);
  const [addingVar, setAddingVar] = useState(false);
  const [testSendOpen, setTestSendOpen] = useState(false);

  const htmlRef = useRef<HTMLTextAreaElement>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);
  const activeTextareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (!template) return;
    const email = template.bodies?.find((b) => b.channel_id === 1);
    if (email) {
      setBodyHtml(email.body_html);
      setBodyText(email.body_text ?? "");
    }
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
    upsertBodies.mutate(
      { id, bodies: [{ channel_id: 1, body_html: bodyHtml, body_text: bodyText }] },
      {
        onSuccess: () => toast.toast("Body saved", "success"),
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
    return <div className="p-8 text-zinc-500">Template not found.</div>;
  }

  return (
    <div className="flex h-[calc(100vh-64px)] flex-col" data-testid="designer-page">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-3 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center gap-3">
          <Link href="/notify/templates" className="text-sm text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300">
            ← Templates
          </Link>
          <span className="text-zinc-300 dark:text-zinc-600">/</span>
          <span className="font-mono text-sm font-medium">{template.key}</span>
        </div>
        <div className="flex items-center gap-2">
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
            variant="ghost"
            size="sm"
            data-testid="btn-test-send"
            onClick={() => setTestSendOpen(true)}
          >
            Test send
          </Button>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left — editor */}
        <div className="flex w-[55%] flex-col overflow-y-auto border-r border-zinc-200 dark:border-zinc-800">
          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 border-b border-zinc-200 p-5 dark:border-zinc-800">
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

          {/* Email body tabs (only email shown; others disabled) */}
          <div className="flex border-b border-zinc-200 dark:border-zinc-800">
            <button
              type="button"
              className="border-b-2 border-zinc-900 px-5 py-2 text-sm font-medium dark:border-zinc-50"
            >
              Email
            </button>
            <button
              type="button"
              disabled
              title="Coming soon"
              className="cursor-not-allowed px-5 py-2 text-sm text-zinc-400"
            >
              Web Push
            </button>
            <button
              type="button"
              disabled
              title="Coming soon"
              className="cursor-not-allowed px-5 py-2 text-sm text-zinc-400"
            >
              In-app
            </button>
          </div>

          <div className="flex flex-1 flex-col gap-3 p-5">
            <div>
              <label className="mb-1 block text-xs font-medium text-zinc-500">HTML body</label>
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
            <div>
              <label className="mb-1 block text-xs font-medium text-zinc-500">Plain text</label>
              <Textarea
                ref={textRef}
                data-testid="textarea-body-text"
                rows={4}
                placeholder="Plain-text fallback"
                value={bodyText}
                onChange={(e) => setBodyText(e.target.value)}
                onFocus={() => { activeTextareaRef.current = textRef.current; }}
              />
            </div>
            <div className="flex justify-end">
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
        <div className="flex w-[45%] flex-col overflow-y-auto">
          {/* Preview pane */}
          <div className="flex-1 p-5">
            <p className="mb-2 text-xs font-medium text-zinc-500">Preview</p>
            {previewHtml ? (
              <div
                data-testid="preview-pane"
                className="min-h-[200px] rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900"
                // DOMPurify not available server-side; rendered HTML is from our own DB + Jinja substitution
                // eslint-disable-next-line react/no-danger
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />
            ) : (
              <div
                data-testid="preview-pane"
                className="flex min-h-[200px] items-center justify-center rounded-lg border border-dashed border-zinc-200 dark:border-zinc-700"
              >
                <p className="text-sm text-zinc-400">Click &quot;Preview&quot; to render</p>
              </div>
            )}
          </div>

          {/* Variable panel */}
          {showVars && (
            <div className="border-t border-zinc-200 p-5 dark:border-zinc-800">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-xs font-medium text-zinc-500">Variables — click to insert at cursor</p>
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

              <div className="mt-2 flex flex-col gap-1.5">
                {(vars.data?.items ?? []).map((v: NotifyTemplateVariable) => (
                  <button
                    key={v.id}
                    type="button"
                    data-testid={`var-pill-${v.name}`}
                    className="flex items-center gap-2 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-left hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:bg-zinc-800"
                    onClick={() => insertVariable(v.name)}
                  >
                    <code className="text-xs font-mono text-zinc-800 dark:text-zinc-200">
                      {`{{ ${v.name} }}`}
                    </code>
                    <Badge tone={varTypeTone(v.var_type)} >
                      {v.var_type === "static" ? "static" : "SQL"}
                    </Badge>
                    {v.description && (
                      <span className="ml-auto text-xs text-zinc-400">{v.description}</span>
                    )}
                  </button>
                ))}
                {vars.data?.items.length === 0 && (
                  <p className="text-xs text-zinc-400">No variables registered for this template.</p>
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
