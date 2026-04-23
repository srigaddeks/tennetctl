"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { usePasswordResetComplete } from "@/features/auth/hooks/use-auth";

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

function PasswordResetForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [mismatch, setMismatch] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const complete = usePasswordResetComplete();

  function fieldStyle(name: string): React.CSSProperties {
    return {
      ...inputStyle,
      borderColor: focusedField === name ? "var(--accent)" : "var(--border)",
      boxShadow: focusedField === name ? "0 0 0 3px var(--accent-muted)" : "none",
    };
  }

  if (!token) {
    return (
      <div className="flex flex-col gap-4" data-testid="password-reset-no-token-state">
        <div
          className="flex flex-col gap-2 rounded px-4 py-3"
          style={{
            background: "var(--danger-muted)",
            border: "1px solid var(--danger)",
          }}
        >
          <p
            className="text-sm font-semibold"
            style={{ color: "var(--danger)" }}
            data-testid="password-reset-no-token"
          >
            Invalid or missing reset link
          </p>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            This link may have expired or already been used.
          </p>
        </div>
        <Link
          href="/auth/forgot-password"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "13px",
            color: "var(--accent)",
            textDecoration: "none",
            fontWeight: 500,
          }}
        >
          Request a new reset link →
        </Link>
      </div>
    );
  }

  return (
    <form
      className="flex flex-col gap-4"
      data-testid="password-reset-form"
      onSubmit={async (e) => {
        e.preventDefault();
        setMismatch(false);
        if (password !== confirm) {
          setMismatch(true);
          return;
        }
        await complete.mutateAsync(
          { token, new_password: password },
          { onSuccess: () => router.replace("/") }
        );
      }}
    >
      {/* Password strength hint */}
      <div
        className="flex items-center gap-2 rounded px-3 py-2 text-xs"
        style={{
          background: "var(--accent-muted)",
          border: "1px solid var(--accent-dim)",
          color: "var(--text-secondary)",
        }}
      >
        <span style={{ color: "var(--accent)" }}>🔒</span>
        Use at least 8 characters. Mix letters, numbers and symbols for a stronger password.
      </div>

      {/* New password */}
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="reset-new-password"
          className="label-caps"
          style={{ color: "var(--text-secondary)" }}
        >
          New password
        </label>
        <input
          id="reset-new-password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onFocus={() => setFocusedField("password")}
          onBlur={() => setFocusedField(null)}
          style={fieldStyle("password")}
          placeholder="············"
          data-testid="password-reset-new"
        />
      </div>

      {/* Confirm password */}
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="reset-confirm-password"
          className="label-caps"
          style={{ color: "var(--text-secondary)" }}
        >
          Confirm password
        </label>
        <input
          id="reset-confirm-password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          onFocus={() => setFocusedField("confirm")}
          onBlur={() => setFocusedField(null)}
          style={{
            ...fieldStyle("confirm"),
            borderColor: mismatch
              ? "var(--danger)"
              : focusedField === "confirm"
              ? "var(--accent)"
              : "var(--border)",
            boxShadow: mismatch
              ? "0 0 0 3px var(--danger-muted)"
              : focusedField === "confirm"
              ? "0 0 0 3px var(--accent-muted)"
              : "none",
          }}
          placeholder="············"
          data-testid="password-reset-confirm"
        />
      </div>

      {mismatch ? (
        <p
          className="text-xs"
          style={{ color: "var(--danger)" }}
          data-testid="password-reset-mismatch"
        >
          ⚠ Passwords do not match.
        </p>
      ) : null}

      {complete.error ? (
        <div
          className="flex items-center gap-2 rounded px-3 py-2 text-xs"
          style={{
            background: "var(--danger-muted)",
            border: "1px solid var(--danger)",
            color: "var(--danger)",
          }}
          data-testid="password-reset-error"
        >
          <span>⚠</span>
          {complete.error.message}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={complete.isPending}
        data-testid="password-reset-submit"
        style={{
          marginTop: "2px",
          background: complete.isPending ? "var(--accent-dim)" : "var(--accent)",
          color: "white",
          border: "none",
          borderRadius: "6px",
          padding: "10px 16px",
          fontSize: "13px",
          fontWeight: 600,
          cursor: complete.isPending ? "not-allowed" : "pointer",
          opacity: complete.isPending ? 0.7 : 1,
          transition: "background 0.15s, opacity 0.15s",
          fontFamily: "var(--font-sans)",
          letterSpacing: "0.01em",
        }}
      >
        {complete.isPending ? "Saving…" : "Set new password"}
      </button>
    </form>
  );
}

export default function PasswordResetPage() {
  return (
    <AuthShell
      title="Set new password"
      subtitle="Choose a strong password for your account."
    >
      <Suspense
        fallback={
          <div
            className="text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            Loading…
          </div>
        }
      >
        <PasswordResetForm />
      </Suspense>
    </AuthShell>
  );
}
