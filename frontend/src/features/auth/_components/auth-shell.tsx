import Link from "next/link";

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-zinc-50 px-4 py-12 dark:bg-zinc-950">
      <div className="w-full max-w-sm">
        <Link href="/" className="mb-10 flex items-center gap-2" data-testid="auth-logo">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-sm font-bold text-white dark:bg-zinc-100 dark:text-zinc-900">
            T
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold">TennetCTL</div>
            <div className="text-[10px] text-zinc-500 dark:text-zinc-400">v0.1 · self-hosted</div>
          </div>
        </Link>
        <h1 className="text-xl font-semibold" data-testid="auth-title">{title}</h1>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{subtitle}</p>
        <div className="mt-8">{children}</div>
        {footer ? <div className="mt-6 text-sm text-zinc-600 dark:text-zinc-400">{footer}</div> : null}
      </div>
    </main>
  );
}
