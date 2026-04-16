"use client";

import { useState, useEffect, Suspense } from "react";
import { AuthPage } from "@kcontrol/ui";
import { useRouter, useSearchParams } from "next/navigation";
import { loginUser, loginWithGoogle } from "@/lib/api/auth";
import { useAccess } from "@/components/providers/AccessProvider";
import { previewInvitation } from "@/lib/api/admin";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID || "";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshAccess } = useAccess();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const returnUrl = searchParams.get("returnUrl");
  const inviteToken = searchParams.get("invite_token");
  const [inviteEmail, setInviteEmail] = useState<string | undefined>(undefined);
  const [emailLoading, setEmailLoading] = useState(!!inviteToken);

  useEffect(() => {
    if (!inviteToken) return;
    previewInvitation(inviteToken)
      .then((preview) => {
        if (preview?.email) setInviteEmail(preview.email);
      })
      .catch(() => {/* best-effort */})
      .finally(() => setEmailLoading(false));
  }, [inviteToken]);

  const handleLogin = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await loginUser(email, password);
      await refreshAccess();
      if (returnUrl) {
        // Append auto_accept=1 so the destination page knows to proceed immediately
        const separator = returnUrl.includes("?") ? "&" : "?";
        router.replace(`${returnUrl}${separator}auto_accept=1`);
      } else {
        router.replace("/dashboard");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to login. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async (idToken: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await loginWithGoogle(idToken);
      await refreshAccess();
      if (returnUrl) {
        const separator = returnUrl.includes("?") ? "&" : "?";
        router.replace(`${returnUrl}${separator}auto_accept=1`);
      } else {
        router.replace("/dashboard");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Google login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthPage
      mode="login"
      onSubmit={handleLogin}
      onGoogleLogin={handleGoogleLogin}
      googleClientId={GOOGLE_CLIENT_ID}
      isLoading={isLoading}
      error={error}
      defaultEmail={inviteEmail}
      lockEmail={!!inviteToken && !!inviteEmail}
      emailLoading={emailLoading}
    />
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  );
}
