"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { AuthResponseBody } from "@/types/api";

function MagicLinkCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const qc = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setError("No token provided in link.");
      return;
    }
    apiFetch<AuthResponseBody>("/v1/auth/magic-link/consume", {
      method: "POST",
      body: JSON.stringify({ token }),
    })
      .then(() => {
        qc.invalidateQueries();
        router.replace("/");
      })
      .catch((err: Error) => {
        setError(err.message || "Invalid or expired link.");
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="max-w-sm text-center">
          <h1 className="mb-2 text-lg font-semibold" data-testid="magic-link-error-heading">
            Sign-in link invalid
          </h1>
          <p className="mb-4 text-sm text-zinc-500">{error}</p>
          <a
            href="/auth/signin"
            className="text-sm font-medium underline"
            data-testid="magic-link-back"
          >
            Back to sign in
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-sm text-zinc-500" data-testid="magic-link-loading">
        Signing you in…
      </p>
    </div>
  );
}

export default function MagicLinkCallbackPage() {
  return (
    <Suspense fallback={null}>
      <MagicLinkCallbackInner />
    </Suspense>
  );
}
