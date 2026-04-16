"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Button, Input, Label } from "@kcontrol/ui";
import {
  Bell,
  AlertCircle,
  Loader2,
  Radio,
  FileText,
  Sliders,
  Megaphone,
  Tag,
  Siren,
  Plus,
  CheckCircle2,
  XCircle,
  Lock,
  ChevronDown,
  ChevronUp,
  Send,
  Archive,
  Eye,
  X,
  Save,
  MessageSquare,
  RefreshCw,
  Database,
  Monitor,
  RotateCcw,
  Trash2,
  Clock,
  MousePointer,
  Copy,
  Pencil,
  Zap,
  Search,
} from "lucide-react";
import {
  getNotificationConfig,
  listNotificationTemplates,
  listBroadcasts,
  listReleases,
  listIncidents,
  createTemplate,
  getTemplateDetail,
  updateTemplate,
  createTemplateVersion,
  createBroadcast,
  sendBroadcast,
  createRelease,
  getReleaseDetail,
  updateRelease,
  publishRelease,
  archiveRelease,
  createIncident,
  getIncidentDetail,
  updateIncident,
  postIncidentUpdate,
  previewTemplate,
  getNotificationQueue,
  getSmtpConfig,
  saveSmtpConfig,
  testSmtp,
  sendTestNotification,
  getDeliveryReport,
  getNotificationDetail,
  retryQueueItem,
  deadLetterQueueItem,
  renderRaw,
  listVariableQueries,
  createVariableQuery,
  updateVariableQuery,
  deleteVariableQuery,
  previewVariableQuery,
  testVariableQuery,
  fetchSchemaMetadata,
  fetchAuditEventTypes,
  fetchRecentAuditEvents,
  listVariableKeys,
  createVariableKey,
  updateVariableKey,
  deleteVariableKey,
  listNotificationRules,
  createRule,
  getRuleDetail,
  updateRule,
  setRuleChannel,
  addRuleCondition,
  removeRuleCondition,
} from "@/lib/api/admin";
import SqlEditor, { BindParamToolbar } from "@/components/editors/SqlEditor";
import type {
  NotificationConfigResponse,
  ChannelResponse,
  QueueAdminResponse,
  QueueItemAdminResponse,
  QueueStatsResponse,
  PreviewTemplateResponse,
  CategoryResponse,
  NotificationTypeResponse,
  TemplateResponse,
  TemplateListResponse,
  TemplateDetailResponse,
  TemplateVersionResponse,
  BroadcastResponse,
  BroadcastFullResponse,
  ReleaseResponse,
  ReleaseListResponse,
  ReleaseFullResponse,
  IncidentResponse,
  IncidentListResponse,
  IncidentFullResponse,
  IncidentUpdateResponse,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  CreateTemplateVersionRequest,
  CreateBroadcastRequest,
  CreateReleaseRequest,
  UpdateReleaseRequest,
  CreateIncidentRequest,
  UpdateIncidentRequest,
  CreateIncidentUpdateRequest,
  SmtpConfigRequest,
  SmtpConfigResponse,
  DeliveryReportResponse,
  NotificationDetailResponse,
  DeliveryLogResponse,
  TrackingEventResponse,
  TemplateVariableKeyResponse,
  CreateVariableKeyRequest,
  UpdateVariableKeyRequest,
  VariableQueryResponse,
  VariableQueryListResponse,
  CreateVariableQueryRequest,
  UpdateVariableQueryRequest,
  BindParamDefinition,
  ResultColumnDefinition,
  TestQueryRequest,
  PreviewQueryRequest,
  QueryPreviewResponse,
  TableMetadata,
  AuditEventTypeInfo,
  AuditEventTypesResponse,
  RecentAuditEventResponse,
} from "@/lib/types/admin";

// ── Types ──────────────────────────────────────────────────────────────────

type TabId =
  | "overview"
  | "templates"
  | "variable-queries"
  | "announcements"
  | "queue"
  | "reports"
  | "send-test";

// ── Helpers ────────────────────────────────────────────────────────────────

