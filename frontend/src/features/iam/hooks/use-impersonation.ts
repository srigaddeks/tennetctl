import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { ImpersonationStatus, StartImpersonationRequest } from "@/types/api";

const BASE = "/v1/iam/impersonation";

async function fetchStatus(): Promise<ImpersonationStatus> {
  try {
    return await apiFetch<ImpersonationStatus>(BASE);
  } catch {
    return { active: false };
  }
}

async function startImpersonation(
  body: StartImpersonationRequest,
): Promise<{ session_token: string; impersonated_user_id: string; expires_at: string }> {
  return apiFetch(BASE, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

async function endImpersonation(): Promise<void> {
  return apiFetch<void>(BASE, { method: "DELETE" });
}

export function useImpersonationStatus() {
  return useQuery({
    queryKey: ["impersonation-status"],
    queryFn: fetchStatus,
    refetchInterval: 30_000,
  });
}

export function useStartImpersonation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: startImpersonation,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["impersonation-status"] }),
  });
}

export function useEndImpersonation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: endImpersonation,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["impersonation-status"] }),
  });
}
