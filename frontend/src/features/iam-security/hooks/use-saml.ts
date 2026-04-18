"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { SamlProvider, SamlProviderCreateBody } from "@/types/api";

const QK = ["iam-security", "saml-providers"] as const;

export function useSamlProviders() {
  return useQuery({
    queryKey: QK,
    queryFn: () =>
      apiFetch<SamlProvider[]>("/v1/iam/saml-providers").then((r) =>
        Array.isArray(r) ? r : [],
      ),
  });
}

export function useCreateSamlProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SamlProviderCreateBody) =>
      apiFetch<SamlProvider>("/v1/iam/saml-providers", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}

export function useDeleteSamlProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/iam/saml-providers/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}
