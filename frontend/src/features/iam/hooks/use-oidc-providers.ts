"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { OidcProvider, OidcProviderCreateBody } from "@/types/api";

const keys = {
  list: () => ["iam", "oidc-providers"] as const,
};

export function useOidcProviders() {
  return useQuery({
    queryKey: keys.list(),
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
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.list() }),
  });
}

export function useDeleteOidcProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (providerId: string) =>
      fetch(`/v1/iam/oidc-providers/${providerId}`, { method: "DELETE" }).then(
        (res) => {
          if (!res.ok && res.status !== 204) throw new Error("Delete failed");
        },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.list() }),
  });
}
