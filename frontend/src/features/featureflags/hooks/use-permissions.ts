"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  ListResult,
  RoleFlagPermission,
  RoleFlagPermissionCreateBody,
} from "@/types/api";

const key = {
  all: ["ff", "permissions"] as const,
  list: (flagId: string | null) =>
    ["ff", "permissions", "list", flagId ?? "all"] as const,
};

export function useFlagPermissions(
  flagId: string | null
): UseQueryResult<ListResult<RoleFlagPermission>> {
  return useQuery({
    queryKey: key.list(flagId),
    queryFn: () =>
      apiList<RoleFlagPermission>(
        `/v1/flag-permissions${buildQuery({ flag_id: flagId, limit: 500 })}`
      ),
    enabled: flagId !== null,
  });
}

export function useGrantPermission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RoleFlagPermissionCreateBody) =>
      apiFetch<RoleFlagPermission>("/v1/flag-permissions", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useRevokePermission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/flag-permissions/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}
