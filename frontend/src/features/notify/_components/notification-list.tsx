"use client";

import { useMarkRead } from "@/features/notify/hooks/use-in-app-notifications";
import { cn } from "@/lib/cn";
import type { InAppDelivery } from "@/types/api";

type Props = {
  items: InAppDelivery[];
  onClose: () => void;
};

const PRIORITY_BADGE: Record<string, string> = {
  critical: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400",
  high: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400",
  normal: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400",
  low: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

function NotificationItem({
  delivery,
  onRead,
}: {
  delivery: InAppDelivery;
  onRead: (id: string) => void;
}) {
  const isUnread = !["opened", "clicked", "failed", "unsubscribed"].includes(
    delivery.status_code,
  );
  const vars = delivery.resolved_variables as Record<string, string>;
  const title = vars.subject ?? vars.title ?? "Notification";
  const body = vars.body ?? vars.message ?? "";

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg p-3 transition-colors",
        isUnread
          ? "bg-blue-50 dark:bg-blue-950/30"
          : "hover:bg-zinc-50 dark:hover:bg-zinc-900",
      )}
      data-testid={`notification-item-${delivery.id}`}
    >
      {isUnread && (
        <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue-500" />
      )}
      {!isUnread && <div className="mt-1.5 h-2 w-2 shrink-0" />}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
            {title}
          </span>
          <span
            className={cn(
              "shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
              PRIORITY_BADGE[delivery.priority_code] ?? PRIORITY_BADGE.normal,
            )}
          >
            {delivery.priority_code}
          </span>
        </div>
        {body && (
          <p className="mt-0.5 truncate text-xs text-zinc-500 dark:text-zinc-400">
            {body}
          </p>
        )}
        <p className="mt-1 text-[10px] text-zinc-400 dark:text-zinc-600">
          {new Date(delivery.created_at).toLocaleString()}
        </p>
      </div>
      {isUnread && (
        <button
          type="button"
          onClick={() => onRead(delivery.id)}
          className="shrink-0 rounded px-2 py-0.5 text-[10px] font-medium text-blue-600 hover:bg-blue-100 dark:text-blue-400 dark:hover:bg-blue-900/40"
          data-testid={`mark-read-${delivery.id}`}
        >
          Mark read
        </button>
      )}
    </div>
  );
}

export function NotificationList({ items, onClose }: Props) {
  const markRead = useMarkRead();

  const handleRead = (id: string) => {
    markRead.mutate(id);
  };

  if (items.length === 0) {
    return (
      <div className="px-4 py-8 text-center">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          No notifications
        </p>
      </div>
    );
  }

  return (
    <div className="flex max-h-[400px] flex-col overflow-y-auto">
      <div className="flex items-center justify-between border-b border-zinc-200 px-3 py-2 dark:border-zinc-800">
        <span className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Notifications
        </span>
        <button
          type="button"
          onClick={onClose}
          className="text-xs text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
        >
          Close
        </button>
      </div>
      <div className="divide-y divide-zinc-100 px-2 py-1 dark:divide-zinc-900">
        {items.map((d) => (
          <NotificationItem key={d.id} delivery={d} onRead={handleRead} />
        ))}
      </div>
    </div>
  );
}

/** Persistent banner for critical unread notifications. */
export function CriticalBanner({ items }: { items: InAppDelivery[] }) {
  const critical = items.filter(
    (d) =>
      d.priority_code === "critical" &&
      !["opened", "clicked", "failed", "unsubscribed"].includes(d.status_code),
  );
  const markRead = useMarkRead();

  if (critical.length === 0) return null;

  const first = critical[0];
  const vars = first.resolved_variables as Record<string, string>;
  const title = vars.subject ?? vars.title ?? "Critical Alert";

  return (
    <div
      className="flex items-center gap-3 bg-red-600 px-4 py-2 text-white dark:bg-red-700"
      data-testid="critical-banner"
      role="alert"
    >
      <span className="text-xs font-bold uppercase tracking-wide">
        Critical
      </span>
      <span className="flex-1 truncate text-sm font-medium">{title}</span>
      {critical.length > 1 && (
        <span className="shrink-0 text-xs text-red-200">
          +{critical.length - 1} more
        </span>
      )}
      <button
        type="button"
        onClick={() => markRead.mutate(first.id)}
        className="shrink-0 rounded bg-white/20 px-2 py-0.5 text-xs font-medium hover:bg-white/30"
        data-testid="critical-banner-dismiss"
      >
        Dismiss
      </button>
    </div>
  );
}
