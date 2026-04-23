import { Suspense } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { SignUpForm } from "@/features/auth/_components/signup-form";

export default function SignUpPage() {
  return (
    <AuthShell
      title="Create your account"
      subtitle="Join TennetCTL — your unified developer operations platform."
    >
      <Suspense fallback={null}>
        <SignUpForm />
      </Suspense>
    </AuthShell>
  );
}
