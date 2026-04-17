"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useCreateInitialAdmin } from "@/features/iam/hooks/use-setup";
import type { InitialAdminResult } from "@/types/api";

type Step = "form" | "totp" | "done";

export function SetupWizard() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("form");
  const [result, setResult] = useState<InitialAdminResult | null>(null);
  const [savedConfirmed, setSavedConfirmed] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const createAdmin = useCreateInitialAdmin();

  async function handleFormSubmit(e: React.FormEvent) {
    e.preventDefault();
    const data = await createAdmin.mutateAsync({ email, password, display_name: displayName });
    setResult(data);
    setStep("totp");
  }

  function handleContinue() {
    router.replace("/");
    router.refresh();
  }

  if (step === "form") {
    return (
      <form
        className="flex flex-col gap-3"
        data-testid="setup-form"
        onSubmit={handleFormSubmit}
      >
        <label className="flex flex-col gap-1 text-xs font-medium">
          Display name
          <input
            type="text"
            required
            minLength={1}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            data-testid="setup-display-name"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium">
          Email
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            data-testid="setup-email"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium">
          Password (min 8 chars)
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            data-testid="setup-password"
          />
        </label>
        {createAdmin.error ? (
          <p className="text-xs text-red-600" data-testid="setup-error">
            {createAdmin.error.message}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={createAdmin.isPending}
          data-testid="setup-submit"
          className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
        >
          {createAdmin.isPending ? "Creating admin…" : "Create admin account"}
        </button>
      </form>
    );
  }

  if (step === "totp" && result !== null) {
    return (
      <div className="flex flex-col gap-4" data-testid="setup-totp-step">
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Scan this QR code with your authenticator app. This is shown{" "}
          <strong>once only</strong>.
        </p>
        {/* QR rendered client-side via otpauth URI embedded in an img tag via a QR service */}
        <img
          src={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(result.otpauth_uri)}&size=200x200`}
          alt="TOTP QR code"
          className="mx-auto rounded-lg border border-zinc-200 dark:border-zinc-700"
          data-testid="setup-totp-qr"
        />
        <p className="text-xs text-zinc-500 dark:text-zinc-400 text-center break-all" data-testid="setup-totp-uri">
          {result.otpauth_uri}
        </p>

        <div className="mt-2">
          <p className="text-sm font-medium mb-2">Backup codes (save these now):</p>
          <ul
            className="grid grid-cols-2 gap-1 rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-800"
            data-testid="setup-backup-codes"
          >
            {result.backup_codes.map((code) => (
              <li key={code} className="font-mono text-xs text-zinc-700 dark:text-zinc-300">
                {code}
              </li>
            ))}
          </ul>
        </div>

        <label className="flex items-center gap-2 text-sm" data-testid="setup-saved-label">
          <input
            type="checkbox"
            checked={savedConfirmed}
            onChange={(e) => setSavedConfirmed(e.target.checked)}
            data-testid="setup-saved-checkbox"
            className="h-4 w-4 rounded border-zinc-300 dark:border-zinc-600"
          />
          I have saved my TOTP QR code and backup codes in a secure place.
        </label>

        <button
          type="button"
          disabled={!savedConfirmed}
          onClick={handleContinue}
          data-testid="setup-continue"
          className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
        >
          Continue to dashboard
        </button>
      </div>
    );
  }

  return null;
}
