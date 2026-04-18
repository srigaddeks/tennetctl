"use client";

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

  const passkeys = passkeyData?.items ?? [];

  const [setupState, setSetupState] = useState<TotpSetupResponse | null>(null);
  const [verifyCode, setVerifyCode] = useState("");
  const [verified, setVerified] = useState(false);
  const [deviceName, setDeviceName] = useState("Authenticator");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const credentials = listData?.items ?? [];

  return (
    <>
      <PageHeader
        title="Security"
        description="Manage your two-factor authentication and passkey devices."
        testId="security-heading"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mx-auto w-full max-w-2xl space-y-6">

      {/* Enrolled TOTP devices */}
      <section className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            Authenticator apps
          </h2>
          <Badge tone={credentials.length > 0 ? "emerald" : "zinc"}>
            {credentials.length > 0
              ? `${credentials.length} enrolled`
              : "not enrolled"}
          </Badge>
        </div>
        {isLoading ? (
          <p className="text-xs text-zinc-400">Loading…</p>
        ) : credentials.length === 0 ? (
          <p className="text-xs text-zinc-400" data-testid="no-totp-devices">No authenticator apps enrolled.</p>
        ) : (
          <ul className="divide-y divide-zinc-100 rounded-lg border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
            {credentials.map((cred) => (
              <li key={cred.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-sm font-medium" data-testid={`totp-device-${cred.id}`}>{cred.device_name}</p>
                  <p className="text-xs text-zinc-400">
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
                    try {
                      await totpDelete.mutateAsync(cred.id);
                    } finally {
                      setDeletingId(null);
                    }
                  }}
                  className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Enroll new TOTP device */}
      <section>
        <h2 className="mb-3 text-sm font-semibold">Add authenticator app</h2>
        {verified ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950" data-testid="totp-enrolled-success">
            <p className="text-sm font-medium text-emerald-800 dark:text-emerald-200">Authenticator enrolled!</p>
            <p className="mt-1 text-xs text-emerald-700 dark:text-emerald-300">You can now sign in using your authenticator app.</p>
            <button
              type="button"
              className="mt-3 text-xs text-emerald-600 underline dark:text-emerald-400"
              onClick={() => { setSetupState(null); setVerified(false); setVerifyCode(""); setDeviceName("Authenticator"); }}
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
            <label className="flex flex-col gap-1 text-xs font-medium">
              Device name
              <input
                type="text"
                value={deviceName}
                onChange={(e) => setDeviceName(e.target.value)}
                className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
                data-testid="totp-device-name"
                placeholder="e.g. iPhone, Google Authenticator"
              />
            </label>
            {totpSetup.error ? (
              <p className="text-xs text-red-600" data-testid="totp-setup-error">{totpSetup.error.message}</p>
            ) : null}
            <button
              type="submit"
              disabled={totpSetup.isPending}
              data-testid="totp-setup-submit"
              className="rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
            >
              {totpSetup.isPending ? "Generating…" : "Set up authenticator"}
            </button>
          </form>
        ) : (
          <div className="flex flex-col gap-4 max-w-sm" data-testid="totp-qr-step">
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              Scan this QR code with your authenticator app (e.g. Google Authenticator, Authy, 1Password).
            </p>
            <div className="flex justify-center rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(setupState.otpauth_uri)}`}
                alt="TOTP QR code"
                width={200}
                height={200}
                data-testid="totp-qr-code"
              />
            </div>
            <p className="text-[11px] text-zinc-400 break-all">{setupState.otpauth_uri}</p>
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
              <label className="flex flex-col gap-1 text-xs font-medium">
                Verification code
                <input
                  type="text"
                  required
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  placeholder="000000"
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ""))}
                  className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-center text-lg font-mono tracking-[0.3em] dark:border-zinc-700 dark:bg-zinc-900"
                  data-testid="totp-verify-input"
                  autoFocus
                />
              </label>
              {totpVerify.error ? (
                <p className="text-xs text-red-600" data-testid="totp-verify-error">{totpVerify.error.message}</p>
              ) : null}
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={totpVerify.isPending || verifyCode.length < 6}
                  data-testid="totp-verify-submit"
                  className="flex-1 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
                >
                  {totpVerify.isPending ? "Verifying…" : "Verify & save"}
                </button>
                <button
                  type="button"
                  onClick={() => { setSetupState(null); setVerifyCode(""); }}
                  className="rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-600 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </section>

      {/* Passkeys section */}
      <section className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            Passkeys
          </h2>
          <Badge tone={passkeys.length > 0 ? "emerald" : "zinc"}>
            {passkeys.length > 0
              ? `${passkeys.length} registered`
              : "not set up"}
          </Badge>
        </div>
        <p className="mb-4 text-xs text-zinc-500 dark:text-zinc-400">
          Passkeys use your device&apos;s biometrics or PIN for passwordless sign-in.
        </p>
        {passkeyLoading ? (
          <p className="text-xs text-zinc-400">Loading…</p>
        ) : passkeys.length > 0 ? (
          <ul className="mb-4 divide-y divide-zinc-100 rounded-lg border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
            {passkeys.map((pk) => (
              <li key={pk.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-sm font-medium" data-testid={`passkey-device-${pk.id}`}>{pk.device_name}</p>
                  <p className="text-xs text-zinc-400">
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
                  className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        ) : null}

        {passkeyEnrolled ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950" data-testid="passkey-enrolled-success">
            <p className="text-sm font-medium text-emerald-800 dark:text-emerald-200">Passkey enrolled!</p>
            <button
              type="button"
              className="mt-2 text-xs text-emerald-600 underline dark:text-emerald-400"
              onClick={() => { setPasskeyEnrolled(false); setPasskeyDeviceName("Passkey"); setPasskeyError(null); }}
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
                // Use browser WebAuthn API
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
            <label className="flex flex-col gap-1 text-xs font-medium">
              Device name
              <input
                type="text"
                value={passkeyDeviceName}
                onChange={(e) => setPasskeyDeviceName(e.target.value)}
                className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
                data-testid="passkey-device-name"
                placeholder="e.g. MacBook Touch ID"
              />
            </label>
            {passkeyError ? (
              <p className="text-xs text-red-600" data-testid="passkey-error">{passkeyError}</p>
            ) : null}
            <button
              type="submit"
              disabled={passkeyEnrolling}
              data-testid="passkey-enroll-submit"
              className="rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
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
