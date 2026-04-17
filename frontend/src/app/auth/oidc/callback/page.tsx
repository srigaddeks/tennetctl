"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

function OidcCallbackContent() {
  const router = useRouter();
  const params = useSearchParams();
  const error = params.get("error");

  useEffect(() => {
    if (!error) {
      const timer = setTimeout(() => router.push("/"), 800);
      return () => clearTimeout(timer);
    }
  }, [error, router]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-sm w-full border rounded-lg p-8 text-center">
          <h1 className="text-lg font-semibold text-red-600 mb-2">Sign-in failed</h1>
          <p className="text-sm text-gray-500 mb-6">
            Your SSO sign-in could not be completed. Please try again.
          </p>
          <a
            href="/auth/signin"
            className="text-sm text-blue-600 hover:underline"
          >
            Back to sign in
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
        <p className="text-sm text-gray-500">Signing you in…</p>
      </div>
    </div>
  );
}

export default function OidcCallbackPage() {
  return (
    <Suspense>
      <OidcCallbackContent />
    </Suspense>
  );
}
