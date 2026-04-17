"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"idle" | "consuming" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const [resendEmail, setResendEmail] = useState("");
  const [resendStatus, setResendStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");

  useEffect(() => {
    if (token) {
      setStatus("consuming");
      apiFetch("/v1/auth/verify-email/consume", {
        method: "POST",
        body: JSON.stringify({ token }),
      })
        .then(() => {
          setStatus("success");
          setMessage("Your email has been verified successfully.");
          setTimeout(() => router.push("/"), 2000);
        })
        .catch((err: unknown) => {
          setStatus("error");
          setMessage(
            err instanceof Error ? err.message : "Verification failed. The link may have expired.",
          );
        });
    }
  }, [token, router]);

  const handleResend = async () => {
    if (!resendEmail) return;
    setResendStatus("sending");
    try {
      await apiFetch("/v1/auth/verify-email/send", {
        method: "POST",
        body: JSON.stringify({ email: resendEmail }),
      });
      setResendStatus("sent");
    } catch {
      setResendStatus("error");
    }
  };

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 p-8">
      <div className="w-full max-w-md rounded-lg border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="mb-4 text-xl font-semibold">Email Verification</h1>

        {token ? (
          <div data-testid="verify-email-token-state">
            {status === "consuming" && (
              <p className="text-zinc-500">Verifying your email address…</p>
            )}
            {status === "success" && (
              <p className="text-green-600" data-testid="verify-email-success">
                {message} Redirecting…
              </p>
            )}
            {status === "error" && (
              <p className="text-red-600" data-testid="verify-email-error">
                {message}
              </p>
            )}
          </div>
        ) : (
          <div data-testid="verify-email-resend-form">
            <p className="mb-4 text-sm text-zinc-600 dark:text-zinc-400">
              Enter your email address below to receive a new verification link.
            </p>
            <div className="flex flex-col gap-3">
              <input
                type="email"
                placeholder="you@example.com"
                value={resendEmail}
                onChange={(e) => setResendEmail(e.target.value)}
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-900"
                data-testid="verify-email-input"
              />
              <button
                onClick={handleResend}
                disabled={resendStatus === "sending" || !resendEmail}
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
                data-testid="verify-email-resend-btn"
              >
                {resendStatus === "sending" ? "Sending…" : "Resend Verification Email"}
              </button>
              {resendStatus === "sent" && (
                <p className="text-sm text-green-600" data-testid="verify-email-resend-sent">
                  Verification email sent. Check your inbox.
                </p>
              )}
              {resendStatus === "error" && (
                <p className="text-sm text-red-600" data-testid="verify-email-resend-error">
                  Failed to send email. Please try again.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="flex flex-1 items-center justify-center p-8 text-sm text-zinc-500">Loading…</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
