import { Suspense } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { SignInForm } from "@/features/auth/_components/signin-form";

export default function SignInPage() {
  return (
    <AuthShell title="Sign in" subtitle="Welcome back to TennetCTL.">
      <Suspense fallback={null}>
        <SignInForm />
      </Suspense>
    </AuthShell>
  );
}
