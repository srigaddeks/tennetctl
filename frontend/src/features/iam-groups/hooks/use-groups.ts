"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  Group,
  GroupCreateBody,
  GroupUpdateBody,
  ListResult,
} from "@/types/api";

type ListParams = {
  limit?: number;
  offset?: number;
  org_id?: string | null;
  is_active?: boolean;
};

const key = {
  all: ["iam", "groups"] as const,
  list: (p?: ListParams) => ["iam", "groups", "list", p ?? {}] as const,
  one: (id: string) => ["iam", "groups", "one", id] as const,
};

export function useGroups(params?: ListParams): UseQueryResult<ListResult<Group>> {
  return useQuery({
    queryKey: key.list(params),
    queryFn: () => apiList<Group>(`/v1/groups${buildQuery(params ?? {})}`),
  });
}

export function useGroup(id: string | null): UseQueryResult<Group | null> {
  return useQuery({
    queryKey: key.one(id ?? ""),
    queryFn: async () => (id ? apiFetch<Group>(`/v1/groups/${id}`) : null),
    enabled: id !== null,
  });
}

export function useCreateGroup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: GroupCreateBody) =>
      apiFetch<Group>("/v1/groups", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useUpdateGroup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: GroupUpdateBody }) =>
      apiFetch<Group>(`/v1/groups/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: key.all });
      qc.setQueryData(key.one(data.id), data);
    },
  });
}

export function useDeleteGroup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/groups/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}