function priorityClass(priority: string): string {
  switch (priority.toLowerCase()) {
    case "critical":
      return "bg-red-500/10 text-red-500 border-red-500/20";
    case "high":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    case "normal":
      return "bg-blue-500/10 text-blue-500 border-blue-500/20";
    case "low":
      return "bg-muted text-muted-foreground border-border";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function broadcastStatusClass(status: string | undefined | null): string {
  switch ((status ?? "").toLowerCase()) {
    case "sent":
      return "bg-green-500/10 text-green-500 border-green-500/20";
    case "scheduled":
      return "bg-blue-500/10 text-blue-500 border-blue-500/20";
    case "draft":
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function releaseStatusClass(status: string): string {
  switch (status.toLowerCase()) {
    case "published":
      return "bg-green-500/10 text-green-500 border-green-500/20";
    case "draft":
      return "bg-muted text-muted-foreground border-border";
    case "archived":
      return "bg-muted text-muted-foreground border-border";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function incidentSeverityClass(severity: string): string {
  switch (severity.toLowerCase()) {
    case "critical":
      return "bg-red-500/10 text-red-500 border-red-500/20";
    case "high":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    case "medium":
      return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
    case "low":
      return "bg-muted text-muted-foreground border-border";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function incidentStatusClass(status: string): string {
  switch (status.toLowerCase()) {
    case "open":
      return "bg-red-500/10 text-red-500 border-red-500/20";
    case "investigating":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    case "identified":
      return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
    case "monitoring":
      return "bg-blue-500/10 text-blue-500 border-blue-500/20";
    case "resolved":
      return "bg-green-500/10 text-green-500 border-green-500/20";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function channelBadgeClass(channel: string): string {
  switch (channel.toLowerCase()) {
    case "email":
      return "bg-blue-500/10 text-blue-500 border-blue-500/20";
    case "in_app":
      return "bg-purple-500/10 text-purple-500 border-purple-500/20";
    case "sms":
      return "bg-green-500/10 text-green-500 border-green-500/20";
    case "webhook":
      return "bg-orange-500/10 text-orange-500 border-orange-500/20";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function StatusChip({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${active
        ? "bg-green-500/10 text-green-500 border-green-500/20"
        : "bg-muted text-muted-foreground border-border"
        }`}
    >
      {active ? (
        <CheckCircle2 className="h-3 w-3" />
      ) : (
        <XCircle className="h-3 w-3" />
      )}
      {label}
    </span>
  );
}

function InlineBadge({
  label,
  className,
}: {
  label: string;
  className: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${className}`}
    >
      {label}
    </span>
  );
}

// ── Shared form components ──────────────────────────────────────────────────

function FormSelect({
  label,
  value,
  onChange,
  options,
  placeholder,
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs font-medium text-muted-foreground">
        {label}
      </Label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        className="flex h-9 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function FormTextarea({
  label,
  value,
  onChange,
  rows,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs font-medium text-muted-foreground">
        {label}
      </Label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows ?? 3}
        placeholder={placeholder}
        className="flex w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-ring resize-y"
      />
    </div>
  );
}

function FormField({
  label,
  value,
  onChange,
  placeholder,
  required,
  type,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs font-medium text-muted-foreground">
        {label}
      </Label>
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        type={type}
      />
    </div>
  );
}

// ── KeyValueEditor ──────────────────────────────────────────────────────────

function KeyValueEditor({
  label,
  value,
  onChange,
  placeholder,
  suggestions,
}: {
  label: string;
  value: Record<string, string>;
  onChange: (v: Record<string, string>) => void;
  placeholder?: { key?: string; value?: string };
  suggestions?: string[];
}) {
  const entries = Object.entries(value);

  function setKey(idx: number, newKey: string) {
    const next = [...entries];
    const oldKey = next[idx][0];
    const val = next[idx][1];
    next.splice(idx, 1);
    // Re-insert with new key (preserve order)
    const before = next.slice(0, idx);
    const after = next.slice(idx);
    const updated = Object.fromEntries([...before, [newKey, val], ...after]);
    // Remove old key if key changed
    if (oldKey !== newKey) delete updated[oldKey];
    onChange(updated);
  }

  function setValue(idx: number, newVal: string) {
    const next = { ...value };
    next[entries[idx][0]] = newVal;
    onChange(next);
  }

  function removeEntry(idx: number) {
    const next = { ...value };
    delete next[entries[idx][0]];
    onChange(next);
  }

  function addEntry() {
    const next = { ...value };
    let key = "variable.key";
    let i = 1;
    while (key in next) {
      key = `variable.key${i++}`;
    }
    next[key] = "";
    onChange(next);
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-xs font-medium text-muted-foreground">
          {label}
        </Label>
        <button
          type="button"
          onClick={addEntry}
          className="flex items-center gap-1 text-xs text-primary hover:underline"
        >
          <Plus className="h-3 w-3" /> Add Variable
        </button>
      </div>
      {entries.length === 0 ? (
        <p className="text-xs text-muted-foreground italic py-1">
          No static variables defined.
        </p>
      ) : (
        <div className="space-y-2">
          {entries.map(([k, v], idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div className="flex-1 min-w-0">
                {suggestions && suggestions.length > 0 ? (
                  <select
                    value={k}
                    onChange={(e) => setKey(idx, e.target.value)}
                    className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs font-mono text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    {!suggestions.includes(k) && <option value={k}>{k}</option>}
                    {suggestions.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                ) : (
                  <Input
                    value={k}
                    onChange={(e) => setKey(idx, e.target.value)}
                    placeholder={placeholder?.key ?? "variable.key"}
                    className="font-mono text-xs h-8"
                  />
                )}
              </div>
              <div className="flex-[2] min-w-0">
                <Input
                  value={v}
                  onChange={(e) => setValue(idx, e.target.value)}
                  placeholder={placeholder?.value ?? "Static value"}
                  className="text-xs h-8"
                />
              </div>
              <button
                type="button"
                onClick={() => removeEntry(idx)}
                className="shrink-0 text-muted-foreground hover:text-destructive transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
      {suggestions && suggestions.length > 0 && (
        <p className="text-xs text-muted-foreground">
          Keys are variable codes used in your template (e.g.{" "}
          <span className="font-mono">
            &#123;&#123;platform.app_name&#125;&#125;
          </span>
          ). Static values are defaults when dynamic resolution returns nothing.
        </p>
      )}
    </div>
  );
}

function InlineError({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 mt-2">
      <AlertCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
      <p className="text-xs text-red-500">{message}</p>
    </div>
  );
}

// ── Loading / Error / Empty ────────────────────────────────────────────────

function TabSpinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

function TabError({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 mt-4">
      <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
      <p className="text-sm text-red-500">{message}</p>
    </div>
  );
}

function EmptyState({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
        {icon}
      </div>
      <p className="text-sm font-medium text-foreground">{label}</p>
    </div>
  );
}

// ── Tab 1: Overview ────────────────────────────────────────────────────────

function OverviewTab() {
  const [config, setConfig] = useState<NotificationConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getNotificationConfig()
      .then((data) => setConfig(data as NotificationConfigResponse))
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load config")
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <TabSpinner />;
  if (error) return <TabError message={error} />;
  if (!config) return null;

  return (
    <div className="space-y-8 pt-4">
      {/* Channels */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Channels
        </h3>
        {config.channels.length === 0 ? (
          <EmptyState
            icon={<Radio className="h-6 w-6 text-muted-foreground" />}
            label="No channels configured"
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {config.channels.map((ch: ChannelResponse) => (
              <div
                key={ch.id}
                className="flex items-start gap-3 rounded-xl border border-border bg-background p-4"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                  <Radio className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="flex flex-col gap-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-foreground">
                      {ch.name}
                    </span>
                    <InlineBadge
                      label={ch.code}
                      className="bg-muted text-muted-foreground border-border font-mono"
                    />
                  </div>
                  {ch.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {ch.description}
                    </p>
                  )}
                  <div className="mt-1">
                    <StatusChip
                      label={ch.is_available ? "Available" : "Unavailable"}
                      active={ch.is_available}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Categories */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Categories
        </h3>
        {config.categories.length === 0 ? (
          <EmptyState
            icon={<Tag className="h-6 w-6 text-muted-foreground" />}
            label="No categories"
          />
        ) : (
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            {config.categories.map((cat: CategoryResponse, i: number) => (
              <div
                key={cat.id}
                className={`flex items-center justify-between gap-4 px-4 py-3 ${i < config.categories.length - 1
                  ? "border-b border-border"
                  : ""
                  }`}
              >
                <div className="flex flex-col gap-0.5 min-w-0">
                  <span className="text-sm font-medium text-foreground">
                    {cat.name}
                  </span>
                  {cat.description && (
                    <span className="text-xs text-muted-foreground">
                      {cat.description}
                    </span>
                  )}
                </div>
                {cat.is_mandatory && (
                  <span className="flex items-center gap-1 shrink-0 rounded-md border border-amber-500/20 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-500">
                    <Lock className="h-3 w-3" /> Mandatory
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Notification Types */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Notification Types
        </h3>
        {config.types.length === 0 ? (
          <EmptyState
            icon={<Bell className="h-6 w-6 text-muted-foreground" />}
            label="No notification types"
          />
        ) : (
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/30">
                    {[
                      "Name",
                      "Category",
                      "Mandatory",
                      "User-triggered",
                      "Default enabled",
                      "Cooldown",
                    ].map((h) => (
                      <th
                        key={h}
                        className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {config.types.map(
                    (t: NotificationTypeResponse, i: number) => (
                      <tr
                        key={t.id}
                        className={`${i < config.types.length - 1 ? "border-b border-border" : ""} hover:bg-muted/20 transition-colors`}
                      >
                        <td className="px-4 py-3">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-sm font-medium text-foreground">
                              {t.name}
                            </span>
                            <span className="font-mono text-xs text-muted-foreground">
                              {t.code}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-xs text-muted-foreground">
                            {t.category_code}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <StatusChip
                            label={t.is_mandatory ? "Yes" : "No"}
                            active={t.is_mandatory}
                          />
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <StatusChip
                            label={t.is_user_triggered ? "Yes" : "No"}
                            active={t.is_user_triggered}
                          />
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <StatusChip
                            label={t.default_enabled ? "Yes" : "No"}
                            active={t.default_enabled}
                          />
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-xs text-muted-foreground">
                            {t.cooldown_seconds != null
                              ? `${t.cooldown_seconds}s`
                              : "\u2014"}
                          </span>
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* SMTP Config */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          SMTP Configuration
        </h3>
        <SmtpConfigPanel />
      </div>
    </div>
  );
}

// ── SMTP Config Panel (inside Overview) ────────────────────────────────────

function SmtpConfigPanel() {
  const [config, setConfig] = useState<SmtpConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Configure form
  const [showConfigure, setShowConfigure] = useState(false);
  const [cfgHost, setCfgHost] = useState("");
  const [cfgPort, setCfgPort] = useState("465");
  const [cfgUser, setCfgUser] = useState("");
  const [cfgPassword, setCfgPassword] = useState("");
  const [cfgFromEmail, setCfgFromEmail] = useState("");
  const [cfgFromName, setCfgFromName] = useState("Kreesalis Team");
  const [cfgUseTls, setCfgUseTls] = useState(true);
  const [cfgStartTls, setCfgStartTls] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  // Test form
  const [testEmail, setTestEmail] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    detail?: string | null;
  } | null>(null);

  function populateConfigForm(d: SmtpConfigResponse) {
    setCfgHost(d.host ?? "");
    setCfgPort(String(d.port ?? 465));
    setCfgUser(d.username ?? "");
    setCfgFromEmail(d.from_email ?? "");
    setCfgFromName(d.from_name ?? "Kreesalis Team");
    setCfgUseTls(d.use_tls);
    setCfgStartTls(d.start_tls);
  }

  useEffect(() => {
    getSmtpConfig()
      .then((d) => {
        setConfig(d);
        populateConfigForm(d);
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load SMTP config")
      )
      .finally(() => setLoading(false));
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaveResult(null);
    try {
      const payload: SmtpConfigRequest = {
        host: cfgHost,
        port: Number(cfgPort),
        username: cfgUser || null,
        password: cfgPassword || null,
        from_email: cfgFromEmail,
        from_name: cfgFromName,
        use_tls: cfgUseTls,
        start_tls: cfgStartTls,
      };
      const updated = await saveSmtpConfig(payload);
      setConfig(updated);
      populateConfigForm(updated);
      setCfgPassword("");
      setSaveResult({ success: true, message: "SMTP configuration saved." });
      setShowConfigure(false);
    } catch (e) {
      setSaveResult({
        success: false,
        message: e instanceof Error ? e.message : "Save failed",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleTest(e: React.FormEvent) {
    e.preventDefault();
    if (!testEmail) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await testSmtp({ to_email: testEmail });
      setTestResult(res);
    } catch (e) {
      setTestResult({
        success: false,
        message: e instanceof Error ? e.message : "Test failed",
      });
    } finally {
      setTesting(false);
    }
  }

  if (loading)
    return (
      <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading SMTP config…
      </div>
    );

  return (
    <div className="space-y-4">
      {/* Current config display */}
      <div className="rounded-xl border border-border bg-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-foreground">
            Current Configuration
          </h4>
          <div className="flex items-center gap-2">
            {config && (
              <span
                className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${config.is_configured
                  ? "bg-green-500/10 text-green-500 border-green-500/20"
                  : "bg-amber-500/10 text-amber-500 border-amber-500/20"
                  }`}
              >
                {config.is_configured ? (
                  <CheckCircle2 className="h-3 w-3" />
                ) : (
                  <AlertCircle className="h-3 w-3" />
                )}
                {config.is_configured ? "Configured" : "Not configured"}
              </span>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setShowConfigure(!showConfigure);
                setSaveResult(null);
              }}
              className="gap-1.5 h-7 text-xs"
            >
              <Save className="h-3 w-3" />
              {showConfigure ? "Cancel" : "Configure SMTP"}
            </Button>
          </div>
        </div>
        {error && <InlineError message={error} />}
        {saveResult && (
          <div
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 ${saveResult.success ? "border-green-500/30 bg-green-500/10" : "border-red-500/30 bg-red-500/10"}`}
          >
            {saveResult.success ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
            <span
              className={`text-xs font-medium ${saveResult.success ? "text-green-500" : "text-red-500"}`}
            >
              {saveResult.message}
            </span>
          </div>
        )}
        {config && !showConfigure && (
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Host</span>
              <span className="font-mono text-foreground">
                {config.host ?? "—"}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Port</span>
              <span className="font-mono text-foreground">{config.port}</span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Username</span>
              <span className="font-mono text-foreground">
                {config.username ?? "—"}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">From Email</span>
              <span className="font-mono text-foreground">
                {config.from_email ?? "—"}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">From Name</span>
              <span className="text-foreground">{config.from_name}</span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">TLS</span>
              <span className="text-foreground">
                {config.use_tls
                  ? "Implicit TLS (port 465)"
                  : config.start_tls
                    ? "STARTTLS (port 587)"
                    : "None"}
              </span>
            </div>
          </div>
        )}

        {/* Configure form (inline) */}
        {showConfigure && (
          <form onSubmit={handleSave} className="space-y-3 pt-1">
            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="SMTP Host"
                value={cfgHost}
                onChange={setCfgHost}
                placeholder="smtp.gmail.com"
                required
              />
              <FormField
                label="Port"
                value={cfgPort}
                onChange={setCfgPort}
                placeholder="465"
                type="number"
                required
              />
              <FormField
                label="Username"
                value={cfgUser}
                onChange={setCfgUser}
                placeholder="no-reply@yourdomain.com"
              />
              <FormField
                label="Password"
                value={cfgPassword}
                onChange={setCfgPassword}
                placeholder={
                  config?.is_configured
                    ? "Leave blank to keep current"
                    : "App password"
                }
                type="password"
              />
              <FormField
                label="From Email"
                value={cfgFromEmail}
                onChange={setCfgFromEmail}
                placeholder="no-reply@yourdomain.com"
                required
              />
              <FormField
                label="From Name"
                value={cfgFromName}
                onChange={setCfgFromName}
                placeholder="Kreesalis Team"
                required
              />
            </div>
            <div className="flex items-center gap-6 pt-1">
              <div className="flex items-center gap-2">
                <input
                  id="cfg-use-tls"
                  type="checkbox"
                  checked={cfgUseTls}
                  onChange={(e) => {
                    setCfgUseTls(e.target.checked);
                    if (e.target.checked) setCfgStartTls(false);
                  }}
                  className="h-4 w-4 rounded border-border"
                />
                <label
                  htmlFor="cfg-use-tls"
                  className="text-xs text-muted-foreground cursor-pointer select-none"
                >
                  Implicit TLS (port 465)
                </label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  id="cfg-start-tls"
                  type="checkbox"
                  checked={cfgStartTls}
                  onChange={(e) => {
                    setCfgStartTls(e.target.checked);
                    if (e.target.checked) setCfgUseTls(false);
                  }}
                  className="h-4 w-4 rounded border-border"
                />
                <label
                  htmlFor="cfg-start-tls"
                  className="text-xs text-muted-foreground cursor-pointer select-none"
                >
                  STARTTLS (port 587)
                </label>
              </div>
            </div>
            <Button
              type="submit"
              size="sm"
              disabled={saving || !cfgHost || !cfgFromEmail}
              className="gap-1.5"
            >
              {saving ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Save className="h-3.5 w-3.5" />
              )}
              {saving ? "Saving…" : "Save Configuration"}
            </Button>
          </form>
        )}
      </div>

      {/* Test connection form */}
      <div className="rounded-xl border border-border bg-card p-4 space-y-4">
        <h4 className="text-sm font-semibold text-foreground">
          Send Test Email
        </h4>
        <form onSubmit={handleTest} className="space-y-3">
          <FormField
            label="Send test email to"
            value={testEmail}
            onChange={setTestEmail}
            placeholder="sri.gadde@kreesalis.com"
            required
            type="email"
          />
          <Button
            type="submit"
            size="sm"
            disabled={testing || !testEmail || !config?.is_configured}
            className="gap-1.5"
          >
            {testing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
            {testing ? "Sending…" : "Send Test Email"}
          </Button>
          {!config?.is_configured && (
            <p className="text-xs text-amber-500">
              Configure SMTP above before sending a test email.
            </p>
          )}
          {testResult && (
            <div
              className={`flex items-start gap-2 rounded-lg border px-3 py-2 ${testResult.success
                ? "border-green-500/30 bg-green-500/10"
                : "border-red-500/30 bg-red-500/10"
                }`}
            >
              {testResult.success ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500 mt-0.5" />
              ) : (
                <XCircle className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
              )}
              <div className="flex flex-col gap-0.5">
                <span
                  className={`text-sm font-medium ${testResult.success ? "text-green-500" : "text-red-500"}`}
                >
                  {testResult.message}
                </span>
                {testResult.detail && (
                  <span className="text-xs text-muted-foreground font-mono">
                    {testResult.detail}
                  </span>
                )}
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

// ── Tab 2: Templates ───────────────────────────────────────────────────────

function TemplateTriggersPanel({ template }: { template: TemplateResponse }) {
  const [rules, setRules] = useState<any[]>([]);
  const [eventTypes, setEventTypes] = useState<AuditEventTypeInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newRuleEvent, setNewRuleEvent] = useState("");
  const [newRuleRecipient, setNewRuleRecipient] = useState("actor");
  const [saving, setSaving] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [rulesData, typesData] = await Promise.all([
        listNotificationRules(),
        fetchAuditEventTypes(),
      ]);

      const parsedRules = Array.isArray(rulesData)
        ? rulesData
        : (rulesData as any).items || [];
      const relevant = parsedRules.filter(
        (r: any) => r.notification_type_code === template.notification_type_code
      );
      setRules(relevant);
      setEventTypes((typesData as any).event_types || []);
    } catch (err) {
      console.error("Failed to load triggers", err);
    } finally {
      setLoading(false);
    }
  }, [template.notification_type_code]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  async function handleAdd() {
    if (!newRuleEvent) return;
    setSaving(true);
    try {
      const ruleCode =
        `rule_${template.notification_type_code}_${newRuleEvent.replace(/\./g, "_")}_${Date.now()}`
          .toLowerCase()
          .substring(0, 100);
      const res: any = await createRule({
        code: ruleCode,
        name: `Trigger for ${template.name}`,
        source_event_type: newRuleEvent,
        notification_type_code: template.notification_type_code,
        recipient_strategy: newRuleRecipient,
        is_active: true,
      });

      await setRuleChannel(res.id, template.channel_code, {
        template_code: template.code,
        is_active: true,
      });

      setShowAdd(false);
      setNewRuleEvent("");
      void loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to add trigger");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between border-b border-border pb-1">
        <h5 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
          <Zap className="h-3 w-3 text-amber-500" />
          Event Triggers (Rules)
        </h5>
        {!showAdd && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowAdd(true)}
            className="h-6 text-[10px] px-2 gap-1"
          >
            <Zap className="h-3 w-3" /> Add Trigger
          </Button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center p-4">
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="space-y-2">
          {rules.length === 0 && !showAdd ? (
            <p className="text-[11px] text-muted-foreground italic">
              No automatic triggers assigned. This template must be sent
              manually or by code.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {rules.map((r) => (
                <div
                  key={r.id}
                  className="flex items-center justify-between bg-muted/20 border border-border/50 rounded-md px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-foreground bg-muted px-1.5 py-0.5 rounded">
                      {r.source_event_type}
                    </span>
                    <span className="text-[10px] text-muted-foreground">→</span>
                    <span className="text-[10px] text-muted-foreground uppercase">
                      {r.recipient_strategy}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusChip label={r.is_active ? "Active" : "Inactive"} active={!!r.is_active} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {showAdd && (
            <div className="bg-muted/10 border border-border rounded-md p-3 space-y-3 mt-2">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-[10px] uppercase text-muted-foreground">
                    When this happens:
                  </Label>
                  <select
                    className="flex h-8 w-full rounded-md border border-border bg-background px-3 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                    value={newRuleEvent}
                    onChange={(e) => setNewRuleEvent(e.target.value)}
                  >
                    <option value="">Select Audit Event...</option>
                    {eventTypes.map((et) => (
                      <option key={`${et.event_category}.${et.event_type}`} value={et.event_type}>
                        {et.event_category}.{et.event_type}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] uppercase text-muted-foreground">
                    Send to:
                  </Label>
                  <select
                    className="flex h-8 w-full rounded-md border border-border bg-background px-3 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                    value={newRuleRecipient}
                    onChange={(e) => setNewRuleRecipient(e.target.value)}
                  >
                    <option value="actor">
                      Actor (The user who triggered it)
                    </option>
                    <option value="entity_owner">Entity Owner</option>
                    <option value="broadcast">Broadcast (All Users)</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAdd(false)}
                  className="h-7 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={handleAdd}
                  disabled={saving || !newRuleEvent}
                  className="h-7 text-xs bg-primary text-primary-foreground"
                >
                  {saving ? (
                    <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  ) : null}{" "}
                  Create Trigger
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TemplatesTab() {
  const [templates, setTemplates] = useState<TemplateResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<TemplateDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create form
  const [createForm, setCreateForm] = useState<CreateTemplateRequest>({
    code: "",
    name: "",
    description: "",
    notification_type_code: "",
    channel_code: "",
    static_variables: {},
  });
  const [createError, setCreateError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  // Edit form
  const [editForm, setEditForm] = useState<UpdateTemplateRequest>({});
  const [editStaticVars, setEditStaticVars] = useState<Record<string, string>>(
    {}
  );
  const [editError, setEditError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Version form
  const [showVersionForm, setShowVersionForm] = useState(false);
  const [versionForm, setVersionForm] = useState<CreateTemplateVersionRequest>({
    subject_line: "",
    body_html: "",
    body_text: "",
    body_short: "",
    change_notes: "",
  });
  const [versionError, setVersionError] = useState<string | null>(null);
  const [creatingVersion, setCreatingVersion] = useState(false);

  // Variable keys (from config)
  const [variableKeys, setVariableKeys] = useState<TemplateVariableKeyResponse[]>([])

  useEffect(() => {
    getNotificationConfig().then((cfg) => {
      setVariableKeys((cfg as { variable_keys: TemplateVariableKeyResponse[] }).variable_keys ?? [])
    }).catch(() => {/* non-fatal */})
  }, [])

  // Preview state
  const [previewTemplateId, setPreviewTemplateId] = useState<string | null>(
    null
  );
  const [previewVars, setPreviewVars] = useState<Record<string, string>>({});
  const [previewResult, setPreviewResult] =
    useState<PreviewTemplateResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewTab, setPreviewTab] = useState<"html" | "text">("html");

  // Audit Event selection for preview
  const [previewDataSource, setPreviewDataSource] = useState<
    "manual" | "audit"
  >("manual");
  const [recentEvents, setRecentEvents] = useState<RecentAuditEventResponse[]>(
    []
  );
  const [selectedEventId, setSelectedEventId] = useState<string>("");
  const [loadingEvents, setLoadingEvents] = useState(false);

  // Audit event TYPE selection for variable library filtering
  const [allAuditEventTypes, setAllAuditEventTypes] = useState<AuditEventTypeInfo[]>([]);
  const [selectedAuditEventType, setSelectedAuditEventType] = useState<string>("");
  const [varSearch, setVarSearch] = useState<string>("");

  useEffect(() => {
    fetchAuditEventTypes()
      .then((res) => setAllAuditEventTypes((res as AuditEventTypesResponse).event_types ?? []))
      .catch(() => {/* non-fatal */ });
  }, []);

  // Send Test Email
  const [testEmail, setTestEmail] = useState("");
  const [sendingTest, setSendingTest] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    detail?: string | null;
  } | null>(null);

  const ANNOUNCEMENT_TYPE_CODES = ["broadcast", "release", "incident"];

  async function loadRecentEvents() {
    if (recentEvents.length > 0) return;
    setLoadingEvents(true);
    try {
      const res = await fetchRecentAuditEvents();
      setRecentEvents(res.events || []);
    } catch (err) {
      console.error("Failed to load events", err);
    } finally {
      setLoadingEvents(false);
    }
  }

  function handleSelectEvent(eventId: string) {
    setSelectedEventId(eventId);
    const event = recentEvents.find((e) => e.id === eventId);
    if (event) {
      const newVars: Record<string, string> = { ...editStaticVars };
      for (const [k, v] of Object.entries(event.properties || {})) {
        if (
          typeof v === "string" ||
          typeof v === "number" ||
          typeof v === "boolean"
        ) {
          newVars[k] = String(v);
        }
      }
      setPreviewVars(newVars);
      if (expandedId) void handlePreviewWithVars(expandedId, newVars);
    }
  }

  async function handleSendTest() {
    if (!expandedId || !testEmail) return;
    setSendingTest(true);
    setTestResult(null);
    try {
      const template = templates.find((t) => t.id === expandedId);
      if (!template) throw new Error("Template not found");

      const payload = {
        to_email: testEmail,
        notification_type_code: template.notification_type_code,
        channel_code: template.channel_code,
        variables: previewVars,
      };
      const res = await sendTestNotification(payload);
      setTestResult({
        success: true,
        message: `Test sent to ${testEmail}!`,
        detail: res.queue_id || "Queued successfully",
      });
    } catch (err) {
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : "Failed to send test.",
      });
    } finally {
      setSendingTest(false);
    }
  }

  const fetchTemplates = useCallback(() => {
    setLoading(true);
    listNotificationTemplates()
      .then((data) => {
        const list = data as TemplateListResponse;
        const all = list.items ?? [];
        setTemplates(
          all.filter(
            (t) => !ANNOUNCEMENT_TYPE_CODES.includes(t.notification_type_code)
          )
        );
        setError(null);
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load templates")
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      await createTemplate(createForm);
      setShowCreate(false);
      setCreateForm({
        code: "",
        name: "",
        description: "",
        notification_type_code: "",
        channel_code: "",
        static_variables: {},
      });
      fetchTemplates();
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create template"
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleExpand(t: TemplateResponse) {
    if (expandedId === t.id) {
      setExpandedId(null);
      setDetail(null);
      return;
    }
    setExpandedId(t.id);
    setDetailLoading(true);
    setEditError(null);
    setShowVersionForm(false);
    try {
      const d = await getTemplateDetail(t.id);
      setDetail(d);
      setEditForm({ name: d.name, description: d.description });
      setEditStaticVars((t.static_variables as Record<string, string>) ?? {});
    } catch (err) {
      setEditError(
        err instanceof Error ? err.message : "Failed to load template detail"
      );
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleSaveEdit() {
    if (!expandedId) return;
    setSaving(true);
    setEditError(null);
    try {
      await updateTemplate(expandedId, {
        ...editForm,
        static_variables: editStaticVars,
      });
      setExpandedId(null);
      setDetail(null);
      fetchTemplates();
    } catch (err) {
      setEditError(
        err instanceof Error ? err.message : "Failed to update template"
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateVersion() {
    if (!expandedId) return;
    setCreatingVersion(true);
    setVersionError(null);
    try {
      await createTemplateVersion(expandedId, versionForm);
      setShowVersionForm(false);
      setVersionForm({
        subject_line: "",
        body_html: "",
        body_text: "",
        body_short: "",
        change_notes: "",
      });
      const d = await getTemplateDetail(expandedId);
      setDetail(d);
    } catch (err) {
      setVersionError(
        err instanceof Error ? err.message : "Failed to create version"
      );
    } finally {
      setCreatingVersion(false);
    }
  }

  // Extract {{ variable.name }} tokens from active template version
  const detectedVarCodes = useMemo(() => {
    if (!detail) return [];
    const activeVersion = detail.versions?.find(
      (v: TemplateVersionResponse) => v.id === detail.active_version_id
    );
    if (!activeVersion) return [];
    const content = [
      activeVersion.subject_line ?? "",
      activeVersion.body_html ?? "",
      activeVersion.body_text ?? "",
      activeVersion.body_short ?? "",
    ].join(" ");
    const matches = content.matchAll(/\{\{\s*([\w.]+)\s*\}\}/g);
    const codes = new Set<string>();
    for (const m of matches) codes.add(m[1]);
    return Array.from(codes).sort();
  }, [detail]);

  // Build enriched variable info for panel
  const detectedVarInfo = useMemo(() => {
    return detectedVarCodes.map((code) => {
      const known = variableKeys.find((k) => k.code === code);
      return { code, known: !!known, meta: known ?? null };
    });
  }, [detectedVarCodes, variableKeys]);

  function openPreview(templateId: string) {
    // Merge static_variables (as lowest-priority defaults), then preview_defaults, then existing previewVars
    const defaults: Record<string, string> = { ...editStaticVars };
    for (const { code, meta } of detectedVarInfo) {
      defaults[code] =
        previewVars[code] ??
        meta?.preview_default ??
        meta?.example_value ??
        defaults[code] ??
        "";
    }
    setPreviewVars(defaults);
    setPreviewTemplateId(templateId);
    setPreviewResult(null);
    setPreviewError(null);
    void handlePreviewWithVars(templateId, defaults);
  }

  async function handlePreview(templateId: string) {
    setPreviewTemplateId(templateId);
    setPreviewResult(null);
    setPreviewError(null);
    setPreviewLoading(true);
    try {
      const result = await previewTemplate(templateId, previewVars);
      setPreviewResult(result as PreviewTemplateResponse);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handlePreviewWithVars(
    templateId: string,
    vars: Record<string, string>
  ) {
    setPreviewLoading(true);
    try {
      const result = await previewTemplate(templateId, vars);
      setPreviewResult(result as PreviewTemplateResponse);
      setPreviewError(null);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setPreviewLoading(false);
    }
  }

  if (loading) return <TabSpinner />;
  if (error) return <TabError message={error} />;

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-end">
        <Button
          size="sm"
          className="gap-1.5"
          onClick={() => setShowCreate(!showCreate)}
        >
          {showCreate ? (
            <X className="h-3.5 w-3.5" />
          ) : (
            <Plus className="h-3.5 w-3.5" />
          )}
          {showCreate ? "Cancel" : "Create Template"}
        </Button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="rounded-xl border border-border bg-card p-5">
          <form onSubmit={handleCreate} className="space-y-4">
            <h4 className="text-sm font-semibold text-foreground">
              New Template
            </h4>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField label="Code" value={createForm.code} onChange={(v) => setCreateForm((p) => ({ ...p, code: v }))} placeholder="e.g. welcome_email" required />
              <FormField label="Name" value={createForm.name} onChange={(v) => setCreateForm((p) => ({ ...p, name: v }))} placeholder="Welcome Email" required />
              <FormField label="Notification Type Code" value={createForm.notification_type_code} onChange={(v) => setCreateForm((p) => ({ ...p, notification_type_code: v }))} placeholder="e.g. system_alert" required />
              <FormSelect
                label="Channel"
                value={createForm.channel_code}
                onChange={(v) =>
                  setCreateForm((p) => ({ ...p, channel_code: v }))
                }
                options={[
                  { value: "email", label: "Email" },
                  { value: "in_app", label: "In-App" },
                  { value: "sms", label: "SMS" },
                  { value: "webhook", label: "Webhook" },
                ]}
                placeholder="Select channel..."
                required
              />
            </div>
            <FormTextarea
              label="Description"
              value={createForm.description ?? ""}
              onChange={(v) => setCreateForm((p) => ({ ...p, description: v }))}
              rows={2}
              placeholder="Optional description..."
            />
            <KeyValueEditor
              label="Static Variables"
              value={createForm.static_variables ?? {}}
              onChange={(v) =>
                setCreateForm((p) => ({ ...p, static_variables: v }))
              }
              placeholder={{ key: "variable.key", value: "static value" }}
              suggestions={variableKeys.map((k) => k.code)}
            />
            {createError && <InlineError message={createError} />}
            <div className="flex justify-end">
              <Button
                type="submit"
                size="sm"
                disabled={creating}
                className="gap-1.5"
              >
                {creating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Create
              </Button>
            </div>
          </form>
        </div>
      )}

      {templates.length === 0 ? (
        <EmptyState
          icon={<FileText className="h-6 w-6 text-muted-foreground" />}
          label="No templates yet"
        />
      ) : (
        <div className="space-y-3">
          {templates.map((t: TemplateResponse) => {
            const tBorderCls =
              t.channel_code === "email"
                ? "border-l-blue-500"
                : t.channel_code === "in_app"
                  ? "border-l-violet-500"
                  : t.channel_code === "sms"
                    ? "border-l-green-500"
                    : t.channel_code === "webhook"
                      ? "border-l-orange-500"
                      : "border-l-primary";
            return (
              <div
                key={t.id}
                className={`rounded-xl border border-l-[3px] ${tBorderCls} border-border bg-background overflow-hidden`}
              >
                {/* Summary row */}
                <button
                  type="button"
                  onClick={() => handleExpand(t)}
                  className="flex w-full items-center justify-between gap-4 p-4 hover:bg-muted/10 transition-colors text-left"
                >
                  <div className="flex flex-col gap-0.5 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-foreground">
                        {t.name}
                      </span>
                      <span className="font-mono text-xs text-muted-foreground">
                        {t.code}
                      </span>
                    </div>
                    {t.description && (
                      <p className="text-xs text-muted-foreground line-clamp-1">
                        {t.description}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <InlineBadge
                      label={t.channel_code}
                      className={channelBadgeClass(t.channel_code)}
                    />
                    {Object.keys(t.static_variables ?? {}).length > 0 && (
                      <InlineBadge
                        label={`${Object.keys(t.static_variables).length} static var${Object.keys(t.static_variables).length > 1 ? "s" : ""}`}
                        className="border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-700 dark:bg-amber-900/20 dark:text-amber-400"
                      />
                    )}
                    <StatusChip
                      label={t.is_active ? "Active" : "Inactive"}
                      active={t.is_active}
                    />
                    {expandedId === t.id ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                </button>

                {/* Expanded detail */}
                {expandedId === t.id && (
                  <div className="border-t border-border bg-muted/5 p-4 space-y-4">
                    {detailLoading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                      </div>
                    ) : (
                      <>
                        {/* Edit form */}
                        <div className="space-y-3">
                          <h5 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                            Edit Template
                          </h5>
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                            <FormField
                              label="Name"
                              value={editForm.name ?? ""}
                              onChange={(v) =>
                                setEditForm((p) => ({ ...p, name: v }))
                              }
                            />
                            <FormSelect
                              label="Status"
                              value={
                                editForm.is_disabled === true
                                  ? "disabled"
                                  : "active"
                              }
                              onChange={(v) =>
                                setEditForm((p) => ({
                                  ...p,
                                  is_disabled: v === "disabled",
                                }))
                              }
                              options={[
                                { value: "active", label: "Active" },
                                { value: "disabled", label: "Disabled" },
                              ]}
                            />
                          </div>
                          <FormTextarea
                            label="Description"
                            value={editForm.description ?? ""}
                            onChange={(v) =>
                              setEditForm((p) => ({ ...p, description: v }))
                            }
                            rows={2}
                          />
                          <KeyValueEditor
                            label="Static Variables"
                            value={editStaticVars}
                            onChange={setEditStaticVars}
                            placeholder={{
                              key: "variable.key",
                              value: "static value",
                            }}
                            suggestions={variableKeys.map((k) => k.code)}
                          />
                          {editError && <InlineError message={editError} />}
                          <div className="flex items-center gap-2 justify-end">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setExpandedId(null);
                                setDetail(null);
                              }}
                            >
                              Cancel
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              onClick={handleSaveEdit}
                              disabled={saving}
                              className="gap-1.5"
                            >
                              {saving && (
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              )}
                              <Save className="h-3.5 w-3.5" /> Save
                            </Button>
                          </div>
                        </div>

                        {/* Event Triggers (Rules) */}
                        <TemplateTriggersPanel template={t} />

                        {/* Variable Library — Event-Aware */}
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-1">
                            <h5 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
                              <Database className="h-3 w-3" />
                              Available Variables
                            </h5>
                            <div className="flex items-center gap-2 shrink-0">
                              <Label className="text-[10px] uppercase text-muted-foreground whitespace-nowrap">Filter by Event:</Label>
                              <select
                                className="h-7 rounded-md border border-border bg-background px-2 text-[11px] text-foreground focus:outline-none focus:ring-1 focus:ring-ring max-w-[200px]"
                                value={selectedAuditEventType}
                                onChange={(e) => setSelectedAuditEventType(e.target.value)}
                              >
                                <option value="">— All Static Only —</option>
                                {allAuditEventTypes.map((et) => (
                                  <option key={`${et.event_category}.${et.event_type}`} value={et.event_type}>
                                    {et.event_category}.{et.event_type}
                                  </option>
                                ))}
                              </select>
                            </div>
                          </div>

                          {/* Search bar for variables */}
                          <div className="relative">
                            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
                            <input
                              type="text"
                              placeholder="Search variables..."
                              value={varSearch}
                              onChange={(e) => setVarSearch(e.target.value)}
                              className="w-full h-8 rounded-md border border-border bg-background pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                            />
                          </div>

                          {(() => {
                            const selectedEventInfo = allAuditEventTypes.find(et => et.event_type === selectedAuditEventType);
                            const eventProps = new Set(selectedEventInfo?.available_properties ?? []);
                            const searchLower = varSearch.toLowerCase();

                            const filtered = variableKeys.filter((k) => {
                              // Search filter
                              if (searchLower && !k.code.toLowerCase().includes(searchLower) && !k.name.toLowerCase().includes(searchLower)) {
                                return false;
                              }
                              if (k.resolution_source === "static" || k.resolution_source === "platform" || k.resolution_source === "user_property" || k.resolution_source === "computed") {
                                return true;
                              }
                              if (k.resolution_source === "custom_query") {
                                return selectedAuditEventType !== "" && eventProps.size > 0;
                              }
                              return true;
                            });

                            if (filtered.length === 0) return (
                              <p className="text-[11px] text-muted-foreground italic">
                                {varSearch ? "No variables matching your search." : selectedAuditEventType ? "No variables configured for this event type." : "No static variables defined. Select an event above to see dynamic variables."}
                              </p>
                            );

                            const sourceColors: Record<string, string> = {
                              static: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800",
                              platform: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800",
                              user_property: "bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-950/30 dark:text-violet-400 dark:border-violet-800",
                              computed: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800",
                              custom_query: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-800",
                              audit_property: "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/30 dark:text-orange-400 dark:border-orange-800",
                              actor_property: "bg-pink-50 text-pink-700 border-pink-200 dark:bg-pink-950/30 dark:text-pink-400 dark:border-pink-800",
                              org: "bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950/30 dark:text-cyan-400 dark:border-cyan-800",
                              workspace: "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/30 dark:text-teal-400 dark:border-teal-800",
                            };

                            return (
                              <div className="rounded-md border border-border overflow-hidden">
                                <table className="w-full text-xs">
                                  <thead className="sticky top-0 z-10">
                                    <tr className="bg-muted/30 border-b border-border">
                                      <th className="text-left px-3 py-1.5 text-[10px] font-semibold uppercase text-muted-foreground">Variable</th>
                                      <th className="text-left px-3 py-1.5 text-[10px] font-semibold uppercase text-muted-foreground hidden sm:table-cell">Label</th>
                                      <th className="text-left px-3 py-1.5 text-[10px] font-semibold uppercase text-muted-foreground">Type</th>
                                      <th className="text-left px-3 py-1.5 text-[10px] font-semibold uppercase text-muted-foreground hidden md:table-cell">Value / Hint</th>
                                      <th className="px-3 py-1.5 text-[10px] font-semibold uppercase text-muted-foreground text-right"></th>
                                    </tr>
                                  </thead>
                                </table>
                                <div className="max-h-[240px] overflow-y-auto">
                                  <table className="w-full text-xs">
                                    <tbody className="divide-y divide-border/50">
                                      {filtered.map((k) => (
                                        <tr key={k.code} className="hover:bg-muted/10 transition-colors">
                                          <td className="px-3 py-2">
                                            <code className="font-mono text-[11px] text-primary">{`{{ ${k.code} }}`}</code>
                                          </td>
                                          <td className="px-3 py-2 text-muted-foreground hidden sm:table-cell">{k.name}</td>
                                          <td className="px-3 py-2">
                                            <span className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider ${sourceColors[k.resolution_source] ?? "bg-muted text-muted-foreground border-transparent"}`}>
                                              {k.resolution_source === "custom_query" ? "DYNAMIC" : k.resolution_source.replace("_", " ")}
                                            </span>
                                          </td>
                                          <td className="px-3 py-2 text-muted-foreground max-w-[160px] truncate hidden md:table-cell" title={k.static_value ?? k.example_value ?? k.preview_default ?? ""}>
                                            {k.static_value ?? k.example_value ?? k.preview_default ?? <span className="italic opacity-50">—</span>}
                                          </td>
                                          <td className="px-3 py-2 text-right">
                                            <button
                                              type="button"
                                              title="Copy to clipboard"
                                              onClick={() => navigator.clipboard.writeText(`{{ ${k.code} }}`)}
                                              className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                                            >
                                              <Copy className="h-3 w-3" /> Copy
                                            </button>
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                                <div className="bg-muted/20 border-t border-border px-3 py-1 text-[10px] text-muted-foreground">
                                  {filtered.length} variable{filtered.length !== 1 ? "s" : ""}
                                </div>
                              </div>
                            );
                          })()}
                        </div>


                        {/* Versions */}
                        {detail && (
                          <div className="space-y-3">
                            <div className="flex items-center justify-between">
                              <h5 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                                Versions ({detail.versions?.length ?? 0})
                              </h5>
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                className="gap-1.5"
                                onClick={() =>
                                  setShowVersionForm(!showVersionForm)
                                }
                              >
                                {showVersionForm ? (
                                  <X className="h-3 w-3" />
                                ) : (
                                  <Plus className="h-3 w-3" />
                                )}
                                {showVersionForm ? "Cancel" : "New Version"}
                              </Button>
                            </div>

                            {showVersionForm && (
                              <div className="rounded-lg border border-border bg-background p-4 space-y-3">
                                <FormField
                                  label="Subject Line"
                                  value={versionForm.subject_line ?? ""}
                                  onChange={(v) =>
                                    setVersionForm((p) => ({
                                      ...p,
                                      subject_line: v,
                                    }))
                                  }
                                  placeholder="Email subject..."
                                />
                                <FormTextarea
                                  label="Body HTML"
                                  value={versionForm.body_html ?? ""}
                                  onChange={(v) =>
                                    setVersionForm((p) => ({
                                      ...p,
                                      body_html: v,
                                    }))
                                  }
                                  rows={4}
                                  placeholder="<h1>Hello {{name}}</h1>"
                                />
                                <FormTextarea
                                  label="Body Text"
                                  value={versionForm.body_text ?? ""}
                                  onChange={(v) =>
                                    setVersionForm((p) => ({
                                      ...p,
                                      body_text: v,
                                    }))
                                  }
                                  rows={3}
                                  placeholder="Plain text version..."
                                />
                                <FormField
                                  label="Body Short"
                                  value={versionForm.body_short ?? ""}
                                  onChange={(v) =>
                                    setVersionForm((p) => ({
                                      ...p,
                                      body_short: v,
                                    }))
                                  }
                                  placeholder="Short notification text..."
                                />
                                <FormField
                                  label="Change Notes"
                                  value={versionForm.change_notes ?? ""}
                                  onChange={(v) =>
                                    setVersionForm((p) => ({
                                      ...p,
                                      change_notes: v,
                                    }))
                                  }
                                  placeholder="What changed in this version..."
                                />
                                {versionError && (
                                  <InlineError message={versionError} />
                                )}
                                <div className="flex justify-end">
                                  <Button
                                    type="button"
                                    size="sm"
                                    onClick={handleCreateVersion}
                                    disabled={creatingVersion}
                                    className="gap-1.5"
                                  >
                                    {creatingVersion && (
                                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    )}
                                    Create Version
                                  </Button>
                                </div>
                              </div>
                            )}

                            {detail.versions && detail.versions.length > 0 ? (
                              <div className="rounded-lg border border-border bg-background overflow-hidden">
                                {detail.versions.map(
                                  (v: TemplateVersionResponse, i: number) => (
                                    <div
                                      key={v.id}
                                      className={`px-4 py-3 ${i < detail.versions.length - 1 ? "border-b border-border" : ""}`}
                                    >
                                      <div className="flex items-center justify-between gap-3">
                                        <div className="flex items-center gap-2">
                                          <span className="text-sm font-medium text-foreground">
                                            v{v.version_number}
                                          </span>
                                          {v.subject_line && (
                                            <span className="text-xs text-muted-foreground truncate max-w-xs">
                                              {v.subject_line}
                                            </span>
                                          )}
                                        </div>
                                        <div className="flex items-center gap-2 shrink-0">
                                          <StatusChip
                                            label={
                                              v.is_active
                                                ? "Active"
                                                : "Inactive"
                                            }
                                            active={v.is_active}
                                          />
                                          <span className="text-xs text-muted-foreground">
                                            {new Date(
                                              v.created_at
                                            ).toLocaleDateString()}
                                          </span>
                                          {v.is_active && (
                                            <Button
                                              type="button"
                                              variant="outline"
                                              size="sm"
                                              className="h-7 gap-1 text-xs"
                                              onClick={() => {
                                                if (
                                                  previewTemplateId ===
                                                  expandedId
                                                ) {
                                                  setPreviewTemplateId(null);
                                                  setPreviewResult(null);
                                                } else {
                                                  openPreview(expandedId!);
                                                }
                                              }}
                                            >
                                              <Eye className="h-3 w-3" />
                                              {previewTemplateId === expandedId
                                                ? "Close"
                                                : "Preview"}
                                            </Button>
                                          )}
                                        </div>
                                      </div>
                                      {v.change_notes && (
                                        <p className="text-xs text-muted-foreground mt-1">
                                          {v.change_notes}
                                        </p>
                                      )}
                                    </div>
                                  )
                                )}
                              </div>
                            ) : (
                              <p className="text-xs text-muted-foreground italic">
                                No versions yet.
                              </p>
                            )}

                            {/* ── Live HTML Preview Panel ── */}
                            {previewTemplateId === expandedId && (
                              <div className="rounded-lg border border-primary/30 bg-background overflow-hidden">
                                <div className="flex items-center justify-between px-4 py-2 bg-primary/5 border-b border-primary/20">
                                  <div className="flex items-center gap-2">
                                    <Monitor className="h-3.5 w-3.5 text-primary" />
                                    <span className="text-xs font-semibold text-primary">
                                      Live Preview
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <div className="flex rounded-md border border-border overflow-hidden">
                                      <button
                                        type="button"
                                        onClick={() => setPreviewTab("html")}
                                        className={`px-3 py-1 text-xs font-medium transition-colors ${previewTab === "html" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:text-foreground"}`}
                                      >
                                        HTML
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => setPreviewTab("text")}
                                        className={`px-3 py-1 text-xs font-medium transition-colors ${previewTab === "text" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:text-foreground"}`}
                                      >
                                        Text
                                      </button>
                                    </div>
                                    <Button
                                      type="button"
                                      variant="outline"
                                      size="sm"
                                      className="h-7 gap-1 text-xs"
                                      onClick={() => handlePreview(expandedId!)}
                                      disabled={previewLoading}
                                    >
                                      {previewLoading ? (
                                        <Loader2 className="h-3 w-3 animate-spin" />
                                      ) : (
                                        <RefreshCw className="h-3 w-3" />
                                      )}
                                      Refresh
                                    </Button>
                                  </div>
                                </div>

                                {/* Smart Variable Panel */}
                                {detectedVarInfo.length > 0 && (
                                  <div className="border-b border-border bg-muted/10">
                                    <div className="px-4 py-2 flex items-center flex-wrap gap-4 justify-between border-b border-border/50">
                                      <div className="flex items-center gap-2">
                                        <Tag className="h-3.5 w-3.5 text-muted-foreground" />
                                        <span className="text-xs font-semibold text-foreground">
                                          Preview Variables
                                        </span>
                                      </div>
                                      <div className="flex rounded-md border border-border overflow-hidden shrink-0">
                                        <button
                                          type="button"
                                          onClick={() =>
                                            setPreviewDataSource("manual")
                                          }
                                          className={`px-3 py-1 text-[11px] font-medium transition-colors ${previewDataSource === "manual" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:bg-muted/50 hover:text-foreground"}`}
                                        >
                                          Manual
                                        </button>
                                        <button
                                          type="button"
                                          onClick={() => {
                                            setPreviewDataSource("audit");
                                            void loadRecentEvents();
                                          }}
                                          className={`px-3 py-1 text-[11px] font-medium transition-colors ${previewDataSource === "audit" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:bg-muted/50 hover:text-foreground"}`}
                                        >
                                          Audit Event
                                        </button>
                                      </div>
                                    </div>

                                    {previewDataSource === "audit" ? (
                                      <div className="p-4 space-y-3">
                                        <div className="flex flex-col gap-2">
                                          <Label className="text-xs font-semibold text-muted-foreground">
                                            Select a recent audit event (last
                                            24h) to map data:
                                          </Label>
                                          <div className="flex items-center gap-2">
                                            <select
                                              className="flex h-8 w-full rounded-md border border-border bg-background px-3 py-1 text-xs text-foreground shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                                              value={selectedEventId}
                                              onChange={(e) =>
                                                handleSelectEvent(
                                                  e.target.value
                                                )
                                              }
                                            >
                                              <option value="">
                                                -- Choose Audit Event --
                                              </option>
                                              {recentEvents.map((e) => (
                                                <option key={e.id} value={e.id}>
                                                  {e.event_category}.
                                                  {e.event_type} -{" "}
                                                  {new Date(
                                                    e.occurred_at
                                                  ).toLocaleString()}{" "}
                                                  {e.entity_type
                                                    ? `[${e.entity_type}]`
                                                    : ""}
                                                </option>
                                              ))}
                                            </select>
                                            {loadingEvents && (
                                              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground shrink-0" />
                                            )}
                                          </div>
                                        </div>

                                        <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1">
                                          {detectedVarInfo.map(({ code }) => (
                                            <div
                                              key={code}
                                              className="flex justify-between items-center border-b border-border/40 pb-1"
                                            >
                                              <span className="font-mono text-[10px] text-foreground">
                                                {code}
                                              </span>
                                              <span
                                                className="text-[10px] text-muted-foreground truncate max-w-[120px]"
                                                title={
                                                  previewVars[code] || "(empty)"
                                                }
                                              >
                                                {previewVars[code] || "(empty)"}
                                              </span>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    ) : (
                                      <>
                                        <div className="px-4 py-1.5 flex justify-end">
                                          <button
                                            type="button"
                                            onClick={() => {
                                              const defaults: Record<
                                                string,
                                                string
                                              > = {};
                                              for (const {
                                                code,
                                                meta,
                                              } of detectedVarInfo) {
                                                defaults[code] =
                                                  meta?.preview_default ??
                                                  meta?.example_value ??
                                                  "";
                                              }
                                              setPreviewVars(defaults);
                                              void handlePreviewWithVars(
                                                expandedId!,
                                                defaults
                                              );
                                            }}
                                            className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground hover:text-foreground flex items-center gap-1"
                                          >
                                            <RotateCcw className="h-3 w-3" />
                                            Reset Context
                                          </button>
                                        </div>
                                        <div className="divide-y divide-border/50">
                                          {detectedVarInfo.map(
                                            ({ code, known, meta }) => (
                                              <div
                                                key={code}
                                                className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 px-4 py-2"
                                              >
                                                {/* Left: variable info */}
                                                <div className="flex items-center gap-2 min-w-0">
                                                  <span className="font-mono text-xs text-foreground truncate">{`{{ ${code} }}`}</span>
                                                  {known ? (
                                                    <span
                                                      className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium border ${meta!
                                                        .resolution_source ===
                                                        "static"
                                                        ? "bg-blue-500/10 text-blue-600 border-blue-500/20"
                                                        : meta!
                                                          .resolution_source ===
                                                          "custom_query"
                                                          ? "bg-purple-500/10 text-purple-600 border-purple-500/20"
                                                          : "bg-green-500/10 text-green-600 border-green-500/20"
                                                        }`}
                                                    >
                                                      {meta!
                                                        .resolution_source ===
                                                        "static" &&
                                                        meta!.static_value
                                                        ? `"${meta!.static_value.slice(0, 20)}${meta!.static_value.length > 20 ? "…" : ""}"`
                                                        : meta!
                                                          .resolution_source}
                                                    </span>
                                                  ) : (
                                                    <span
                                                      title="Not in global variable registry. Define it in Variable Queries → Variable Keys."
                                                      className="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium bg-amber-500/10 text-amber-600 border border-amber-500/20 cursor-help"
                                                    >
                                                      not configured
                                                    </span>
                                                  )}
                                                </div>
                                                {/* Middle: description */}
                                                <span className="text-xs text-muted-foreground truncate hidden sm:block">
                                                  {meta?.name ??
                                                    (known
                                                      ? code
                                                      : "→ define in Variable Keys")}
                                                </span>
                                                {/* Right: editable preview value */}
                                                <input
                                                  type="text"
                                                  value={
                                                    previewVars[code] ?? ""
                                                  }
                                                  placeholder={
                                                    meta?.static_value ??
                                                    meta?.preview_default ??
                                                    meta?.example_value ??
                                                    "preview value"
                                                  }
                                                  onChange={(e) =>
                                                    setPreviewVars((prev) => ({
                                                      ...prev,
                                                      [code]: e.target.value,
                                                    }))
                                                  }
                                                  onBlur={() =>
                                                    void handlePreviewWithVars(
                                                      expandedId!,
                                                      {
                                                        ...previewVars,
                                                        [code]:
                                                          previewVars[code] ??
                                                          "",
                                                      }
                                                    )
                                                  }
                                                  className="text-xs rounded-md border border-border bg-background px-2 py-1 outline-none focus:ring-1 focus:ring-ring w-full min-w-0"
                                                />
                                              </div>
                                            )
                                          )}
                                        </div>
                                      </>
                                    )}
                                  </div>
                                )}

                                {/* Preview content */}
                                <div className="p-0">
                                  {previewLoading ? (
                                    <div className="flex items-center justify-center py-12">
                                      <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                                    </div>
                                  ) : previewError ? (
                                    <div className="p-4">
                                      <InlineError message={previewError} />
                                    </div>
                                  ) : previewResult ? (
                                    <>
                                      {previewResult.rendered_subject && (
                                        <div className="px-4 py-2 border-b border-border bg-muted/10">
                                          <span className="text-xs text-muted-foreground">
                                            Subject:{" "}
                                          </span>
                                          <span className="text-xs font-medium text-foreground">
                                            {previewResult.rendered_subject}
                                          </span>
                                        </div>
                                      )}
                                      {previewTab === "html" ? (
                                        previewResult.rendered_body_html ? (
                                          <iframe
                                            srcDoc={
                                              previewResult.rendered_body_html
                                            }
                                            sandbox="allow-same-origin"
                                            className="w-full min-h-96 border-0 bg-white"
                                            title="Email HTML preview"
                                          />
                                        ) : (
                                          <p className="text-xs text-muted-foreground italic p-4">
                                            No HTML body in active version.
                                          </p>
                                        )
                                      ) : (
                                        <pre className="whitespace-pre-wrap text-xs text-foreground font-mono p-4 max-h-96 overflow-auto">
                                          {previewResult.rendered_body_text ||
                                            "(no plain text body)"}
                                        </pre>
                                      )}
                                      {previewResult.rendered_body_short && (
                                        <div className="px-4 py-2 border-t border-border bg-muted/10">
                                          <span className="text-xs text-muted-foreground">
                                            Short:{" "}
                                          </span>
                                          <span className="text-xs text-foreground">
                                            {previewResult.rendered_body_short}
                                          </span>
                                        </div>
                                      )}

                                      {/* Send Test Email Action */}
                                      <div className="border-t border-primary/20 bg-primary/5 p-4 space-y-3">
                                        <div className="flex items-center gap-2 mb-1">
                                          <Send className="h-4 w-4 text-primary" />
                                          <span className="text-xs font-semibold text-primary">
                                            Send Test Notification
                                          </span>
                                        </div>
                                        <div className="flex gap-2 items-center">
                                          <input
                                            type="email"
                                            placeholder="Recipient email address"
                                            value={testEmail}
                                            onChange={(e) =>
                                              setTestEmail(e.target.value)
                                            }
                                            className="flex-1 h-8 rounded-md border border-border bg-background px-3 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                                          />
                                          <Button
                                            type="button"
                                            size="sm"
                                            className="h-8 gap-1.5 bg-primary hover:bg-primary/90 text-primary-foreground"
                                            onClick={handleSendTest}
                                            disabled={sendingTest || !testEmail}
                                          >
                                            {sendingTest ? (
                                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                            ) : (
                                              <Send className="h-3.5 w-3.5" />
                                            )}
                                            Send
                                          </Button>
                                        </div>
                                        {testResult && (
                                          <div
                                            className={`text-xs p-2 rounded-md ${testResult.success ? "bg-green-500/10 text-green-600 border border-green-500/20" : "bg-red-500/10 text-red-600 border border-red-500/20"}`}
                                          >
                                            <p className="font-semibold">
                                              {testResult.message}
                                            </p>
                                            {testResult.detail && (
                                              <p className="font-mono mt-1 opacity-80">
                                                {testResult.detail}
                                              </p>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    </>
                                  ) : (
                                    <div className="flex items-center justify-center py-12">
                                      <p className="text-xs text-muted-foreground">
                                        Click Preview on the active version to
                                        render.
                                      </p>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Shared inline template editor + preview ────────────────────────────────

interface InlineTemplateValue {
  subject_line: string;
  body_html: string;
  body_text: string;
}

const DEFAULT_EMAIL_HTML = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1a1a1a; margin: 0; padding: 0; background: #f4f4f5; }
    .wrapper { max-width: 600px; margin: 32px auto; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e4e4e7; }
    .header { background: #18181b; padding: 24px 32px; }
    .header h1 { color: #ffffff; margin: 0; font-size: 20px; font-weight: 600; }
    .body { padding: 32px; }
    .body p { margin: 0 0 16px; line-height: 1.6; color: #3f3f46; font-size: 14px; }
    .footer { padding: 20px 32px; border-top: 1px solid #e4e4e7; text-align: center; }
    .footer p { margin: 0; font-size: 12px; color: #a1a1aa; }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>{{ title }}</h1>
    </div>
    <div class="body">
      <p>{{ message }}</p>
    </div>
    <div class="footer">
      <p>You received this because you are a member of this platform.</p>
    </div>
  </div>
</body>
</html>`;

function InlineTemplateEditor({
  value,
  onChange,
}: {
  value: InlineTemplateValue;
  onChange: (v: InlineTemplateValue) => void;
}) {
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewTab, setPreviewTab] = useState<"html" | "text">("html");
  const [showPreview, setShowPreview] = useState(false);

  async function handlePreview() {
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const result = await renderRaw({
        subject_line: value.subject_line || null,
        body_html: value.body_html || null,
        body_text: value.body_text || null,
        variables: {},
      });
      setPreviewHtml(result.rendered_body_html ?? null);
      setShowPreview(true);
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Preview failed");
    } finally {
      setPreviewLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      <FormField
        label="Email Subject"
        value={value.subject_line}
        onChange={(v) => onChange({ ...value, subject_line: v })}
        placeholder="Your subject line here..."
      />
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <Label className="text-xs font-medium text-muted-foreground">
            Body HTML
          </Label>
          <button
            type="button"
            onClick={() =>
              onChange({ ...value, body_html: DEFAULT_EMAIL_HTML })
            }
            className="text-xs text-primary hover:underline"
          >
            Use default template
          </button>
        </div>
        <textarea
          value={value.body_html}
          onChange={(e) => onChange({ ...value, body_html: e.target.value })}
          rows={10}
          placeholder={
            "<!DOCTYPE html>\n<html>\n<body>\n  <h1>Hello!</h1>\n</body>\n</html>"
          }
          className="w-full rounded-md border border-border bg-muted/20 px-3 py-2 text-xs font-mono outline-none focus:ring-1 focus:ring-ring resize-y"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label className="text-xs font-medium text-muted-foreground">
          Body Plain Text
        </Label>
        <textarea
          value={value.body_text}
          onChange={(e) => onChange({ ...value, body_text: e.target.value })}
          rows={4}
          placeholder="Plain text version for email clients that don't render HTML..."
          className="w-full rounded-md border border-border bg-muted/20 px-3 py-2 text-xs outline-none focus:ring-1 focus:ring-ring resize-y"
        />
      </div>

      {/* Preview toggle */}
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={handlePreview}
          disabled={previewLoading}
        >
          {previewLoading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Eye className="h-3.5 w-3.5" />
          )}
          {showPreview ? "Refresh Preview" : "Preview"}
        </Button>
        {showPreview && (
          <button
            type="button"
            onClick={() => setShowPreview(false)}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Hide
          </button>
        )}
      </div>

      {previewError && <InlineError message={previewError} />}

      {showPreview && (
        <div className="rounded-lg border border-primary/30 bg-background overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 bg-primary/5 border-b border-primary/20">
            <div className="flex items-center gap-2">
              <Monitor className="h-3.5 w-3.5 text-primary" />
              <span className="text-xs font-semibold text-primary">
                Preview
              </span>
            </div>
            <div className="flex rounded-md border border-border overflow-hidden">
              <button
                type="button"
                onClick={() => setPreviewTab("html")}
                className={`px-3 py-1 text-xs font-medium transition-colors ${previewTab === "html" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:text-foreground"}`}
              >
                HTML
              </button>
              <button
                type="button"
                onClick={() => setPreviewTab("text")}
                className={`px-3 py-1 text-xs font-medium transition-colors ${previewTab === "text" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:text-foreground"}`}
              >
                Text
              </button>
            </div>
          </div>
          {previewTab === "html" ? (
            previewHtml ? (
              <iframe
                srcDoc={previewHtml}
                sandbox="allow-same-origin"
                className="w-full min-h-96 border-0 bg-white"
                title="Email HTML preview"
              />
            ) : (
              <p className="text-xs text-muted-foreground italic p-4">
                No HTML body.
              </p>
            )
          ) : (
            <pre className="whitespace-pre-wrap text-xs text-foreground font-mono p-4 max-h-96 overflow-auto">
              {value.body_text || "(no plain text)"}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

// ── Tab 4: Announcements (Broadcasts + Releases + Incidents merged) ─────────

function AnnouncementsTab() {
  const [section, setSection] = useState<
    "broadcasts" | "releases" | "incidents"
  >("broadcasts");
  return (
    <div className="space-y-4 pt-4">
      {/* Sub-nav */}
      <div className="flex gap-1 rounded-lg border border-border bg-muted/30 p-1 w-fit">
        {(["broadcasts", "releases", "incidents"] as const).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSection(s)}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors capitalize ${section === s
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
              }`}
          >
            {s === "broadcasts"
              ? "Broadcasts"
              : s === "releases"
                ? "Releases"
                : "Incidents"}
          </button>
        ))}
      </div>
      {section === "broadcasts" && <BroadcastsSection />}
      {section === "releases" && <ReleasesSection />}
      {section === "incidents" && <IncidentsSection />}
    </div>
  );
}

const ANNOUNCEMENTS_PAGE_SIZE = 10;

function BroadcastsSection() {
  const [broadcasts, setBroadcasts] = useState<BroadcastResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Create form
  const [createForm, setCreateForm] = useState<CreateBroadcastRequest>({
    title: "",
    body_text: "",
    body_html: "",
    scope: "global",
    scope_org_id: "",
    scope_workspace_id: "",
    priority_code: "normal",
    severity: "",
    is_critical: false,
    scheduled_at: "",
  });
  const [templateContent, setTemplateContent] = useState<InlineTemplateValue>({
    subject_line: "",
    body_html: "",
    body_text: "",
  });
  const [createError, setCreateError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  // Action state
  const [actionError, setActionError] = useState<string | null>(null);
  const [sending, setSending] = useState<string | null>(null);

  const fetchBroadcasts = useCallback(() => {
    setLoading(true);
    listBroadcasts({ limit: ANNOUNCEMENTS_PAGE_SIZE, offset })
      .then((data) => {
        const list = data as { items?: BroadcastResponse[]; total?: number };
        setBroadcasts(list.items ?? (Array.isArray(data) ? data : []));
        setTotal(list.total ?? 0);
        setError(null);
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load broadcasts")
      )
      .finally(() => setLoading(false));
  }, [offset]);

  useEffect(() => {
    fetchBroadcasts();
  }, [fetchBroadcasts]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const payload: CreateBroadcastRequest = {
        title: createForm.title,
        body_text: templateContent.body_text || createForm.body_text,
        scope: createForm.scope,
      };
      if (templateContent.body_html)
        payload.body_html = templateContent.body_html;
      if (templateContent.subject_line)
        payload.subject_line = templateContent.subject_line;
      if (createForm.scope_org_id)
        payload.scope_org_id = createForm.scope_org_id;
      if (createForm.scope_workspace_id)
        payload.scope_workspace_id = createForm.scope_workspace_id;
      if (createForm.priority_code)
        payload.priority_code = createForm.priority_code;
      if (createForm.severity) payload.severity = createForm.severity;
      if (createForm.is_critical) payload.is_critical = true;
      if (createForm.scheduled_at)
        payload.scheduled_at = createForm.scheduled_at;
      await createBroadcast(payload);
      setShowCreate(false);
      setCreateForm({
        title: "",
        body_text: "",
        body_html: "",
        scope: "global",
        scope_org_id: "",
        scope_workspace_id: "",
        priority_code: "normal",
        severity: "",
        is_critical: false,
        scheduled_at: "",
      });
      setTemplateContent({ subject_line: "", body_html: "", body_text: "" });
      fetchBroadcasts();
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create broadcast"
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleSend(id: string) {
    setSending(id);
    setActionError(null);
    try {
      await sendBroadcast(id);
      fetchBroadcasts();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to send broadcast"
      );
    } finally {
      setSending(null);
    }
  }

  if (loading) return <TabSpinner />;
  if (error) return <TabError message={error} />;

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-end">
        <Button
          size="sm"
          className="gap-1.5"
          onClick={() => setShowCreate(!showCreate)}
        >
          {showCreate ? (
            <X className="h-3.5 w-3.5" />
          ) : (
            <Plus className="h-3.5 w-3.5" />
          )}
          {showCreate ? "Cancel" : "Create Broadcast"}
        </Button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="rounded-xl border border-border bg-card p-5">
          <form onSubmit={handleCreate} className="space-y-4">
            <h4 className="text-sm font-semibold text-foreground">
              New Broadcast
            </h4>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField
                label="Title"
                value={createForm.title}
                onChange={(v) => setCreateForm((p) => ({ ...p, title: v }))}
                placeholder="Broadcast title"
                required
              />
              <FormSelect
                label="Scope"
                value={createForm.scope}
                onChange={(v) => setCreateForm((p) => ({ ...p, scope: v }))}
                options={[
                  { value: "global", label: "Global" },
                  { value: "org", label: "Organization" },
                  { value: "workspace", label: "Workspace" },
                ]}
                required
              />
              {createForm.scope === "org" && (
                <FormField
                  label="Org ID"
                  value={createForm.scope_org_id ?? ""}
                  onChange={(v) =>
                    setCreateForm((p) => ({ ...p, scope_org_id: v }))
                  }
                  placeholder="UUID of the organization"
                />
              )}
              {createForm.scope === "workspace" && (
                <FormField
                  label="Workspace ID"
                  value={createForm.scope_workspace_id ?? ""}
                  onChange={(v) =>
                    setCreateForm((p) => ({ ...p, scope_workspace_id: v }))
                  }
                  placeholder="UUID of the workspace"
                />
              )}
              <FormSelect
                label="Priority"
                value={createForm.priority_code ?? "normal"}
                onChange={(v) =>
                  setCreateForm((p) => ({ ...p, priority_code: v }))
                }
                options={[
                  { value: "critical", label: "Critical" },
                  { value: "high", label: "High" },
                  { value: "normal", label: "Normal" },
                  { value: "low", label: "Low" },
                ]}
              />
              <FormField
                label="Scheduled At"
                value={createForm.scheduled_at ?? ""}
                onChange={(v) =>
                  setCreateForm((p) => ({ ...p, scheduled_at: v }))
                }
                type="datetime-local"
                placeholder="Leave empty for draft"
              />
            </div>
            <div className="rounded-lg border border-border bg-muted/5 p-4 space-y-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
                Email Template
              </p>
              <InlineTemplateEditor
                value={templateContent}
                onChange={setTemplateContent}
              />
            </div>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                <input
                  type="checkbox"
                  checked={createForm.is_critical ?? false}
                  onChange={(e) =>
                    setCreateForm((p) => ({
                      ...p,
                      is_critical: e.target.checked,
                    }))
                  }
                  className="rounded border-border"
                />
                Mark as Critical
              </label>
            </div>
            {createError && <InlineError message={createError} />}
            <div className="flex justify-end">
              <Button
                type="submit"
                size="sm"
                disabled={creating}
                className="gap-1.5"
              >
                {creating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Create
              </Button>
            </div>
          </form>
        </div>
      )}

      {actionError && <InlineError message={actionError} />}

      {broadcasts.length === 0 ? (
        <EmptyState
          icon={<Megaphone className="h-6 w-6 text-muted-foreground" />}
          label="No broadcasts yet"
        />
      ) : (
        <div className="space-y-3">
          {broadcasts.map((b: BroadcastResponse) => {
            const bBorderCls =
              b.status?.toLowerCase() === "sent"
                ? "border-l-green-500"
                : b.status?.toLowerCase() === "scheduled"
                  ? "border-l-blue-500"
                  : "border-l-primary";
            return (
              <div
                key={b.id}
                className={`rounded-xl border border-l-[3px] ${bBorderCls} border-border bg-background overflow-hidden`}
              >
                <button
                  type="button"
                  onClick={() =>
                    setExpandedId(expandedId === b.id ? null : b.id)
                  }
                  className="flex w-full items-start justify-between gap-4 p-4 hover:bg-muted/10 transition-colors text-left"
                >
                  <div className="flex flex-col gap-1 min-w-0">
                    <span className="text-sm font-semibold text-foreground">
                      {b.title}
                    </span>
                    {b.body_text && (
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {b.body_text}
                      </p>
                    )}
                    <span className="text-xs text-muted-foreground capitalize">
                      Scope: {b.target_scope}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <InlineBadge
                      label={b.status}
                      className={broadcastStatusClass(b.status)}
                    />
                    <span className="text-xs text-muted-foreground">
                      {b.sent_at
                        ? `Sent ${new Date(b.sent_at).toLocaleDateString()}`
                        : b.scheduled_at
                          ? `Scheduled ${new Date(b.scheduled_at).toLocaleDateString()}`
                          : `Created ${new Date(b.created_at).toLocaleDateString()}`}
                    </span>
                    {expandedId === b.id ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                </button>

                {expandedId === b.id && (
                  <div className="border-t border-border bg-muted/5 p-4 space-y-3">
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 text-xs">
                      <div>
                        <span className="text-muted-foreground">Status:</span>{" "}
                        <span className="font-medium text-foreground capitalize">
                          {b.status}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Scope:</span>{" "}
                        <span className="font-medium text-foreground capitalize">
                          {b.target_scope}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Created:</span>{" "}
                        <span className="font-medium text-foreground">
                          {new Date(b.created_at).toLocaleString()}
                        </span>
                      </div>
                      {b.scheduled_at && (
                        <div>
                          <span className="text-muted-foreground">
                            Scheduled:
                          </span>{" "}
                          <span className="font-medium text-foreground">
                            {new Date(b.scheduled_at).toLocaleString()}
                          </span>
                        </div>
                      )}
                      {b.sent_at && (
                        <div>
                          <span className="text-muted-foreground">Sent:</span>{" "}
                          <span className="font-medium text-foreground">
                            {new Date(b.sent_at).toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                    {b.body_text && (
                      <div>
                        <h5 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-1">
                          Body
                        </h5>
                        <p className="text-sm text-foreground whitespace-pre-wrap">
                          {b.body_text}
                        </p>
                      </div>
                    )}
                    {b.status.toLowerCase() === "draft" && (
                      <div className="flex justify-end">
                        <Button
                          type="button"
                          size="sm"
                          className="gap-1.5"
                          disabled={sending === b.id}
                          onClick={() => handleSend(b.id)}
                        >
                          {sending === b.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Send className="h-3.5 w-3.5" />
                          )}
                          Send Now
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      {total > ANNOUNCEMENTS_PAGE_SIZE && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">
            Showing {offset + 1}–
            {Math.min(offset + ANNOUNCEMENTS_PAGE_SIZE, total)} of {total}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() =>
                setOffset(Math.max(0, offset - ANNOUNCEMENTS_PAGE_SIZE))
              }
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={offset + ANNOUNCEMENTS_PAGE_SIZE >= total}
              onClick={() => setOffset(offset + ANNOUNCEMENTS_PAGE_SIZE)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Releases section ───────────────────────────────────────────────────────

function ReleasesSection() {
  const [releases, setReleases] = useState<ReleaseResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ReleaseFullResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create form
  const [createForm, setCreateForm] = useState<CreateReleaseRequest>({
    version: "",
    title: "",
    summary: "",
    body_markdown: "",
    changelog_url: "",
    release_date: "",
  });
  const [templateContent, setTemplateContent] = useState<InlineTemplateValue>({
    subject_line: "",
    body_html: "",
    body_text: "",
  });
  const [createError, setCreateError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  // Edit form
  const [editForm, setEditForm] = useState<UpdateReleaseRequest>({});
  const [editError, setEditError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Action state
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchReleases = useCallback(() => {
    setLoading(true);
    listReleases({ limit: ANNOUNCEMENTS_PAGE_SIZE, offset })
      .then((data) => {
        const list = data as ReleaseListResponse;
        setReleases(list.items ?? (Array.isArray(data) ? data : []));
        setTotal(list.total ?? 0);
        setError(null);
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load releases")
      )
      .finally(() => setLoading(false));
  }, [offset]);

  useEffect(() => {
    fetchReleases();
  }, [fetchReleases]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const payload: CreateReleaseRequest = {
        version: createForm.version,
        title: createForm.title,
        summary: createForm.summary,
      };
      if (createForm.body_markdown)
        payload.body_markdown = createForm.body_markdown;
      if (createForm.changelog_url)
        payload.changelog_url = createForm.changelog_url;
      if (createForm.release_date)
        payload.release_date = createForm.release_date;
      await createRelease(payload);
      setShowCreate(false);
      setCreateForm({
        version: "",
        title: "",
        summary: "",
        body_markdown: "",
        changelog_url: "",
        release_date: "",
      });
      setTemplateContent({ subject_line: "", body_html: "", body_text: "" });
      fetchReleases();
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create release"
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleExpand(r: ReleaseResponse) {
    if (expandedId === r.id) {
      setExpandedId(null);
      setDetail(null);
      return;
    }
    setExpandedId(r.id);
    setDetailLoading(true);
    setEditError(null);
    setActionError(null);
    try {
      const d = await getReleaseDetail(r.id);
      setDetail(d);
      setEditForm({
        title: d.title,
        summary: d.summary,
        body_markdown: d.body_markdown ?? "",
        changelog_url: d.changelog_url ?? "",
        release_date: d.release_date ?? "",
      });
    } catch (err) {
      setEditError(
        err instanceof Error ? err.message : "Failed to load release detail"
      );
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleSaveEdit() {
    if (!expandedId) return;
    setSaving(true);
    setEditError(null);
    try {
      await updateRelease(expandedId, editForm);
      setExpandedId(null);
      setDetail(null);
      fetchReleases();
    } catch (err) {
      setEditError(
        err instanceof Error ? err.message : "Failed to update release"
      );
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish(id: string) {
    setActionLoading(id);
    setActionError(null);
    try {
      await publishRelease(id, true);
      setExpandedId(null);
      setDetail(null);
      fetchReleases();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to publish release"
      );
    } finally {
      setActionLoading(null);
    }
  }

  async function handleArchive(id: string) {
    setActionLoading(id);
    setActionError(null);
    try {
      await archiveRelease(id);
      setExpandedId(null);
      setDetail(null);
      fetchReleases();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to archive release"
      );
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) return <TabSpinner />;
  if (error) return <TabError message={error} />;

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-end">
        <Button
          size="sm"
          className="gap-1.5"
          onClick={() => setShowCreate(!showCreate)}
        >
          {showCreate ? (
            <X className="h-3.5 w-3.5" />
          ) : (
            <Plus className="h-3.5 w-3.5" />
          )}
          {showCreate ? "Cancel" : "New Release"}
        </Button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="rounded-xl border border-border bg-card p-5">
          <form onSubmit={handleCreate} className="space-y-4">
            <h4 className="text-sm font-semibold text-foreground">
              New Release
            </h4>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField
                label="Version"
                value={createForm.version}
                onChange={(v) => setCreateForm((p) => ({ ...p, version: v }))}
                placeholder="e.g. 1.2.0"
                required
              />
              <FormField
                label="Title"
                value={createForm.title}
                onChange={(v) => setCreateForm((p) => ({ ...p, title: v }))}
                placeholder="Release title"
                required
              />
              <FormField
                label="Changelog URL"
                value={createForm.changelog_url ?? ""}
                onChange={(v) =>
                  setCreateForm((p) => ({ ...p, changelog_url: v }))
                }
                placeholder="https://..."
              />
              <FormField
                label="Release Date"
                value={createForm.release_date ?? ""}
                onChange={(v) =>
                  setCreateForm((p) => ({ ...p, release_date: v }))
                }
                type="date"
              />
            </div>
            <FormTextarea
              label="Summary"
              value={createForm.summary}
              onChange={(v) => setCreateForm((p) => ({ ...p, summary: v }))}
              rows={2}
              placeholder="Brief summary of the release..."
            />
            <FormTextarea
              label="Body (Markdown)"
              value={createForm.body_markdown ?? ""}
              onChange={(v) =>
                setCreateForm((p) => ({ ...p, body_markdown: v }))
              }
              rows={5}
              placeholder="## What's new\n\n- Feature A\n- Fix B"
            />
            <div className="rounded-lg border border-border bg-muted/5 p-4 space-y-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
                Email Template (optional)
              </p>
              <InlineTemplateEditor
                value={templateContent}
                onChange={setTemplateContent}
              />
            </div>
            {createError && <InlineError message={createError} />}
            <div className="flex justify-end">
              <Button
                type="submit"
                size="sm"
                disabled={creating}
                className="gap-1.5"
              >
                {creating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Create
              </Button>
            </div>
          </form>
        </div>
      )}

      {actionError && <InlineError message={actionError} />}

      {releases.length === 0 ? (
        <EmptyState
          icon={<Tag className="h-6 w-6 text-muted-foreground" />}
          label="No releases yet"
        />
      ) : (
        <div className="space-y-3">
          {releases.map((r: ReleaseResponse) => {
            const rBorderCls =
              r.status?.toLowerCase() === "published"
                ? "border-l-green-500"
                : r.status?.toLowerCase() === "archived"
                  ? "border-l-slate-400"
                  : "border-l-primary";
            return (
              <div
                key={r.id}
                className={`rounded-xl border border-l-[3px] ${rBorderCls} border-border bg-background overflow-hidden`}
              >
                <button
                  type="button"
                  onClick={() => handleExpand(r)}
                  className="flex w-full items-start justify-between gap-4 p-4 hover:bg-muted/10 transition-colors text-left"
                >
                  <div className="flex flex-col gap-1.5 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="inline-flex items-center rounded-md border border-primary/20 bg-primary/10 px-2 py-0.5 text-xs font-mono font-semibold text-primary">
                        v{r.version}
                      </span>
                      <span className="text-sm font-semibold text-foreground">
                        {r.title}
                      </span>
                    </div>
                    {r.summary && (
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {r.summary}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <InlineBadge
                      label={r.status}
                      className={releaseStatusClass(r.status)}
                    />
                    <span className="text-xs text-muted-foreground">
                      {r.published_at
                        ? `Published ${new Date(r.published_at).toLocaleDateString()}`
                        : `Created ${new Date(r.created_at).toLocaleDateString()}`}
                    </span>
                    {expandedId === r.id ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                </button>

                {expandedId === r.id && (
                  <div className="border-t border-border bg-muted/5 p-4 space-y-4">
                    {detailLoading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                      </div>
                    ) : (
                      <>
                        {/* Edit form */}
                        <div className="space-y-3">
                          <h5 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                            Edit Release
                          </h5>
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                            <FormField
                              label="Title"
                              value={editForm.title ?? ""}
                              onChange={(v) =>
                                setEditForm((p) => ({ ...p, title: v }))
                              }
                            />
                            <FormField
                              label="Changelog URL"
                              value={editForm.changelog_url ?? ""}
                              onChange={(v) =>
                                setEditForm((p) => ({ ...p, changelog_url: v }))
                              }
                              placeholder="https://..."
                            />
                            <FormField
                              label="Release Date"
                              value={editForm.release_date ?? ""}
                              onChange={(v) =>
                                setEditForm((p) => ({ ...p, release_date: v }))
                              }
                              type="date"
                            />
                          </div>
                          <FormTextarea
                            label="Summary"
                            value={editForm.summary ?? ""}
                            onChange={(v) =>
                              setEditForm((p) => ({ ...p, summary: v }))
                            }
                            rows={2}
                          />
                          <FormTextarea
                            label="Body (Markdown)"
                            value={editForm.body_markdown ?? ""}
                            onChange={(v) =>
                              setEditForm((p) => ({ ...p, body_markdown: v }))
                            }
                            rows={5}
                          />
                          {editError && <InlineError message={editError} />}
                          <div className="flex items-center gap-2 justify-end">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setExpandedId(null);
                                setDetail(null);
                              }}
                            >
                              Cancel
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              onClick={handleSaveEdit}
                              disabled={saving}
                              className="gap-1.5"
                            >
                              {saving && (
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              )}
                              <Save className="h-3.5 w-3.5" /> Save
                            </Button>
                          </div>
                        </div>

                        {/* Status actions */}
                        <div className="flex items-center gap-2 pt-2 border-t border-border">
                          {r.status.toLowerCase() === "draft" && (
                            <Button
                              type="button"
                              size="sm"
                              className="gap-1.5"
                              disabled={actionLoading === r.id}
                              onClick={() => handlePublish(r.id)}
                            >
                              {actionLoading === r.id ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              ) : (
                                <Eye className="h-3.5 w-3.5" />
                              )}
                              Publish
                            </Button>
                          )}
                          {(r.status.toLowerCase() === "draft" ||
                            r.status.toLowerCase() === "published") && (
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                className="gap-1.5"
                                disabled={actionLoading === r.id}
                                onClick={() => handleArchive(r.id)}
                              >
                                {actionLoading === r.id ? (
                                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                ) : (
                                  <Archive className="h-3.5 w-3.5" />
                                )}
                                Archive
                              </Button>
                            )}
                        </div>

                        {/* Detail metadata */}
                        {detail && (
                          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs pt-2 border-t border-border">
                            {detail.changelog_url && (
                              <div>
                                <span className="text-muted-foreground">
                                  Changelog:
                                </span>{" "}
                                <a
                                  href={detail.changelog_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary hover:underline"
                                >
                                  {detail.changelog_url}
                                </a>
                              </div>
                            )}
                            {detail.release_date && (
                              <div>
                                <span className="text-muted-foreground">
                                  Release Date:
                                </span>{" "}
                                <span className="text-foreground">
                                  {new Date(
                                    detail.release_date
                                  ).toLocaleDateString()}
                                </span>
                              </div>
                            )}
                            {detail.published_at && (
                              <div>
                                <span className="text-muted-foreground">
                                  Published At:
                                </span>{" "}
                                <span className="text-foreground">
                                  {new Date(
                                    detail.published_at
                                  ).toLocaleString()}
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      {total > ANNOUNCEMENTS_PAGE_SIZE && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">
            Showing {offset + 1}–
            {Math.min(offset + ANNOUNCEMENTS_PAGE_SIZE, total)} of {total}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() =>
                setOffset(Math.max(0, offset - ANNOUNCEMENTS_PAGE_SIZE))
              }
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={offset + ANNOUNCEMENTS_PAGE_SIZE >= total}
              onClick={() => setOffset(offset + ANNOUNCEMENTS_PAGE_SIZE)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Incidents section ──────────────────────────────────────────────────────

function IncidentsSection() {
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<IncidentFullResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create form
  const [createForm, setCreateForm] = useState<CreateIncidentRequest>({
    title: "",
    description: "",
    severity: "minor",
    affected_components: "",
    notify_users: true,
  });
  const [templateContent, setTemplateContent] = useState<InlineTemplateValue>({
    subject_line: "",
    body_html: "",
    body_text: "",
  });
  const [createError, setCreateError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  // Edit form
  const [editForm, setEditForm] = useState<UpdateIncidentRequest>({});
  const [editError, setEditError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Status update form
  const [showUpdateForm, setShowUpdateForm] = useState(false);
  const [updateForm, setUpdateForm] = useState<CreateIncidentUpdateRequest>({
    status: "investigating",
    message: "",
    is_public: true,
    notify_users: true,
  });
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [postingUpdate, setPostingUpdate] = useState(false);

  const fetchIncidents = useCallback(() => {
    setLoading(true);
    listIncidents({ limit: ANNOUNCEMENTS_PAGE_SIZE, offset })
      .then((data) => {
        const list = data as IncidentListResponse;
        setIncidents(list.items ?? (Array.isArray(data) ? data : []));
        setTotal(list.total ?? 0);
        setError(null);
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load incidents")
      )
      .finally(() => setLoading(false));
  }, [offset]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const payload: CreateIncidentRequest = {
        title: createForm.title,
        description: createForm.description,
        severity: createForm.severity,
        notify_users: createForm.notify_users,
      };
      if (createForm.affected_components)
        payload.affected_components = createForm.affected_components;
      await createIncident(payload);
      setShowCreate(false);
      setCreateForm({
        title: "",
        description: "",
        severity: "minor",
        affected_components: "",
        notify_users: true,
      });
      setTemplateContent({ subject_line: "", body_html: "", body_text: "" });
      fetchIncidents();
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create incident"
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleExpand(inc: IncidentResponse) {
    if (expandedId === inc.id) {
      setExpandedId(null);
      setDetail(null);
      return;
    }
    setExpandedId(inc.id);
    setDetailLoading(true);
    setEditError(null);
    setShowUpdateForm(false);
    try {
      const d = await getIncidentDetail(inc.id);
      setDetail(d);
      setEditForm({
        title: d.title,
        description: d.description,
        severity: d.severity,
        affected_components: d.affected_components ?? "",
      });
    } catch (err) {
      setEditError(
        err instanceof Error ? err.message : "Failed to load incident detail"
      );
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleSaveEdit() {
    if (!expandedId) return;
    setSaving(true);
    setEditError(null);
    try {
      await updateIncident(expandedId, editForm);
      setExpandedId(null);
      setDetail(null);
      fetchIncidents();
    } catch (err) {
      setEditError(
        err instanceof Error ? err.message : "Failed to update incident"
      );
    } finally {
      setSaving(false);
    }
  }

  async function handlePostUpdate() {
    if (!expandedId) return;
    setPostingUpdate(true);
    setUpdateError(null);
    try {
      await postIncidentUpdate(expandedId, updateForm);
      setShowUpdateForm(false);
      setUpdateForm({
        status: "investigating",
        message: "",
        is_public: true,
        notify_users: true,
      });
      const d = await getIncidentDetail(expandedId);
      setDetail(d);
      fetchIncidents();
    } catch (err) {
      setUpdateError(
        err instanceof Error ? err.message : "Failed to post update"
      );
    } finally {
      setPostingUpdate(false);
    }
  }

  if (loading) return <TabSpinner />;
  if (error) return <TabError message={error} />;

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-end">
        <Button
          size="sm"
          className="gap-1.5"
          onClick={() => setShowCreate(!showCreate)}
        >
          {showCreate ? (
            <X className="h-3.5 w-3.5" />
          ) : (
            <Plus className="h-3.5 w-3.5" />
          )}
          {showCreate ? "Cancel" : "Report Incident"}
        </Button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="rounded-xl border border-border bg-card p-5">
          <form onSubmit={handleCreate} className="space-y-4">
            <h4 className="text-sm font-semibold text-foreground">
              Report Incident
            </h4>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField
                label="Title"
                value={createForm.title}
                onChange={(v) => setCreateForm((p) => ({ ...p, title: v }))}
                placeholder="Incident title"
                required
              />
              <FormSelect
                label="Severity"
                value={createForm.severity}
                onChange={(v) => setCreateForm((p) => ({ ...p, severity: v }))}
                options={[
                  { value: "critical", label: "Critical" },
                  { value: "major", label: "Major" },
                  { value: "minor", label: "Minor" },
                  { value: "informational", label: "Informational" },
                ]}
                required
              />
              <FormField
                label="Affected Components"
                value={createForm.affected_components ?? ""}
                onChange={(v) =>
                  setCreateForm((p) => ({ ...p, affected_components: v }))
                }
                placeholder="e.g. API, Dashboard"
              />
            </div>
            <FormTextarea
              label="Description"
              value={createForm.description}
              onChange={(v) => setCreateForm((p) => ({ ...p, description: v }))}
              rows={3}
              placeholder="Describe what happened..."
            />
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                <input
                  type="checkbox"
                  checked={createForm.notify_users ?? true}
                  onChange={(e) =>
                    setCreateForm((p) => ({
                      ...p,
                      notify_users: e.target.checked,
                    }))
                  }
                  className="rounded border-border"
                />
                Notify users
              </label>
            </div>
            {createForm.notify_users && (
              <div className="rounded-lg border border-border bg-muted/5 p-4 space-y-3">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
                  Email Template (optional)
                </p>
                <InlineTemplateEditor
                  value={templateContent}
                  onChange={setTemplateContent}
                />
              </div>
            )}
            {createError && <InlineError message={createError} />}
            <div className="flex justify-end">
              <Button
                type="submit"
                size="sm"
                disabled={creating}
                className="gap-1.5"
              >
                {creating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Report
              </Button>
            </div>
          </form>
        </div>
      )}

      {incidents.length === 0 ? (
        <EmptyState
          icon={<Siren className="h-6 w-6 text-muted-foreground" />}
          label="No incidents yet"
        />
      ) : (
        <div className="space-y-3">
          {incidents.map((inc: IncidentResponse) => {
            const incBorderCls =
              inc.status?.toLowerCase() === "resolved"
                ? "border-l-green-500"
                : inc.status?.toLowerCase() === "monitoring"
                  ? "border-l-blue-500"
                  : inc.status?.toLowerCase() === "identified"
                    ? "border-l-amber-500"
                    : inc.status?.toLowerCase() === "investigating"
                      ? "border-l-amber-500"
                      : "border-l-red-500";
            return (
              <div
                key={inc.id}
                className={`rounded-xl border border-l-[3px] ${incBorderCls} border-border bg-background overflow-hidden`}
              >
                <button
                  type="button"
                  onClick={() => handleExpand(inc)}
                  className="flex w-full items-start justify-between gap-4 p-4 hover:bg-muted/10 transition-colors text-left"
                >
                  <div className="flex flex-col gap-1.5 min-w-0">
                    <span className="text-sm font-semibold text-foreground">
                      {inc.title}
                    </span>
                    {inc.summary && (
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {inc.summary}
                      </p>
                    )}
                    <span className="text-xs text-muted-foreground">
                      Started {new Date(inc.started_at).toLocaleString()}
                      {inc.resolved_at && (
                        <>
                          {" "}
                          &middot; Resolved{" "}
                          {new Date(inc.resolved_at).toLocaleString()}
                        </>
                      )}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <InlineBadge
                      label={inc.severity}
                      className={incidentSeverityClass(inc.severity)}
                    />
                    <InlineBadge
                      label={inc.status}
                      className={incidentStatusClass(inc.status)}
                    />
                    {expandedId === inc.id ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                </button>

                {expandedId === inc.id && (
                  <div className="border-t border-border bg-muted/5 p-4 space-y-5">
                    {detailLoading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                      </div>
                    ) : (
                      <>
                        {/* Edit form */}
                        <div className="space-y-3">
                          <h5 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                            Edit Incident
                          </h5>
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                            <FormField
                              label="Title"
                              value={editForm.title ?? ""}
                              onChange={(v) =>
                                setEditForm((p) => ({ ...p, title: v }))
                              }
                            />
                            <FormSelect
                              label="Severity"
                              value={editForm.severity ?? "minor"}
                              onChange={(v) =>
                                setEditForm((p) => ({ ...p, severity: v }))
                              }
                              options={[
                                { value: "critical", label: "Critical" },
                                { value: "major", label: "Major" },
                                { value: "minor", label: "Minor" },
                                {
                                  value: "informational",
                                  label: "Informational",
                                },
                              ]}
                            />
                            <FormField
                              label="Affected Components"
                              value={editForm.affected_components ?? ""}
                              onChange={(v) =>
                                setEditForm((p) => ({
                                  ...p,
                                  affected_components: v,
                                }))
                              }
                              placeholder="e.g. API, Dashboard"
                            />
                          </div>
                          <FormTextarea
                            label="Description"
                            value={editForm.description ?? ""}
                            onChange={(v) =>
                              setEditForm((p) => ({ ...p, description: v }))
                            }
                            rows={3}
                          />
                          {editError && <InlineError message={editError} />}
                          <div className="flex items-center gap-2 justify-end">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setExpandedId(null);
                                setDetail(null);
                              }}
                            >
                              Cancel
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              onClick={handleSaveEdit}
                              disabled={saving}
                              className="gap-1.5"
                            >
                              {saving && (
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              )}
                              <Save className="h-3.5 w-3.5" /> Save
                            </Button>
                          </div>
                        </div>

                        {/* Post Status Update */}
                        <div className="space-y-3 pt-2 border-t border-border">
                          <div className="flex items-center justify-between">
                            <h5 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                              Status Updates
                            </h5>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              className="gap-1.5"
                              onClick={() => setShowUpdateForm(!showUpdateForm)}
                            >
                              {showUpdateForm ? (
                                <X className="h-3 w-3" />
                              ) : (
                                <MessageSquare className="h-3 w-3" />
                              )}
                              {showUpdateForm ? "Cancel" : "Post Update"}
                            </Button>
                          </div>

                          {showUpdateForm && (
                            <div className="rounded-lg border border-border bg-background p-4 space-y-3">
                              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                <FormSelect
                                  label="Status"
                                  value={updateForm.status}
                                  onChange={(v) =>
                                    setUpdateForm((p) => ({ ...p, status: v }))
                                  }
                                  options={[
                                    {
                                      value: "investigating",
                                      label: "Investigating",
                                    },
                                    {
                                      value: "identified",
                                      label: "Identified",
                                    },
                                    {
                                      value: "monitoring",
                                      label: "Monitoring",
                                    },
                                    { value: "resolved", label: "Resolved" },
                                  ]}
                                  required
                                />
                                <div className="flex items-end gap-4 pb-1">
                                  <label className="flex items-center gap-2 text-xs text-foreground cursor-pointer">
                                    <input
                                      type="checkbox"
                                      checked={updateForm.is_public ?? true}
                                      onChange={(e) =>
                                        setUpdateForm((p) => ({
                                          ...p,
                                          is_public: e.target.checked,
                                        }))
                                      }
                                      className="rounded border-border"
                                    />
                                    Public
                                  </label>
                                  <label className="flex items-center gap-2 text-xs text-foreground cursor-pointer">
                                    <input
                                      type="checkbox"
                                      checked={updateForm.notify_users ?? true}
                                      onChange={(e) =>
                                        setUpdateForm((p) => ({
                                          ...p,
                                          notify_users: e.target.checked,
                                        }))
                                      }
                                      className="rounded border-border"
                                    />
                                    Notify Users
                                  </label>
                                </div>
                              </div>
                              <FormTextarea
                                label="Message"
                                value={updateForm.message}
                                onChange={(v) =>
                                  setUpdateForm((p) => ({ ...p, message: v }))
                                }
                                rows={3}
                                placeholder="Describe the current situation..."
                              />
                              {updateError && (
                                <InlineError message={updateError} />
                              )}
                              <div className="flex justify-end">
                                <Button
                                  type="button"
                                  size="sm"
                                  onClick={handlePostUpdate}
                                  disabled={postingUpdate}
                                  className="gap-1.5"
                                >
                                  {postingUpdate && (
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                  )}
                                  <Send className="h-3.5 w-3.5" /> Post Update
                                </Button>
                              </div>
                            </div>
                          )}

                          {/* Update history */}
                          {detail &&
                            detail.updates &&
                            detail.updates.length > 0 ? (
                            <div className="rounded-lg border border-border bg-background overflow-hidden">
                              {detail.updates.map(
                                (upd: IncidentUpdateResponse, i: number) => (
                                  <div
                                    key={upd.id}
                                    className={`px-4 py-3 ${i < (detail.updates?.length ?? 0) - 1 ? "border-b border-border" : ""}`}
                                  >
                                    <div className="flex items-center justify-between gap-3 mb-1">
                                      <div className="flex items-center gap-2">
                                        <InlineBadge
                                          label={upd.status}
                                          className={incidentStatusClass(
                                            upd.status
                                          )}
                                        />
                                        {upd.is_public && (
                                          <span className="text-xs text-muted-foreground">
                                            Public
                                          </span>
                                        )}
                                      </div>
                                      <span className="text-xs text-muted-foreground">
                                        {new Date(
                                          upd.created_at
                                        ).toLocaleString()}
                                      </span>
                                    </div>
                                    <p className="text-sm text-foreground">
                                      {upd.message}
                                    </p>
                                  </div>
                                )
                              )}
                            </div>
                          ) : (
                            <p className="text-xs text-muted-foreground italic">
                              No status updates yet.
                            </p>
                          )}
                        </div>

                        {/* Incident metadata */}
                        {detail && (
                          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs pt-2 border-t border-border">
                            {detail.affected_components && (
                              <div>
                                <span className="text-muted-foreground">
                                  Affected Components:
                                </span>{" "}
                                <span className="text-foreground">
                                  {detail.affected_components}
                                </span>
                              </div>
                            )}
                            <div>
                              <span className="text-muted-foreground">
                                Started:
                              </span>{" "}
                              <span className="text-foreground">
                                {new Date(detail.started_at).toLocaleString()}
                              </span>
                            </div>
                            {detail.resolved_at && (
                              <div>
                                <span className="text-muted-foreground">
                                  Resolved:
                                </span>{" "}
                                <span className="text-foreground">
                                  {new Date(
                                    detail.resolved_at
                                  ).toLocaleString()}
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      {total > ANNOUNCEMENTS_PAGE_SIZE && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">
            Showing {offset + 1}–
            {Math.min(offset + ANNOUNCEMENTS_PAGE_SIZE, total)} of {total}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() =>
                setOffset(Math.max(0, offset - ANNOUNCEMENTS_PAGE_SIZE))
              }
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={offset + ANNOUNCEMENTS_PAGE_SIZE >= total}
              onClick={() => setOffset(offset + ANNOUNCEMENTS_PAGE_SIZE)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Tab 7: Delivery Queue ──────────────────────────────────────────────────

function statusQueueClass(s: string): string {
  switch (s.toLowerCase()) {
    case "queued":
      return "bg-blue-500/10 text-blue-500 border-blue-500/20";
    case "processing":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    case "sent":
      return "bg-green-500/10 text-green-500 border-green-500/20";
    case "delivered":
      return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
    case "failed":
      return "bg-red-500/10 text-red-500 border-red-500/20";
    case "dead_letter":
      return "bg-red-700/10 text-red-700 border-red-700/20";
    case "suppressed":
      return "bg-muted text-muted-foreground border-border";
    default:
      return "bg-muted text-muted-foreground border-border";
  }
}

function QueueItemDetail({
  item,
  onAction,
}: {
  item: QueueItemAdminResponse;
  onAction: () => void;
}) {
  const [detail, setDetail] = useState<NotificationDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionResult, setActionResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  useEffect(() => {
    setDetailLoading(true);
    getNotificationDetail(item.id)
      .then(setDetail)
      .catch(() => {
        /* detail is supplementary */
      })
      .finally(() => setDetailLoading(false));
  }, [item.id]);

  async function handleRetry() {
    setActionLoading(true);
    setActionResult(null);
    try {
      const res = await retryQueueItem(item.id);
      setActionResult(res);
      if (res.success) onAction();
    } catch (e) {
      setActionResult({
        success: false,
        message: e instanceof Error ? e.message : "Failed",
      });
    } finally {
      setActionLoading(false);
    }
  }

  async function handleDeadLetter() {
    setActionLoading(true);
    setActionResult(null);
    try {
      const res = await deadLetterQueueItem(
        item.id,
        "Manually dead-lettered by admin"
      );
      setActionResult(res);
      if (res.success) onAction();
    } catch (e) {
      setActionResult({
        success: false,
        message: e instanceof Error ? e.message : "Failed",
      });
    } finally {
      setActionLoading(false);
    }
  }

  const canRetry = ["failed", "dead_letter"].includes(item.status_code);
  const canDeadLetter = ![
    "sent",
    "delivered",
    "opened",
    "clicked",
    "dead_letter",
  ].includes(item.status_code);
  const logs = detail?.delivery_logs ?? [];
  const events = detail?.tracking_events ?? [];

  return (
    <div className="space-y-4">
      {/* Metadata grid */}
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs">
        <div>
          <span className="text-muted-foreground">ID: </span>
          <span className="font-mono text-foreground">{item.id}</span>
        </div>
        {item.user_id && (
          <div>
            <span className="text-muted-foreground">User: </span>
            <span className="font-mono text-foreground">{item.user_id}</span>
          </div>
        )}
        {item.template_id && (
          <div>
            <span className="text-muted-foreground">Template: </span>
            <span className="font-mono text-foreground">
              {item.template_id}
            </span>
          </div>
        )}
        {item.source_rule_id && (
          <div>
            <span className="text-muted-foreground">Rule: </span>
            <span className="font-mono text-foreground">
              {item.source_rule_id}
            </span>
          </div>
        )}
        {item.broadcast_id && (
          <div>
            <span className="text-muted-foreground">Broadcast: </span>
            <span className="font-mono text-foreground">
              {item.broadcast_id}
            </span>
          </div>
        )}
        <div>
          <span className="text-muted-foreground">Scheduled: </span>
          <span className="text-foreground">
            {new Date(item.scheduled_at).toLocaleString()}
          </span>
        </div>
        {item.next_retry_at && (
          <div>
            <span className="text-muted-foreground">Next retry: </span>
            <span className="text-foreground">
              {new Date(item.next_retry_at).toLocaleString()}
            </span>
          </div>
        )}
        {item.completed_at && (
          <div>
            <span className="text-muted-foreground">Completed: </span>
            <span className="text-foreground">
              {new Date(item.completed_at).toLocaleString()}
            </span>
          </div>
        )}
        {item.last_error && (
          <div className="sm:col-span-2">
            <span className="text-muted-foreground">Last error: </span>
            <span className="text-red-500 font-mono break-all">
              {item.last_error}
            </span>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 flex-wrap">
        {canRetry && (
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={handleRetry}
            disabled={actionLoading}
          >
            <RotateCcw className="h-3 w-3" /> Retry
          </Button>
        )}
        {canDeadLetter && (
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1 text-red-500 hover:text-red-600"
            onClick={handleDeadLetter}
            disabled={actionLoading}
          >
            <Trash2 className="h-3 w-3" /> Dead Letter
          </Button>
        )}
        {actionLoading && (
          <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
        )}
        {actionResult && (
          <span
            className={`text-xs font-medium ${actionResult.success ? "text-green-500" : "text-red-500"}`}
          >
            {actionResult.message}
          </span>
        )}
      </div>

      {/* Delivery Logs */}
      {detailLoading ? (
        <div className="flex items-center gap-2 text-xs text-muted-foreground py-2">
          <Loader2 className="h-3.5 w-3.5 animate-spin" /> Loading delivery
          details…
        </div>
      ) : (
        <>
          {logs.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                <Send className="h-3 w-3" /> Delivery Log ({logs.length} attempt
                {logs.length !== 1 ? "s" : ""})
              </h5>
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-muted/30 border-b border-border">
                      {[
                        "#",
                        "Status",
                        "Duration",
                        "Provider ID",
                        "Error",
                        "Time",
                      ].map((h) => (
                        <th
                          key={h}
                          className="px-2.5 py-1.5 text-left font-semibold text-muted-foreground"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log: DeliveryLogResponse, li: number) => (
                      <tr
                        key={log.id}
                        className={
                          li < logs.length - 1 ? "border-b border-border" : ""
                        }
                      >
                        <td className="px-2.5 py-1.5 text-muted-foreground">
                          {log.attempt_number}
                        </td>
                        <td className="px-2.5 py-1.5">
                          <span
                            className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${log.status === "sent"
                              ? "bg-green-500/10 text-green-500"
                              : "bg-red-500/10 text-red-500"
                              }`}
                          >
                            {log.status}
                          </span>
                        </td>
                        <td className="px-2.5 py-1.5 text-muted-foreground tabular-nums">
                          {log.duration_ms != null
                            ? `${log.duration_ms}ms`
                            : "—"}
                        </td>
                        <td className="px-2.5 py-1.5 font-mono text-muted-foreground truncate max-w-[120px]">
                          {log.provider_message_id ?? "—"}
                        </td>
                        <td className="px-2.5 py-1.5 text-red-400 font-mono truncate max-w-[200px]">
                          {log.error_message ?? "—"}
                        </td>
                        <td className="px-2.5 py-1.5 text-muted-foreground whitespace-nowrap">
                          {new Date(log.occurred_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tracking Events */}
          {events.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                <MousePointer className="h-3 w-3" /> Tracking Events (
                {events.length})
              </h5>
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-muted/30 border-b border-border">
                      {["Event", "Channel", "URL", "IP", "Time"].map((h) => (
                        <th
                          key={h}
                          className="px-2.5 py-1.5 text-left font-semibold text-muted-foreground"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((ev: TrackingEventResponse, ei: number) => (
                      <tr
                        key={ev.id}
                        className={
                          ei < events.length - 1 ? "border-b border-border" : ""
                        }
                      >
                        <td className="px-2.5 py-1.5">
                          <span
                            className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${ev.tracking_event_type_code === "opened"
                              ? "bg-purple-500/10 text-purple-500"
                              : ev.tracking_event_type_code === "clicked"
                                ? "bg-pink-500/10 text-pink-500"
                                : "bg-muted text-muted-foreground"
                              }`}
                          >
                            {ev.tracking_event_type_code}
                          </span>
                        </td>
                        <td className="px-2.5 py-1.5">
                          <InlineBadge
                            label={ev.channel_code}
                            className={channelBadgeClass(ev.channel_code)}
                          />
                        </td>
                        <td className="px-2.5 py-1.5 font-mono text-muted-foreground truncate max-w-[200px]">
                          {ev.click_url ?? "—"}
                        </td>
                        <td className="px-2.5 py-1.5 font-mono text-muted-foreground">
                          {ev.ip_address ?? "—"}
                        </td>
                        <td className="px-2.5 py-1.5 text-muted-foreground whitespace-nowrap">
                          {new Date(ev.occurred_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {logs.length === 0 && events.length === 0 && (
            <p className="text-xs text-muted-foreground py-1">
              No delivery logs or tracking events yet.
            </p>
          )}
        </>
      )}
    </div>
  );
}

function DeliveryQueueTab() {
  const [data, setData] = useState<QueueAdminResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [channelFilter, setChannelFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const LIMIT = 50;

  const fetchQueue = useCallback(() => {
    setLoading(true);
    getNotificationQueue({
      status_code: statusFilter || undefined,
      channel_code: channelFilter || undefined,
      limit: LIMIT,
      offset,
    })
      .then((d) => {
        setData(d as QueueAdminResponse);
        setError(null);
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load queue")
      )
      .finally(() => setLoading(false));
  }, [statusFilter, channelFilter, offset]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const stats = data?.stats;
  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  const STAT_TILES = stats
    ? [
      {
        label: "Queued",
        value: stats.queued,
        numCls: "text-blue-500",
        borderCls: "border-l-blue-500",
        icon: Clock,
      },
      {
        label: "Processing",
        value: stats.processing,
        numCls: "text-amber-500",
        borderCls: "border-l-amber-500",
        icon: Loader2,
      },
      {
        label: "Sent",
        value: stats.sent,
        numCls: "text-green-500",
        borderCls: "border-l-green-500",
        icon: Send,
      },
      {
        label: "Delivered",
        value: stats.delivered,
        numCls: "text-emerald-500",
        borderCls: "border-l-emerald-500",
        icon: CheckCircle2,
      },
      {
        label: "Failed",
        value: stats.failed,
        numCls: "text-red-500",
        borderCls: "border-l-red-500",
        icon: XCircle,
      },
      {
        label: "Dead Letter",
        value: stats.dead_letter,
        numCls: "text-red-700",
        borderCls: "border-l-red-700",
        icon: Archive,
      },
      {
        label: "Suppressed",
        value: stats.suppressed,
        numCls: "text-muted-foreground",
        borderCls: "border-l-slate-400",
        icon: Lock,
      },
    ]
    : [];

  return (
    <div className="space-y-5 pt-4">
      {/* KPI stat cards */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          {STAT_TILES.map((tile) => {
            const statusCode = tile.label.toLowerCase().replace(" ", "_");
            const isActive = statusFilter === statusCode;
            const TileIcon = tile.icon;
            return (
              <button
                key={tile.label}
                type="button"
                onClick={() => {
                  setStatusFilter(isActive ? "" : statusCode);
                  setOffset(0);
                }}
                className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${tile.borderCls} bg-card px-4 py-3 text-left transition-all hover:brightness-105 ${isActive ? "ring-2 ring-primary/30" : ""}`}
              >
                <div className="shrink-0 rounded-lg p-2 bg-muted">
                  <TileIcon className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
                <div className="min-w-0">
                  <span
                    className={`text-2xl font-bold tabular-nums leading-none ${tile.numCls}`}
                  >
                    {tile.value}
                  </span>
                  <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">
                    {tile.label}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 flex flex-wrap items-center gap-2">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setOffset(0);
          }}
          className="h-8 rounded-md border border-border bg-background px-2 text-xs text-foreground"
        >
          <option value="">All statuses</option>
          {[
            "queued",
            "processing",
            "sent",
            "delivered",
            "failed",
            "dead_letter",
            "suppressed",
          ].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={channelFilter}
          onChange={(e) => {
            setChannelFilter(e.target.value);
            setOffset(0);
          }}
          className="h-8 rounded-md border border-border bg-background px-2 text-xs text-foreground"
        >
          <option value="">All channels</option>
          {["email", "in_app", "sms", "web_push", "webhook"].map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        {/* Active filter chips */}
        {statusFilter && (
          <button
            type="button"
            onClick={() => {
              setStatusFilter("");
              setOffset(0);
            }}
            className="inline-flex items-center gap-1 rounded-full bg-primary/10 border border-primary/20 text-primary px-2 py-0.5 text-[11px] font-medium hover:bg-primary/20 transition-colors"
          >
            status: {statusFilter}
            <X className="h-2.5 w-2.5 ml-0.5" />
          </button>
        )}
        {channelFilter && (
          <button
            type="button"
            onClick={() => {
              setChannelFilter("");
              setOffset(0);
            }}
            className="inline-flex items-center gap-1 rounded-full bg-primary/10 border border-primary/20 text-primary px-2 py-0.5 text-[11px] font-medium hover:bg-primary/20 transition-colors"
          >
            channel: {channelFilter}
            <X className="h-2.5 w-2.5 ml-0.5" />
          </button>
        )}

        <div className="flex-1" />
        <Button
          variant="outline"
          size="sm"
          className="h-8 gap-1.5 text-xs"
          onClick={fetchQueue}
          disabled={loading}
        >
          {loading ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3" />
          )}
          Refresh
        </Button>
        <span className="text-xs text-muted-foreground">
          {total} total (last 7 days)
        </span>
      </div>

      {error && <TabError message={error} />}

      {loading && !data ? (
        <TabSpinner />
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Database className="h-6 w-6 text-muted-foreground" />}
          label="No notifications in queue"
        />
      ) : (
        <>
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/30">
                    {[
                      "Status",
                      "Channel",
                      "Type",
                      "Recipient",
                      "Subject",
                      "Priority",
                      "Attempts",
                      "Created",
                    ].map((h) => (
                      <th
                        key={h}
                        className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((item: QueueItemAdminResponse, i: number) => (
                    <React.Fragment key={item.id}>
                      <tr
                        onClick={() =>
                          setExpandedId(expandedId === item.id ? null : item.id)
                        }
                        className={`cursor-pointer transition-colors hover:bg-muted/20 ${i < items.length - 1 ? "border-b border-border" : ""} ${expandedId === item.id ? "bg-muted/10" : ""}`}
                      >
                        <td className="px-3 py-2.5 whitespace-nowrap">
                          <InlineBadge
                            label={item.status_code}
                            className={statusQueueClass(item.status_code)}
                          />
                        </td>
                        <td className="px-3 py-2.5 whitespace-nowrap">
                          <InlineBadge
                            label={item.channel_code}
                            className={channelBadgeClass(item.channel_code)}
                          />
                        </td>
                        <td className="px-3 py-2.5">
                          <span className="font-mono text-xs text-muted-foreground">
                            {item.notification_type_code}
                          </span>
                        </td>
                        <td className="px-3 py-2.5">
                          <span className="text-xs text-foreground truncate max-w-[160px] block">
                            {item.recipient_email ?? "—"}
                          </span>
                        </td>
                        <td className="px-3 py-2.5">
                          <span className="text-xs text-foreground truncate max-w-[200px] block">
                            {item.rendered_subject ?? "—"}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 whitespace-nowrap">
                          <InlineBadge
                            label={item.priority_code}
                            className={priorityClass(item.priority_code)}
                          />
                        </td>
                        <td className="px-3 py-2.5 whitespace-nowrap text-xs text-muted-foreground">
                          {item.attempt_count}/{item.max_attempts}
                        </td>
                        <td className="px-3 py-2.5 whitespace-nowrap text-xs text-muted-foreground">
                          {new Date(item.created_at).toLocaleString()}
                        </td>
                      </tr>
                      {expandedId === item.id && (
                        <tr className="border-b border-border bg-muted/5">
                          <td colSpan={8} className="px-4 py-3">
                            <QueueItemDetail
                              item={item}
                              onAction={fetchQueue}
                            />
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {total > LIMIT && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                Showing {offset + 1}–{Math.min(offset + LIMIT, total)} of{" "}
                {total}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - LIMIT))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={offset + LIMIT >= total}
                  onClick={() => setOffset(offset + LIMIT)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Tab 8: Reports ─────────────────────────────────────────────────────────

function ReportsTab() {
  const [report, setReport] = useState<DeliveryReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodHours, setPeriodHours] = useState(24);

  const load = useCallback((hours: number) => {
    setLoading(true);
    setError(null);
    getDeliveryReport({ period_hours: hours })
      .then(setReport)
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load report")
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load(periodHours);
  }, [load, periodHours]);

  const PERIOD_OPTIONS = [
    { value: 1, label: "Last 1 hour" },
    { value: 6, label: "Last 6 hours" },
    { value: 24, label: "Last 24 hours" },
    { value: 72, label: "Last 3 days" },
    { value: 168, label: "Last 7 days" },
    { value: 720, label: "Last 30 days" },
  ];

  const statusColors: Record<string, string> = {
    queued: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    processing: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    sent: "bg-cyan-500/10 text-cyan-500 border-cyan-500/20",
    delivered: "bg-green-500/10 text-green-500 border-green-500/20",
    opened: "bg-purple-500/10 text-purple-500 border-purple-500/20",
    clicked: "bg-pink-500/10 text-pink-500 border-pink-500/20",
    failed: "bg-red-500/10 text-red-500 border-red-500/20",
    dead_letter: "bg-red-800/10 text-red-800 border-red-800/20",
    suppressed: "bg-muted text-muted-foreground border-border",
  };

  return (
    <div className="space-y-6 pt-4">
      {/* Header + period selector */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h3 className="text-base font-semibold text-foreground">
            Delivery Analytics
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Funnel metrics and breakdown by type, channel, and status.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={periodHours}
            onChange={(e) => setPeriodHours(Number(e.target.value))}
            className="flex h-8 rounded-md border border-border bg-background px-2.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {PERIOD_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5"
            onClick={() => load(periodHours)}
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {loading && <TabSpinner />}
      {!loading && error && <TabError message={error} />}
      {!loading && !error && report && (
        <>
          {/* Funnel tiles */}
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
            {(
              ["sent", "delivered", "opened", "clicked", "failed"] as const
            ).map((key) => {
              const value = report.funnel[key as keyof typeof report.funnel];
              return (
                <div
                  key={key}
                  className={`flex flex-col gap-1 rounded-xl border p-3 ${statusColors[key] ?? "bg-muted border-border"}`}
                >
                  <span className="text-xs font-medium capitalize">{key}</span>
                  <span className="text-2xl font-bold tabular-nums">
                    {value as number}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Rate metrics */}
          <div className="grid grid-cols-3 gap-3">
            {[
              {
                label: "Delivery Rate",
                value: report.funnel.delivery_rate,
                suffix: "%",
              },
              {
                label: "Open Rate",
                value: report.funnel.open_rate,
                suffix: "%",
              },
              {
                label: "Click Rate",
                value: report.funnel.click_rate,
                suffix: "%",
              },
            ].map((m) => (
              <div
                key={m.label}
                className="rounded-xl border border-border bg-card p-4 flex flex-col gap-1"
              >
                <span className="text-xs text-muted-foreground font-medium">
                  {m.label}
                </span>
                <span className="text-3xl font-bold text-foreground tabular-nums">
                  {m.value.toFixed(1)}
                  <span className="text-lg font-normal text-muted-foreground">
                    {m.suffix}
                  </span>
                </span>
              </div>
            ))}
          </div>

          {/* Extra stats */}
          <div className="grid grid-cols-4 gap-3">
            {(
              ["queued", "processing", "dead_letter", "suppressed"] as const
            ).map((key) => (
              <div
                key={key}
                className={`flex flex-col gap-1 rounded-xl border p-3 ${statusColors[key] ?? "bg-muted border-border"}`}
              >
                <span className="text-xs font-medium capitalize">
                  {key.replace("_", " ")}
                </span>
                <span className="text-xl font-bold tabular-nums">
                  {report.funnel[key as keyof typeof report.funnel] as number}
                </span>
              </div>
            ))}
          </div>

          {/* Row breakdown table */}
          {report.rows.length > 0 ? (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-foreground">
                Hourly Breakdown
              </h4>
              <div className="rounded-xl border border-border bg-card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border bg-muted/30">
                        {["Hour", "Type", "Channel", "Status", "Count"].map(
                          (h) => (
                            <th
                              key={h}
                              className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                            >
                              {h}
                            </th>
                          )
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {report.rows.map((row, i) => (
                        <tr
                          key={i}
                          className={`${i < report.rows.length - 1 ? "border-b border-border" : ""} hover:bg-muted/20 transition-colors`}
                        >
                          <td className="px-4 py-2.5 whitespace-nowrap">
                            <span className="font-mono text-xs text-muted-foreground">
                              {row.hour_bucket.replace("T", " ").slice(0, 16)}
                            </span>
                          </td>
                          <td className="px-4 py-2.5">
                            <span className="font-mono text-xs text-foreground">
                              {row.notification_type_code}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 whitespace-nowrap">
                            <span
                              className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-xs font-medium ${channelBadgeClass(row.channel_code)}`}
                            >
                              {row.channel_code}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 whitespace-nowrap">
                            <span
                              className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-xs font-medium ${statusColors[row.status_code] ?? "bg-muted text-muted-foreground border-border"}`}
                            >
                              {row.status_code}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 tabular-nums font-medium text-foreground">
                            {row.total_count.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <EmptyState
              icon={<Monitor className="h-6 w-6 text-muted-foreground" />}
              label="No delivery data for this period"
            />
          )}
        </>
      )}
    </div>
  );
}

// ── Tab 9: Send Test ───────────────────────────────────────────────────────

function SendTestTab() {
  const [config, setConfig] = useState<NotificationConfigResponse | null>(null);
  const [configLoading, setConfigLoading] = useState(true);

  const [toEmail, setToEmail] = useState("");
  const [typeCode, setTypeCode] = useState("");
  const [channelCode, setChannelCode] = useState("email");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    getNotificationConfig()
      .then((d) => setConfig(d as NotificationConfigResponse))
      .catch(() => {
        /* non-critical */
      })
      .finally(() => setConfigLoading(false));
  }, []);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!toEmail || !typeCode) return;
    setSending(true);
    setResult(null);
    setFormError(null);
    try {
      const res = await sendTestNotification({
        to_email: toEmail,
        notification_type_code: typeCode,
        channel_code: channelCode,
        subject: subject || undefined,
        body: body || undefined,
      });
      setResult(res);
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Failed to send");
    } finally {
      setSending(false);
    }
  }

  const typeOptions =
    config?.types.map((t) => ({
      value: t.code,
      label: `${t.name} (${t.code})`,
    })) ?? [];
  const channelOptions = config?.channels.map((c) => ({
    value: c.code,
    label: c.name,
  })) ?? [{ value: "email", label: "Email" }];

  return (
    <div className="space-y-6 pt-4 max-w-2xl">
      <div>
        <h3 className="text-base font-semibold text-foreground">
          Send Test Notification
        </h3>
        <p className="text-xs text-muted-foreground mt-0.5">
          Send a test notification to verify channel delivery end-to-end.
        </p>
      </div>

      <form onSubmit={handleSend} className="space-y-4">
        <FormField
          label="Recipient email"
          value={toEmail}
          onChange={setToEmail}
          placeholder="recipient@example.com"
          required
          type="email"
        />

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label className="text-xs font-medium text-muted-foreground">
              Notification type
            </Label>
            {configLoading ? (
              <div className="flex h-9 items-center">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <select
                value={typeCode}
                onChange={(e) => setTypeCode(e.target.value)}
                required
                className="flex h-9 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">Select type…</option>
                {typeOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs font-medium text-muted-foreground">
              Channel
            </Label>
            {configLoading ? (
              <div className="flex h-9 items-center">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <select
                value={channelCode}
                onChange={(e) => setChannelCode(e.target.value)}
                className="flex h-9 w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {channelOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        <FormField
          label="Subject (optional — overrides template)"
          value={subject}
          onChange={setSubject}
          placeholder="[Test] My notification"
        />

        <FormTextarea
          label="Body (optional — overrides template)"
          value={body}
          onChange={setBody}
          rows={4}
          placeholder="<p>Test notification body…</p>"
        />

        {formError && <InlineError message={formError} />}

        {result && (
          <div
            className={`flex items-start gap-2 rounded-lg border px-3 py-2.5 ${result.success
              ? "border-green-500/30 bg-green-500/10"
              : "border-red-500/30 bg-red-500/10"
              }`}
          >
            {result.success ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500 mt-0.5" />
            ) : (
              <XCircle className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
            )}
            <span
              className={`text-sm font-medium ${result.success ? "text-green-500" : "text-red-500"}`}
            >
              {result.message}
            </span>
          </div>
        )}

        <div className="flex gap-2">
          <Button
            type="submit"
            disabled={sending || !toEmail || !typeCode}
            className="gap-1.5"
          >
            {sending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            {sending ? "Sending…" : "Send Test"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setResult(null);
              setFormError(null);
              setToEmail("");
              setTypeCode("");
              setSubject("");
              setBody("");
            }}
          >
            Clear
          </Button>
        </div>
      </form>
    </div>
  );
}

// ── Tab 3: Variable Queries ────────────────────────────────────────────────

const BIND_PARAM_KEYS = [
  "$user_id",
  "$org_id",
  "$workspace_id",
  "$framework_id",
  "$control_id",
  "$task_id",
  "$risk_id",
  "$actor_id",
  "$tenant_key",
];

const DATA_TYPE_OPTIONS: {
  value: ResultColumnDefinition["data_type"];
  label: string;
}[] = [
    { value: "string", label: "String" },
    { value: "integer", label: "Integer" },
    { value: "boolean", label: "Boolean" },
    { value: "datetime", label: "Datetime" },
  ];

function emptyBindParam(position: number): BindParamDefinition {
  return {
    key: "$user_id",
    position,
    source: "context",
    required: true,
    default_value: null,
  };
}

function emptyResultColumn(): ResultColumnDefinition {
  return { name: "", data_type: "string", default_value: null };
}

function VariableQueriesTab() {
  const [queries, setQueries] = useState<VariableQueryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ── Variable Keys state ────────────────────────────────────────────────────
  const [varKeys, setVarKeys] = useState<TemplateVariableKeyResponse[]>([]);
  const [showVarKeyCreate, setShowVarKeyCreate] = useState(false);
  const [vkCode, setVkCode] = useState("");
  const [vkName, setVkName] = useState("");
  const [vkDesc, setVkDesc] = useState("");
  const [vkSource, setVkSource] = useState<"static" | "custom_query">("static");
  const [vkStaticValue, setVkStaticValue] = useState("");
  const [vkQueryId, setVkQueryId] = useState("");
  const [vkCreateError, setVkCreateError] = useState<string | null>(null);
  const [vkCreating, setVkCreating] = useState(false);
  const [vkEditCode, setVkEditCode] = useState<string | null>(null);
  const [vkEditName, setVkEditName] = useState("");
  const [vkEditValue, setVkEditValue] = useState("");
  const [vkEditQueryId, setVkEditQueryId] = useState("");
  const [vkEditSource, setVkEditSource] = useState("");
  const [vkSaving, setVkSaving] = useState(false);
  const [vkEditError, setVkEditError] = useState<string | null>(null);
  const [vkDeleting, setVkDeleting] = useState<string | null>(null);
  const [showAllVarKeys, setShowAllVarKeys] = useState(false);

  // Create state
  const [showCreate, setShowCreate] = useState(false);
  const [createCode, setCreateCode] = useState("");
  const [createName, setCreateName] = useState("");
  const [createDesc, setCreateDesc] = useState("");
  const [createSql, setCreateSql] = useState("");
  const [createBindParams, setCreateBindParams] = useState<
    BindParamDefinition[]
  >([emptyBindParam(1)]);
  const [createResultCols, setCreateResultCols] = useState<
    ResultColumnDefinition[]
  >([emptyResultColumn()]);
  const [createLinkedEvents, setCreateLinkedEvents] = useState<string[]>([]);
  const [createTimeout, setCreateTimeout] = useState("3000");
  const [createError, setCreateError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  // Expand / Edit state
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editSql, setEditSql] = useState("");
  const [editBindParams, setEditBindParams] = useState<BindParamDefinition[]>(
    []
  );
  const [editResultCols, setEditResultCols] = useState<
    ResultColumnDefinition[]
  >([]);
  const [editLinkedEvents, setEditLinkedEvents] = useState<string[]>([]);
  const [editTimeout, setEditTimeout] = useState("3000");
  const [editActive, setEditActive] = useState(true);
  const [editError, setEditError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Schema metadata for SQL editor autocomplete
  const [schemaMetadata, setSchemaMetadata] = useState<TableMetadata[]>([]);
  const createEditorRef = useRef<HTMLDivElement>(null);
  const editEditorRef = useRef<HTMLDivElement>(null);

  // Audit event context state
  const [auditEventTypes, setAuditEventTypes] = useState<AuditEventTypeInfo[]>(
    []
  );
  const [selectedEventType, setSelectedEventType] = useState("");
  const [recentEvents, setRecentEvents] = useState<RecentAuditEventResponse[]>(
    []
  );
  const [showAuditExplorer, setShowAuditExplorer] = useState(false);

  // Test state (shared between create & edit)
  const [testUseProfile, setTestUseProfile] = useState(true);
  const [testAuditEventId, setTestAuditEventId] = useState("");
  const [testEventTypeFilter, setTestEventTypeFilter] = useState("");
  const [testParamOverrides, setTestParamOverrides] = useState<
    Record<string, string>
  >({});
  const [testResult, setTestResult] = useState<QueryPreviewResponse | null>(
    null
  );
  const [testLoading, setTestLoading] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);

  const fetchQueries = useCallback(() => {
    setLoading(true);
    listVariableQueries()
      .then((data) => {
        const list = data as VariableQueryListResponse;
        setQueries(list.items ?? []);
        setError(null);
      })
      .catch((e) =>
        setError(
          e instanceof Error ? e.message : "Failed to load variable queries"
        )
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchQueries();
  }, [fetchQueries]);

  // Fetch variable keys
  const fetchVarKeys = useCallback(() => {
    listVariableKeys()
      .then(setVarKeys)
      .catch(() => { });
  }, []);
  useEffect(() => {
    fetchVarKeys();
  }, [fetchVarKeys]);

  async function handleVkCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!vkCode.trim() || !vkName.trim()) {
      setVkCreateError("Code and name are required");
      return;
    }
    if (vkSource === "static" && !vkStaticValue.trim()) {
      setVkCreateError("Static value is required");
      return;
    }
    if (vkSource === "custom_query" && !vkQueryId.trim()) {
      setVkCreateError("Query is required");
      return;
    }
    setVkCreating(true);
    setVkCreateError(null);
    try {
      const payload: CreateVariableKeyRequest = {
        code: vkCode.trim(),
        name: vkName.trim(),
        description: vkDesc.trim(),
        resolution_source: vkSource,
        ...(vkSource === "static"
          ? { static_value: vkStaticValue.trim() }
          : { query_id: vkQueryId.trim() }),
      };
      await createVariableKey(payload);
      fetchVarKeys();
      setShowVarKeyCreate(false);
      setVkCode("");
      setVkName("");
      setVkDesc("");
      setVkStaticValue("");
      setVkQueryId("");
    } catch (e) {
      setVkCreateError(e instanceof Error ? e.message : "Failed");
    } finally {
      setVkCreating(false);
    }
  }

  async function handleVkSaveEdit(code: string) {
    setVkSaving(true);
    setVkEditError(null);
    try {
      const payload: UpdateVariableKeyRequest = {
        name: vkEditName || undefined,
        ...(vkEditSource === "static"
          ? { static_value: vkEditValue }
          : { query_id: vkEditQueryId }),
      };
      await updateVariableKey(code, payload);
      fetchVarKeys();
      setVkEditCode(null);
    } catch (e) {
      setVkEditError(e instanceof Error ? e.message : "Failed");
    } finally {
      setVkSaving(false);
    }
  }

  async function handleVkDelete(code: string) {
    if (
      !confirm(
        `Delete variable key "${code}"? Templates using {{ ${code} }} won't resolve it anymore.`
      )
    )
      return;
    setVkDeleting(code);
    try {
      await deleteVariableKey(code);
      fetchVarKeys();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to delete");
    } finally {
      setVkDeleting(null);
    }
  }

  // Fetch schema metadata + audit event types once on mount
  useEffect(() => {
    fetchSchemaMetadata()
      .then((data) => setSchemaMetadata(data.tables ?? []))
      .catch(() => { }); // non-critical
    fetchAuditEventTypes()
      .then((data) => setAuditEventTypes(data.event_types ?? []))
      .catch(() => { }); // non-critical
  }, []);

  function resetCreateForm() {
    setCreateCode("");
    setCreateName("");
    setCreateDesc("");
    setCreateSql("");
    setCreateBindParams([emptyBindParam(1)]);
    setCreateResultCols([emptyResultColumn()]);
    setCreateLinkedEvents([]);
    setCreateTimeout("3000");
    setCreateError(null);
    resetTestState();
  }

  function resetTestState() {
    setTestUseProfile(true);
    setTestAuditEventId("");
    setTestParamOverrides({});
    setTestResult(null);
    setTestLoading(false);
    setTestError(null);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (
      createResultCols.length === 0 ||
      createResultCols.some((c) => !c.name.trim())
    ) {
      setCreateError("At least one result column with a name is required");
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      const payload: CreateVariableQueryRequest = {
        code: createCode,
        name: createName,
        description: createDesc || undefined,
        sql_template: createSql,
        bind_params: createBindParams,
        result_columns: createResultCols,
        linked_event_type_codes: createLinkedEvents,
        timeout_ms: Math.min(
          10000,
          Math.max(100, parseInt(createTimeout) || 3000)
        ),
      };
      await createVariableQuery(payload);
      setShowCreate(false);
      resetCreateForm();
      fetchQueries();
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create variable query"
      );
    } finally {
      setCreating(false);
    }
  }

  function handleExpand(q: VariableQueryResponse) {
    if (expandedId === q.id) {
      setExpandedId(null);
      resetTestState();
      return;
    }
    setExpandedId(q.id);
    setEditName(q.name);
    setEditDesc(q.description ?? "");
    setEditSql(q.sql_template);
    setEditBindParams(
      q.bind_params.length > 0 ? [...q.bind_params] : [emptyBindParam(1)]
    );
    setEditResultCols(
      q.result_columns.length > 0
        ? [...q.result_columns]
        : [emptyResultColumn()]
    );
    setEditLinkedEvents(q.linked_event_type_codes ?? []);
    setEditTimeout(String(q.timeout_ms));
    setEditActive(q.is_active);
    setEditError(null);
    resetTestState();
  }

  async function handleSaveEdit() {
    if (!expandedId) return;
    const currentQuery = queries.find((q) => q.id === expandedId);
    const isSystem = currentQuery?.is_system ?? false;

    if (
      !isSystem &&
      (editResultCols.length === 0 ||
        editResultCols.some((c) => !c.name.trim()))
    ) {
      setEditError("At least one result column with a name is required");
      return;
    }
    setSaving(true);
    setEditError(null);
    try {
      const payload: UpdateVariableQueryRequest = {
        name: editName,
        description: editDesc || undefined,
        timeout_ms: Math.min(
          10000,
          Math.max(100, parseInt(editTimeout) || 3000)
        ),
        is_active: editActive,
        linked_event_type_codes: editLinkedEvents,
        // System queries: only name/description/timeout/active are editable
        ...(isSystem
          ? {}
          : {
            sql_template: editSql,
            bind_params: editBindParams,
            result_columns: editResultCols,
          }),
      };
      await updateVariableQuery(expandedId, payload);
      setExpandedId(null);
      fetchQueries();
    } catch (err) {
      setEditError(
        err instanceof Error ? err.message : "Failed to update variable query"
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    setDeleting(true);
    try {
      await deleteVariableQuery(id);
      setExpandedId(null);
      fetchQueries();
    } catch (err) {
      setEditError(
        err instanceof Error ? err.message : "Failed to delete variable query"
      );
    } finally {
      setDeleting(false);
    }
  }

  async function handleTestExisting() {
    if (!expandedId) return;
    setTestLoading(true);
    setTestError(null);
    setTestResult(null);
    try {
      const payload: PreviewQueryRequest = {
        param_values:
          Object.keys(testParamOverrides).length > 0
            ? testParamOverrides
            : undefined,
        use_my_profile: testUseProfile,
        audit_event_id: testAuditEventId || null,
      };
      const result = await previewVariableQuery(expandedId, payload);
      setTestResult(result);
      if (!result.success && result.error) setTestError(result.error);
    } catch (err) {
      setTestError(
        err instanceof Error ? err.message : "Test execution failed"
      );
    } finally {
      setTestLoading(false);
    }
  }

  async function handleTestNew() {
    setTestLoading(true);
    setTestError(null);
    setTestResult(null);
    try {
      const payload: TestQueryRequest = {
        sql_template: createSql,
        bind_params: createBindParams,
        param_values:
          Object.keys(testParamOverrides).length > 0
            ? testParamOverrides
            : undefined,
        use_my_profile: testUseProfile,
      };
      const result = await testVariableQuery(payload);
      setTestResult(result);
      if (!result.success && result.error) setTestError(result.error);
    } catch (err) {
      setTestError(
        err instanceof Error ? err.message : "Test execution failed"
      );
    } finally {
      setTestLoading(false);
    }
  }

  // ── Bind params array helpers ──────────────────────────────────────────────

  function updateBindParam(
    list: BindParamDefinition[],
    setList: (v: BindParamDefinition[]) => void,
    index: number,
    patch: Partial<BindParamDefinition>
  ) {
    const next = list.map((p, i) => (i === index ? { ...p, ...patch } : p));
    setList(next);
  }

  function addBindParam(
    list: BindParamDefinition[],
    setList: (v: BindParamDefinition[]) => void
  ) {
    setList([...list, emptyBindParam(list.length + 1)]);
  }

  function removeBindParam(
    list: BindParamDefinition[],
    setList: (v: BindParamDefinition[]) => void,
    index: number
  ) {
    const next = list
      .filter((_, i) => i !== index)
      .map((p, i) => ({ ...p, position: i + 1 }));
    setList(next);
  }

  // ── Result columns array helpers ───────────────────────────────────────────

  function updateResultCol(
    list: ResultColumnDefinition[],
    setList: (v: ResultColumnDefinition[]) => void,
    index: number,
    patch: Partial<ResultColumnDefinition>
  ) {
    const next = list.map((c, i) => (i === index ? { ...c, ...patch } : c));
    setList(next);
  }

  function addResultCol(
    list: ResultColumnDefinition[],
    setList: (v: ResultColumnDefinition[]) => void
  ) {
    setList([...list, emptyResultColumn()]);
  }

  function removeResultCol(
    list: ResultColumnDefinition[],
    setList: (v: ResultColumnDefinition[]) => void,
    index: number
  ) {
    if (list.length <= 1) return;
    setList(list.filter((_, i) => i !== index));
  }

  // ── Reusable sub-components ────────────────────────────────────────────────

  function BindParamsEditor({
    params,
    setParams,
  }: {
    params: BindParamDefinition[];
    setParams: (v: BindParamDefinition[]) => void;
  }) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-xs font-medium text-muted-foreground">
            Bind Parameters
          </Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-6 gap-1 text-xs"
            onClick={() => addBindParam(params, setParams)}
          >
            <Plus className="h-3 w-3" /> Add
          </Button>
        </div>
        {params.map((bp, idx) => (
          <div
            key={idx}
            className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2"
          >
            <span className="text-xs font-mono text-muted-foreground w-5 shrink-0">
              ${bp.position}
            </span>
            <select
              value={bp.key}
              onChange={(e) =>
                updateBindParam(params, setParams, idx, { key: e.target.value })
              }
              className="h-7 rounded-md border border-border bg-background px-2 text-xs min-w-[120px]"
            >
              {BIND_PARAM_KEYS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
            <select
              value={bp.source}
              onChange={(e) =>
                updateBindParam(params, setParams, idx, {
                  source: e.target.value as "context" | "audit_property",
                })
              }
              className="h-7 rounded-md border border-border bg-background px-2 text-xs"
            >
              <option value="context">context</option>
              <option value="audit_property">audit_property</option>
            </select>
            <label className="flex items-center gap-1 text-xs text-muted-foreground">
              <input
                type="checkbox"
                checked={bp.required}
                onChange={(e) =>
                  updateBindParam(params, setParams, idx, {
                    required: e.target.checked,
                  })
                }
                className="h-3.5 w-3.5"
              />
              Req
            </label>
            <Input
              value={bp.default_value ?? ""}
              onChange={(e) =>
                updateBindParam(params, setParams, idx, {
                  default_value: e.target.value || null,
                })
              }
              placeholder="Default"
              className="h-7 text-xs flex-1 min-w-[80px]"
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 text-muted-foreground hover:text-red-500"
              onClick={() => removeBindParam(params, setParams, idx)}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        ))}
      </div>
    );
  }

  function ResultColumnsEditor({
    cols,
    setCols,
  }: {
    cols: ResultColumnDefinition[];
    setCols: (v: ResultColumnDefinition[]) => void;
  }) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-xs font-medium text-muted-foreground">
            Result Columns (min 1)
          </Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-6 gap-1 text-xs"
            onClick={() => addResultCol(cols, setCols)}
          >
            <Plus className="h-3 w-3" /> Add
          </Button>
        </div>
        {cols.map((col, idx) => (
          <div
            key={idx}
            className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2"
          >
            <Input
              value={col.name}
              onChange={(e) =>
                updateResultCol(cols, setCols, idx, { name: e.target.value })
              }
              placeholder="Column name"
              className="h-7 text-xs flex-1 min-w-[100px]"
            />
            <select
              value={col.data_type}
              onChange={(e) =>
                updateResultCol(cols, setCols, idx, {
                  data_type: e.target
                    .value as ResultColumnDefinition["data_type"],
                })
              }
              className="h-7 rounded-md border border-border bg-background px-2 text-xs"
            >
              {DATA_TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <Input
              value={col.default_value ?? ""}
              onChange={(e) =>
                updateResultCol(cols, setCols, idx, {
                  default_value: e.target.value || null,
                })
              }
              placeholder="Default"
              className="h-7 text-xs flex-1 min-w-[80px]"
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 text-muted-foreground hover:text-red-500"
              disabled={cols.length <= 1}
              onClick={() => removeResultCol(cols, setCols, idx)}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        ))}
      </div>
    );
  }

  // ── Audit Context Explorer ────────────────────────────────────────────────

  function AuditContextExplorer({
    onApplyQuery,
  }: {
    onApplyQuery: (
      sql: string,
      params: BindParamDefinition[],
      cols: ResultColumnDefinition[]
    ) => void;
  }) {
    const filteredTypes = selectedEventType
      ? auditEventTypes.filter(
        (et) =>
          et.event_type.includes(selectedEventType) ||
          et.entity_type.includes(selectedEventType) ||
          et.event_category.includes(selectedEventType)
      )
      : auditEventTypes;

    const selectedInfo = auditEventTypes.find(
      (et) => et.event_type === selectedEventType
    );

    // Map entity type to suggested query template
    function suggestQuery(
      entityType: string,
      eventType: string
    ): {
      sql: string;
      params: BindParamDefinition[];
      cols: ResultColumnDefinition[];
    } | null {
      const suggestions: Record<
        string,
        { sql: string; param: string; cols: ResultColumnDefinition[] }
      > = {
        task: {
          sql: `SELECT title, description, status_code, priority_code,\n       assignee_name, assignee_email,\n       reporter_name, org_name, workspace_name,\n       due_date::text AS due_date\nFROM "08_tasks"."50_vw_task_notification"\nWHERE task_id = $1`,
          param: "$task_id",
          cols: [
            { name: "title", data_type: "string" as const },
            { name: "status_code", data_type: "string" as const },
            { name: "priority_code", data_type: "string" as const },
            { name: "assignee_name", data_type: "string" as const },
            { name: "assignee_email", data_type: "string" as const },
            { name: "reporter_name", data_type: "string" as const },
            { name: "org_name", data_type: "string" as const },
            { name: "workspace_name", data_type: "string" as const },
            { name: "due_date", data_type: "string" as const },
          ],
        },
        control: {
          sql: `SELECT control_code, control_name, description,\n       category_name, criticality_name,\n       framework_name, framework_code\nFROM "05_grc_library"."50_vw_control_notification"\nWHERE control_id = $1`,
          param: "$control_id",
          cols: [
            { name: "control_code", data_type: "string" as const },
            { name: "control_name", data_type: "string" as const },
            { name: "category_name", data_type: "string" as const },
            { name: "criticality_name", data_type: "string" as const },
            { name: "framework_name", data_type: "string" as const },
          ],
        },
        risk: {
          sql: `SELECT risk_code, title, risk_level_name,\n       risk_category_name, risk_status,\n       treatment_type_code, owner_name,\n       org_name, workspace_name,\n       latest_risk_score::text AS latest_risk_score\nFROM "14_risk_registry"."50_vw_risk_notification"\nWHERE risk_id = $1`,
          param: "$risk_id",
          cols: [
            { name: "risk_code", data_type: "string" as const },
            { name: "title", data_type: "string" as const },
            { name: "risk_level_name", data_type: "string" as const },
            { name: "risk_category_name", data_type: "string" as const },
            { name: "owner_name", data_type: "string" as const },
            { name: "latest_risk_score", data_type: "string" as const },
          ],
        },
        user: {
          sql: `SELECT first_name, last_name, display_name,\n       email, username\nFROM "03_auth_manage"."50_vw_user_profile"\nWHERE user_id = $1`,
          param: "$user_id",
          cols: [
            { name: "first_name", data_type: "string" as const },
            { name: "display_name", data_type: "string" as const },
            { name: "email", data_type: "string" as const },
          ],
        },
        org: {
          sql: `SELECT org_name, org_slug, org_type_name\nFROM "03_auth_manage"."51_vw_org_detail"\nWHERE org_id = $1`,
          param: "$org_id",
          cols: [
            { name: "org_name", data_type: "string" as const },
            { name: "org_slug", data_type: "string" as const },
            { name: "org_type_name", data_type: "string" as const },
          ],
        },
        workspace: {
          sql: `SELECT workspace_name, workspace_slug,\n       workspace_type_name, org_name\nFROM "03_auth_manage"."52_vw_workspace_detail"\nWHERE workspace_id = $1`,
          param: "$workspace_id",
          cols: [
            { name: "workspace_name", data_type: "string" as const },
            { name: "workspace_slug", data_type: "string" as const },
            { name: "org_name", data_type: "string" as const },
          ],
        },
        framework: {
          sql: `SELECT framework_code, framework_name,\n       publisher_name, framework_type_name,\n       framework_category_name\nFROM "05_grc_library"."50_vw_framework_notification"\nWHERE framework_id = $1`,
          param: "$framework_id",
          cols: [
            { name: "framework_code", data_type: "string" as const },
            { name: "framework_name", data_type: "string" as const },
            { name: "publisher_name", data_type: "string" as const },
          ],
        },
      };

      const s = suggestions[entityType];
      if (!s) return null;
      return {
        sql: s.sql,
        params: [
          {
            key: s.param,
            position: 1,
            source: "audit_property" as const,
            required: true,
          },
        ],
        cols: s.cols,
      };
    }

    return (
      <div className="space-y-3 rounded-xl border border-border bg-muted/10 p-4">
        <button
          type="button"
          className="flex w-full items-center justify-between text-xs font-semibold uppercase tracking-widest text-muted-foreground"
          onClick={() => setShowAuditExplorer(!showAuditExplorer)}
        >
          Audit Context Helper
          {showAuditExplorer ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </button>

        {showAuditExplorer && (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">
                Filter by event type / entity / category
              </Label>
              <Input
                value={selectedEventType}
                onChange={(e) => setSelectedEventType(e.target.value)}
                placeholder="e.g. task, status_changed, login"
                className="h-7 text-xs"
              />
            </div>

            {filteredTypes.length > 0 && (
              <div className="max-h-48 overflow-y-auto space-y-1 rounded-lg border border-border p-2">
                {filteredTypes.slice(0, 20).map((et) => {
                  const suggestion = suggestQuery(
                    et.entity_type,
                    et.event_type
                  );
                  return (
                    <div
                      key={`${et.entity_type}.${et.event_type}`}
                      className="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted/50 group"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-xs font-mono font-medium text-foreground">
                            {et.event_type}
                          </span>
                          <InlineBadge
                            label={et.entity_type}
                            className="bg-muted text-muted-foreground border-border"
                          />
                          <InlineBadge
                            label={et.event_category}
                            className="bg-muted text-muted-foreground border-border"
                          />
                          <span className="text-[10px] text-muted-foreground">
                            ({et.event_count})
                          </span>
                        </div>
                        {et.available_properties.length > 0 && (
                          <div className="flex flex-wrap gap-0.5 mt-0.5">
                            {et.available_properties.slice(0, 6).map((p) => (
                              <span
                                key={p}
                                className="text-[9px] font-mono text-muted-foreground bg-muted/50 px-1 rounded"
                              >
                                {p}
                              </span>
                            ))}
                            {et.available_properties.length > 6 && (
                              <span className="text-[9px] text-muted-foreground">
                                +{et.available_properties.length - 6} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      {suggestion && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-6 gap-1 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() =>
                            onApplyQuery(
                              suggestion.sql,
                              suggestion.params,
                              suggestion.cols
                            )
                          }
                        >
                          Use Query
                        </Button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {filteredTypes.length === 0 && selectedEventType && (
              <p className="text-xs text-muted-foreground italic">
                No event types matching &quot;{selectedEventType}&quot;
              </p>
            )}

            {auditEventTypes.length === 0 && (
              <p className="text-xs text-muted-foreground italic">
                No audit events recorded yet
              </p>
            )}
          </div>
        )}
      </div>
    );
  }

  function TestPanel({
    bindParams,
    onRun,
    queryCode,
  }: {
    bindParams: BindParamDefinition[];
    onRun: () => void;
    queryCode?: string;
  }) {
    const [showRecentEvents, setShowRecentEvents] = useState(false);
    const [loadingEvents, setLoadingEvents] = useState(false);
    const [localEventTypeFilter, setLocalEventTypeFilter] = useState(testEventTypeFilter);
    const [selectedEventPreview, setSelectedEventPreview] = useState<import("@/lib/types/admin").RecentAuditEventResponse | null>(null);

    async function handleBrowseEvents(eventType?: string) {
      const type = eventType ?? localEventTypeFilter;
      setShowRecentEvents(true);
      setLoadingEvents(true);
      try {
        const data = await fetchRecentAuditEvents(type || undefined);
        setRecentEvents(data.events ?? []);
      } catch {
        // non-critical
      } finally {
        setLoadingEvents(false);
      }
    }

    function handleSelectEvent(ev: import("@/lib/types/admin").RecentAuditEventResponse) {
      setTestAuditEventId(ev.id);
      setSelectedEventPreview(ev);
      setShowRecentEvents(false);
    }

    return (
      <div className="space-y-3 rounded-xl border border-border bg-muted/20 p-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Test Query
          </h4>
          <Button
            type="button"
            variant="default"
            size="sm"
            className="h-7 gap-1.5 text-xs"
            onClick={onRun}
            disabled={testLoading}
          >
            {testLoading ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Eye className="h-3 w-3" />
            )}
            Run Test
          </Button>
        </div>

        {/* ── Audit event picker ── */}
        <div className="space-y-2 rounded-lg border border-border bg-background/60 p-3">
          <Label className="text-xs font-medium text-muted-foreground">Audit Event Context</Label>

          {/* Event type select */}
          <div className="flex items-center gap-2">
            <select
              value={localEventTypeFilter}
              onChange={(e) => {
                setLocalEventTypeFilter(e.target.value);
                setTestEventTypeFilter(e.target.value);
                setTestAuditEventId("");
                setSelectedEventPreview(null);
                setRecentEvents([]);
                setShowRecentEvents(false);
              }}
              className="h-7 flex-1 rounded-md border border-border bg-background px-2 text-xs outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="">— Any event type —</option>
              {auditEventTypes.map((et) => (
                <option key={`${et.event_category}.${et.event_type}`} value={et.event_type}>
                  {et.event_type} ({et.entity_type}, {et.event_count})
                </option>
              ))}
            </select>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 gap-1 text-xs shrink-0"
              onClick={() => handleBrowseEvents()}
            >
              {loadingEvents ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Database className="h-3 w-3" />
              )}
              Browse events
            </Button>
          </div>

          {/* Selected event summary */}
          {selectedEventPreview && (
            <div className="rounded-md border border-border bg-muted/40 px-3 py-2 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-medium text-foreground">
                  {selectedEventPreview.event_type}
                </span>
                <button
                  type="button"
                  className="text-[10px] text-muted-foreground hover:text-red-400"
                  onClick={() => { setTestAuditEventId(""); setSelectedEventPreview(null); }}
                >
                  ✕ clear
                </button>
              </div>
              <div className="flex flex-wrap gap-1">
                {Object.entries(selectedEventPreview.properties).map(([k, v]) => (
                  <span
                    key={k}
                    className="inline-flex items-center rounded border border-border bg-muted px-1 py-0.5 text-[9px] font-mono text-muted-foreground"
                  >
                    <span className="text-foreground/70">{k}:</span>
                    <span className="ml-1 text-foreground truncate max-w-[120px]">{v}</span>
                  </span>
                ))}
                {Object.keys(selectedEventPreview.properties).length === 0 && (
                  <span className="text-[10px] text-muted-foreground italic">No properties</span>
                )}
              </div>
              <div className="text-[9px] text-muted-foreground font-mono">
                ID: {selectedEventPreview.id} · {new Date(selectedEventPreview.occurred_at).toLocaleString()}
              </div>
            </div>
          )}

          {/* Manual event ID fallback */}
          {!selectedEventPreview && (
            <div className="flex items-center gap-1.5">
              <Label className="text-xs text-muted-foreground whitespace-nowrap">Or paste Event ID</Label>
              <Input
                value={testAuditEventId}
                onChange={(e) => setTestAuditEventId(e.target.value)}
                placeholder="UUID of a specific audit event"
                className="h-7 text-xs flex-1 font-mono"
              />
            </div>
          )}
        </div>

        {/* Recent events picker */}
        {showRecentEvents && (
          <div className="rounded-lg border border-border overflow-hidden">
            <div className="bg-muted/50 px-3 py-1.5 border-b border-border flex items-center justify-between">
              <span className="text-[10px] font-semibold text-muted-foreground">
                {localEventTypeFilter ? `Recent: ${localEventTypeFilter}` : "Recent events (all types)"}
              </span>
              <button
                type="button"
                className="text-[10px] text-muted-foreground hover:text-foreground"
                onClick={() => setShowRecentEvents(false)}
              >
                ✕ close
              </button>
            </div>
            <div className="max-h-52 overflow-y-auto">
              <table className="w-full text-[10px]">
                <thead>
                  <tr className="border-b border-border bg-muted/30 sticky top-0">
                    <th className="px-2 py-1 text-left font-medium text-muted-foreground">Event Type</th>
                    <th className="px-2 py-1 text-left font-medium text-muted-foreground">Entity</th>
                    <th className="px-2 py-1 text-left font-medium text-muted-foreground">Time</th>
                    <th className="px-2 py-1 text-left font-medium text-muted-foreground">Props</th>
                  </tr>
                </thead>
                <tbody>
                  {recentEvents.map((ev) => (
                    <tr
                      key={ev.id}
                      className="border-b border-border last:border-0 hover:bg-primary/5 cursor-pointer transition-colors"
                      onClick={() => handleSelectEvent(ev)}
                    >
                      <td className="px-2 py-1.5 font-mono font-medium text-foreground">{ev.event_type}</td>
                      <td className="px-2 py-1.5 text-muted-foreground">{ev.entity_type}</td>
                      <td className="px-2 py-1.5 text-muted-foreground whitespace-nowrap">
                        {new Date(ev.occurred_at).toLocaleString()}
                      </td>
                      <td className="px-2 py-1.5">
                        <div className="flex flex-wrap gap-0.5">
                          {Object.entries(ev.properties).slice(0, 3).map(([k, v]) => (
                            <span key={k} className="text-[9px] font-mono bg-muted px-1 rounded text-muted-foreground">
                              {k}={String(v).slice(0, 20)}
                            </span>
                          ))}
                          {Object.keys(ev.properties).length > 3 && (
                            <span className="text-[9px] text-muted-foreground">+{Object.keys(ev.properties).length - 3}</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {recentEvents.length === 0 && !loadingEvents && (
                    <tr>
                      <td colSpan={4} className="px-2 py-3 text-center text-muted-foreground italic">
                        No events found{localEventTypeFilter ? ` for "${localEventTypeFilter}"` : ""}
                      </td>
                    </tr>
                  )}
                  {loadingEvents && (
                    <tr>
                      <td colSpan={4} className="px-2 py-3 text-center">
                        <Loader2 className="h-3 w-3 animate-spin mx-auto" />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={testUseProfile}
            onChange={(e) => setTestUseProfile(e.target.checked)}
            className="h-3.5 w-3.5"
          />
          Inject my user profile into context
        </label>

        {bindParams.length > 0 && (
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">
              Param Overrides
            </Label>
            <div className="grid grid-cols-2 gap-2">
              {bindParams.map((bp) => (
                <div key={bp.key} className="flex items-center gap-1.5">
                  <span className="text-xs font-mono text-muted-foreground w-28 truncate">
                    {bp.key}
                  </span>
                  <Input
                    value={testParamOverrides[bp.key] ?? ""}
                    onChange={(e) =>
                      setTestParamOverrides((prev) => ({
                        ...prev,
                        [bp.key]: e.target.value,
                      }))
                    }
                    placeholder={bp.default_value ?? "auto"}
                    className="h-7 text-xs flex-1"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {testError && <InlineError message={testError} />}

        {testResult && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              {testResult.success ? (
                <InlineBadge
                  label="Success"
                  className="bg-green-500/10 text-green-500 border-green-500/20"
                />
              ) : (
                <InlineBadge
                  label="Failed"
                  className="bg-red-500/10 text-red-500 border-red-500/20"
                />
              )}
              {testResult.execution_ms != null && (
                <span className="text-xs text-muted-foreground">
                  {testResult.execution_ms}ms
                </span>
              )}
            </div>

            {/* Resolved params */}
            {testResult.resolved_params && Object.keys(testResult.resolved_params).length > 0 && (
              <div className="space-y-1">
                <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Resolved bind params</span>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(testResult.resolved_params).map(([k, v]) => (
                    <span
                      key={k}
                      className="inline-flex items-center rounded-md border border-border bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground"
                    >
                      {k}=<span className="text-foreground ml-0.5">{v}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Results table */}
            {testResult.columns.length > 0 && testResult.rows.length > 0 && (
              <div className="space-y-1">
                <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Variable output</span>
                <div className="overflow-x-auto rounded-lg border border-border">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border bg-muted/50">
                        {testResult.columns.map((col) => (
                          <th
                            key={col}
                            className="px-3 py-2 text-left font-medium text-muted-foreground"
                          >
                            <div>{col}</div>
                            {queryCode && (
                              <div className="font-mono font-normal text-[9px] text-primary/70 mt-0.5">
                                {`{{ custom.${queryCode}.${col} }}`}
                              </div>
                            )}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {testResult.rows.map((row, ri) => (
                        <tr
                          key={ri}
                          className="border-b border-border last:border-0"
                        >
                          {testResult.columns.map((col) => (
                            <td
                              key={col}
                              className="px-3 py-2 text-foreground font-mono"
                            >
                              {row[col] ?? <span className="text-muted-foreground italic">null</span>}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            {testResult.success && testResult.rows.length === 0 && (
              <p className="text-xs text-muted-foreground italic">
                Query returned 0 rows
              </p>
            )}
          </div>
        )}
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  if (loading) return <TabSpinner />;
  if (error) return <TabError message={error} />;

  // Classify var keys
  const userVarKeys = varKeys.filter((k) => k.is_user_defined);
  const systemVarKeys = varKeys.filter((k) => !k.is_user_defined);
  const queryMap = Object.fromEntries(queries.map((q) => [q.id, q.name]));

  return (
    <div className="space-y-6 pt-4">
      {/* ── Section: Static & Custom Variable Keys ── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
              Variable Keys
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Define global variables that templates can use with{" "}
              <span className="font-mono text-foreground">{`{{ variable.code }}`}</span>
              . Static = fixed value. Query = fetched from DB at send time.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5 text-xs shrink-0"
            onClick={() => setShowVarKeyCreate(!showVarKeyCreate)}
          >
            {showVarKeyCreate ? (
              <X className="h-3.5 w-3.5" />
            ) : (
              <Plus className="h-3.5 w-3.5" />
            )}
            {showVarKeyCreate ? "Cancel" : "Add Variable"}
          </Button>
        </div>

        {showVarKeyCreate && (
          <form
            onSubmit={handleVkCreate}
            className="rounded-xl border border-border bg-background p-4 space-y-3"
          >
            <h4 className="text-xs font-semibold text-foreground">
              New Variable Key
            </h4>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <FormField
                label="Code"
                value={vkCode}
                onChange={setVkCode}
                placeholder="e.g. platform.company"
                required
              />
              <FormField
                label="Name"
                value={vkName}
                onChange={setVkName}
                placeholder="e.g. Company Name"
                required
              />
            </div>
            <FormTextarea
              label="Description"
              value={vkDesc}
              onChange={setVkDesc}
              placeholder="What this variable represents"
              rows={1}
            />
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-muted-foreground">
                Resolution Type
              </Label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setVkSource("static")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium border transition-colors ${vkSource === "static" ? "bg-primary text-primary-foreground border-primary" : "bg-background text-muted-foreground border-border hover:border-foreground/30"}`}
                >
                  Static (fixed value)
                </button>
                <button
                  type="button"
                  onClick={() => setVkSource("custom_query")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium border transition-colors ${vkSource === "custom_query" ? "bg-primary text-primary-foreground border-primary" : "bg-background text-muted-foreground border-border hover:border-foreground/30"}`}
                >
                  Query (from DB)
                </button>
              </div>
            </div>
            {vkSource === "static" ? (
              <FormField
                label="Static Value"
                value={vkStaticValue}
                onChange={setVkStaticValue}
                placeholder="e.g. Kreesalis"
                required
              />
            ) : (
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-muted-foreground">
                  Variable Query
                </Label>
                <select
                  value={vkQueryId}
                  onChange={(e) => setVkQueryId(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">Select a query...</option>
                  {queries.map((q) => (
                    <option key={q.id} value={q.id}>
                      {q.name} ({q.code})
                    </option>
                  ))}
                </select>
              </div>
            )}
            {vkCreateError && <InlineError message={vkCreateError} />}
            <Button
              type="submit"
              size="sm"
              className="h-7 text-xs"
              disabled={vkCreating}
            >
              {vkCreating ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
              ) : (
                <Plus className="h-3.5 w-3.5 mr-1" />
              )}
              Create
            </Button>
          </form>
        )}

        {/* User-defined variable keys */}
        {userVarKeys.length > 0 && (
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-3 py-2 bg-muted/20 border-b border-border">
              <span className="text-xs font-semibold text-foreground">
                Custom Variables ({userVarKeys.length})
              </span>
            </div>
            <div className="divide-y divide-border/50">
              {userVarKeys.map((k) => (
                <div key={k.code} className="px-3 py-2">
                  {vkEditCode === k.code ? (
                    <div className="space-y-2">
                      <FormField
                        label="Name"
                        value={vkEditName}
                        onChange={setVkEditName}
                        placeholder="Display name"
                      />
                      {vkEditSource === "static" ? (
                        <FormField
                          label="Static Value"
                          value={vkEditValue}
                          onChange={setVkEditValue}
                          placeholder="Value"
                        />
                      ) : (
                        <div className="space-y-1.5">
                          <Label className="text-xs font-medium text-muted-foreground">
                            Variable Query
                          </Label>
                          <select
                            value={vkEditQueryId}
                            onChange={(e) => setVkEditQueryId(e.target.value)}
                            className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs outline-none focus:ring-1 focus:ring-ring"
                          >
                            <option value="">Select a query...</option>
                            {queries.map((q) => (
                              <option key={q.id} value={q.id}>
                                {q.name} ({q.code})
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                      {vkEditError && <InlineError message={vkEditError} />}
                      <div className="flex gap-2">
                        <Button
                          type="button"
                          size="sm"
                          className="h-7 text-xs"
                          onClick={() => handleVkSaveEdit(k.code)}
                          disabled={vkSaving}
                        >
                          {vkSaving ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Save className="h-3.5 w-3.5" />
                          )}{" "}
                          Save
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs"
                          onClick={() => setVkEditCode(null)}
                        >
                          <X className="h-3.5 w-3.5" /> Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-xs text-foreground">{`{{ ${k.code} }}`}</span>
                          <span
                            className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium border ${k.resolution_source === "static"
                              ? "bg-blue-500/10 text-blue-600 border-blue-500/20"
                              : "bg-purple-500/10 text-purple-600 border-purple-500/20"
                              }`}
                          >
                            {k.resolution_source === "static"
                              ? "static"
                              : "query"}
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {k.resolution_source === "static" ? (
                            <span className="font-mono text-green-600 dark:text-green-400">
                              "{k.static_value}"
                            </span>
                          ) : (
                            <span>
                              {queryMap[k.query_id ?? ""] ?? k.query_id}
                            </span>
                          )}
                          {k.name && k.name !== k.code && (
                            <span className="ml-2 text-muted-foreground">
                              — {k.name}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-1 shrink-0">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          onClick={() => {
                            setVkEditCode(k.code);
                            setVkEditName(k.name ?? "");
                            setVkEditSource(k.resolution_source);
                            setVkEditValue(k.static_value ?? "");
                            setVkEditQueryId(k.query_id ?? "");
                            setVkEditError(null);
                          }}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-red-500 hover:text-red-600 hover:bg-red-500/10"
                          onClick={() => handleVkDelete(k.code)}
                          disabled={vkDeleting === k.code}
                        >
                          {vkDeleting === k.code ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Trash2 className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {userVarKeys.length === 0 && !showVarKeyCreate && (
          <div className="rounded-xl border border-dashed border-border p-6 text-center">
            <p className="text-xs text-muted-foreground">
              No custom variable keys yet. Click <strong>Add Variable</strong>{" "}
              to define static values or link to a query.
            </p>
          </div>
        )}

        {/* System variable keys (collapsible) */}
        <button
          type="button"
          onClick={() => setShowAllVarKeys(!showAllVarKeys)}
          className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1.5"
        >
          <ChevronDown
            className={`h-3 w-3 transition-transform ${showAllVarKeys ? "rotate-180" : ""}`}
          />
          {showAllVarKeys ? "Hide" : "Show"} {systemVarKeys.length}{" "}
          system-defined variable keys
        </button>
        {showAllVarKeys && (
          <div className="rounded-xl border border-border bg-muted/10 overflow-hidden max-h-64 overflow-y-auto">
            <div className="divide-y divide-border/50">
              {systemVarKeys.map((k) => (
                <div
                  key={k.code}
                  className="px-3 py-1.5 flex items-center gap-2"
                >
                  <span className="font-mono text-xs text-foreground w-40 truncate shrink-0">{`{{ ${k.code} }}`}</span>
                  <span className="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium bg-green-500/10 text-green-600 border border-green-500/20">
                    {k.resolution_source}
                  </span>
                  <span className="text-xs text-muted-foreground truncate">
                    {k.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      <div className="border-t border-border" />
      {/* ── Section: Variable Queries (SQL-based) ── */}
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
              Variable Queries
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              SQL queries that fetch dynamic values at notification send time.
            </p>
          </div>
          <Button
            variant="default"
            size="sm"
            className="h-8 gap-1.5 text-xs"
            onClick={() => {
              setShowCreate(!showCreate);
              if (!showCreate) resetCreateForm();
            }}
          >
            <Plus className="h-3.5 w-3.5" />
            New Query
          </Button>
        </div>

        {/* Create form */}
        {showCreate && (
          <form
            onSubmit={handleCreate}
            className="space-y-4 rounded-xl border border-border bg-background p-4"
          >
            <h4 className="text-sm font-semibold text-foreground">
              Create Variable Query
            </h4>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField
                label="Code"
                value={createCode}
                onChange={setCreateCode}
                placeholder="e.g. org_active_users"
                required
              />
              <FormField
                label="Name"
                value={createName}
                onChange={setCreateName}
                placeholder="e.g. Org Active Users"
                required
              />
            </div>
            <FormTextarea
              label="Description"
              value={createDesc}
              onChange={setCreateDesc}
              placeholder="Optional description"
              rows={2}
            />
            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-muted-foreground">
                SQL Template
              </Label>
              <BindParamToolbar editorContainerRef={createEditorRef} />
              <div ref={createEditorRef}>
                <SqlEditor
                  value={createSql}
                  onChange={setCreateSql}
                  schemaMetadata={schemaMetadata}
                  placeholderText="SELECT ... FROM ... WHERE user_id = $1"
                />
              </div>
              <p className="text-[10px] text-muted-foreground">
                Use $1, $2, ... for bind parameters. Must be a SELECT statement.
                Autocomplete available for tables and columns.
              </p>
            </div>

            <BindParamsEditor
              params={createBindParams}
              setParams={setCreateBindParams}
            />
            <ResultColumnsEditor
              cols={createResultCols}
              setCols={setCreateResultCols}
            />

            <FormField
              label="Timeout (ms)"
              value={createTimeout}
              onChange={setCreateTimeout}
              type="number"
              placeholder="3000"
            />

            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-muted-foreground">
                Linked Audit Events (Optional)
              </Label>
              <select
                multiple
                value={createLinkedEvents}
                onChange={(e) => {
                  const opts = Array.from(e.target.selectedOptions).map(o => o.value);
                  setCreateLinkedEvents(opts);
                }}
                className="w-full h-32 rounded-lg border border-border bg-background px-3 py-2 text-xs outline-none focus:ring-1 focus:ring-ring"
              >
                {auditEventTypes.map((et) => (
                  <option key={`${et.event_category}.${et.event_type}`} value={et.event_type}>
                    {et.event_type} ({et.entity_type})
                  </option>
                ))}
              </select>
              <p className="text-[10px] text-muted-foreground">
                Hold CMD/CTRL to select multiple. These tell the system which events this query can be safely used for.
              </p>
            </div>

            <AuditContextExplorer
              onApplyQuery={(sql, params, cols) => {
                setCreateSql(sql);
                setCreateBindParams(params);
                setCreateResultCols(cols);
              }}
            />

            <TestPanel
              bindParams={createBindParams}
              onRun={handleTestNew}
              queryCode={createCode || undefined}
            />

            {createError && <InlineError message={createError} />}
            <div className="flex items-center gap-2">
              <Button
                type="submit"
                size="sm"
                className="h-8 gap-1.5 text-xs"
                disabled={creating}
              >
                {creating ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Save className="h-3.5 w-3.5" />
                )}
                Create
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-8 gap-1.5 text-xs"
                onClick={() => {
                  setShowCreate(false);
                  resetCreateForm();
                }}
              >
                <X className="h-3.5 w-3.5" /> Cancel
              </Button>
            </div>
          </form>
        )}

        {/* List */}
        {queries.length === 0 ? (
          <EmptyState
            icon={<Database className="h-6 w-6 text-muted-foreground" />}
            label="No variable queries yet"
          />
        ) : (
          <div className="space-y-2">
            {queries.map((q) => (
              <div
                key={q.id}
                className="rounded-xl border border-border bg-background"
              >
                {/* Summary row */}
                <button
                  type="button"
                  className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/30"
                  onClick={() => handleExpand(q)}
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                    <Database className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-foreground">
                        {q.name}
                      </span>
                      <InlineBadge
                        label={q.code}
                        className="bg-muted text-muted-foreground border-border font-mono"
                      />
                      {q.is_system && (
                        <InlineBadge
                          label="System"
                          className="bg-purple-500/10 text-purple-500 border-purple-500/20"
                        />
                      )}
                      <InlineBadge
                        label={`${q.result_columns.length} col${q.result_columns.length !== 1 ? "s" : ""}`}
                        className="bg-blue-500/10 text-blue-500 border-blue-500/20"
                      />
                      <StatusChip
                        label={q.is_active ? "Active" : "Inactive"}
                        active={q.is_active}
                      />
                    </div>
                    {q.description && (
                      <p className="text-xs text-muted-foreground line-clamp-1">
                        {q.description}
                      </p>
                    )}
                    {q.variable_keys.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {q.variable_keys.map((vk) => (
                          <span
                            key={vk}
                            className="inline-flex items-center rounded-md border border-border bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground"
                          >
                            {vk}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  {expandedId === q.id ? (
                    <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                </button>

                {/* Expanded edit panel */}
                {expandedId === q.id && (
                  <div className="border-t border-border px-4 py-4 space-y-4">
                    {q.is_system && (
                      <div className="flex items-center gap-2 rounded-lg border border-purple-500/20 bg-purple-500/5 px-3 py-2">
                        <span className="text-xs text-purple-500">
                          System query — SQL, bind params, and result columns
                          are read-only. Clone to customize.
                        </span>
                        <div className="flex-1" />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="h-7 gap-1.5 text-xs"
                          onClick={() => {
                            setShowCreate(true);
                            setCreateCode(q.code + "_custom");
                            setCreateName(q.name + " (Custom)");
                            setCreateDesc(q.description ?? "");
                            setCreateSql(q.sql_template);
                            setCreateBindParams([...q.bind_params]);
                            setCreateResultCols([...q.result_columns]);
                            setCreateTimeout(String(q.timeout_ms));
                            setExpandedId(null);
                            resetTestState();
                          }}
                        >
                          <Copy className="h-3 w-3" /> Clone
                        </Button>
                      </div>
                    )}
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      <FormField
                        label="Name"
                        value={editName}
                        onChange={setEditName}
                        required
                      />
                      <FormField
                        label="Timeout (ms)"
                        value={editTimeout}
                        onChange={setEditTimeout}
                        type="number"
                      />
                    </div>
                    <FormTextarea
                      label="Description"
                      value={editDesc}
                      onChange={setEditDesc}
                      rows={2}
                    />
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-muted-foreground">
                        SQL Template{" "}
                        {q.is_system && (
                          <span className="text-purple-500">(read-only)</span>
                        )}
                      </Label>
                      {!q.is_system && (
                        <BindParamToolbar editorContainerRef={editEditorRef} />
                      )}
                      <div ref={editEditorRef}>
                        <SqlEditor
                          value={editSql}
                          onChange={setEditSql}
                          schemaMetadata={schemaMetadata}
                          readOnly={q.is_system}
                        />
                      </div>
                      <p className="text-[10px] text-muted-foreground">
                        Use $1, $2, ... for bind parameters. Must be a SELECT
                        statement.
                      </p>
                    </div>

                    {q.is_system ? (
                      <>
                        <div className="space-y-2">
                          <Label className="text-xs font-medium text-muted-foreground">
                            Bind Parameters{" "}
                            <span className="text-purple-500">(read-only)</span>
                          </Label>
                          {editBindParams.map((bp, idx) => (
                            <div
                              key={idx}
                              className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2 opacity-70"
                            >
                              <span className="text-xs font-mono text-muted-foreground">
                                ${bp.position}
                              </span>
                              <span className="text-xs">{bp.key}</span>
                              <InlineBadge
                                label={bp.source}
                                className="bg-muted text-muted-foreground border-border"
                              />
                              {bp.required && (
                                <InlineBadge
                                  label="required"
                                  className="bg-amber-500/10 text-amber-500 border-amber-500/20"
                                />
                              )}
                            </div>
                          ))}
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs font-medium text-muted-foreground">
                            Result Columns{" "}
                            <span className="text-purple-500">(read-only)</span>
                          </Label>
                          {editResultCols.map((col, idx) => (
                            <div
                              key={idx}
                              className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2 opacity-70"
                            >
                              <span className="text-xs font-mono">
                                {col.name}
                              </span>
                              <InlineBadge
                                label={col.data_type}
                                className="bg-muted text-muted-foreground border-border"
                              />
                            </div>
                          ))}
                        </div>
                      </>
                    ) : (
                      <>
                        <BindParamsEditor
                          params={editBindParams}
                          setParams={setEditBindParams}
                        />
                        <ResultColumnsEditor
                          cols={editResultCols}
                          setCols={setEditResultCols}
                        />
                      </>
                    )}

                    <div className="space-y-1.5 pt-2">
                      <Label className="text-xs font-medium text-muted-foreground">
                        Linked Audit Events (Optional)
                      </Label>
                      <select
                        multiple
                        value={editLinkedEvents}
                        onChange={(e) => {
                          const opts = Array.from(e.target.selectedOptions).map(o => o.value);
                          setEditLinkedEvents(opts);
                        }}
                        className="w-full h-32 rounded-lg border border-border bg-background px-3 py-2 text-xs outline-none focus:ring-1 focus:ring-ring"
                      >
                        {auditEventTypes.map((et) => (
                          <option key={`${et.event_category}.${et.event_type}`} value={et.event_type}>
                            {et.event_type} ({et.entity_type})
                          </option>
                        ))}
                      </select>
                      <p className="text-[10px] text-muted-foreground">
                        Hold CMD/CTRL to select multiple. These tell the system which events this query can be safely used for.
                      </p>
                    </div>

                    <div className="flex items-center gap-3 pt-2">
                      <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <input
                          type="checkbox"
                          checked={editActive}
                          onChange={(e) => setEditActive(e.target.checked)}
                          className="h-3.5 w-3.5"
                        />
                        Active
                      </label>
                    </div>

                    <TestPanel
                      bindParams={editBindParams}
                      onRun={handleTestExisting}
                      queryCode={queries.find((q) => q.id === expandedId)?.code}
                    />

                    {editError && <InlineError message={editError} />}
                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        size="sm"
                        className="h-8 gap-1.5 text-xs"
                        onClick={handleSaveEdit}
                        disabled={saving}
                      >
                        {saving ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Save className="h-3.5 w-3.5" />
                        )}
                        Save
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-8 gap-1.5 text-xs"
                        onClick={() => {
                          setExpandedId(null);
                          resetTestState();
                        }}
                      >
                        <X className="h-3.5 w-3.5" /> Cancel
                      </Button>
                      <div className="flex-1" />
                      {!q.is_system && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-8 gap-1.5 text-xs text-red-500 hover:text-red-600 hover:bg-red-500/10"
                          onClick={() => handleDelete(q.id)}
                          disabled={deleting}
                        >
                          {deleting ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                          )}
                          Delete
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>{" "}
      {/* end Variable Queries section */}
    </div>
  );
}

// ── Tab definitions ────────────────────────────────────────────────────────

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "overview", label: "Overview", icon: <Bell className="h-3.5 w-3.5" /> },
  {
    id: "templates",
    label: "Templates",
    icon: <FileText className="h-3.5 w-3.5" />,
  },
  {
    id: "variable-queries",
    label: "Variable Queries",
    icon: <Database className="h-3.5 w-3.5" />,
  },
  {
    id: "announcements",
    label: "Announcements",
    icon: <Megaphone className="h-3.5 w-3.5" />,
  },
  {
    id: "queue",
    label: "Queue",
    icon: <MousePointer className="h-3.5 w-3.5" />,
  },
  {
    id: "reports",
    label: "Reports",
    icon: <Monitor className="h-3.5 w-3.5" />,
  },
  {
    id: "send-test",
    label: "Send Test",
    icon: <Send className="h-3.5 w-3.5" />,
  },
];

// ── Page ───────────────────────────────────────────────────────────────────

export default function NotificationsAdminPage() {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [mountedTabs, setMountedTabs] = useState<Set<TabId>>(
    new Set(["overview"])
  );

  function handleTabChange(tab: TabId) {
    setActiveTab(tab);
    setMountedTabs((prev) => new Set([...prev, tab]));
  }

  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start gap-4">
        <div className="rounded-xl bg-primary/10 p-3 shrink-0">
          <Bell className="h-6 w-6 text-primary" />
        </div>
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">
            Notifications Admin
          </h2>
          <p className="text-sm text-muted-foreground">
            Manage channels, templates, broadcasts, releases, incidents,
            delivery queue, reports, and send test notifications.
          </p>
        </div>
      </div>

      {/* ── Tab pills ──────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-1.5 rounded-xl border border-border bg-muted/30 p-1.5">
        {TABS.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? "default" : "ghost"}
            size="sm"
            className={`h-8 gap-1.5 rounded-lg text-xs font-medium transition-all ${activeTab === tab.id
              ? ""
              : "text-muted-foreground hover:text-foreground"
              }`}
            onClick={() => handleTabChange(tab.id)}
          >
            {tab.icon}
            {tab.label}
          </Button>
        ))}
      </div>

      {/* ── Tab content — mount-once, show/hide to avoid re-fetching ──── */}
      <div>
        {mountedTabs.has("overview") && (
          <div className={activeTab === "overview" ? undefined : "hidden"}>
            <OverviewTab />
          </div>
        )}
        {mountedTabs.has("templates") && (
          <div className={activeTab === "templates" ? undefined : "hidden"}>
            <TemplatesTab />
          </div>
        )}
        {mountedTabs.has("variable-queries") && (
          <div
            className={activeTab === "variable-queries" ? undefined : "hidden"}
          >
            <VariableQueriesTab />
          </div>
        )}
        {mountedTabs.has("announcements") && (
          <div className={activeTab === "announcements" ? undefined : "hidden"}>
            <AnnouncementsTab />
          </div>
        )}
        {mountedTabs.has("queue") && (
          <div className={activeTab === "queue" ? undefined : "hidden"}>
            <DeliveryQueueTab />
          </div>
        )}
        {mountedTabs.has("reports") && (
          <div className={activeTab === "reports" ? undefined : "hidden"}>
            <ReportsTab />
          </div>
        )}
        {mountedTabs.has("send-test") && (
          <div className={activeTab === "send-test" ? undefined : "hidden"}>
            <SendTestTab />
          </div>
        )}
      </div>
    </div>
  );
}
