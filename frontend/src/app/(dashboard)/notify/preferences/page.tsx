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
import { cn } from "@/lib/cn";
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

      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="notify-preferences-body">
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
          <div className="overflow-x-auto">
            <table
              className="w-full border-collapse text-sm"
              data-testid="preferences-grid"
            >
              <thead>
                <tr>
                  <th className="pb-3 pr-6 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                    Category
                  </th>
                  {CHANNELS.map((ch) => (
                    <th
                      key={ch.code}
                      className={cn(
                        "pb-3 pr-4 text-center text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400",
                        ch.disabled && "opacity-50",
                      )}
                    >
                      <div className="flex flex-col items-center gap-0.5">
                        {ch.label}
                        {ch.disabled && (
                          <span className="rounded-full bg-zinc-100 px-1.5 py-px text-[9px] font-medium normal-case tracking-normal text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                            Coming soon
                          </span>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {CATEGORIES.map((cat) => {
                  const locked = isLocked(cat.code);
                  return (
                    <tr key={cat.code} className={locked ? "opacity-70" : ""}>
                      <td className="py-4 pr-6">
                        <div className="font-medium text-zinc-900 dark:text-zinc-50">
                          {cat.label}
                          {locked && (
                            <span className="ml-2 rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
                              Always on
                            </span>
                          )}
                        </div>
                        <div className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">
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
                          <td key={ch.code} className="py-4 pr-4 text-center">
                            <button
                              type="button"
                              role="switch"
                              aria-checked={channelDisabled ? false : checked}
                              aria-label={`${ch.label} ${cat.label}`}
                              disabled={buttonDisabled}
                              title={channelDisabled ? `${ch.label} delivery is not yet available.` : undefined}
                              data-testid={`pref-toggle-${ch.code}-${cat.code}`}
                              onClick={() => toggle(ch.code, cat.code)}
                              className={cn(
                                "relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500",
                                channelDisabled
                                  ? "bg-zinc-200 dark:bg-zinc-800"
                                  : checked
                                  ? "bg-zinc-900 dark:bg-zinc-100"
                                  : "bg-zinc-200 dark:bg-zinc-700",
                                buttonDisabled && "cursor-not-allowed opacity-50",
                              )}
                            >
                              <span
                                className={cn(
                                  "inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform dark:bg-zinc-900",
                                  channelDisabled ? "translate-x-1" : checked ? "translate-x-4" : "translate-x-1",
                                )}
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
  // Defer capability + permission detection until mount so SSR and first client
  // render agree (typeof window === "undefined" flips after hydration).
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
      className="mb-6 rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="browser-push-section"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
            Browser push notifications
          </h2>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Allow TennetCTL to push notifications to this browser so you see them
            even when the app is not open. Bell-icon notifications inside the app
            keep working regardless of this setting.
          </p>
          {mounted && !supported && (
            <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
              This browser does not support web push.
            </p>
          )}
          {mounted && supported && permission === "denied" && (
            <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
              Permission is blocked. Re-enable notifications for this site in browser settings, then retry.
            </p>
          )}
          <p className="mt-2 text-[11px] text-zinc-500 dark:text-zinc-500">
            iOS: add TennetCTL to your home screen first (Safari → Share → Add to Home Screen) — Apple only allows push from installed web apps.
          </p>
          {enable.error && (
            <p className="mt-2 text-xs text-red-600" data-testid="webpush-enable-error">
              {enable.error.message}
            </p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {mounted && supported && !hasActive && (
            <button
              type="button"
              disabled={enable.isPending || permission === "denied"}
              onClick={() => enable.mutate(undefined)}
              data-testid="webpush-enable"
              className="rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {enable.isPending ? "Enabling…" : "Enable browser push"}
            </button>
          )}
        </div>
      </div>

      {mounted && isLoading && supported ? (
        <p className="mt-4 text-xs text-zinc-400">Loading devices…</p>
      ) : mounted && hasActive ? (
        <ul className="mt-4 divide-y divide-zinc-100 rounded-md border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
          {subscriptions.map((s) => (
            <li key={s.id} className="flex items-center justify-between px-4 py-3 text-xs">
              <div className="min-w-0">
                <div className="font-medium text-zinc-900 dark:text-zinc-50">
                  {s.device_label ?? "Browser"}
                </div>
                <div className="mt-0.5 truncate text-zinc-500 dark:text-zinc-400">
                  {new URL(s.endpoint).host}
                </div>
              </div>
              <button
                type="button"
                data-testid={`webpush-disable-${s.id}`}
                disabled={disable.isPending}
                onClick={() => disable.mutate(s.id)}
                className="text-red-600 hover:text-red-700 disabled:opacity-50"
              >
                Disable
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
