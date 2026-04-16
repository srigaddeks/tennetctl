"use client";

/**
 * Vault secrets — TanStack Query hooks.
 *
 * Reveal-once policy (ADR-028): the mutation hooks NEVER cache the raw plaintext
 * user entered. POST/rotate responses are metadata-only. The UI create/rotate
 * dialogs hold the just-entered value in a ref and hand it to the reveal-once
 * dialog, then clear the ref.
 *
 * Scope (plan 07-03): every mutation identifies the secret by
 * (scope, org_id, workspace_id, key). Rotate + Delete pass these as query params.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  ListResult,
  VaultScope,
  VaultSecretCreateBody,
  VaultSecretMeta,
  VaultSecretRotateBody,
} from "@/types/api";

type ListParams = {
  limit?: number;
  scope?: VaultScope | null;
  org_id?: string | null;
  workspace_id?: string | null;
};

export type SecretIdentity = {
  key: string;
  scope: VaultScope;
  org_id: string | null;
  workspace_id: string | null;
};

const key = {
  all: ["vault", "secrets"] as const,
  list: (p?: ListParams) => ["vault", "secrets", "list", p ?? {}] as const,
};

export function useSecrets(
  params?: ListParams,
): UseQueryResult<ListResult<VaultSecretMeta>> {
  return useQuery({
    queryKey: key.list(params),
    queryFn: () =>
      apiList<VaultSecretMeta>(
        `/v1/vault${buildQuery({ limit: 200, ...(params ?? {}) })}`,
      ),
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

function identityQuery(id: SecretIdentity): string {
  return buildQuery({
    scope: id.scope,
    org_id: id.org_id,
    workspace_id: id.workspace_id,
  });
}

export function useRotateSecret(id: SecretIdentity) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: VaultSecretRotateBody) =>
      apiFetch<VaultSecretMeta>(
        `/v1/vault/${encodeURIComponent(id.key)}/rotate${identityQuery(id)}`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useDeleteSecret(id: SecretIdentity) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<void>(
        `/v1/vault/${encodeURIComponent(id.key)}${identityQuery(id)}`,
        { method: "DELETE" },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}
