"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ApiEnvelope, AuthResponse } from "@/types/api";

function storeToken(token: string): void {
  if (typeof window !== "undefined") {
    try { window.localStorage.setItem("somaerp_token", token); } catch {}
  }
  document.cookie = `somaerp_token=${encodeURIComponent(token)}; path=/; max-age=604800; SameSite=Lax`;
}

export default function SignupPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const base = process.env.NEXT_PUBLIC_TENNETCTL_BACKEND ?? "http://localhost:51734";
      const res = await fetch(`${base}/v1/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: displayName, email, password }),
      });
      const data = (await res.json()) as ApiEnvelope<AuthResponse>;
      if (!data.ok) { setError(data.error?.message ?? "Sign up failed."); return; }
      storeToken(data.data.token);
      router.push("/");
    } catch {
      setError("Unable to reach the server. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-bg">
      {/* Left branded panel */}
      <div className="auth-panel-left">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 48 }}>
            <div style={{
              width: 32, height: 32,
              background: "var(--grey-900)",
              borderRadius: 6,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
              </svg>
            </div>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: 18, fontWeight: 500, color: "var(--grey-50)", letterSpacing: "-0.01em" }}>somaerp</span>
          </div>

          <h1 style={{ fontSize: 28, fontWeight: 700, color: "var(--grey-50)", lineHeight: 1.2, letterSpacing: "-0.02em", marginBottom: 12 }}>
            Built for the<br />4 AM shift.
          </h1>
          <p style={{ fontSize: 14, color: "var(--grey-400)", lineHeight: 1.6, marginBottom: 40 }}>
            Operational precision for food businesses — from raw materials to doorstep delivery.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[
              { icon: "⬡", label: "Multi-kitchen production tracking" },
              { icon: "◈", label: "Live BOM cost and inventory" },
              { icon: "◎", label: "Subscription + delivery management" },
            ].map(({ icon, label }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ color: "var(--grey-900)", fontSize: 16 }}>{icon}</span>
                <span style={{ fontSize: 13, color: "var(--grey-300)" }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ borderTop: "1px solid var(--grey-800)", paddingTop: 20 }}>
          <p style={{ fontFamily: "var(--font-heading)", fontSize: 11, color: "var(--grey-500)", letterSpacing: "0.04em" }}>
            POWERED BY TENNETCTL · v0.9.0
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="auth-panel-right">
        <div className="auth-card">
          <div style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
              Create account
            </h2>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>
              Get started with somaerp
            </p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="erp-form-group">
              <label className="erp-label" htmlFor="display-name">Display name</label>
              <input
                id="display-name"
                type="text"
                className="erp-input"
                value={displayName}
                onChange={e => setDisplayName(e.target.value)}
                required
                autoFocus
                autoComplete="name"
                placeholder="Your name"
              />
            </div>

            <div className="erp-form-group">
              <label className="erp-label" htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                className="erp-input"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="you@example.com"
              />
            </div>

            <div className="erp-form-group">
              <label className="erp-label" htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                className="erp-input"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
            </div>

            <div className="erp-form-group">
              <label className="erp-label" htmlFor="confirm-password">Confirm password</label>
              <input
                id="confirm-password"
                type="password"
                className="erp-input"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
            </div>

            {error && (
              <div style={{
                padding: "10px 12px",
                background: "var(--status-error-bg)",
                border: "1px solid var(--grey-300)",
                borderRadius: 6,
                fontSize: 13,
                color: "var(--status-error-text)",
              }}>
                {error}
              </div>
            )}

            <button type="submit" className="btn-primary" disabled={loading} style={{ justifyContent: "center", marginTop: 4 }}>
              {loading ? "Creating account…" : "Create account →"}
            </button>
          </form>

          <p style={{ marginTop: 20, textAlign: "center", fontSize: 13, color: "var(--text-secondary)" }}>
            Already have an account?{" "}
            <Link href="/login" style={{ color: "var(--accent)", fontWeight: 600, textDecoration: "none" }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
