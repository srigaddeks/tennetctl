import { Suspense } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { SetupWizard } from "@/features/iam/_components/setup-wizard";

export const metadata = {
  title: "Initial Setup — TennetCTL",
};

export default function SetupPage() {
  return (
    <AuthShell
      title="First-run setup"
      subtitle="Create the initial platform admin account. MFA is mandatory."
    >
      <Suspense fallback={null}>
        <SetupWizard />
      </Suspense>
    </AuthShell>
  );
}
