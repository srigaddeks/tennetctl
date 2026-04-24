"use client";

import Link from "next/link";
import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui";
import {
  usePasskeyDelete,
  usePasskeyList,
  usePasskeyRegisterBegin,
  usePasskeyRegisterComplete,
  useTotpDelete,
  useTotpList,
  useTotpSetup,
  useTotpVerify,
} from "@/features/auth/hooks/use-auth";
import type { TotpSetupResponse } from "@/types/api";

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-elevated)",
  border: "1px solid var(--border)",
  borderRadius: "6px",
  padding: "8px 12px",
  fontSize: "13px",
  color: "var(--text-primary)",
  outline: "none",
  transition: "border-color 0.15s, box-shadow 0.15s",
  fontFamily: "var(--font-sans)",
};

const sectionStyle: React.CSSProperties = {
  background: "var(--bg-surface)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  padding: "20px 24px",
};

const submitBtnStyle: React.CSSProperties = {
  background: "var(--accent)",
  color: "white",
  border: "none",
  borderRadius: "6px",
  padding: "8px 14px",
  fontSize: "12px",
  fontWeight: 600,
  cursor: "pointer",
  transition: "background 0.15s",
  fontFamily: "var(--font-sans)",
};

export default function SecurityPage() {
  const { data: listData, isLoading } = useTotpList();
  const totpSetup = useTotpSetup();
  const totpVerify = useTotpVerify();
  const totpDelete = useTotpDelete();

  const { data: passkeyData, isLoading: passkeyLoading } = usePasskeyList();
  const passkeyRegisterBegin = usePasskeyRegisterBegin();
  const passkeyRegisterComplete = usePasskeyRegisterComplete();
  const passkeyDelete = usePasskeyDelete();

  const [passkeyEnrolling, setPasskeyEnrolling] = useState(false);
  const [passkeyEnrolled, setPasskeyEnrolled] = useState(false);
  const [passkeyDeviceName, setPasskeyDeviceName] = useState("Passkey");
  const [passkeyDeletingId, setPasskeyDeletingId] = useState<string | null>(null);
  const [passkeyError, setPasskeyError] = useState<string | null>(null);
  const [passkeyFocused, setPasskeyFocused] = useState(false);

  const passkeys = passkeyData?.items ?? [];

  const [setupState, setSetupState] = useState<TotpSetupResponse | null>(null);
  const [verifyCode, setVerifyCode] = useState("");
  const [verified, setVerified] = useState(false);
  const [deviceName, setDeviceName] = useState("Authenticator");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [totpDeviceNameFocused, setTotpDeviceNameFocused] = useState(false);
  const [totpVerifyFocused, setTotpVerifyFocused] = useState(false);

  const credentials = listData?.items ?? [];

  // Security score
  const totpScore = credentials.length > 0 ? 40 : 0;
  const passkeyScore = passkeys.length > 0 ? 40 : 0;
  const baseScore = 20;
  const securityScore = baseScore + totpScore + passkeyScore;
  const scoreColor =
    securityScore >= 80 ? "var(--success)" :
    securityScore >= 40 ? "var(--warning)" :
    "var(--danger)";
  const scoreLabel =
    securityScore >= 80 ? "Strong" :
    securityScore >= 40 ? "Fair" :
    "Weak";

  return (
    <>
      <PageHeader
        title="Security"
        description="Manage your two-factor authentication and passkey devices."
        testId="security-heading"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in">
        <div className="mx-auto w-full max-w-2xl space-y-5">

          {/* Manage applications — admin shortcut */}
          <Link
            href="/iam/applications"
            className="block rounded-lg px-5 py-4 transition hover:opacity-90"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--accent)",
              color: "var(--text-primary)",
            }}
            data-testid="manage-applications-card"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="label-caps" style={{ color: "var(--accent)" }}>
                  Admin
                </div>
                <div className="text-base font-semibold mt-0.5">
                  Manage applications
                </div>
                <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                  tennetctl admins use this for app management.
                </p>
              </div>
              <span className="text-xl" style={{ color: "var(--accent)" }}>→</span>
            </div>
          </Link>

          {/* Security score */}
          <div
            className="rounded-lg px-5 py-4"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
            }}
          >
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="label-caps" style={{ color: "var(--text-muted)" }}>
                  Security score
                </div>
                <div
                  className="text-2xl font-bold font-mono-data mt-0.5"
                  style={{ color: scoreColor }}
                >
                  {securityScore}
                  <span className="text-sm font-normal ml-1" style={{ color: "var(--text-secondary)" }}>
                    / 100
                  </span>
                </div>
              </div>
              <Badge
                tone={securityScore >= 80 ? "emerald" : securityScore >= 40 ? "amber" : "red"}
              >
                {scoreLabel}
              </Badge>
            </div>
            <div
              className="h-2 rounded-full overflow-hidden"
              style={{ background: "var(--bg-elevated)" }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${securityScore}%`,
                  background: scoreColor,
                  boxShadow: `0 0 8px ${scoreColor}40`,
                }}
              />
            </div>
            <div className="flex gap-4 mt-3">
              <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ background: credentials.length > 0 ? "var(--success)" : "var(--text-muted)" }}
                />
                Authenticator app
              </div>
              <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ background: passkeys.length > 0 ? "var(--success)" : "var(--text-muted)" }}
                />
                Passkey
              </div>
            </div>
          </div>

          {/* TOTP enrolled devices */}
          <section style={sectionStyle}>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="label-caps mb-1" style={{ color: "var(--text-muted)" }}>
                  Two-factor authentication
                </div>
                <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  Authenticator apps
                </h2>
              </div>
              <Badge tone={credentials.length > 0 ? "emerald" : "default"} dot={credentials.length > 0}>
                {credentials.length > 0 ? `${credentials.length} enrolled` : "not enrolled"}
              </Badge>
            </div>

            {isLoading ? (
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Loading…</p>
            ) : credentials.length === 0 ? (
              <p className="text-xs" style={{ color: "var(--text-muted)" }} data-testid="no-totp-devices">
                No authenticator apps enrolled.
              </p>
            ) : (
              <ul
                className="divide-y rounded overflow-hidden"
                style={{
                  borderColor: "var(--border)",
                  border: "1px solid var(--border)",
                  marginBottom: "4px",
                }}
              >
                {credentials.map((cred) => (
                  <li
                    key={cred.id}
                    className="flex items-center justify-between px-4 py-3"
                    style={{ background: "var(--bg-elevated)" }}
                  >
                    <div>
                      <p
                        className="text-sm font-medium"
                        style={{ color: "var(--text-primary)" }}
                        data-testid={`totp-device-${cred.id}`}
                      >
                        {cred.device_name}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {cred.last_used_at
                          ? `Last used ${new Date(cred.last_used_at).toLocaleDateString()}`
                          : "Never used"}
                      </p>
                    </div>
                    <button
                      type="button"
                      data-testid={`totp-delete-${cred.id}`}
                      disabled={deletingId === cred.id}
                      onClick={async () => {
                        setDeletingId(cred.id);
                        try { await totpDelete.mutateAsync(cred.id); }
                        finally { setDeletingId(null); }
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        fontSize: "12px",
                        color: "var(--danger)",
                        cursor: deletingId === cred.id ? "not-allowed" : "pointer",
                        opacity: deletingId === cred.id ? 0.5 : 1,
                        fontFamily: "var(--font-sans)",
                      }}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Enroll TOTP */}
          <section style={sectionStyle}>
            <div className="label-caps mb-3" style={{ color: "var(--text-muted)" }}>
              Add authenticator app
            </div>
            {verified ? (
              <div
                className="flex flex-col gap-2 rounded px-4 py-3"
                style={{
                  background: "var(--success-muted)",
                  border: "1px solid var(--success)",
                }}
                data-testid="totp-enrolled-success"
              >
                <p className="text-sm font-semibold" style={{ color: "var(--success)" }}>
                  Authenticator enrolled!
                </p>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  You can now sign in using your authenticator app.
                </p>
                <button
                  type="button"
                  style={{
                    alignSelf: "flex-start",
                    background: "none",
                    border: "none",
                    padding: 0,
                    fontSize: "11px",
                    color: "var(--success)",
                    cursor: "pointer",
                    textDecoration: "underline",
                    fontFamily: "var(--font-sans)",
                  }}
                  onClick={() => {
                    setSetupState(null);
                    setVerified(false);
                    setVerifyCode("");
                    setDeviceName("Authenticator");
                  }}
                >
                  Add another device
                </button>
              </div>
            ) : !setupState ? (
              <form
                className="flex flex-col gap-3 max-w-sm"
                data-testid="totp-setup-form"
                onSubmit={async (e) => {
                  e.preventDefault();
                  const result = await totpSetup.mutateAsync({ device_name: deviceName });
                  setSetupState(result);
                }}
              >
                <div className="flex flex-col gap-1.5">
                  <label
                    className="label-caps"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Device name
                  </label>
                  <input
                    type="text"
                    value={deviceName}
                    onChange={(e) => setDeviceName(e.target.value)}
                    onFocus={() => setTotpDeviceNameFocused(true)}
                    onBlur={() => setTotpDeviceNameFocused(false)}
                    style={{
                      ...inputStyle,
                      borderColor: totpDeviceNameFocused ? "var(--accent)" : "var(--border)",
                      boxShadow: totpDeviceNameFocused ? "0 0 0 3px var(--accent-muted)" : "none",
                    }}
                    data-testid="totp-device-name"
                    placeholder="iPhone, Google Authenticator, Authy…"
                  />
                </div>
                {totpSetup.error ? (
                  <p className="text-xs" style={{ color: "var(--danger)" }} data-testid="totp-setup-error">
                    {totpSetup.error.message}
                  </p>
                ) : null}
                <button
                  type="submit"
                  disabled={totpSetup.isPending}
                  data-testid="totp-setup-submit"
                  style={{
                    ...submitBtnStyle,
                    opacity: totpSetup.isPending ? 0.6 : 1,
                    cursor: totpSetup.isPending ? "not-allowed" : "pointer",
                  }}
                >
                  {totpSetup.isPending ? "Generating…" : "Set up authenticator"}
                </button>
              </form>
            ) : (
              <div className="flex flex-col gap-4 max-w-sm" data-testid="totp-qr-step">
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Scan this QR code with your authenticator app (Google Authenticator, Authy, 1Password, etc.).
                </p>
                <div
                  className="flex justify-center rounded p-3"
                  style={{
                    background: "white",
                    border: "1px solid var(--border)",
                  }}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(setupState.otpauth_uri)}`}
                    alt="TOTP QR code"
                    width={200}
                    height={200}
                    data-testid="totp-qr-code"
                  />
                </div>
                <p
                  className="font-mono-data text-[10px] break-all px-3 py-2 rounded"
                  style={{
                    background: "var(--bg-elevated)",
                    color: "var(--text-muted)",
                    border: "1px solid var(--border)",
                  }}
                >
                  {setupState.otpauth_uri}
                </p>
                <form
                  className="flex flex-col gap-3"
                  onSubmit={async (e) => {
                    e.preventDefault();
                    await totpVerify.mutateAsync(
                      { credential_id: setupState.credential_id, code: verifyCode },
                      { onSuccess: () => setVerified(true) }
                    );
                  }}
                >
                  <div className="flex flex-col gap-1.5">
                    <label
                      className="label-caps"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Verification code
                    </label>
                    <input
                      type="text"
                      required
                      inputMode="numeric"
                      pattern="[0-9]{6}"
                      maxLength={6}
                      placeholder="000 000"
                      value={verifyCode}
                      onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ""))}
                      onFocus={() => setTotpVerifyFocused(true)}
                      onBlur={() => setTotpVerifyFocused(false)}
                      style={{
                        ...inputStyle,
                        textAlign: "center",
                        fontSize: "22px",
                        fontFamily: "var(--font-mono)",
                        letterSpacing: "0.3em",
                        borderColor: totpVerifyFocused ? "var(--accent)" : "var(--border)",
                        boxShadow: totpVerifyFocused ? "0 0 0 3px var(--accent-muted)" : "none",
                      }}
                      data-testid="totp-verify-input"
                      autoFocus
                    />
                  </div>
                  {totpVerify.error ? (
                    <p className="text-xs" style={{ color: "var(--danger)" }} data-testid="totp-verify-error">
                      {totpVerify.error.message}
                    </p>
                  ) : null}
                  <div className="flex gap-2">
                    <button
                      type="submit"
                      disabled={totpVerify.isPending || verifyCode.length < 6}
                      data-testid="totp-verify-submit"
                      style={{
                        flex: 1,
                        ...submitBtnStyle,
                        opacity: (totpVerify.isPending || verifyCode.length < 6) ? 0.5 : 1,
                        cursor: (totpVerify.isPending || verifyCode.length < 6) ? "not-allowed" : "pointer",
                      }}
                    >
                      {totpVerify.isPending ? "Verifying…" : "Verify & save"}
                    </button>
                    <button
                      type="button"
                      onClick={() => { setSetupState(null); setVerifyCode(""); }}
                      style={{
                        background: "var(--bg-elevated)",
                        border: "1px solid var(--border)",
                        borderRadius: "6px",
                        padding: "8px 14px",
                        fontSize: "12px",
                        color: "var(--text-secondary)",
                        cursor: "pointer",
                        fontFamily: "var(--font-sans)",
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}
          </section>

          {/* Passkeys section */}
          <section style={sectionStyle}>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="label-caps mb-1" style={{ color: "var(--text-muted)" }}>
                  Passwordless
                </div>
                <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  Passkeys
                </h2>
              </div>
              <Badge tone={passkeys.length > 0 ? "emerald" : "default"} dot={passkeys.length > 0}>
                {passkeys.length > 0 ? `${passkeys.length} registered` : "not set up"}
              </Badge>
            </div>
            <p className="mb-4 text-xs" style={{ color: "var(--text-secondary)" }}>
              Passkeys use your device&apos;s biometrics or PIN for passwordless sign-in. More secure than passwords.
            </p>

            {passkeyLoading ? (
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Loading…</p>
            ) : passkeys.length > 0 ? (
              <ul
                className="mb-4 rounded overflow-hidden divide-y"
                style={{ border: "1px solid var(--border)" }}
              >
                {passkeys.map((pk) => (
                  <li
                    key={pk.id}
                    className="flex items-center justify-between px-4 py-3"
                    style={{ background: "var(--bg-elevated)" }}
                  >
                    <div>
                      <p
                        className="text-sm font-medium"
                        style={{ color: "var(--text-primary)" }}
                        data-testid={`passkey-device-${pk.id}`}
                      >
                        {pk.device_name}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {pk.last_used_at
                          ? `Last used ${new Date(pk.last_used_at).toLocaleDateString()}`
                          : "Never used"}
                      </p>
                    </div>
                    <button
                      type="button"
                      data-testid={`passkey-delete-${pk.id}`}
                      disabled={passkeyDeletingId === pk.id}
                      onClick={async () => {
                        setPasskeyDeletingId(pk.id);
                        try { await passkeyDelete.mutateAsync(pk.id); }
                        finally { setPasskeyDeletingId(null); }
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        fontSize: "12px",
                        color: "var(--danger)",
                        cursor: passkeyDeletingId === pk.id ? "not-allowed" : "pointer",
                        opacity: passkeyDeletingId === pk.id ? 0.5 : 1,
                        fontFamily: "var(--font-sans)",
                      }}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}

            {passkeyEnrolled ? (
              <div
                className="flex flex-col gap-2 rounded px-4 py-3"
                style={{
                  background: "var(--success-muted)",
                  border: "1px solid var(--success)",
                }}
                data-testid="passkey-enrolled-success"
              >
                <p className="text-sm font-semibold" style={{ color: "var(--success)" }}>
                  Passkey enrolled!
                </p>
                <button
                  type="button"
                  style={{
                    alignSelf: "flex-start",
                    background: "none",
                    border: "none",
                    padding: 0,
                    fontSize: "11px",
                    color: "var(--success)",
                    cursor: "pointer",
                    textDecoration: "underline",
                    fontFamily: "var(--font-sans)",
                  }}
                  onClick={() => {
                    setPasskeyEnrolled(false);
                    setPasskeyDeviceName("Passkey");
                    setPasskeyError(null);
                  }}
                >
                  Add another passkey
                </button>
              </div>
            ) : (
              <form
                className="flex flex-col gap-3 max-w-sm"
                data-testid="passkey-enroll-form"
                onSubmit={async (e) => {
                  e.preventDefault();
                  setPasskeyError(null);
                  setPasskeyEnrolling(true);
                  try {
                    const beginResult = await passkeyRegisterBegin.mutateAsync({ device_name: passkeyDeviceName });
                    const options = JSON.parse(beginResult.options_json);
                    const credential = await (navigator.credentials as unknown as { create(opts: unknown): Promise<unknown> }).create({
                      publicKey: {
                        ...options,
                        challenge: Uint8Array.from(atob(options.challenge.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0)),
                        user: {
                          ...options.user,
                          id: Uint8Array.from(atob(options.user.id.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0)),
                        },
                        excludeCredentials: (options.excludeCredentials ?? []).map((c: { id: string; type: string }) => ({
                          ...c,
                          id: Uint8Array.from(atob(c.id.replace(/-/g, "+").replace(/_/g, "/")), (ch) => ch.charCodeAt(0)),
                        })),
                      },
                    });
                    await passkeyRegisterComplete.mutateAsync({
                      challenge_id: beginResult.challenge_id,
                      credential_json: JSON.stringify(credential),
                    });
                    setPasskeyEnrolled(true);
                  } catch (err) {
                    setPasskeyError(err instanceof Error ? err.message : "Enrollment failed.");
                  } finally {
                    setPasskeyEnrolling(false);
                  }
                }}
              >
                <div className="flex flex-col gap-1.5">
                  <label
                    className="label-caps"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Device name
                  </label>
                  <input
                    type="text"
                    value={passkeyDeviceName}
                    onChange={(e) => setPasskeyDeviceName(e.target.value)}
                    onFocus={() => setPasskeyFocused(true)}
                    onBlur={() => setPasskeyFocused(false)}
                    style={{
                      ...inputStyle,
                      borderColor: passkeyFocused ? "var(--accent)" : "var(--border)",
                      boxShadow: passkeyFocused ? "0 0 0 3px var(--accent-muted)" : "none",
                    }}
                    data-testid="passkey-device-name"
                    placeholder="MacBook Touch ID, YubiKey, iPhone…"
                  />
                </div>
                {passkeyError ? (
                  <p className="text-xs" style={{ color: "var(--danger)" }} data-testid="passkey-error">
                    {passkeyError}
                  </p>
                ) : null}
                <button
                  type="submit"
                  disabled={passkeyEnrolling}
                  data-testid="passkey-enroll-submit"
                  style={{
                    ...submitBtnStyle,
                    opacity: passkeyEnrolling ? 0.6 : 1,
                    cursor: passkeyEnrolling ? "not-allowed" : "pointer",
                  }}
                >
                  {passkeyEnrolling ? "Enrolling…" : "Add passkey"}
                </button>
              </form>
            )}
          </section>

        </div>
      </div>
    </>
  );
}
