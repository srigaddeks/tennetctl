import { Suspense } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { SetupWizard } from "@/features/iam/_components/setup-wizard";

export const metadata = {
  title: "Initial Setup — TennetCTL",
};

export default function SetupPage() {
  return (
    <AuthShell
      title="Platform initialization"
      subtitle="No admin account found. Complete first-run setup to activate the control plane."
    >
      <Suspense fallback={null}>
        <SetupWizard />
      </Suspense>
    </AuthShell>
  );
}
