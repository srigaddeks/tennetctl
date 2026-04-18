"use client";

import { useEndImpersonation, useImpersonationStatus } from "@/features/iam/hooks/use-impersonation";

export function ImpersonationBanner() {
  const { data: status } = useImpersonationStatus();
  const endMutation = useEndImpersonation();

  if (!status?.active) return null;

  const name = status.impersonated_display_name ?? status.impersonated_email ?? status.impersonated_user_id ?? "unknown";

  async function handleEnd() {
    try {
      await endMutation.mutateAsync();
      window.location.reload();
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="w-full bg-red-600 text-white text-sm flex items-center justify-between px-4 py-2" role="alert">
      <span>
        You are impersonating <strong>{name}</strong>.
        {status.session_expires_at && (
          <> Session expires at {new Date(status.session_expires_at).toLocaleTimeString()}.</>
        )}
      </span>
      <button
        onClick={handleEnd}
        disabled={endMutation.isPending}
        className="ml-4 underline font-medium hover:text-red-200 disabled:opacity-50"
        data-testid="end-impersonation-btn"
      >
        {endMutation.isPending ? "Ending…" : "End session"}
      </button>
    </div>
  );
}
