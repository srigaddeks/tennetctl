"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { MfaPolicyStatus } from "@/types/api";

const QK = ["iam-security", "mfa-policy"] as const;

export function useMfaPolicy() {
  return useQuery({
    queryKey: QK,
    queryFn: () => apiFetch<MfaPolicyStatus>("/v1/iam/mfa-policy"),
  });
}

export function useSetMfaPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (required: boolean) =>
      apiFetch<MfaPolicyStatus>("/v1/iam/mfa-policy", {
        method: "PUT",
        body: JSON.stringify({ required }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}
