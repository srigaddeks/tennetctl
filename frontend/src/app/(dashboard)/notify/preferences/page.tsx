"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { ErrorState, Skeleton } from "@/components/ui";
import { useMe } from "@/features/auth/hooks/use-auth";
import {
  useNotifyPreferences,
  useUpdatePreferences,
} from "@/features/notify/hooks/use-notify-preferences";
import {
  notificationPermission,
  useDisableWebPush,
  useEnableWebPush,
  useWebPushSubscriptions,
  webPushSupported,
} from "@/features/notify/hooks/use-webpush";
import type { NotifyChannelCode, NotifyCategoryCode } from "@/types/api";

// Column order: channels across the top
const CHANNELS: { code: NotifyChannelCode; label: string; disabled?: boolean }[] = [
  { code: "email",   label: "Email" },
  { code: "webpush", label: "Web Push" },
  { code: "in_app",  label: "In-App" },
  { code: "sms",     label: "SMS", disabled: true },
];

// Row order: categories down the side
const CATEGORIES: {
  code: NotifyCategoryCode;
  label: string;
  description: string;
}[] = [
  {
    code: "transactional",
    label: "Transactional",
    description: "Account actions — sign-in, API key rotation, password reset.",
  },
  {
    code: "critical",
    label: "Critical",
    description: "Security alerts. Always delivered — cannot be opted out.",
  },
  {
    code: "marketing",
    label: "Marketing",
    description: "Product announcements and promotional content.",
  },
  {
    code: "digest",
    label: "Digest",
    description: "Batched daily or weekly summaries.",
  },
];

type GridKey = `${NotifyChannelCode}:${NotifyCategoryCode}`;

function gridKey(ch: NotifyChannelCode, cat: NotifyCategoryCode): GridKey {
  return `${ch}:${cat}`;
}

