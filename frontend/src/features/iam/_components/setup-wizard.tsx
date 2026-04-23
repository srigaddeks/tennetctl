"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useCreateInitialAdmin } from "@/features/iam/hooks/use-setup";
import type { InitialAdminResult } from "@/types/api";

type Step = "form" | "totp" | "done";

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

function StepIndicator({ current }: { current: Step }) {
  const steps: { id: Step; label: string }[] = [
    { id: "form", label: "Admin account" },
    { id: "totp", label: "MFA setup" },
    { id: "done", label: "Complete" },
  ];
  const currentIdx = steps.findIndex((s) => s.id === current);

  return (
    <div className="flex items-center gap-0 mb-6">
      {steps.map((step, idx) => {
        const done = idx < currentIdx;
        const active = idx === currentIdx;
        return (
          <div key={step.id} className="flex items-center" style={{ flex: 1 }}>
            <div className="flex flex-col items-center gap-1" style={{ flex: 1 }}>
              <div
                className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold transition-all"
                style={{
                  background: done
                    ? "var(--success)"
                    : active
                    ? "var(--accent)"
                    : "var(--bg-elevated)",
                  color: done || active ? "white" : "var(--text-muted)",
                  border: `1px solid ${done ? "var(--success)" : active ? "var(--accent)" : "var(--border)"}`,
                  boxShadow: active ? "0 0 10px rgba(45,126,247,0.4)" : "none",
                }}
              >
                {done ? "✓" : idx + 1}
              </div>
              <span
                className="label-caps"
                style={{
                  color: active ? "var(--text-primary)" : done ? "var(--success)" : "var(--text-muted)",
                  fontSize: "9px",
                }}
              >
                {step.label}
              </span>
            </div>
            {idx < steps.length - 1 && (
              <div
                className="h-px flex-1 mx-1 mb-4"
                style={{
                  background: done ? "var(--success)" : "var(--border)",
                  transition: "background 0.3s",
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function SetupWizard() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("form");
  const [result, setResult] = useState<InitialAdminResult | null>(null);
  const [savedConfirmed, setSavedConfirmed] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const createAdmin = useCreateInitialAdmin();

  function fieldStyle(name: string): React.CSSProperties {
    return {
      ...inputStyle,
      borderColor: focusedField === name ? "var(--accent)" : "var(--border)",
      boxShadow: focusedField === name ? "0 0 0 3px var(--accent-muted)" : "none",
    };
  }

  async function handleFormSubmit(e: React.FormEvent) {
    e.preventDefault();
    const data = await createAdmin.mutateAsync({ email, password, display_name: displayName });
    setResult(data);
    setStep("totp");
  }

  function handleContinue() {
    router.replace("/iam/orgs?welcome=true");
    router.refresh();
  }

  if (step === "form") {
    return (
      <>
        <StepIndicator current="form" />
        <form
          className="flex flex-col gap-4"
          data-testid="setup-form"
          onSubmit={handleFormSubmit}
        >
          {/* Init sequence indicator */}
          <div
            className="flex items-center gap-2 rounded px-3 py-2 text-xs mb-1"
            style={{
              background: "var(--accent-muted)",
              border: "1px solid var(--accent-dim)",
              color: "var(--text-secondary)",
              fontFamily: "var(--font-mono)",
            }}
          >
            <span
              className="h-1.5 w-1.5 rounded-full animate-pulse"
              style={{ background: "var(--accent)", flexShrink: 0 }}
            />
            <span>INIT — No admin account found. Creating first operator.</span>
          </div>

          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="setup-display-name"
              className="label-caps"
              style={{ color: "var(--text-secondary)" }}
            >
              Display name
            </label>
            <input
              id="setup-display-name"
              type="text"
              required
              minLength={1}
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              onFocus={() => setFocusedField("displayName")}
              onBlur={() => setFocusedField(null)}
              style={fieldStyle("displayName")}
              placeholder="Platform Admin"
              data-testid="setup-display-name"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="setup-email"
              className="label-caps"
              style={{ color: "var(--text-secondary)" }}
            >
              Email address
            </label>
            <input
              id="setup-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onFocus={() => setFocusedField("email")}
              onBlur={() => setFocusedField(null)}
              style={fieldStyle("email")}
              placeholder="admin@company.com"
              data-testid="setup-email"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="setup-password"
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
              id="setup-password"
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
              data-testid="setup-password"
            />
          </div>

          {createAdmin.error ? (
            <div
              className="flex items-center gap-2 rounded px-3 py-2 text-xs"
              style={{
                background: "var(--danger-muted)",
                border: "1px solid var(--danger)",
                color: "var(--danger)",
              }}
              data-testid="setup-error"
            >
              <span>⚠</span>
              {createAdmin.error.message}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={createAdmin.isPending}
            data-testid="setup-submit"
            style={{
              marginTop: "4px",
              background: createAdmin.isPending ? "var(--accent-dim)" : "var(--accent)",
              color: "white",
              border: "none",
              borderRadius: "6px",
              padding: "10px 16px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: createAdmin.isPending ? "not-allowed" : "pointer",
              opacity: createAdmin.isPending ? 0.7 : 1,
              transition: "background 0.15s, opacity 0.15s",
              fontFamily: "var(--font-sans)",
              letterSpacing: "0.01em",
            }}
          >
            {createAdmin.isPending ? "Creating admin…" : "Create admin account"}
          </button>
        </form>
      </>
    );
  }

  if (step === "totp" && result !== null) {
    return (
      <>
        <StepIndicator current="totp" />
        <div className="flex flex-col gap-4" data-testid="setup-totp-step">
          {/* Critical notice */}
          <div
            className="flex items-start gap-2 rounded px-3 py-2.5 text-xs"
            style={{
              background: "var(--warning-muted)",
              border: "1px solid var(--warning)",
            }}
          >
            <span style={{ color: "var(--warning)", flexShrink: 0 }}>⚠</span>
            <div>
              <span className="font-semibold" style={{ color: "var(--warning)" }}>
                Shown once only.{" "}
              </span>
              <span style={{ color: "var(--text-secondary)" }}>
                Scan this QR code with your authenticator app and save your backup codes before continuing.
              </span>
            </div>
          </div>

          {/* QR code */}
          <div
            className="flex justify-center rounded p-3"
            style={{ background: "white", border: "1px solid var(--border)" }}
          >
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(result.otpauth_uri)}&size=200x200`}
              alt="TOTP QR code"
              width={200}
              height={200}
              style={{ display: "block" }}
              data-testid="setup-totp-qr"
            />
          </div>

          <p
            className="font-mono-data text-[10px] break-all px-3 py-2 rounded text-center"
            style={{
              background: "var(--bg-elevated)",
              color: "var(--text-muted)",
              border: "1px solid var(--border)",
            }}
            data-testid="setup-totp-uri"
          >
            {result.otpauth_uri}
          </p>

          {/* Backup codes */}
          <div>
            <div
              className="label-caps mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              Backup codes — save these now
            </div>
            <ul
              className="grid grid-cols-2 gap-1.5 rounded p-3"
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--border-bright)",
              }}
              data-testid="setup-backup-codes"
            >
              {result.backup_codes.map((code) => (
                <li
                  key={code}
                  className="font-mono-data text-xs px-2 py-1 rounded text-center"
                  style={{
                    background: "var(--bg-surface)",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border)",
                    letterSpacing: "0.08em",
                  }}
                >
                  {code}
                </li>
              ))}
            </ul>
          </div>

          {/* Confirmation checkbox */}
          <label
            className="flex items-start gap-3 rounded px-3 py-2.5 cursor-pointer"
            style={{
              background: savedConfirmed ? "var(--success-muted)" : "var(--bg-elevated)",
              border: `1px solid ${savedConfirmed ? "var(--success)" : "var(--border)"}`,
              transition: "background 0.15s, border-color 0.15s",
            }}
            data-testid="setup-saved-label"
          >
            <input
              type="checkbox"
              checked={savedConfirmed}
              onChange={(e) => setSavedConfirmed(e.target.checked)}
              data-testid="setup-saved-checkbox"
              style={{ marginTop: "2px", accentColor: "var(--success)" }}
            />
            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
              I have saved my TOTP QR code and backup codes in a secure password manager or vault.
            </span>
          </label>

          <button
            type="button"
            disabled={!savedConfirmed}
            onClick={handleContinue}
            data-testid="setup-continue"
            style={{
              background: savedConfirmed ? "var(--accent)" : "var(--accent-dim)",
              color: "white",
              border: "none",
              borderRadius: "6px",
              padding: "10px 16px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: savedConfirmed ? "pointer" : "not-allowed",
              opacity: savedConfirmed ? 1 : 0.5,
              transition: "background 0.15s, opacity 0.15s",
              fontFamily: "var(--font-sans)",
              letterSpacing: "0.01em",
            }}
          >
            Continue to dashboard →
          </button>
        </div>
      </>
    );
  }

  return null;
}
