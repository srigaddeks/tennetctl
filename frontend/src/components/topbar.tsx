"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { FEATURES, activeFeature } from "@/config/features";
import { useMe, useSignout } from "@/features/auth/hooks/use-auth";
import { NotificationBell } from "@/features/notify/_components/notification-bell";
import { CriticalBanner } from "@/features/notify/_components/notification-list";
import { useInAppNotifications } from "@/features/notify/hooks/use-in-app-notifications";
import { cn } from "@/lib/cn";

export function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const current = activeFeature(pathname);
  const me = useMe();
  const signout = useSignout();
  const user = me.data?.user ?? null;
  const session = me.data?.session ?? null;

  // In-app notifications — only fetched when authenticated
  const notifs = useInAppNotifications(
    user?.id ?? null,
    session?.org_id ?? null,
  );
  const inAppItems = notifs.data?.items ?? [];

  return (
    <>
      <CriticalBanner items={inAppItems} />
      <header className="flex h-14 shrink-0 items-center gap-6 border-b border-zinc-200 bg-white px-5 dark:border-zinc-800 dark:bg-zinc-950">
        <Link href="/" className="flex items-center gap-2" data-testid="topbar-logo">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-zinc-900 text-xs font-bold text-white dark:bg-zinc-100 dark:text-zinc-900">
            T
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold">TennetCTL</div>
            <div className="text-[10px] text-zinc-500 dark:text-zinc-400">
              v0.1 · self-hosted
            </div>
          </div>
        </Link>
        <nav className="flex items-center gap-1">
          {FEATURES.map((f) => {
            const active = f.key === current.key;
            const landing = f.subFeatures[0]?.href ?? f.basePath;
            return (
              <Link
                key={f.key}
                href={landing}
                data-testid={f.testId}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm transition",
                  active
                    ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                    : "text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-900",
                )}
              >
                {f.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          {user && (
            <NotificationBell userId={user.id} orgId={session?.org_id ?? null} />
          )}
          {user ? (
            <>
              <div className="flex items-center gap-2" data-testid="topbar-user">
                {user.avatar_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={user.avatar_url}
                    alt=""
                    className="h-7 w-7 rounded-full border border-zinc-200 object-cover dark:border-zinc-800"
                  />
                ) : (
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-200 text-xs font-semibold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200">
                    {(user.display_name ?? user.email ?? "?")
                      .slice(0, 1)
                      .toUpperCase()}
                  </div>
                )}
                <div className="leading-tight">
                  <div
                    className="text-xs font-semibold"
                    data-testid="topbar-user-name"
                  >
                    {user.display_name ?? user.email ?? "Anonymous"}
                  </div>
                  {user.email ? (
                    <div className="text-[10px] text-zinc-500 dark:text-zinc-400">
                      {user.email}
                    </div>
                  ) : null}
                </div>
              </div>
              <button
                type="button"
                data-testid="topbar-signout"
                disabled={signout.isPending}
                className="rounded-md border border-zinc-200 px-2 py-1 text-xs font-medium transition hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
                onClick={async () => {
                  await signout.mutateAsync();
                  router.replace("/auth/signin");
                }}
              >
                {signout.isPending ? "…" : "Sign out"}
              </button>
            </>
          ) : (
            <Link
              href="/auth/signin"
              data-testid="topbar-signin"
              className="rounded-md border border-zinc-200 px-3 py-1 text-xs font-medium hover:bg-zinc-100 dark:border-zinc-800 dark:hover:bg-zinc-900"
            >
              Sign in
            </Link>
          )}
        </div>
      </header>
    </>
  );
}
