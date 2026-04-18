import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { SamlProvider, SamlProviderCreateBody } from "@/types/api";

async function fetchProviders(): Promise<SamlProvider[]> {
  const res = await fetch("/v1/iam/saml-providers", { credentials: "include" });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Failed to load SAML providers");
  return data.data ?? [];
}

async function createProvider(body: SamlProviderCreateBody): Promise<SamlProvider> {
  const res = await fetch("/v1/iam/saml-providers", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Failed to create SAML provider");
  return data.data;
}

async function deleteProvider(id: string): Promise<void> {
  const res = await fetch(`/v1/iam/saml-providers/${id}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (res.status !== 204) {
    const data = await res.json();
    throw new Error(data.error?.message ?? "Failed to delete SAML provider");
  }
}

export function useSamlProviders() {
  return useQuery({ queryKey: ["saml-providers"], queryFn: fetchProviders });
}

export function useCreateSamlProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createProvider,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saml-providers"] }),
  });
}

export function useDeleteSamlProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteProvider,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saml-providers"] }),
  });
}
