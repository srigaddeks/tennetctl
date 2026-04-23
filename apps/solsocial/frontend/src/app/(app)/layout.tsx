"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useMe } from "@/features/auth/use-auth";
import { getToken, setToken } from "@/lib/api";
import { Wordmark } from "@/components/sun-mark";

const NAV = [
  { href: "/",          label: "Front", short: "Front" },
  { href: "/composer",  label: "Compose" },
  { href: "/posts",     label: "Posts" },
  { href: "/queue",     label: "Queue" },
  { href: "/calendar",  label: "Calendar" },
  { href: "/ideas",     label: "Ideas" },
  { href: "/channels",  label: "Channels" },
];

function formatToday() {
  const d = new Date();
  return d.toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric", year: "numeric",
  });
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const path = usePathname();
  const me = useMe();

  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => { if (mounted && !getToken()) router.replace("/signin"); }, [mounted, router]);
  useEffect(() => { if (me.isError) router.replace("/signin"); }, [me.isError, router]);

  // SSR + first client tick render an empty shell so hydration sees the same
  // markup (localStorage isn't available on the server).
  if (!mounted) return <div className="min-h-screen relative z-10" />;
  if (!getToken()) return null;

  const user = me.data?.user;
  const session = me.data?.session;

  return (
    <div className="min-h-screen relative z-10">
      {/* Masthead */}
      <header className="px-8 pt-8 pb-4">
        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline gap-6">
            <Link href="/"><Wordmark /></Link>
            <span className="kicker hidden md:inline" suppressHydrationWarning>
              vol. i · issue i · {formatToday()}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden md:block">
              <div className="mono text-[11px] text-[color:var(--ink-40)]">
                ws · <span className="text-[color:var(--ink-70)]">{session?.workspace_id?.slice(0, 8) ?? "—"}</span>
              </div>
              <div className="text-[12px]">{user?.display_name ?? user?.email ?? "…"}</div>
            </div>
            <button
              onClick={() => { setToken(null); router.push("/signin"); }}
              className="btn-ghost"
              title="Sign out"
            >
              sign out
            </button>
          </div>
        </div>
        <div className="mt-5 h-px bg-[color:var(--ink)]" />
        <div className="mt-[2px] h-px bg-[color:var(--ink)] opacity-60" />
      </header>

      {/* Nav */}
      <nav className="px-8 pt-3 pb-6 border-b border-[color:var(--rule)]">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          {NAV.map(item => {
            const active = path === item.href;
            return (
              <Link
                key={item.href} href={item.href}
                className="relative py-1 text-[14px] text-[color:var(--ink-70)] hover:text-[color:var(--ink)] transition"
              >
                <span className={active ? "text-[color:var(--ink)] font-medium" : ""}>
                  {item.label}
                </span>
                {active && (
                  <span className="absolute left-0 right-0 -bottom-[7px] h-[2px] bg-[color:var(--ember)]" />
                )}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Page content */}
      <main className="px-8 py-10">{children}</main>

      {/* Footer */}
      <footer className="px-8 py-10 border-t border-[color:var(--rule)] mt-16">
        <div className="flex items-center justify-between">
          <span className="kicker">© {new Date().getFullYear()} · solsocial · an almanac for your feed</span>
          <span className="mono text-[10px] text-[color:var(--ink-40)]">hand-set in fraunces &amp; ibm plex · published on tennetctl</span>
        </div>
      </footer>
    </div>
  );
}
