"use client";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  Checkbox,
  ErrorState,
  Skeleton,
} from "@/components/ui";
import {
  useMfaPolicy,
  useSetMfaPolicy,
} from "@/features/iam-security/hooks/use-mfa";
import { ApiClientError } from "@/lib/api";

const BREADCRUMBS = [
  { label: "Identity", href: "/iam/users" },
  { label: "Security" },
  { label: "MFA" },
];

export default function MFAPolicyPage() {
  const { data: policy, isLoading, isError, error, refetch } = useMfaPolicy();
  const set = useSetMfaPolicy();
  const { toast } = useToast();

  async function onToggle(next: boolean) {
    try {
      await set.mutateAsync(next);
      toast(
        next ? "MFA is now required for all users" : "MFA is now optional",
        "success",
      );
    } catch (e) {
      toast(e instanceof ApiClientError ? e.message : String(e), "error");
    }
  }

  return (
    <>
      <PageHeader
        title="MFA Enforcement"
        description="Require every member of this org to enroll in TOTP multi-factor authentication before signing in."
        testId="heading-iam-mfa"
        breadcrumbs={BREADCRUMBS}
      />
      <div
        className="flex-1 overflow-y-auto px-8 py-6 space-y-6"
        data-testid="iam-mfa-body"
      >
        {isLoading && <Skeleton className="h-24 w-full max-w-xl" />}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {policy && (
          <>
            <section className="max-w-xl rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-sm font-semibold">
                    Require MFA for sign-in
                  </h2>
                  <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                    {policy.required
                      ? "All users must enroll in TOTP before they can sign in."
                      : "MFA is optional — users can enroll but are not required to."}
                  </p>
                </div>
                <Badge tone={policy.required ? "emerald" : "zinc"}>
                  {policy.required ? "required" : "optional"}
                </Badge>
              </div>
              <div className="mt-4">
                <Checkbox
                  id="mfa-required"
                  label="Enforce TOTP for all members"
                  hint="Users without an enrolled authenticator will be blocked at sign-in."
                  checked={policy.required}
                  disabled={set.isPending}
                  onChange={(e) => onToggle(e.target.checked)}
                  data-testid="mfa-required-toggle"
                />
              </div>
            </section>

            <section className="max-w-xl rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
              <h2 className="text-sm font-semibold">Your TOTP status</h2>
              <div className="mt-2 flex items-center gap-2">
                <Badge tone={policy.totp_enrolled ? "emerald" : "amber"}>
                  {policy.totp_enrolled ? "enrolled" : "not enrolled"}
                </Badge>
              </div>
              {!policy.totp_enrolled && (
                <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
                  Go to Account → Security → Authenticator App to enroll a TOTP
                  device.
                </p>
              )}
              {!policy.totp_enrolled && (
                <div className="mt-3">
                  <a href="/account/security">
                    <Button variant="secondary" size="sm" type="button">
                      Open account security
                    </Button>
                  </a>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </>
  );
}
