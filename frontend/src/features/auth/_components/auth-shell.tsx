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
    <main
      className="relative flex min-h-dvh items-center justify-center px-4 py-12 overflow-hidden"
      style={{ background: "var(--bg-base)" }}
    >
      {/* Background grid */}
      <div
        className="absolute inset-0 bg-grid-dots opacity-30 pointer-events-none"
        aria-hidden
      />

      {/* Radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 60% 50% at 50% 0%, rgba(45,126,247,0.06) 0%, transparent 100%)",
        }}
        aria-hidden
      />

      <div className="relative w-full max-w-sm animate-slide-up">
        {/* Logo */}
        <Link
          href="/"
          className="mb-8 flex items-center gap-3 group"
          data-testid="auth-logo"
        >
          <div
            className="flex h-9 w-9 items-center justify-center rounded text-sm font-bold tracking-widest transition-all duration-200 group-hover:shadow-[0_0_16px_rgba(45,126,247,0.5)]"
            style={{
              background: "var(--accent)",
              color: "white",
              fontFamily: "var(--font-mono)",
            }}
          >
            T
          </div>
          <div className="leading-tight">
            <div
              className="text-[15px] font-semibold tracking-wide"
              style={{ color: "var(--text-primary)" }}
            >
              TennetCTL
            </div>
            <div
              className="text-[9px] tracking-widest uppercase"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              v0.1 · self-hosted
            </div>
          </div>
        </Link>

        {/* Card */}
        <div
          className="rounded border px-7 py-6"
          style={{
            background: "var(--bg-surface)",
            borderColor: "var(--border)",
            boxShadow: "0 0 40px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.02)",
          }}
        >
          {/* Header */}
          <div className="mb-6">
            <div
              className="h-px w-8 rounded-full mb-3"
              style={{ background: "var(--accent)" }}
              aria-hidden
            />
            <h1
              className="text-lg font-semibold tracking-wide"
              style={{ color: "var(--text-primary)" }}
              data-testid="auth-title"
            >
              {title}
            </h1>
            <p
              className="mt-1 text-[12px] leading-relaxed"
              style={{ color: "var(--text-muted)" }}
            >
              {subtitle}
            </p>
          </div>

          {children}
        </div>

        {footer ? (
          <div
            className="mt-4 text-center text-[12px]"
            style={{ color: "var(--text-muted)" }}
          >
            {footer}
          </div>
        ) : null}
      </div>
    </main>
  );
}
