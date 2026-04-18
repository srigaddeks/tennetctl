"use client";

import { useMfaPolicy, useSetMfaPolicy } from "@/features/iam/hooks/use-mfa-policy";

export default function MFAPolicyPage() {
  const { data: policy, isLoading } = useMfaPolicy();
  const setMutation = useSetMfaPolicy();

  async function toggle() {
    if (!policy) return;
    try {
      await setMutation.mutateAsync(!policy.required);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">MFA Enforcement</h1>
        <p className="text-sm text-gray-500 mt-1">
          Require all org members to enroll in TOTP multi-factor authentication before signing in.
        </p>
      </div>

      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}

      {policy && (
        <div className="border rounded p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">Require MFA for sign-in</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {policy.required
                  ? "All users must enroll in TOTP before they can sign in."
                  : "MFA is optional — users can enroll but are not required to."}
              </p>
            </div>
            <button
              onClick={toggle}
              disabled={setMutation.isPending}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none disabled:opacity-50 ${
                policy.required ? "bg-blue-600" : "bg-gray-200"
              }`}
              role="switch"
              aria-checked={policy.required}
              data-testid="mfa-required-toggle"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  policy.required ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <div className="border-t pt-3 text-sm">
            <p className="text-gray-500">Your TOTP status</p>
            <p className={`font-medium mt-0.5 ${policy.totp_enrolled ? "text-green-700" : "text-amber-600"}`}>
              {policy.totp_enrolled ? "Enrolled" : "Not enrolled"}
            </p>
            {!policy.totp_enrolled && (
              <p className="text-xs text-gray-400 mt-1">
                Go to Account → Security → Authenticator App to enroll.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
