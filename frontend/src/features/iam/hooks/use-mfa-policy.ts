import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { MfaPolicyStatus } from "@/types/api";

const BASE = "/v1/iam/mfa-policy";

async function fetchPolicy(): Promise<MfaPolicyStatus> {
  const res = await fetch(BASE, { credentials: "include" });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Failed to fetch MFA policy");
  return data.data;
}

async function setPolicy(required: boolean): Promise<MfaPolicyStatus> {
  const res = await fetch(BASE, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ required }),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Failed to update MFA policy");
  return data.data;
}

export function useMfaPolicy() {
  return useQuery({ queryKey: ["mfa-policy"], queryFn: fetchPolicy });
}

export function useSetMfaPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: setPolicy,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mfa-policy"] }),
  });
}
