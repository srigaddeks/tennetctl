"use client";

import { useRef, useState } from "react";

import {
  useInAppNotifications,
  useUnreadCount,
} from "@/features/notify/hooks/use-in-app-notifications";
import { NotificationList } from "@/features/notify/_components/notification-list";
import { useOnClickOutside } from "@/lib/use-on-click-outside";

type Props = {
  userId: string;
  orgId: string | null;
};

export function NotificationBell({ userId, orgId }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const notifs = useInAppNotifications(userId, orgId);
  const unread = useUnreadCount(userId, orgId);

  useOnClickOutside(ref, () => setOpen(false));

  const items = notifs.data?.items ?? [];

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        aria-label="Notifications"
        data-testid="notification-bell"
        onClick={() => setOpen((o) => !o)}
        className="relative flex h-8 w-8 items-center justify-center rounded-md text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-100"
      >
        <BellIcon />
        {unread > 0 && (
          <span
            className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-blue-600 px-0.5 text-[10px] font-bold text-white"
            data-testid="notification-badge"
          >
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          className="absolute right-0 top-full z-50 mt-1 w-80 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-lg dark:border-zinc-800 dark:bg-zinc-950"
          data-testid="notification-panel"
        >
          <NotificationList items={items} onClose={() => setOpen(false)} />
        </div>
      )}
    </div>
  );
}

function BellIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
    </svg>
  );
}
