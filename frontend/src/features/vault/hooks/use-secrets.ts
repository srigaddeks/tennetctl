"use client";

/**
 * Vault — TanStack Query hooks.
 *
 * Reveal-once policy (ADR-028): the mutation hooks NEVER cache the raw plaintext
 * user entered. The server response to POST /v1/vault is metadata-only. The UI
 * layer (create/rotate dialogs) holds the just-entered value in a ref and hands
 * it to the reveal-once dialog, which unmounts the value on dismiss.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList } from "@/lib/api";
import type {
  ListResult,
  VaultSecretCreateBody,
  VaultSecretMeta,
  VaultSecretRotateBody,
} from "@/types/api";

const key = {
  all: ["vault", "secrets"] as const,
  list: () => ["vault", "secrets", "list"] as const,
};

export function useSecrets(): UseQueryResult<ListResult<VaultSecretMeta>> {
  return useQuery({
    queryKey: key.list(),
    queryFn: () => apiList<VaultSecretMeta>("/v1/vault?limit=200"),
  });
}

export function useCreateSecret() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: VaultSecretCreateBody) =>
      apiFetch<VaultSecretMeta>("/v1/vault", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useRotateSecret(secretKey: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: VaultSecretRotateBody) =>
      apiFetch<VaultSecretMeta>(
        `/v1/vault/${encodeURIComponent(secretKey)}/rotate`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useDeleteSecret(secretKey: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<void>(`/v1/vault/${encodeURIComponent(secretKey)}`, {
        method: "DELETE",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}