export default function NotificationPreferencesPage() {
  const me = useMe();
  const user = me.data?.user ?? null;
  const session = me.data?.session ?? null;

  const userId = user?.id ?? null;
  const orgId = session?.org_id ?? null;

  const { data: prefs, isLoading, isError, error } = useNotifyPreferences(userId, orgId);
  const updateMutation = useUpdatePreferences(userId, orgId);

  // Local optimistic state: map from "channel:category" → is_opted_in
  const [localState, setLocalState] = useState<Map<GridKey, boolean>>(new Map());
  const [saving, setSaving] = useState<Set<GridKey>>(new Set());

  // Sync remote data into local state on load
  useEffect(() => {
    if (!prefs) return;
    setLocalState(
      new Map(prefs.map((p) => [gridKey(p.channel_code, p.category_code), p.is_opted_in])),
    );
  }, [prefs]);

  function getCurrent(ch: NotifyChannelCode, cat: NotifyCategoryCode): boolean {
    const key = gridKey(ch, cat);
    return localState.get(key) ?? true;
  }

  function isLocked(cat: NotifyCategoryCode): boolean {
    return cat === "critical";
  }

  async function toggle(ch: NotifyChannelCode, cat: NotifyCategoryCode) {
    if (isLocked(cat)) return;
    const key = gridKey(ch, cat);
    const current = getCurrent(ch, cat);
    const next = !current;

    // Optimistic update
    setLocalState((prev) => new Map(prev).set(key, next));
    setSaving((prev) => new Set(prev).add(key));

    try {
      await updateMutation.mutateAsync([
        { channel_code: ch, category_code: cat, is_opted_in: next },
      ]);
    } catch {
      // Rollback on error
      setLocalState((prev) => new Map(prev).set(key, current));
    } finally {
      setSaving((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  }

  return (
    <>
      <PageHeader
        title="Notification Preferences"
        description="Choose which notifications you receive on each channel. Critical security alerts cannot be disabled."
        testId="heading-notify-preferences"
      />

      <div
        className="flex-1 overflow-y-auto"
        style={{ padding: "24px 32px" }}
        data-testid="notify-preferences-body"
      >
        <div
          className="mb-5 flex items-start gap-2 rounded-md px-3 py-2 text-xs"
          style={{
            background: "var(--info-muted)",
            border: "1px solid var(--info)",
            color: "var(--text-secondary)",
          }}
          data-testid="notify-preferences-scope-banner"
        >
          <span style={{ color: "var(--info)", fontWeight: 600 }}>ⓘ</span>
          <span>
            Preferences apply per-user across all applications. Per-application
            overrides are not yet supported.
          </span>
        </div>

        <BrowserPushSection />

        {isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}

        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Failed to load preferences"}
          />
        )}

        {!isLoading && !isError && (
          <div
            style={{
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--bg-surface)",
              overflow: "hidden",
            }}
          >
            <table
              style={{ width: "100%", borderCollapse: "collapse" }}
              data-testid="preferences-grid"
            >
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  <th
                    style={{
                      padding: "12px 20px",
                      textAlign: "left",
                      fontSize: 10,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.07em",
                      color: "var(--text-muted)",
                      width: "40%",
                    }}
                  >
                    Category
                  </th>
                  {CHANNELS.map((ch) => (
                    <th
                      key={ch.code}
                      style={{
                        padding: "12px 16px",
                        textAlign: "center",
                        fontSize: 10,
                        fontWeight: 700,
                        textTransform: "uppercase",
                        letterSpacing: "0.07em",
                        color: ch.disabled ? "var(--text-muted)" : "var(--text-secondary)",
                        opacity: ch.disabled ? 0.5 : 1,
                      }}
                    >
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                        {ch.label}
                        {ch.disabled && (
                          <span
                            style={{
                              padding: "1px 6px",
                              borderRadius: 9999,
                              background: "var(--bg-elevated)",
                              fontSize: 9,
                              fontWeight: 600,
                              textTransform: "none",
                              letterSpacing: "0.03em",
                              color: "var(--text-muted)",
                              border: "1px solid var(--border)",
                            }}
                          >
                            Soon
                          </span>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CATEGORIES.map((cat, catIdx) => {
                  const locked = isLocked(cat.code);
                  return (
                    <tr
                      key={cat.code}
                      style={{
                        borderBottom: catIdx < CATEGORIES.length - 1 ? "1px solid var(--border)" : "none",
                        opacity: locked ? 0.75 : 1,
                      }}
                    >
                      <td style={{ padding: "16px 20px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <div
                            style={{
                              fontWeight: 600,
                              fontSize: 14,
                              color: "var(--text-primary)",
                            }}
                          >
                            {cat.label}
                          </div>
                          {locked && (
                            <span
                              style={{
                                padding: "2px 8px",
                                borderRadius: 9999,
                                background: "var(--warning-muted)",
                                border: "1px solid var(--warning)",
                                fontSize: 10,
                                fontWeight: 700,
                                color: "var(--warning)",
                                letterSpacing: "0.05em",
                                textTransform: "uppercase",
                              }}
                            >
                              Always on
                            </span>
                          )}
                        </div>
                        <div
                          style={{
                            marginTop: 3,
                            fontSize: 12,
                            color: "var(--text-muted)",
                          }}
                        >
                          {cat.description}
                        </div>
                      </td>
                      {CHANNELS.map((ch) => {
                        const key = gridKey(ch.code, cat.code);
                        const checked = locked ? true : getCurrent(ch.code, cat.code);
                        const isSaving = saving.has(key);
                        const channelDisabled = Boolean(ch.disabled);
                        const buttonDisabled = locked || isSaving || channelDisabled;

                        return (
                          <td key={ch.code} style={{ padding: "16px", textAlign: "center" }}>
                            <button
                              type="button"
                              role="switch"
                              aria-checked={channelDisabled ? false : checked}
                              aria-label={`${ch.label} ${cat.label}`}
                              disabled={buttonDisabled}
                              title={channelDisabled ? `${ch.label} delivery is not yet available.` : undefined}
                              data-testid={`pref-toggle-${ch.code}-${cat.code}`}
                              onClick={() => toggle(ch.code, cat.code)}
                              style={{
                                position: "relative",
                                display: "inline-flex",
                                width: 36,
                                height: 20,
                                borderRadius: 10,
                                background: channelDisabled
                                  ? "var(--bg-elevated)"
                                  : checked
                                  ? "var(--accent)"
                                  : "var(--border-bright)",
                                border: "none",
                                cursor: buttonDisabled ? "not-allowed" : "pointer",
                                opacity: buttonDisabled ? 0.5 : 1,
                                transition: "background 0.2s",
                                outline: "none",
                                alignItems: "center",
                              }}
                            >
                              <span
                                style={{
                                  position: "absolute",
                                  left: checked ? "calc(100% - 18px)" : 2,
                                  width: 16,
                                  height: 16,
                                  borderRadius: "50%",
                                  background: channelDisabled ? "var(--border)" : "#ffffff",
                                  transition: "left 0.2s",
                                  boxShadow: "0 1px 3px rgba(0,0,0,0.4)",
                                }}
                              />
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

function BrowserPushSection() {
  const [mounted, setMounted] = useState(false);
  const [supported, setSupported] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>("default");

  useEffect(() => {
    setMounted(true);
    setSupported(webPushSupported());
    setPermission(notificationPermission());
  }, []);

  const { data: subs, isLoading } = useWebPushSubscriptions();
  const enable = useEnableWebPush();
  const disable = useDisableWebPush();

  const subscriptions = subs?.subscriptions ?? [];
  const hasActive = subscriptions.length > 0;

  return (
    <section
      style={{
        marginBottom: 24,
        borderRadius: 8,
        border: "1px solid var(--border)",
        background: "var(--bg-surface)",
        padding: 20,
      }}
      data-testid="browser-push-section"
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 16,
        }}
      >
        <div style={{ flex: 1 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 6,
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1C4.69 1 2 3.69 2 7v3.5L1 12h14l-1-1.5V7c0-3.31-2.69-6-6-6z" stroke="var(--info)" strokeWidth="1.2"/>
              <path d="M6 12a2 2 0 004 0" stroke="var(--info)" strokeWidth="1.2"/>
            </svg>
            <h2
              style={{
                fontSize: 14,
                fontWeight: 600,
                color: "var(--text-primary)",
              }}
            >
              Browser Push Notifications
            </h2>
            {mounted && hasActive && (
              <span
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  fontSize: 11,
                  color: "var(--success)",
                  fontWeight: 600,
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "var(--success)",
                  }}
                />
                Active
              </span>
            )}
          </div>
          <p style={{ fontSize: 12, color: "var(--text-muted)", maxWidth: 540, lineHeight: 1.5 }}>
            Allow TennetCTL to push notifications to this browser so you see them
            even when the app is not open. Bell-icon notifications inside the app
            keep working regardless of this setting.
          </p>
          {mounted && !supported && (
            <p
              style={{
                marginTop: 8,
                fontSize: 12,
                color: "var(--warning)",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 1L1 10h10L6 1z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
                <path d="M6 5v2.5M6 9h.01" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              This browser does not support web push.
            </p>
          )}
          {mounted && supported && permission === "denied" && (
            <p
              style={{
                marginTop: 8,
                fontSize: 12,
                color: "var(--warning)",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 1L1 10h10L6 1z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
                <path d="M6 5v2.5M6 9h.01" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              Permission is blocked. Re-enable notifications for this site in browser settings, then retry.
            </p>
          )}
          <p
            style={{
              marginTop: 8,
              fontSize: 11,
              color: "var(--text-muted)",
              opacity: 0.7,
            }}
          >
            iOS: add TennetCTL to your home screen first (Safari → Share → Add to Home Screen) — Apple only allows push from installed web apps.
          </p>
          {enable.error && (
            <p
              style={{ marginTop: 8, fontSize: 12, color: "var(--danger)" }}
              data-testid="webpush-enable-error"
            >
              {enable.error.message}
            </p>
          )}
        </div>
        <div style={{ flexShrink: 0 }}>
          {mounted && supported && !hasActive && (
            <button
              type="button"
              disabled={enable.isPending || permission === "denied"}
              onClick={() => enable.mutate(undefined)}
              data-testid="webpush-enable"
              style={{
                padding: "8px 14px",
                borderRadius: 6,
                background: "var(--accent)",
                color: "#ffffff",
                fontSize: 12,
                fontWeight: 600,
                border: "none",
                cursor: enable.isPending || permission === "denied" ? "not-allowed" : "pointer",
                opacity: enable.isPending || permission === "denied" ? 0.5 : 1,
                transition: "opacity 0.15s",
              }}
            >
              {enable.isPending ? "Enabling…" : "Enable browser push"}
            </button>
          )}
        </div>
      </div>

      {mounted && isLoading && supported ? (
        <p style={{ marginTop: 16, fontSize: 12, color: "var(--text-muted)" }}>Loading devices…</p>
      ) : mounted && hasActive ? (
        <div
          style={{
            marginTop: 16,
            borderRadius: 6,
            border: "1px solid var(--border)",
            overflow: "hidden",
          }}
        >
          {subscriptions.map((s, i) => (
            <div
              key={s.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "10px 14px",
                borderBottom: i < subscriptions.length - 1 ? "1px solid var(--border)" : "none",
                background: "var(--bg-elevated)",
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: "var(--text-primary)",
                  }}
                >
                  {s.device_label ?? "Browser"}
                </div>
                <div
                  style={{
                    marginTop: 2,
                    fontSize: 11,
                    color: "var(--text-muted)",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    fontFamily: "'IBM Plex Mono', monospace",
                  }}
                >
                  {new URL(s.endpoint).host}
                </div>
              </div>
              <button
                type="button"
                data-testid={`webpush-disable-${s.id}`}
                disabled={disable.isPending}
                onClick={() => disable.mutate(s.id)}
                style={{
                  fontSize: 12,
                  fontWeight: 500,
                  color: "var(--danger)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  opacity: disable.isPending ? 0.5 : 1,
                }}
              >
                Disable
              </button>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
