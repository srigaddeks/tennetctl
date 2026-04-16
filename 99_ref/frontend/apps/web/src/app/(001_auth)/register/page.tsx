"use client";

import { useState, useEffect } from "react";
import { AuthPage } from "@kcontrol/ui";
import { useRouter, useSearchParams } from "next/navigation";
import { registerUser, loginUser, loginWithGoogle } from "@/lib/api/auth";
import { useAccess } from "@/components/providers/AccessProvider";
import { previewInvitation } from "@/lib/api/admin";
import { Suspense } from "react";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID || "";

function RegisterContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshAccess } = useAccess();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Invite token passed from /accept-invite when the invited email has no account yet
  const inviteToken = searchParams.get("invite_token");
  const [inviteEmail, setInviteEmail] = useState<string | undefined>(undefined);
  const [emailLoading, setEmailLoading] = useState(!!inviteToken);

  // Fetch the invited email directly from the token — never rely on URL params
  useEffect(() => {
    if (!inviteToken) return;
    previewInvitation(inviteToken)
      .then((preview) => {
        if (preview?.email) setInviteEmail(preview.email);
      })
      .catch(() => {/* best-effort */})
      .finally(() => setEmailLoading(false));
  }, [inviteToken]);

  const handleRegister = async (email: string, password: string) => {
    // Client-side password length guard (backend requires ≥12)
    if (password.length < 12) {
      setError("Password must be at least 12 characters.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      await registerUser(email, password);
      // Auto-login after registration
      await loginUser(email, password);
      await refreshAccess();

      // If we came from an invite link, registration already auto-enrolled the user
      // (process_registration_invites runs on register). Go to dashboard directly.
      if (inviteToken) {
        router.replace("/dashboard");
      } else {
        router.replace("/onboarding");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to register. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async (idToken: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const tokens = await loginWithGoogle(idToken);
      await refreshAccess();
      if (inviteToken) {
        // Registration auto-enrolled the user via process_registration_invites
        router.replace("/dashboard");
      } else {
        // New user from Google → onboarding; existing → dashboard
        router.replace(tokens.user?.is_new_user ? "/onboarding" : "/dashboard");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Google sign up failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthPage
      mode="register"
      onSubmit={handleRegister}
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

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterContent />
    </Suspense>
  );
}
