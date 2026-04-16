"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
} from "@kcontrol/ui";
import {
  AlertCircle,
  Bell,
  BellRing,
  BellOff,
  History,
  ChevronLeft,
  ChevronRight,
  Mail,
  Inbox,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  ExternalLink,
  Filter,
  Monitor,
  ShieldAlert,
  Sparkles,
  CircleCheck,
} from "lucide-react";
import Link from "next/link";
import {
  listMyNotificationPreferences,
  setNotificationPreference,
  listNotificationHistory,
  sendTestWebPush,
} from "@/lib/api/notifications";
import { useWebPush } from "@/lib/hooks/useWebPush";
import { getNotificationConfig } from "@/lib/api/admin";
import type {
  NotificationConfigResponse,
  NotificationTypeResponse,
} from "@/lib/types/admin";
import type { NotificationPreference, NotificationHistoryItem } from "@/lib/api/notifications";

type TabId = "preferences" | "history";

// ── Web Push Card ─────────────────────────────────────────────────────────────

function WebPushCard() {
  const { state, loading, error, subscribe, unsubscribe } = useWebPush();
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  if (state === "unsupported") return null;

  async function handleTest() {
    setTestLoading(true);
    setTestResult(null);
    try {
      const res = await sendTestWebPush("/notifications");
      setTestResult({ success: true, message: res.message || "Test notification sent — check your browser!" });
    } catch (e) {
      setTestResult({ success: false, message: e instanceof Error ? e.message : "Failed to send test" });
    } finally {
      setTestLoading(false);
    }
  }

  // ── Prompt state: ask for permission ─────────────────────────────────────
  if (state === "prompt") {
    return (
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 ring-1 ring-primary/20">
              <Bell className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-foreground">Enable desktop notifications</p>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                Get instant alerts for security events, task assignments, and important updates — right in your browser. Your browser will ask you to confirm.
              </p>
              <div className="flex items-center gap-3 mt-4 flex-wrap">
                <Button
                  size="sm"
                  disabled={loading}
                  onClick={subscribe}
                  className="gap-2 h-8"
                >
                  <BellRing className="h-3.5 w-3.5" />
                  {loading ? "Requesting permission…" : "Allow notifications"}
                </Button>
                <div className="flex items-center gap-3 text-[11px] text-muted-foreground/70">
                  {["Real-time alerts", "Security events", "Deep links"].map((f) => (
                    <span key={f} className="flex items-center gap-1">
                      <CircleCheck className="h-3 w-3 text-primary/60" />
                      {f}
                    </span>
                  ))}
                </div>
              </div>
              {error && (
                <div className="mt-3 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
                  <p className="text-xs text-red-500">{error}</p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // ── Denied state: browser blocked ─────────────────────────────────────────
  if (state === "denied") {
    return (
      <Card className="border-amber-500/20 bg-amber-500/5">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 ring-1 ring-amber-500/20">
              <ShieldAlert className="h-5 w-5 text-amber-500" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-foreground">Notifications blocked by browser</p>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                You previously denied notification permission. To re-enable:
              </p>
              <ol className="mt-2 space-y-1">
                {[
                  "Click the lock icon (or info icon) in your browser's address bar",
                  'Find "Notifications" and change it to "Allow"',
                  "Refresh this page, then click Allow notifications",
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <span className="mt-px flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-600">{i + 1}</span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // ── Subscribed state ──────────────────────────────────────────────────────
  return (
    <Card className="border-emerald-500/20 bg-emerald-500/5">
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 ring-1 ring-emerald-500/20">
            <BellRing className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-sm font-semibold text-foreground">Desktop notifications active</p>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 border border-emerald-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              This browser will receive real-time push notifications with deep links.
            </p>
            <div className="flex items-center gap-2 mt-4 flex-wrap">
              <Button
                size="sm"
                variant="outline"
                disabled={testLoading}
                onClick={handleTest}
                className="h-8 gap-2 text-xs"
              >
                <Sparkles className="h-3.5 w-3.5" />
                {testLoading ? "Sending…" : "Send test notification"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={loading}
                onClick={unsubscribe}
                className="h-8 gap-2 text-xs text-muted-foreground hover:text-red-500 hover:bg-red-500/10"
              >
                <BellOff className="h-3.5 w-3.5" />
                {loading ? "Disabling…" : "Disable"}
              </Button>
            </div>
            {testResult && (
              <div className={`mt-3 flex items-center gap-2 rounded-lg border px-3 py-2 ${testResult.success ? "border-emerald-500/20 bg-emerald-500/10" : "border-red-500/20 bg-red-500/10"}`}>
                {testResult.success
                  ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-500" />
                  : <AlertCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
                }
                <p className={`text-xs ${testResult.success ? "text-emerald-600" : "text-red-500"}`}>{testResult.message}</p>
              </div>
            )}
            {error && (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2">
                <AlertCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
                <p className="text-xs text-red-500">{error}</p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Toggle ──────────────────────────────────────────────────────────────────

function Toggle({
  checked,
  onChange,
  disabled,
}: {
  checked: boolean;
  onChange: (val: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 ${
        checked ? "bg-primary" : "bg-muted"
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
          checked ? "translate-x-4" : "translate-x-0"
        }`}
      />
    </button>
  );
}

// ── Channel badge ────────────────────────────────────────────────────────────

function ChannelBadge({ channel }: { channel: string }) {
  const cls =
    channel === "email" ? "bg-blue-500/10 text-blue-500 border-blue-500/20" :
    channel === "in_app" ? "bg-purple-500/10 text-purple-500 border-purple-500/20" :
    channel === "sms" ? "bg-green-500/10 text-green-500 border-green-500/20" :
    "bg-muted text-muted-foreground border-border";
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium capitalize ${cls}`}>
      {channel === "email" ? <Mail className="h-2.5 w-2.5" /> : <Inbox className="h-2.5 w-2.5" />}
      {channel.replace("_", " ")}
    </span>
  );
}

// ── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "sent" || status === "delivered" ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" :
    status === "failed" ? "bg-red-500/10 text-red-500 border-red-500/20" :
    "bg-muted text-muted-foreground border-border";
  const Icon = status === "sent" || status === "delivered" ? CheckCircle2 : status === "failed" ? XCircle : Clock;
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium capitalize ${cls}`}>
      <Icon className="h-2.5 w-2.5" />
      {status}
    </span>
  );
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

// ── Preferences Tab ──────────────────────────────────────────────────────────

function PreferencesTab() {
  const [config, setConfig] = useState<NotificationConfigResponse | null>(null);
  const [preferences, setPreferences] = useState<NotificationPreference[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cfg, prefs] = await Promise.all([
        getNotificationConfig() as Promise<NotificationConfigResponse>,
        listMyNotificationPreferences(),
      ]);
      setConfig(cfg);
      setPreferences(prefs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load notification settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function getPreference(typeCode: string, channelCode: string): boolean | null {
    const pref = preferences.find(
      (p) => p.notification_type_code === typeCode && p.channel_code === channelCode
    );
    return pref ? pref.is_enabled : null;
  }

  async function handleToggle(typeCode: string, channelCode: string, type: NotificationTypeResponse) {
    if (type.is_mandatory) return;
    const key = `${typeCode}::${channelCode}`;
    const current = getPreference(typeCode, channelCode);
    const nextValue = current === null ? !type.default_enabled : !current;
    setToggling(key);
    try {
      await setNotificationPreference(typeCode, channelCode, nextValue);
      setPreferences((prev) => {
        const existing = prev.find(
          (p) => p.notification_type_code === typeCode && p.channel_code === channelCode
        );
        if (existing) {
          return prev.map((p) =>
            p.notification_type_code === typeCode && p.channel_code === channelCode
              ? { ...p, is_enabled: nextValue }
              : p
          );
        }
        return [...prev, { id: key, notification_type_code: typeCode, channel_code: channelCode, is_enabled: nextValue }];
      });
    } catch {
      await load();
    } finally {
      setToggling(null);
    }
  }

  const typesByCategory = config
    ? config.categories.map((cat) => ({
        category: cat,
        types: config.types.filter((t) => t.category_code === cat.code),
      })).filter((g) => g.types.length > 0)
    : [];

  const availableChannels = config?.channels.filter((c) => c.is_available) ?? [];

  if (loading) return (
    <div className="space-y-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="h-32 rounded-xl bg-muted animate-pulse" />
      ))}
    </div>
  );

  if (error) return (
    <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
      <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
      <p className="text-sm text-red-500">{error}</p>
    </div>
  );

  if (!config) return null;

  if (typesByCategory.length === 0) return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card py-16 gap-3 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
        <Bell className="h-6 w-6 text-muted-foreground" />
      </div>
      <p className="text-sm text-muted-foreground">No notification types configured.</p>
    </div>
  );

  return (
    <div className="space-y-6">
      {typesByCategory.map(({ category, types }) => (
        <Card key={category.id}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              {category.name}
              {category.is_mandatory && (
                <span className="inline-flex items-center rounded-md border border-amber-500/20 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-500">
                  Required
                </span>
              )}
            </CardTitle>
            {category.description && (
              <CardDescription>{category.description}</CardDescription>
            )}
          </CardHeader>
          <CardContent className="p-0">
            <div className="border-t border-border">
              {availableChannels.length > 0 && (
                <div className="flex items-center border-b border-border bg-muted/30 px-4 py-2">
                  <div className="flex-1 text-xs font-medium text-muted-foreground">Notification</div>
                  {availableChannels.map((ch) => (
                    <div key={ch.id} className="w-20 text-center text-xs font-medium text-muted-foreground capitalize">
                      {ch.name}
                    </div>
                  ))}
                </div>
              )}
              {types.map((type, i) => {
                const isLast = i === types.length - 1;
                return (
                  <div
                    key={type.id}
                    className={`flex items-center gap-4 px-4 py-3 ${!isLast ? "border-b border-border" : ""}`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground">{type.name}</p>
                      {type.description && (
                        <p className="text-xs text-muted-foreground mt-0.5">{type.description}</p>
                      )}
                    </div>
                    {availableChannels.map((ch) => {
                      const key = `${type.code}::${ch.code}`;
                      const prefValue = getPreference(type.code, ch.code);
                      const effective = prefValue !== null ? prefValue : type.default_enabled;
                      const isToggling = toggling === key;
                      return (
                        <div key={ch.id} className="w-20 flex justify-center">
                          {type.is_mandatory ? (
                            <Toggle checked={true} onChange={() => {}} disabled />
                          ) : (
                            <Toggle
                              checked={effective}
                              onChange={() => handleToggle(type.code, ch.code, type)}
                              disabled={isToggling}
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ── History Tab ──────────────────────────────────────────────────────────────

const HISTORY_PAGE_SIZE = 20;

const HISTORY_CATEGORY_LABELS: Record<string, string> = {
  security: "Security",
  transactional: "Transactional",
  system: "System",
  org: "Organization",
  workspace: "Workspace",
  engagement: "Engagement",
  marketing: "Marketing",
  product_updates: "Product Updates",
};

function HistoryTab() {
  const [items, setItems] = useState<NotificationHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);
  const [filterChannel, setFilterChannel] = useState<string | undefined>(undefined);

  const load = useCallback(async (p: number) => {
    setLoading(true); setError(null);
    try {
      const res = await listNotificationHistory({ limit: HISTORY_PAGE_SIZE, offset: p * HISTORY_PAGE_SIZE });
      setItems(res.items); setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load notification history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(page); }, [load, page]);

  // Client-side filter on top of loaded page
  const filteredItems = items.filter((item) => {
    if (filterStatus === "unread" && item.read_at) return false;
    if (filterStatus === "read" && !item.read_at) return false;
    if (filterStatus === "sent" && item.status !== "sent" && item.status !== "delivered") return false;
    if (filterStatus === "failed" && item.status !== "failed") return false;
    if (filterChannel && item.channel_code !== filterChannel) return false;
    return true;
  });

  // Counts for filter pills
  const unreadCount = items.filter((i) => !i.read_at).length;
  const failedCount = items.filter((i) => i.status === "failed").length;
  const channelCounts: Record<string, number> = {};
  for (const item of items) channelCounts[item.channel_code] = (channelCounts[item.channel_code] ?? 0) + 1;
  const activeChannels = Object.keys(channelCounts).filter((ch) => channelCounts[ch] > 0);

  const totalPages = Math.ceil(total / HISTORY_PAGE_SIZE);
  const from = page * HISTORY_PAGE_SIZE + 1;
  const to = Math.min((page + 1) * HISTORY_PAGE_SIZE, total);

  function FilterPill({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
    return (
      <button
        onClick={onClick}
        className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
          active ? "bg-primary text-primary-foreground border-primary" : "bg-muted text-muted-foreground border-transparent hover:bg-muted/80"
        }`}
      >{children}</button>
    );
  }

  if (loading) return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-14 rounded-xl bg-muted animate-pulse" />
      ))}
    </div>
  );

  if (error) return (
    <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
      <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
      <p className="text-sm text-red-500">{error}</p>
    </div>
  );

  return (
    <div className="space-y-3">
      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap rounded-lg border border-border bg-muted/20 px-3 py-2">
        <Filter className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        <FilterPill active={!filterStatus} onClick={() => setFilterStatus(undefined)}>All</FilterPill>
        {unreadCount > 0 && <FilterPill active={filterStatus === "unread"} onClick={() => setFilterStatus("unread")}>Unread ({unreadCount})</FilterPill>}
        <FilterPill active={filterStatus === "read"} onClick={() => setFilterStatus("read")}>Read</FilterPill>
        <FilterPill active={filterStatus === "sent"} onClick={() => setFilterStatus("sent")}>Delivered</FilterPill>
        {failedCount > 0 && <FilterPill active={filterStatus === "failed"} onClick={() => setFilterStatus("failed")}>Failed ({failedCount})</FilterPill>}
        {activeChannels.length > 1 && (
          <>
            <span className="h-4 w-px bg-border mx-1" />
            <FilterPill active={!filterChannel} onClick={() => setFilterChannel(undefined)}>All channels</FilterPill>
            {activeChannels.map((ch) => (
              <FilterPill key={ch} active={filterChannel === ch} onClick={() => setFilterChannel(ch)}>
                {ch.replace("_", " ")} ({channelCounts[ch]})
              </FilterPill>
            ))}
          </>
        )}
      </div>

      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          <span className="font-semibold text-foreground">{filteredItems.length}</span>
          {filteredItems.length !== total && <span className="text-muted-foreground/60"> of {total}</span>}
          {" "}notification{total !== 1 ? "s" : ""}
        </p>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => load(page)} title="Refresh">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {filteredItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card py-16 gap-3 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
            <History className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium text-foreground">
            {total === 0 ? "No notifications yet" : "No results for this filter"}
          </p>
          <p className="text-xs text-muted-foreground">
            {total === 0 ? "Your notification history will appear here." : "Try clearing your filters."}
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-border overflow-hidden">
          {filteredItems.map((item, i) => (
            <div
              key={item.id}
              className={`flex items-center gap-3 px-4 py-3 bg-card hover:bg-muted/20 transition-colors ${
                i < filteredItems.length - 1 ? "border-b border-border" : ""
              } ${!item.read_at ? "border-l-2 border-l-primary" : ""}`}
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted shrink-0">
                {item.channel_code === "email" ? (
                  <Mail className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Inbox className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-foreground truncate">
                    {item.subject || item.notification_type_code.replace(/_/g, " ")}
                  </span>
                  {!item.read_at && (
                    <span className="inline-flex items-center rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary border border-primary/20">
                      New
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[11px] text-muted-foreground/60">{fmtDate(item.sent_at)}</span>
                  {item.read_at && (
                    <span className="text-[11px] text-muted-foreground/40">· read {fmtDate(item.read_at)}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <ChannelBadge channel={item.channel_code} />
                <StatusBadge status={item.status} />
              </div>
            </div>
          ))}
        </div>
      )}

      {total > HISTORY_PAGE_SIZE && (
        <div className="flex items-center justify-between pt-1">
          <p className="text-xs text-muted-foreground/60">{from}–{to} of {total}</p>
          <div className="flex items-center gap-1.5">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)} className="h-7 text-xs gap-1">
              <ChevronLeft className="h-3 w-3" />Prev
            </Button>
            <span className="text-xs text-muted-foreground/50 tabular-nums">{page + 1}/{totalPages}</span>
            <Button variant="outline" size="sm" disabled={page + 1 >= totalPages} onClick={() => setPage((p) => p + 1)} className="h-7 text-xs gap-1">
              Next<ChevronRight className="h-3 w-3" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function NotificationsSettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("preferences");

  return (
    <div className="w-full space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">Notifications</h2>
          <p className="text-sm text-muted-foreground">
            Manage how you receive notifications and review your notification history.
          </p>
        </div>
        <Link
          href="/notifications"
          className="shrink-0 hidden sm:inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 shadow-sm transition-colors"
        >
          <Mail className="h-3.5 w-3.5" />
          View inbox
        </Link>
      </div>

      {/* Mobile view inbox button above tabs */}
      <div className="flex justify-end p-1 sm:hidden">
        <Link
          href="/notifications"
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 shadow-sm transition-colors"
        >
          <Mail className="h-3.5 w-3.5" />
          View inbox
        </Link>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-border">
        {([
          { id: "preferences" as const, label: "Preferences", icon: Bell },
          { id: "history" as const,     label: "History",     icon: History },
        ]).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground/60 hover:text-foreground"
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "preferences" && (
        <>
          <WebPushCard />
          <PreferencesTab />
        </>
      )}
      {activeTab === "history" && <HistoryTab />}
    </div>
  );
}
