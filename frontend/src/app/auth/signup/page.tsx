import { Suspense } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { SignUpForm } from "@/features/auth/_components/signup-form";

export default function SignUpPage() {
  return (
    <AuthShell
      title="Create your account"
      subtitle="Spin up your first TennetCTL workspace."
    >
      <Suspense fallback={null}>
        <SignUpForm />
      </Suspense>
    </AuthShell>
  );
}
