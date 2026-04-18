"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { OidcProvider, OidcProviderCreateBody } from "@/types/api";

const QK = ["iam-security", "oidc-providers"] as const;

export function useOidcProviders() {
  return useQuery({
    queryKey: QK,
    queryFn: () =>
      apiFetch<OidcProvider[]>("/v1/iam/oidc-providers").then((r) =>
        Array.isArray(r) ? r : [],
      ),
  });
}

export function useCreateOidcProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: OidcProviderCreateBody) =>
      apiFetch<OidcProvider>("/v1/iam/oidc-providers", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}

export function useDeleteOidcProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/iam/oidc-providers/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}
