"use client";

import Link from "next/link";
import { useState } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { usePasswordResetRequest } from "@/features/auth/hooks/use-auth";

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-elevated)",
  border: "1px solid var(--border)",
  borderRadius: "6px",
  padding: "9px 12px",
  fontSize: "13px",
  color: "var(--text-primary)",
  outline: "none",
  transition: "border-color 0.15s, box-shadow 0.15s",
  fontFamily: "var(--font-sans)",
};

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [focused, setFocused] = useState(false);
  const request = usePasswordResetRequest();

  return (
    <AuthShell
      title="Reset your password"
      subtitle="Enter your email and we'll send a reset link if that account exists."
    >
      {sent ? (
        <div
          className="flex flex-col gap-3 rounded animate-fade-in"
          style={{
            background: "var(--success-muted)",
            border: "1px solid var(--success)",
            padding: "16px",
          }}
          data-testid="forgot-password-sent"
        >
          {/* Icon row */}
          <div className="flex items-center gap-2">
            <div
              className="flex h-7 w-7 items-center justify-center rounded-full text-sm"
              style={{ background: "rgba(0,196,122,0.15)", color: "var(--success)" }}
              aria-hidden
            >
              ✓
            </div>
            <p
              className="text-sm font-semibold"
              style={{ color: "var(--success)" }}
            >
              Check your inbox
            </p>
          </div>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            If that email is registered, a reset link is on its way. The link expires in{" "}
            <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>15 minutes</span>.
          </p>
          <button
            type="button"
            onClick={() => setSent(false)}
            style={{
              alignSelf: "flex-start",
              marginTop: "2px",
              background: "none",
              border: "none",
              padding: 0,
              fontSize: "11px",
              color: "var(--success)",
              cursor: "pointer",
              textDecoration: "underline",
              fontFamily: "var(--font-sans)",
            }}
          >
            Send another link
          </button>
        </div>
      ) : (
        <form
          className="flex flex-col gap-4"
          data-testid="forgot-password-form"
          onSubmit={async (e) => {
            e.preventDefault();
            await request.mutateAsync({ email }, { onSuccess: () => setSent(true) });
          }}
        >
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="forgot-email"
              className="label-caps"
              style={{ color: "var(--text-secondary)" }}
            >
              Email address
            </label>
            <input
              id="forgot-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              style={{
                ...inputStyle,
                borderColor: focused ? "var(--accent)" : "var(--border)",
                boxShadow: focused ? "0 0 0 3px var(--accent-muted)" : "none",
              }}
              placeholder="you@company.com"
              data-testid="forgot-password-email"
            />
          </div>

          {request.error ? (
            <div
              className="flex items-center gap-2 rounded px-3 py-2 text-xs"
              style={{
                background: "var(--danger-muted)",
                border: "1px solid var(--danger)",
                color: "var(--danger)",
              }}
              data-testid="forgot-password-error"
            >
              <span>⚠</span>
              {request.error.message}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={request.isPending}
            data-testid="forgot-password-submit"
            style={{
              marginTop: "2px",
              background: request.isPending ? "var(--accent-dim)" : "var(--accent)",
              color: "white",
              border: "none",
              borderRadius: "6px",
              padding: "10px 16px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: request.isPending ? "not-allowed" : "pointer",
              opacity: request.isPending ? 0.7 : 1,
              transition: "background 0.15s, opacity 0.15s",
              fontFamily: "var(--font-sans)",
              letterSpacing: "0.01em",
            }}
          >
            {request.isPending ? "Sending…" : "Send reset link"}
          </button>
        </form>
      )}

      <div className="mt-6">
        <Link
          href="/auth/signin"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "12px",
            color: "var(--text-secondary)",
            textDecoration: "none",
            transition: "color 0.15s",
          }}
          data-testid="back-to-signin"
        >
          <span style={{ color: "var(--text-muted)" }}>←</span>
          Back to sign in
        </Link>
      </div>
    </AuthShell>
  );
}
