import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ImpersonationStatus, StartImpersonationRequest } from "@/types/api";

const BASE = "/v1/iam/impersonation";

async function fetchStatus(): Promise<ImpersonationStatus> {
  const res = await fetch(BASE, { credentials: "include" });
  const data = await res.json();
  if (!data.ok) return { active: false };
  return data.data;
}

async function startImpersonation(body: StartImpersonationRequest): Promise<{ session_token: string; impersonated_user_id: string; expires_at: string }> {
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Failed to start impersonation");
  return data.data;
}

async function endImpersonation(): Promise<void> {
  const res = await fetch(BASE, { method: "DELETE", credentials: "include" });
  if (!res.ok && res.status !== 204) throw new Error("Failed to end impersonation");
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
