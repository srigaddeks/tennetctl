"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { OAuthButtons } from "@/features/auth/_components/oauth-buttons";
import { useSignup } from "@/features/auth/hooks/use-auth";

const inputStyle = {
  width: "100%",
  background: "var(--bg-elevated)",
  border: "1px solid var(--border)",
  borderRadius: "6px",
  padding: "9px 12px",
  fontSize: "13px",
  color: "var(--text-primary)",
  outline: "none",
  transition: "border-color 0.15s",
  fontFamily: "var(--font-sans)",
} as const;

export function SignUpForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/";
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [focusedField, setFocusedField] = useState<string | null>(null);
  const signup = useSignup();

  function fieldStyle(name: string) {
    return {
      ...inputStyle,
      borderColor: focusedField === name ? "var(--accent)" : "var(--border)",
      boxShadow: focusedField === name ? "0 0 0 3px var(--accent-muted)" : "none",
    };
  }

  return (
    <>
      <form
        className="flex flex-col gap-4"
        data-testid="signup-form"
        onSubmit={async (e) => {
          e.preventDefault();
          await signup.mutateAsync(
            { email, display_name: displayName, password },
            { onSuccess: () => router.replace(next) }
          );
        }}
      >
        {/* Display name */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="signup-display-name"
            className="label-caps"
            style={{ color: "var(--text-secondary)" }}
          >
            Display name
          </label>
          <input
            id="signup-display-name"
            type="text"
            required
            minLength={1}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            onFocus={() => setFocusedField("displayName")}
            onBlur={() => setFocusedField(null)}
            style={fieldStyle("displayName")}
            placeholder="Jane Smith"
            data-testid="signup-display-name"
          />
        </div>

        {/* Email */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="signup-email"
            className="label-caps"
            style={{ color: "var(--text-secondary)" }}
          >
            Email address
          </label>
          <input
            id="signup-email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onFocus={() => setFocusedField("email")}
            onBlur={() => setFocusedField(null)}
            style={fieldStyle("email")}
            placeholder="you@company.com"
            data-testid="signup-email"
          />
        </div>

        {/* Password */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="signup-password"
            className="label-caps"
            style={{ color: "var(--text-secondary)" }}
          >
            Password
            <span
              className="ml-2 normal-case"
              style={{ color: "var(--text-muted)", fontSize: "10px", letterSpacing: "0" }}
            >
              min. 8 characters
            </span>
          </label>
          <input
            id="signup-password"
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
            data-testid="signup-password"
          />
        </div>

        {signup.error ? (
          <div
            className="flex items-center gap-2 rounded px-3 py-2 text-xs"
            style={{
              background: "var(--danger-muted)",
              border: "1px solid var(--danger)",
              color: "var(--danger)",
            }}
            data-testid="signup-error"
          >
            <span>⚠</span>
            {signup.error.message}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={signup.isPending}
          data-testid="signup-submit"
          style={{
            marginTop: "4px",
            background: signup.isPending ? "var(--accent-dim)" : "var(--accent)",
            color: "white",
            border: "none",
            borderRadius: "6px",
            padding: "10px 16px",
            fontSize: "13px",
            fontWeight: 600,
            cursor: signup.isPending ? "not-allowed" : "pointer",
            opacity: signup.isPending ? 0.7 : 1,
            transition: "background 0.15s, opacity 0.15s",
            fontFamily: "var(--font-sans)",
            letterSpacing: "0.01em",
          }}
        >
          {signup.isPending ? "Creating account…" : "Create account"}
        </button>
      </form>

      {/* Divider */}
      <div className="my-5 flex items-center gap-3">
        <div className="h-px flex-1" style={{ background: "var(--border)" }} />
        <span
          className="label-caps"
          style={{ color: "var(--text-muted)" }}
        >
          or
        </span>
        <div className="h-px flex-1" style={{ background: "var(--border)" }} />
      </div>

      <OAuthButtons />

      <p
        className="mt-6 text-center text-xs"
        style={{ color: "var(--text-muted)" }}
      >
        Already have an account?{" "}
        <Link
          href={`/auth/signin${next !== "/" ? `?next=${encodeURIComponent(next)}` : ""}`}
          style={{ color: "var(--accent)", textDecoration: "none", fontWeight: 500 }}
          data-testid="signup-to-signin"
        >
          Sign in
        </Link>
      </p>
    </>
  );
}
