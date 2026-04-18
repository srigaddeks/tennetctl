"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { ScimToken, ScimTokenCreateBody } from "@/types/api";

const QK = ["iam-security", "scim-tokens"] as const;

export function useScimTokens() {
  return useQuery({
    queryKey: QK,
    queryFn: () =>
      apiFetch<ScimToken[]>("/v1/iam/scim-tokens").then((r) =>
        Array.isArray(r) ? r : [],
      ),
  });
}

export function useCreateScimToken() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ScimTokenCreateBody) =>
      apiFetch<ScimToken & { token: string }>("/v1/iam/scim-tokens", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}

export function useRevokeScimToken() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/iam/scim-tokens/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}
