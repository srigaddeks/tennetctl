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
  Role,
  RoleCreateBody,
  RoleUpdateBody,
} from "@/types/api";

type ListParams = {
  limit?: number;
  offset?: number;
  org_id?: string | null;
  role_type?: string | null;
  is_active?: boolean;
};

const key = {
  all: ["iam", "roles"] as const,
  list: (p?: ListParams) => ["iam", "roles", "list", p ?? {}] as const,
  one: (id: string) => ["iam", "roles", "one", id] as const,
};

export function useRoles(
  params?: ListParams
): UseQueryResult<ListResult<Role>> {
  return useQuery({
    queryKey: key.list(params),
    queryFn: () => apiList<Role>(`/v1/roles${buildQuery(params ?? {})}`),
  });
}

export function useRole(id: string | null): UseQueryResult<Role | null> {
  return useQuery({
    queryKey: key.one(id ?? ""),
    queryFn: async () => {
      if (!id) return null;
      return apiFetch<Role>(`/v1/roles/${id}`);
    },
    enabled: id !== null,
  });
}

export function useCreateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RoleCreateBody) =>
      apiFetch<Role>("/v1/roles", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key.all });
    },
  });
}

export function useUpdateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: RoleUpdateBody }) =>
      apiFetch<Role>(`/v1/roles/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: key.all });
      qc.setQueryData(key.one(data.id), data);
    },
  });
}

export function useDeleteRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/roles/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key.all });
    },
  });
}
