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

function PolicySection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className="max-w-xl rounded border"
      style={{
        background: "var(--bg-surface)",
        borderColor: "var(--border)",
      }}
    >
      <div
        className="border-b px-5 py-3"
        style={{ borderColor: "var(--border)" }}
      >
        <h2
          className="label-caps text-xs"
          style={{ color: "var(--text-muted)" }}
        >
          {title}
        </h2>
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

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
        className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in space-y-5"
        data-testid="iam-mfa-body"
      >
        {isLoading && <Skeleton className="h-36 max-w-xl w-full" />}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}

        {policy && (
          <>
            {/* Enforcement section */}
            <PolicySection title="TOTP enforcement">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <p
                    className="text-xs font-medium"
                    style={{ color: "var(--text-primary)" }}
                  >
                    Require MFA for sign-in
                  </p>
                  <p
                    className="mt-1 text-xs leading-relaxed"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {policy.required
                      ? "All users must enroll in TOTP before they can sign in."
                      : "MFA is optional — users can enroll but are not required to."}
                  </p>
                </div>
                <Badge
                  tone={policy.required ? "success" : "default"}
                  dot
                >
                  {policy.required ? "required" : "optional"}
                </Badge>
              </div>

              <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--border)" }}>
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
            </PolicySection>

            {/* Enrollment status */}
            <PolicySection title="Your TOTP status">
              <div className="flex items-center justify-between">
                <div>
                  <p
                    className="text-xs font-medium"
                    style={{ color: "var(--text-primary)" }}
                  >
                    Authenticator app
                  </p>
                  {!policy.totp_enrolled && (
                    <p
                      className="mt-1 text-xs"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      Go to Account → Security → Authenticator App to enroll.
                    </p>
                  )}
                </div>
                <Badge
                  tone={policy.totp_enrolled ? "success" : "warning"}
                  dot
                >
                  {policy.totp_enrolled ? "enrolled" : "not enrolled"}
                </Badge>
              </div>

              {!policy.totp_enrolled && (
                <div className="mt-4">
                  <a href="/account/security">
                    <Button variant="secondary" size="sm" type="button">
                      Open account security
                    </Button>
                  </a>
                </div>
              )}
            </PolicySection>

            {/* Coming soon methods */}
            <PolicySection title="Additional methods (coming soon)">
              <ul className="space-y-3">
                {[
                  { label: "Passkeys (WebAuthn)", note: "Planned for v0.4.0" },
                  { label: "Hardware security keys (FIDO2)", note: "Planned for v0.4.0" },
                  { label: "SMS / email OTP as 2FA", note: "Planned for v0.5.0" },
                ].map(({ label, note }) => (
                  <li
                    key={label}
                    className="flex items-center justify-between rounded border px-3 py-2.5"
                    style={{
                      background: "var(--bg-base)",
                      borderColor: "var(--border)",
                    }}
                  >
                    <span
                      className="text-xs"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {label}
                    </span>
                    <span
                      className="label-caps text-[10px]"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {note}
                    </span>
                  </li>
                ))}
              </ul>
            </PolicySection>
          </>
        )}
      </div>
    </>
  );
}
